package br.ime.fatoutfitin.service;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.LinkedHashSet;

import org.springframework.stereotype.Service;

import br.ime.fatoutfitin.exception.ApiException;
import br.ime.fatoutfitin.model.Exercicio;
import br.ime.fatoutfitin.model.Treino;
import br.ime.fatoutfitin.repository.TreinoRepository;

@Service
public class TreinoService {

    public static final List<String> DIAS = List.of("seg", "ter", "qua", "qui", "sex", "sab", "dom");
    public static final List<String> CORES =
            List.of("padrao", "vermelho", "laranja", "amarelo", "verde", "azul", "roxo", "rosa");

    private final TreinoRepository repository;

    public TreinoService(TreinoRepository repository) {
        this.repository = repository;
    }

    public List<Treino> listar(Long usuarioId, String dia) {
        if (dia != null && !dia.isBlank() && !DIAS.contains(dia)) {
            throw ApiException.badRequest("Filtro 'dia' inválido. Use um destes: " + String.join(", ", DIAS) + ".");
        }
        return repository.listarPorUsuario(usuarioId).stream()
                .filter(t -> dia == null || dia.isBlank() || t.getDia().equals(dia))
                .sorted(Comparator.comparing(Treino::isFixado).reversed()
                        .thenComparing(Treino::getId, Comparator.reverseOrder()))
                .toList();
    }

    public Treino buscar(Long id, Long usuarioId) {
        return repository.buscar(id, usuarioId)
                .orElseThrow(() -> ApiException.notFound("Treino " + id + " não encontrado."));
    }

    public Treino criar(Treino dados, Long usuarioId) {
        validar(dados);
        dados.setId(null);
        dados.setUsuarioId(usuarioId);
        return repository.salvar(dados);
    }

    public Treino atualizar(Long id, Treino dados, Long usuarioId) {
        buscar(id, usuarioId);
        validar(dados);
        dados.setId(id);
        dados.setUsuarioId(usuarioId);
        return repository.salvar(dados);
    }

    /** Marca/desmarca um exercício como concluído (checklist do card). */
    public Treino alternarExercicio(Long id, int indice, Long usuarioId) {
        Treino treino = buscar(id, usuarioId);
        if (indice < 0 || indice >= treino.getExercicios().size()) {
            throw ApiException.notFound("Exercício " + indice + " não existe no treino " + id + ".");
        }
        Exercicio ex = treino.getExercicios().get(indice);
        ex.setFeito(!ex.isFeito());
        return repository.salvar(treino);
    }

    public void excluir(Long id, Long usuarioId) {
        buscar(id, usuarioId);
        repository.excluir(id);
    }

    public Treino buscarCardio(Long id, Long usuarioId) {
        Treino t = buscar(id, usuarioId);
        if (!"cardio".equals(t.getModalidade())) throw ApiException.notFound("Cardio não encontrado.");
        return t;
    }

    public Treino concluirCardio(Long id, Long usuarioId) {
        Treino t = buscarCardio(id, usuarioId);
        t.setConcluido(!t.isConcluido());
        return repository.salvar(t);
    }

    /** Resumo da semana: treinos, exercícios, séries e progresso por dia. */
    public Map<String, Object> resumo(Long usuarioId) {
        List<Treino> todos = repository.listarPorUsuario(usuarioId);
        List<Map<String, Object>> dias = new ArrayList<>();
        int totalExercicios = 0;
        int totalFeitos = 0;
        int totalMinutos = 0;
        int totalCardios = (int) todos.stream().filter(t -> "cardio".equals(t.getModalidade())).count();
        int cardiosFeitos = (int) todos.stream().filter(t -> "cardio".equals(t.getModalidade()) && t.isConcluido()).count();

        for (String dia : DIAS) {
            List<Treino> doDia = todos.stream().filter(t -> t.getDia().equals(dia)).toList();
            int exercicios = doDia.stream().mapToInt(t -> t.getExercicios().size()).sum();
            int feitos = (int) doDia.stream().flatMap(t -> t.getExercicios().stream()).filter(Exercicio::isFeito).count();
            int series = doDia.stream().flatMap(t -> t.getExercicios().stream())
                    .mapToInt(e -> e.getSeries() == null ? 0 : e.getSeries()).sum();
            int minutos = doDia.stream().mapToInt(t -> t.getDuracaoMin() == null ? 0 : t.getDuracaoMin()).sum();

            Map<String, Object> d = new LinkedHashMap<>();
            d.put("dia", dia);
            d.put("treinos", doDia.size());
            d.put("cardios", doDia.stream().filter(t -> "cardio".equals(t.getModalidade())).count());
            d.put("grupos", doDia.stream().flatMap(t -> t.getGruposMusculares().isEmpty()
                    ? (t.getGrupoMuscular() == null || t.getGrupoMuscular().isBlank()
                        ? List.<String>of() : List.of(t.getGrupoMuscular())).stream()
                    : t.getGruposMusculares().stream()).distinct().toList());
            d.put("exercicios", exercicios);
            d.put("series", series);
            d.put("minutos", minutos);
            int cardiosDia = (int) doDia.stream().filter(t -> "cardio".equals(t.getModalidade())).count();
            int cardiosFeitosDia = (int) doDia.stream().filter(t -> "cardio".equals(t.getModalidade()) && t.isConcluido()).count();
            d.put("progresso", exercicios + cardiosDia == 0 ? 0 : Math.round((feitos + cardiosFeitosDia) * 100.0 / (exercicios + cardiosDia)));
            dias.add(d);

            totalExercicios += exercicios;
            totalFeitos += feitos;
            totalMinutos += minutos;
        }

        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("dias", dias);
        resposta.put("totalTreinos", todos.size());
        resposta.put("totalMusculacao", todos.size() - totalCardios);
        resposta.put("totalCardios", totalCardios);
        resposta.put("cardiosConcluidos", cardiosFeitos);
        resposta.put("minutosCardio", todos.stream().filter(t -> "cardio".equals(t.getModalidade()))
                .mapToInt(t -> t.getDuracaoMin() == null ? 0 : t.getDuracaoMin()).sum());
        resposta.put("totalExercicios", totalExercicios);
        resposta.put("totalMinutos", totalMinutos);
        resposta.put("diasDeDescanso", dias.stream().filter(d -> (int) d.get("treinos") == 0).count());
        resposta.put("progressoSemana", totalExercicios + totalCardios == 0 ? 0
                : Math.round((totalFeitos + cardiosFeitos) * 100.0 / (totalExercicios + totalCardios)));
        return resposta;
    }

    private void validar(Treino t) {
        if (t.getModalidade() == null) t.setModalidade("musculacao");
        if (!List.of("musculacao", "cardio").contains(t.getModalidade())) {
            throw ApiException.badRequest("Modalidade inválida. Use musculacao ou cardio.");
        }
        if (t.getTitulo() == null || t.getTitulo().isBlank()) {
            throw ApiException.badRequest("O campo 'titulo' é obrigatório.");
        }
        t.setTitulo(t.getTitulo().trim());
        if (t.getTitulo().length() > 80) {
            throw ApiException.badRequest("O 'titulo' deve ter no máximo 80 caracteres.");
        }
        if (t.getDia() == null || !DIAS.contains(t.getDia())) {
            throw ApiException.badRequest("'dia' inválido. Use um destes: " + String.join(", ", DIAS) + ".");
        }
        if (t.getCor() == null || t.getCor().isBlank()) {
            t.setCor("padrao");
        }
        if (!CORES.contains(t.getCor())) {
            throw ApiException.badRequest("'cor' inválida. Use uma destas: " + String.join(", ", CORES) + ".");
        }
        if (t.getDuracaoMin() != null && (t.getDuracaoMin() < 0 || t.getDuracaoMin() > 600)) {
            throw ApiException.badRequest("'duracaoMin' deve estar entre 0 e 600.");
        }
        if ("cardio".equals(t.getModalidade())) {
            if (t.getTipoCardio() == null || t.getTipoCardio().isBlank() || t.getTipoCardio().length() > 80)
                throw ApiException.badRequest("Informe a atividade de cardio, com até 80 caracteres.");
            if (t.getDuracaoMin() == null || t.getDuracaoMin() < 1)
                throw ApiException.badRequest("Informe a duração do cardio, de 1 a 600 minutos.");
            if (t.getIntensidade() == null || !List.of("leve", "moderada", "intensa").contains(t.getIntensidade()))
                throw ApiException.badRequest("Intensidade inválida. Use leve, moderada ou intensa.");
            if (t.getDistanciaKm() != null && (!Double.isFinite(t.getDistanciaKm()) || t.getDistanciaKm() < 0 || t.getDistanciaKm() > 1000))
                throw ApiException.badRequest("A distância deve estar entre 0 e 1000 km.");
            t.setTipoCardio(t.getTipoCardio().trim());
            t.setExercicios(new ArrayList<>());
            t.setGruposMusculares(new ArrayList<>());
            t.setGrupoMuscular("");
        } else {
            if (t.getGruposMusculares().isEmpty() && t.getGrupoMuscular() != null && !t.getGrupoMuscular().isBlank())
                t.setGruposMusculares(List.of(t.getGrupoMuscular()));
            if (t.getGruposMusculares().size() > 20) throw ApiException.badRequest("Selecione no máximo 20 grupos musculares.");
            List<String> grupos = new ArrayList<>();
            for (String grupo : t.getGruposMusculares()) {
                if (grupo == null || grupo.isBlank() || grupo.length() > 100)
                    throw ApiException.badRequest("Grupo muscular inválido.");
                grupos.add(grupo.trim());
            }
            t.setGruposMusculares(new ArrayList<>(new LinkedHashSet<>(grupos)));
            t.setGrupoMuscular(String.join(", ", t.getGruposMusculares()));
        }
        if (t.getExercicios().size() > 50) throw ApiException.badRequest("Um treino pode ter no máximo 50 exercícios.");
        for (Exercicio e : t.getExercicios()) {
            if (e == null || e.getNome() == null || e.getNome().isBlank()) {
                throw ApiException.badRequest("Cada exercício precisa ter um 'nome'.");
            }
            e.setNome(e.getNome().trim());
            if (e.getNome().length() > 120) throw ApiException.badRequest("O nome do exercício deve ter até 120 caracteres.");
            if (e.getTecnica().length() > 120) throw ApiException.badRequest("A técnica deve ter até 120 caracteres.");
            e.setTecnica(e.getTecnica().trim());
            if (e.getSeries() != null && (e.getSeries() < 0 || e.getSeries() > 50)) {
                throw ApiException.badRequest("'series' de " + e.getNome() + " deve estar entre 0 e 50.");
            }
            if (e.getCarga() != null && (!Double.isFinite(e.getCarga()) || e.getCarga() < 0 || e.getCarga() > 1000)) {
                throw ApiException.badRequest("'carga' de " + e.getNome() + " deve estar entre 0 e 1000 kg.");
            }
        }
        if (t.getNotas() != null && t.getNotas().length() > 500) {
            t.setNotas(t.getNotas().substring(0, 500));
        }
    }
}
