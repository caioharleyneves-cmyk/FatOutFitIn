package br.ime.fatoutfitin.service;

import java.io.IOException;
import java.nio.file.*;
import java.text.Normalizer;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import br.ime.fatoutfitin.exception.ApiException;

/** Opções conhecidas e preferências persistentes, isoladas por usuário. */
@Service
public class CatalogoService {
    public record Personalizado(Long usuarioId, String tipo, String nome) {}
    public record ExercicioOpcao(String nome, String grupo) {}
    private final ObjectMapper mapper = new ObjectMapper();
    private final Path arquivo;
    private final List<Personalizado> personalizados;
    private static final List<String> GRUPOS = List.of("Peito", "Dorsal", "Trapézio", "Ombros", "Bíceps",
            "Tríceps", "Antebraços", "Abdômen", "Quadríceps", "Posterior de coxa", "Glúteos", "Panturrilhas");
    private static final List<ExercicioOpcao> EXERCICIOS = List.of(
            new ExercicioOpcao("Supino reto", "Peito"), new ExercicioOpcao("Supino inclinado", "Peito"),
            new ExercicioOpcao("Crucifixo", "Peito"), new ExercicioOpcao("Crossover", "Peito"),
            new ExercicioOpcao("Flexão de braços", "Peito"),
            new ExercicioOpcao("Puxada frontal", "Dorsal"), new ExercicioOpcao("Remada curvada", "Dorsal"),
            new ExercicioOpcao("Remada baixa", "Dorsal"), new ExercicioOpcao("Barra fixa", "Dorsal"),
            new ExercicioOpcao("Encolhimento", "Trapézio"), new ExercicioOpcao("Desenvolvimento", "Ombros"),
            new ExercicioOpcao("Elevação lateral", "Ombros"), new ExercicioOpcao("Elevação frontal", "Ombros"),
            new ExercicioOpcao("Rosca direta", "Bíceps"), new ExercicioOpcao("Rosca alternada", "Bíceps"),
            new ExercicioOpcao("Rosca martelo", "Bíceps"), new ExercicioOpcao("Tríceps na polia", "Tríceps"),
            new ExercicioOpcao("Tríceps testa", "Tríceps"), new ExercicioOpcao("Tríceps francês", "Tríceps"),
            new ExercicioOpcao("Rosca de punho", "Antebraços"), new ExercicioOpcao("Abdominal", "Abdômen"),
            new ExercicioOpcao("Prancha", "Abdômen"), new ExercicioOpcao("Agachamento livre", "Quadríceps"),
            new ExercicioOpcao("Leg press", "Quadríceps"), new ExercicioOpcao("Cadeira extensora", "Quadríceps"),
            new ExercicioOpcao("Afundo", "Quadríceps"), new ExercicioOpcao("Mesa flexora", "Posterior de coxa"),
            new ExercicioOpcao("Stiff", "Posterior de coxa"), new ExercicioOpcao("Levantamento terra", "Posterior de coxa"),
            new ExercicioOpcao("Elevação pélvica", "Glúteos"), new ExercicioOpcao("Cadeira abdutora", "Glúteos"),
            new ExercicioOpcao("Panturrilha em pé", "Panturrilhas"), new ExercicioOpcao("Panturrilha sentada", "Panturrilhas"));

    public CatalogoService(@Value("${fatoutfitin.arquivo-catalogo:data/catalogo-personalizado.json}") String caminho) throws IOException {
        arquivo = Path.of(caminho).toAbsolutePath();
        personalizados = Files.exists(arquivo)
                ? mapper.readValue(arquivo.toFile(), new TypeReference<ArrayList<Personalizado>>() {})
                : new ArrayList<>();
    }

    public synchronized Map<String,Object> listar(Long usuario) {
        List<String> gruposUsuario = pessoais(usuario, "grupo");
        List<String> exerciciosUsuario = pessoais(usuario, "exercicio");
        List<String> grupos = new ArrayList<>(GRUPOS);
        grupos.addAll(gruposUsuario);
        List<ExercicioOpcao> exercicios = new ArrayList<>(EXERCICIOS);
        exerciciosUsuario.forEach(nome -> exercicios.add(new ExercicioOpcao(nome, "Meus exercícios")));
        Map<String,Object> resposta = new LinkedHashMap<>();
        resposta.put("grupos", grupos);
        resposta.put("exercicios", exercicios);
        resposta.put("tecnicas", List.of("Drop set", "Rest-pause", "Bi-set", "Tri-set", "Super-set",
                "Pirâmide", "Isometria", "Repetições parciais"));
        resposta.put("tiposCardio", List.of("Caminhada", "Corrida", "Bicicleta", "Elíptico", "Escada", "Remo", "Pular corda", "Natação"));
        resposta.put("personalizados", Map.of("grupos", gruposUsuario, "exercicios", exerciciosUsuario));
        return resposta;
    }

    private List<String> pessoais(Long usuario, String tipo) {
        return personalizados.stream().filter(p -> p.usuarioId().equals(usuario) && p.tipo().equals(tipo))
                .map(Personalizado::nome).toList();
    }

    private String normalizar(String nome) {
        return Normalizer.normalize(nome, Normalizer.Form.NFD).replaceAll("\\p{M}", "").toLowerCase(Locale.ROOT);
    }

    public synchronized Map<String,Object> adicionar(Long usuario, String tipo, String nome) throws IOException {
        if (tipo == null || !List.of("grupo", "exercicio").contains(tipo))
            throw ApiException.badRequest("Tipo inválido. Use grupo ou exercicio.");
        int limite = tipo.equals("grupo") ? 40 : 120;
        if (nome == null || nome.isBlank() || nome.length() > limite)
            throw ApiException.badRequest("Informe um nome de 1 a " + limite + " caracteres.");
        nome = nome.strip().replaceAll("\\s+", " ");
        String chave = normalizar(nome);
        boolean existe = tipo.equals("grupo")
                ? GRUPOS.stream().anyMatch(n -> normalizar(n).equals(chave))
                : EXERCICIOS.stream().anyMatch(n -> normalizar(n.nome()).equals(chave));
        existe |= pessoais(usuario, tipo).stream().anyMatch(n -> normalizar(n).equals(chave));
        if (existe) return listar(usuario);
        if (pessoais(usuario, tipo).size() >= 100)
            throw ApiException.badRequest("Limite de 100 opções personalizadas por categoria.");
        List<Personalizado> proximo = new ArrayList<>(personalizados);
        proximo.add(new Personalizado(usuario, tipo, nome));
        Files.createDirectories(arquivo.getParent());
        Path temporario = Files.createTempFile(arquivo.getParent(), "catalogo-", ".tmp");
        try {
            mapper.writerWithDefaultPrettyPrinter().writeValue(temporario.toFile(), proximo);
            try {
                Files.move(temporario, arquivo, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            } catch (AtomicMoveNotSupportedException e) {
                Files.move(temporario, arquivo, StandardCopyOption.REPLACE_EXISTING);
            }
            personalizados.clear();
            personalizados.addAll(proximo);
        } finally {
            Files.deleteIfExists(temporario);
        }
        return listar(usuario);
    }
}
