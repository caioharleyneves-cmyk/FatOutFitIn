package br.ime.fatoutfitin.controller;

import java.io.IOException;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import br.ime.fatoutfitin.service.CatalogoService;

@RestController
@RequestMapping("/api/catalogo-treinos")
public class CatalogoController {
    public record NovaOpcao(String tipo, String nome) {}
    private final CatalogoService service;
    public CatalogoController(CatalogoService service) { this.service = service; }

    @GetMapping
    public Map<String,Object> listar(@RequestAttribute("usuarioId") Long usuario) {
        return service.listar(usuario);
    }
    @PostMapping("/personalizados")
    @ResponseStatus(HttpStatus.CREATED)
    public Map<String,Object> adicionar(@RequestAttribute("usuarioId") Long usuario, @RequestBody NovaOpcao opcao) throws IOException {
        return service.adicionar(usuario, opcao.tipo(), opcao.nome());
    }
}
