package br.ime.fatoutfitin.model;

/** Um exercício dentro de um card de treino (funciona como item de checklist). */
public class Exercicio {

    private String nome;
    private Integer series;
    private String repeticoes;
    private Double carga;
    private boolean feito;
    private String tecnica = "";

    public Exercicio() {
    }

    public String getNome() { return nome; }
    public void setNome(String nome) { this.nome = nome; }

    public Integer getSeries() { return series; }
    public void setSeries(Integer series) { this.series = series; }

    public String getRepeticoes() { return repeticoes; }
    public void setRepeticoes(String repeticoes) { this.repeticoes = repeticoes; }

    public Double getCarga() { return carga; }
    public void setCarga(Double carga) { this.carga = carga; }

    public boolean isFeito() { return feito; }
    public void setFeito(boolean feito) { this.feito = feito; }
    public String getTecnica() { return tecnica; }
    public void setTecnica(String tecnica) { this.tecnica = tecnica == null ? "" : tecnica; }
}
