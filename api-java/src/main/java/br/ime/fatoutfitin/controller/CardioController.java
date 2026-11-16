package br.ime.fatoutfitin.controller;

import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import br.ime.fatoutfitin.model.Treino;
import br.ime.fatoutfitin.service.TreinoService;

@RestController
@RequestMapping("/api/cardios")
public class CardioController {
    private final TreinoService service;
    public CardioController(TreinoService service) { this.service = service; }

    @GetMapping
    public List<Treino> listar(@RequestAttribute("usuarioId") Long usuario,
                               @RequestParam(required=false) String dia) {
        return service.listar(usuario, dia).stream().filter(t -> "cardio".equals(t.getModalidade())).toList();
    }
    @GetMapping("/{id}")
    public Treino buscar(@RequestAttribute("usuarioId") Long usuario, @PathVariable Long id) {
        return service.buscarCardio(id, usuario);
    }
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Treino criar(@RequestAttribute("usuarioId") Long usuario, @RequestBody Treino cardio) {
        cardio.setModalidade("cardio");
        return service.criar(cardio, usuario);
    }
    @PutMapping("/{id}")
    public Treino atualizar(@RequestAttribute("usuarioId") Long usuario, @PathVariable Long id, @RequestBody Treino cardio) {
        service.buscarCardio(id, usuario);
        cardio.setModalidade("cardio");
        return service.atualizar(id, cardio, usuario);
    }
    @PatchMapping("/{id}/concluir")
    public Treino concluir(@RequestAttribute("usuarioId") Long usuario, @PathVariable Long id) {
        return service.concluirCardio(id, usuario);
    }
    @DeleteMapping("/{id}")
    public Map<String,String> excluir(@RequestAttribute("usuarioId") Long usuario, @PathVariable Long id) {
        service.buscarCardio(id, usuario);
        service.excluir(id, usuario);
        return Map.of("mensagem", "Cardio excluído.");
    }
}
