package br.ime.fatoutfitin.model;

import java.util.ArrayList;
import java.util.List;

/** Card de treino exibido no mural. */
public class Treino {

    private Long id;
    private Long usuarioId;
    private String titulo;
    private String dia;
    private String grupoMuscular;
    private String cor = "padrao";
    private boolean fixado;
    private Integer duracaoMin;
    private List<Exercicio> exercicios = new ArrayList<>();
    private String notas = "";

    public Treino() {
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Long getUsuarioId() { return usuarioId; }
    public void setUsuarioId(Long usuarioId) { this.usuarioId = usuarioId; }

    public String getTitulo() { return titulo; }
    public void setTitulo(String titulo) { this.titulo = titulo; }

    public String getDia() { return dia; }
    public void setDia(String dia) { this.dia = dia; }

    public String getGrupoMuscular() { return grupoMuscular; }
    public void setGrupoMuscular(String grupoMuscular) { this.grupoMuscular = grupoMuscular; }

    public String getCor() { return cor; }
    public void setCor(String cor) { this.cor = cor; }

    public boolean isFixado() { return fixado; }
    public void setFixado(boolean fixado) { this.fixado = fixado; }

    public Integer getDuracaoMin() { return duracaoMin; }
    public void setDuracaoMin(Integer duracaoMin) { this.duracaoMin = duracaoMin; }

    public List<Exercicio> getExercicios() { return exercicios; }
    public void setExercicios(List<Exercicio> exercicios) {
        this.exercicios = exercicios == null ? new ArrayList<>() : exercicios;
    }

    public String getNotas() { return notas; }
    public void setNotas(String notas) { this.notas = notas == null ? "" : notas; }
}
