package br.ime.fatoutfitin.repository;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicLong;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Repository;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import br.ime.fatoutfitin.model.Treino;
import jakarta.annotation.PostConstruct;

/**
 * Guarda os treinos em memória e salva tudo num arquivo JSON a cada alteração,
 * para que os dados sobrevivam a reinícios da API.
 */
@Repository
public class TreinoRepository {

    private static final Logger log = LoggerFactory.getLogger(TreinoRepository.class);

    private final Path arquivo;
    private final ObjectMapper mapper = new ObjectMapper().enable(SerializationFeature.INDENT_OUTPUT);
    private final List<Treino> treinos = new ArrayList<>();
    private final AtomicLong sequencia = new AtomicLong(0);

    public TreinoRepository(@Value("${fatoutfitin.arquivo-dados}") String caminho) {
        this.arquivo = Path.of(caminho);
    }

    @PostConstruct
    void carregar() {
        if (!Files.exists(arquivo)) {
            return;
        }
        try {
            List<Treino> salvos = mapper.readValue(arquivo.toFile(), new TypeReference<List<Treino>>() {});
            treinos.addAll(salvos);
            long maiorId = salvos.stream().mapToLong(Treino::getId).max().orElse(0);
            sequencia.set(maiorId);
            log.info("{} treino(s) carregado(s) de {}", salvos.size(), arquivo.toAbsolutePath());
        } catch (IOException e) {
            log.warn("Não foi possível ler {}: {}. Começando com lista vazia.", arquivo, e.getMessage());
        }
    }

    private void persistir() {
        try {
            if (arquivo.getParent() != null) {
                Files.createDirectories(arquivo.getParent());
            }
            mapper.writeValue(arquivo.toFile(), treinos);
        } catch (IOException e) {
            log.error("Falha ao salvar treinos em {}", arquivo, e);
        }
    }

    public synchronized List<Treino> listarPorUsuario(Long usuarioId) {
        return treinos.stream().filter(t -> t.getUsuarioId().equals(usuarioId)).toList();
    }

    public synchronized Optional<Treino> buscar(Long id, Long usuarioId) {
        return treinos.stream()
                .filter(t -> t.getId().equals(id) && t.getUsuarioId().equals(usuarioId))
                .findFirst();
    }

    public synchronized Treino salvar(Treino treino) {
        if (treino.getId() == null) {
            treino.setId(sequencia.incrementAndGet());
            treinos.add(treino);
        } else {
            treinos.replaceAll(t -> t.getId().equals(treino.getId()) ? treino : t);
        }
        persistir();
        return treino;
    }

    public synchronized void excluir(Long id) {
        treinos.removeIf(t -> t.getId().equals(id));
        persistir();
    }
}
