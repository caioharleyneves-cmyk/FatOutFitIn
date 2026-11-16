package br.ime.fatoutfitin.service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.SecureRandom;
import java.util.HexFormat;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.exceptions.JWTVerificationException;

import br.ime.fatoutfitin.exception.ApiException;

@Service
public class AuthService {
    private final JWTVerifier verifier;

    public AuthService(@Value("${fatoutfitin.arquivo-chave:../.local/auth-secret}") String arquivo)
            throws IOException, InterruptedException {
        String chave = System.getenv("FOFI_AUTH_SECRET");
        if (chave == null) chave = carregarChave(Path.of(arquivo));
        if (chave.getBytes(StandardCharsets.UTF_8).length < 32) {
            throw new IllegalStateException("FOFI_AUTH_SECRET precisa ter pelo menos 32 bytes.");
        }
        verifier = JWT.require(Algorithm.HMAC256(chave))
                .withIssuer("fatoutfitin-api-python").withAudience("fatoutfitin")
                .withClaimPresence("sub").withClaimPresence("exp").withClaimPresence("iat")
                .build();
    }

    private static String carregarChave(Path arquivo) throws IOException, InterruptedException {
        arquivo = arquivo.toAbsolutePath();
        Files.createDirectories(arquivo.getParent());
        Path lock = arquivo.resolveSibling(arquivo.getFileName() + ".lock");
        for (int tentativa = 0; ; tentativa++) {
            try {
                Files.createDirectory(lock);
                break;
            } catch (FileAlreadyExistsException e) {
                if (tentativa == 99) throw new IOException("Não foi possível obter o bloqueio da chave de sessão.", e);
                Thread.sleep(50);
            }
        }
        try {
            if (!Files.exists(arquivo)) {
                byte[] bytes = new byte[32];
                new SecureRandom().nextBytes(bytes);
                Path temporario = arquivo.resolveSibling(arquivo.getFileName() + ".tmp");
                Files.writeString(temporario, HexFormat.of().formatHex(bytes), StandardCharsets.UTF_8);
                Files.move(temporario, arquivo);
            }
            return Files.readString(arquivo, StandardCharsets.UTF_8).trim();
        } finally {
            Files.delete(lock);
        }
    }

    public Long usuarioId(String authorization) {
        if (authorization == null || !authorization.regionMatches(true, 0, "Bearer ", 0, 7)) {
            throw semSessao();
        }
        try {
            long id = Long.parseLong(verifier.verify(authorization.substring(7).trim()).getSubject());
            if (id <= 0) throw semSessao();
            return id;
        } catch (JWTVerificationException | NumberFormatException e) {
            throw semSessao();
        }
    }

    private ApiException semSessao() {
        return new ApiException(HttpStatus.UNAUTHORIZED,
                "Sessão ausente, inválida ou expirada. Faça login novamente.");
    }
}
