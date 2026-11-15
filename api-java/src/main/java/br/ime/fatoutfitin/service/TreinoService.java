package br.ime.fatoutfitin.service;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

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

    /** Resumo da semana: treinos, exercícios, séries e progresso por dia. */
    public Map<String, Object> resumo(Long usuarioId) {
        List<Treino> todos = repository.listarPorUsuario(usuarioId);
        List<Map<String, Object>> dias = new ArrayList<>();
        int totalExercicios = 0;
        int totalFeitos = 0;
        int totalMinutos = 0;

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
            d.put("grupos", doDia.stream().map(Treino::getGrupoMuscular)
                    .filter(g -> g != null && !g.isBlank()).distinct().toList());
            d.put("exercicios", exercicios);
            d.put("series", series);
            d.put("minutos", minutos);
            d.put("progresso", exercicios == 0 ? 0 : Math.round(feitos * 100.0 / exercicios));
            dias.add(d);

            totalExercicios += exercicios;
            totalFeitos += feitos;
            totalMinutos += minutos;
        }

        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("dias", dias);
        resposta.put("totalTreinos", todos.size());
        resposta.put("totalExercicios", totalExercicios);
        resposta.put("totalMinutos", totalMinutos);
        resposta.put("diasDeDescanso", dias.stream().filter(d -> (int) d.get("treinos") == 0).count());
        resposta.put("progressoSemana", totalExercicios == 0 ? 0 : Math.round(totalFeitos * 100.0 / totalExercicios));
        return resposta;
    }

    private void validar(Treino t) {
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
        for (Exercicio e : t.getExercicios()) {
            if (e == null || e.getNome() == null || e.getNome().isBlank()) {
                throw ApiException.badRequest("Cada exercício precisa ter um 'nome'.");
            }
            e.setNome(e.getNome().trim());
            if (e.getSeries() != null && (e.getSeries() < 0 || e.getSeries() > 50)) {
                throw ApiException.badRequest("'series' de " + e.getNome() + " deve estar entre 0 e 50.");
            }
            if (e.getCarga() != null && (e.getCarga() < 0 || e.getCarga() > 1000)) {
                throw ApiException.badRequest("'carga' de " + e.getNome() + " deve estar entre 0 e 1000 kg.");
            }
        }
        if (t.getNotas() != null && t.getNotas().length() > 500) {
            t.setNotas(t.getNotas().substring(0, 500));
        }
    }
}
