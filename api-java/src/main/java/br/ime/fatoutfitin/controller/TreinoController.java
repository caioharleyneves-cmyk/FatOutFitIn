package br.ime.fatoutfitin.controller;

import java.util.List;
import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import br.ime.fatoutfitin.model.Treino;
import br.ime.fatoutfitin.service.TreinoService;

/**
 * Endpoints dos cards de treino. O usuário logado é identificado pelo
 * cabeçalho X-Usuario-Id (o login é feito na API Python).
 */
@RestController
@RequestMapping("/api")
public class TreinoController {

    private static final String USUARIO = "X-Usuario-Id";

    private final TreinoService service;

    public TreinoController(TreinoService service) {
        this.service = service;
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        return Map.of("status", "ok", "api", "java", "porta", 8080);
    }

    @GetMapping("/treinos")
    public List<Treino> listar(@RequestHeader(USUARIO) Long usuarioId,
                               @RequestParam(required = false) String dia) {
        return service.listar(usuarioId, dia);
    }

    @GetMapping("/treinos/resumo")
    public Map<String, Object> resumo(@RequestHeader(USUARIO) Long usuarioId) {
        return service.resumo(usuarioId);
    }

    @GetMapping("/treinos/{id}")
    public Treino buscar(@RequestHeader(USUARIO) Long usuarioId, @PathVariable Long id) {
        return service.buscar(id, usuarioId);
    }

    @PostMapping("/treinos")
    @ResponseStatus(HttpStatus.CREATED)
    public Treino criar(@RequestHeader(USUARIO) Long usuarioId, @RequestBody Treino treino) {
        return service.criar(treino, usuarioId);
    }

    @PutMapping("/treinos/{id}")
    public Treino atualizar(@RequestHeader(USUARIO) Long usuarioId, @PathVariable Long id,
                            @RequestBody Treino treino) {
        return service.atualizar(id, treino, usuarioId);
    }

    @PatchMapping("/treinos/{id}/exercicios/{indice}")
    public Treino alternarExercicio(@RequestHeader(USUARIO) Long usuarioId, @PathVariable Long id,
                                    @PathVariable int indice) {
        return service.alternarExercicio(id, indice, usuarioId);
    }

    @DeleteMapping("/treinos/{id}")
    public Map<String, String> excluir(@RequestHeader(USUARIO) Long usuarioId, @PathVariable Long id) {
        service.excluir(id, usuarioId);
        return Map.of("mensagem", "Treino " + id + " excluído.");
    }
}
