// =====================================================================
// Mural de cards: treinos (API Java) + refeições (API Python)
// =====================================================================
const usuario = getUsuario();
if (!usuario) window.location.href = "index.html";

const DIAS = [
  ["seg", "Segunda"], ["ter", "Terça"], ["qua", "Quarta"], ["qui", "Quinta"],
  ["sex", "Sexta"], ["sab", "Sábado"], ["dom", "Domingo"],
];
const NOME_DIA = Object.fromEntries(DIAS);
const NOME_TIPO = {
  cafe: "Café da manhã", almoco: "Almoço", lanche: "Lanche", jantar: "Jantar",
  "pre-treino": "Pré-treino", "pos-treino": "Pós-treino", ceia: "Ceia",
};
const CORES = ["padrao", "vermelho", "laranja", "amarelo", "verde", "azul", "roxo", "rosa"];
const NUTRIENTES = [
  { k: "kcal", rotulo: "Calorias", curto: "", un: "kcal" },
  { k: "proteinas", rotulo: "Proteínas", curto: "P", un: "g" },
  { k: "carboidratos", rotulo: "Carboidratos", curto: "C", un: "g" },
  { k: "gorduras", rotulo: "Gorduras", curto: "G", un: "g" },
  { k: "fibras", rotulo: "Fibras", curto: "Fib", un: "g" },
  { k: "sodio", rotulo: "Sódio", curto: "Na", un: "mg" },
];

const estado = {
  alimentos: [],
  alimentosPorId: {},
  treinos: [],
  refeicoes: [],
  resumoTreinos: null,
  resumoRefeicoes: null,
  filtroTipo: "todos",
  filtroDia: "todos",
  busca: "",
  visao: "mural",
};

const $ = (sel) => document.querySelector(sel);
const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

function diaDeHoje() {
  return ["dom", "seg", "ter", "qua", "qui", "sex", "sab"][new Date().getDay()];
}

// kcal e sódio inteiros; gramas com no máximo 1 casa decimal
function fmt(valor, k) {
  const n = Number(valor) || 0;
  return k === "kcal" || k === "sodio" ? String(Math.round(n)) : String(Math.round(n * 10) / 10).replace(".", ",");
}

function somaNutrientes(lista) {
  const total = Object.fromEntries(NUTRIENTES.map((n) => [n.k, 0]));
  lista.forEach((nutr) => NUTRIENTES.forEach((n) => (total[n.k] += Number(nutr?.[n.k]) || 0)));
  return total;
}

function htmlMacros(nutr, classe = "macros") {
  if (!nutr) return "";
  return `<div class="${classe}">${NUTRIENTES.map((n) =>
    `<span class="macro m-${n.k}" title="${n.rotulo}">${n.curto ? `<b>${n.curto}</b> ` : "🔥 "}${fmt(nutr[n.k], n.k)} ${n.un}</span>`
  ).join("")}</div>`;
}

function toast(texto, erro = false) {
  const t = $("#toast");
  t.textContent = texto;
  t.className = "toast" + (erro ? " erro" : "");
  t.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (t.hidden = true), 3500);
}

// ---------------------------------------------------------------------
// Carregamento de dados (as duas APIs em paralelo; uma falhar não derruba a outra)
// ---------------------------------------------------------------------
async function verificarApis() {
  const [py, jv] = await Promise.allSettled([apiPython.health(), apiJava.health()]);
  $("#status-python").classList.toggle("online", py.status === "fulfilled");
  $("#status-java").classList.toggle("online", jv.status === "fulfilled");
}

async function carregarTudo() {
  const [treinos, refeicoes, rt, rr, alimentos] = await Promise.allSettled([
    apiJava.listarTreinos(),
    apiPython.listarRefeicoes(),
    apiJava.resumoTreinos(),
    apiPython.resumoRefeicoes(),
    apiPython.listarAlimentos(),
  ]);
  if (alimentos.status === "fulfilled") {
    estado.alimentos = alimentos.value;
    estado.alimentosPorId = Object.fromEntries(alimentos.value.map((a) => [a.id, a]));
  }
  estado.treinos = treinos.status === "fulfilled" ? treinos.value : [];
  estado.refeicoes = refeicoes.status === "fulfilled" ? refeicoes.value : [];
  estado.resumoTreinos = rt.status === "fulfilled" ? rt.value : null;
  estado.resumoRefeicoes = rr.status === "fulfilled" ? rr.value : null;

  const falhas = [treinos, refeicoes].filter((r) => r.status === "rejected");
  if (falhas.length) toast(falhas.map((f) => f.reason.message).join(" | "), true);

  verificarApis();
  renderizar();
}

async function recarregarResumos() {
  const [rt, rr] = await Promise.allSettled([apiJava.resumoTreinos(), apiPython.resumoRefeicoes()]);
  if (rt.status === "fulfilled") estado.resumoTreinos = rt.value;
  if (rr.status === "fulfilled") estado.resumoRefeicoes = rr.value;
  renderizarResumo();
  if (estado.visao === "semana") renderizarSemana();
}

// ---------------------------------------------------------------------
// Cards
// ---------------------------------------------------------------------
function todosOsCards() {
  const treinos = estado.treinos.map((t) => ({ ...t, _tipo: "treino" }));
  const refeicoes = estado.refeicoes.map((r) => ({ ...r, _tipo: "refeicao" }));
  const busca = estado.busca.toLowerCase();

  return [...treinos, ...refeicoes]
    .filter((c) => estado.filtroTipo === "todos" || c._tipo === estado.filtroTipo)
    .filter((c) => estado.filtroDia === "todos" || c.dia === estado.filtroDia)
    .filter((c) => {
      if (!busca) return true;
      const itens = c._tipo === "treino" ? c.exercicios.map((e) => e.nome) : c.itens.map((i) => i.texto);
      return [c.titulo, c.notas, c.grupoMuscular, ...itens].join(" ").toLowerCase().includes(busca);
    })
    .sort((a, b) => DIAS.findIndex((d) => d[0] === a.dia) - DIAS.findIndex((d) => d[0] === b.dia));
}

function htmlItens(card) {
  if (card._tipo === "treino") {
    return card.exercicios
      .map((e, i) => {
        const detalhes = [
          e.series ? `${e.series}x` : "",
          e.repeticoes || "",
          e.carga ? `${e.carga} kg` : "",
        ].filter(Boolean).join(" ");
        return `<li class="${e.feito ? "feito" : ""}">
          <label><input type="checkbox" data-acao="marcar" data-indice="${i}" ${e.feito ? "checked" : ""}>
          <span>${esc(e.nome)}</span></label>${detalhes ? `<small>${esc(detalhes)}</small>` : ""}</li>`;
      })
      .join("");
  }
  return card.itens
    .map((it, i) => {
      const detalhes = [
        it.quantidade ? `${fmt(it.quantidade)} ${it.unidade || "g"}` : "",
        it.nutrientes?.kcal ? `${fmt(it.nutrientes.kcal, "kcal")} kcal` : "",
      ].filter(Boolean).join(" · ");
      return `<li class="${it.feito ? "feito" : ""}">
      <label><input type="checkbox" data-acao="marcar" data-indice="${i}" ${it.feito ? "checked" : ""}>
      <span>${esc(it.texto)}</span></label>${detalhes ? `<small>${esc(detalhes)}</small>` : ""}</li>`;
    })
    .join("");
}

function htmlCard(card) {
  const ehTreino = card._tipo === "treino";
  const itens = ehTreino ? card.exercicios : card.itens;
  const feitos = itens.filter((i) => i.feito).length;
  const progresso = itens.length ? Math.round((feitos / itens.length) * 100) : 0;

  const meta = ehTreino
    ? [card.grupoMuscular, card.duracaoMin ? `⏱ ${card.duracaoMin} min` : ""]
    : [NOME_TIPO[card.tipo]];
  const macros = !ehTreino && card.itens.length ? htmlMacros(card.nutrientes) : "";

  return `
  <article class="card cor-${card.cor}" data-tipo="${card._tipo}" data-id="${card.id}">
    <header>
      <span class="etiqueta ${card._tipo}">${ehTreino ? "🏋️ Treino" : "🍽️ Refeição"}</span>
      <span class="etiqueta dia">${NOME_DIA[card.dia]}</span>
      <button class="icone ${card.fixado ? "ativo" : ""}" data-acao="fixar" title="${card.fixado ? "Desafixar" : "Fixar"}">📌</button>
    </header>
    <h3 data-acao="editar">${esc(card.titulo)}</h3>
    <p class="meta">${meta.filter(Boolean).map(esc).join(" · ")}</p>
    ${macros}
    ${itens.length ? `<ul class="checklist">${htmlItens(card)}</ul>
      <div class="progresso" title="${feitos}/${itens.length} concluído(s)"><span style="width:${progresso}%"></span></div>` : ""}
    ${card.notas ? `<p class="notas">${esc(card.notas)}</p>` : ""}
    <footer>
      <span class="origem">${ehTreino ? "☕ API Java" : "🐍 API Python"}</span>
      <div class="paleta">${CORES.map((c) => `<button class="bolinha cor-${c}" data-acao="cor" data-cor="${c}" title="${c}"></button>`).join("")}</div>
      <button class="icone" data-acao="editar" title="Editar">✏️</button>
      <button class="icone" data-acao="excluir" title="Excluir">🗑️</button>
    </footer>
  </article>`;
}

function renderizarMural() {
  const cards = todosOsCards();
  const fixados = cards.filter((c) => c.fixado);
  const outros = cards.filter((c) => !c.fixado);

  $("#mural-fixados").innerHTML = fixados.map(htmlCard).join("");
  $("#mural").innerHTML = outros.map(htmlCard).join("");
  $("#titulo-fixados").hidden = fixados.length === 0;
  $("#titulo-outros").hidden = fixados.length === 0 || outros.length === 0;
  $("#vazio").hidden = cards.length > 0;
}

function renderizarResumo() {
  const rt = estado.resumoTreinos;
  const rr = estado.resumoRefeicoes;
  const bloco = (rotulo, valor, origem) =>
    `<div class="indicador"><b>${valor}</b><span>${rotulo}</span><small>${origem}</small></div>`;

  $("#resumo").innerHTML = [
    rt ? bloco("treinos na semana", rt.totalTreinos, "☕ Java") : "",
    rt ? bloco("exercícios concluídos", `${rt.progressoSemana}%`, "☕ Java") : "",
    rt ? bloco("dias de descanso", rt.diasDeDescanso, "☕ Java") : "",
    rr ? bloco("refeições planejadas", rr.totalRefeicoes, "🐍 Python") : "",
    rr ? bloco("kcal média/dia", fmt(rr.mediaDiaria.kcal, "kcal"), "🐍 Python") : "",
    rr ? bloco("P · C · G média/dia (g)",
      ["proteinas", "carboidratos", "gorduras"].map((k) => fmt(rr.mediaDiaria[k], k)).join(" · "), "🐍 Python") : "",
    rr ? bloco("fibras média/dia (g)", fmt(rr.mediaDiaria.fibras, "fibras"), "🐍 Python") : "",
    rr ? bloco("sódio média/dia (mg)", fmt(rr.mediaDiaria.sodio, "sodio"), "🐍 Python") : "",
  ].join("");
}

function renderizarSemana() {
  const cards = todosOsCards();
  const hoje = diaDeHoje();
  $("#visao-semana").innerHTML = DIAS.map(([codigo, nome]) => {
    const t = estado.resumoTreinos?.dias.find((d) => d.dia === codigo);
    const r = estado.resumoRefeicoes?.dias.find((d) => d.dia === codigo);
    const doDia = cards.filter((c) => c.dia === codigo);
    return `
    <div class="coluna-dia ${codigo === hoje ? "hoje" : ""}">
      <h3>${nome}${codigo === hoje ? " <small>hoje</small>" : ""}</h3>
      <div class="totais">
        ${t ? (t.treinos ? `<span>🏋️ ${t.treinos} treino(s) · ${t.series} séries · ${t.progresso}%</span>` : "<span>😴 Descanso</span>") : ""}
        ${r ? `<span>🍽️ ${r.refeicoes} refeição(ões)</span>` : ""}
      </div>
      ${r && r.refeicoes ? htmlMacros(r.nutrientes, "macros macros-dia") : ""}
      ${doDia.map(htmlCard).join("") || '<p class="vazio">—</p>'}
    </div>`;
  }).join("");
}

function renderizar() {
  renderizarResumo();
  $("#visao-mural").hidden = estado.visao !== "mural";
  $("#visao-semana").hidden = estado.visao !== "semana";
  if (estado.visao === "mural") renderizarMural();
  else renderizarSemana();
}

// ---------------------------------------------------------------------
// Ações nos cards
// ---------------------------------------------------------------------
function acharCard(tipo, id) {
  const lista = tipo === "treino" ? estado.treinos : estado.refeicoes;
  return lista.find((c) => c.id === id);
}

function substituirCard(tipo, novo) {
  const lista = tipo === "treino" ? estado.treinos : estado.refeicoes;
  const i = lista.findIndex((c) => c.id === novo.id);
  if (i >= 0) lista[i] = novo;
  else lista.unshift(novo);
}

function salvarCard(tipo, id, dados) {
  return tipo === "treino" ? apiJava.atualizarTreino(id, dados) : apiPython.atualizarRefeicao(id, dados);
}

async function executarAcao(acao, tipo, id, alvo) {
  const card = acharCard(tipo, id);
  if (!card) return;

  try {
    if (acao === "editar") return abrirEditor(tipo, card);

    if (acao === "excluir") {
      if (!confirm(`Excluir "${card.titulo}"?`)) return;
      if (tipo === "treino") await apiJava.excluirTreino(id);
      else await apiPython.excluirRefeicao(id);
      const lista = tipo === "treino" ? estado.treinos : estado.refeicoes;
      lista.splice(lista.indexOf(card), 1);
      toast("Card excluído.");
    }

    if (acao === "fixar") {
      substituirCard(tipo, await salvarCard(tipo, id, { ...card, fixado: !card.fixado }));
    }

    if (acao === "cor") {
      substituirCard(tipo, await salvarCard(tipo, id, { ...card, cor: alvo.dataset.cor }));
    }

    if (acao === "marcar") {
      const indice = Number(alvo.dataset.indice);
      if (tipo === "treino") {
        // API Java tem um endpoint PATCH específico para marcar exercício
        substituirCard(tipo, await apiJava.alternarExercicio(id, indice));
      } else {
        const itens = card.itens.map((it, i) => (i === indice ? { ...it, feito: !it.feito } : it));
        substituirCard(tipo, await apiPython.atualizarRefeicao(id, { ...card, itens }));
      }
    }
  } catch (erro) {
    toast(erro.message, true);
  }
  renderizar();
  recarregarResumos();
}

$("#conteudo").addEventListener("click", (e) => {
  const alvo = e.target.closest("[data-acao]");
  const cardEl = e.target.closest(".card");
  if (!alvo || !cardEl) return;
  if (alvo.dataset.acao === "marcar" && e.target.tagName !== "INPUT") return;
  executarAcao(alvo.dataset.acao, cardEl.dataset.tipo, Number(cardEl.dataset.id), alvo);
});

// ---------------------------------------------------------------------
// Editor (modal) de criação/edição
// ---------------------------------------------------------------------
const editor = $("#editor");
const formCard = $("#form-card");
let edicao = null; // { tipo, id | null, cor }

function linhaItem(tipo, item = {}) {
  if (tipo === "refeicao") return linhaIngrediente(item);
  const div = document.createElement("div");
  div.className = "item-editor";
  div.innerHTML = `<input type="checkbox" data-campo="feito" ${item.feito ? "checked" : ""} title="Concluído">
       <input data-campo="nome" placeholder="Exercício" value="${esc(item.nome)}" class="cresce">
       <input data-campo="series" type="number" min="0" placeholder="Séries" value="${esc(item.series)}" class="curto">
       <input data-campo="repeticoes" placeholder="Reps" value="${esc(item.repeticoes)}" class="curto">
       <input data-campo="carga" type="number" min="0" step="0.5" placeholder="kg" value="${esc(item.carga)}" class="curto">
       <button type="button" class="icone" title="Remover">✕</button>`;
  div.querySelector("button").onclick = () => div.remove();
  return div;
}

// ---- Ingrediente de refeição: alimento do catálogo ou "Outro" ----
function opcoesAlimentos(selecionado) {
  const categorias = [...new Set(estado.alimentos.map((a) => a.categoria))];
  return `<option value="">Escolha um alimento…</option>` +
    categorias.map((cat) => `<optgroup label="${esc(cat)}">${estado.alimentos
      .filter((a) => a.categoria === cat)
      .map((a) => `<option value="${a.id}" ${String(a.id) === String(selecionado) ? "selected" : ""}>${esc(a.nome)}</option>`)
      .join("")}</optgroup>`).join("") +
    `<option value="outro" ${selecionado === "outro" ? "selected" : ""}>➕ Outro (informar valores)</option>`;
}

function linhaIngrediente(item) {
  const doCatalogo = item.alimentoId != null && estado.alimentosPorId[item.alimentoId];
  const selecionado = doCatalogo ? item.alimentoId : item.texto ? "outro" : "";
  const div = document.createElement("div");
  div.className = "item-editor item-refeicao";
  div.innerHTML = `
    <div class="linha-item">
      <input type="checkbox" data-campo="feito" ${item.feito ? "checked" : ""} title="Preparado/comprado">
      <select data-campo="alimento" class="cresce">${opcoesAlimentos(selecionado)}</select>
      <input data-campo="quantidade" type="number" min="0" step="any" placeholder="qtd" value="${esc(item.quantidade)}" class="curto">
      <span class="unidade">g</span>
      <button type="button" class="icone" data-remover title="Remover">✕</button>
    </div>
    <div class="outro-campos" hidden>
      <input data-campo="texto" placeholder="Nome do ingrediente (ex.: molho caseiro)" value="${esc(doCatalogo ? "" : item.texto)}">
      <p class="ajuda">Valores para a quantidade usada:</p>
      <div class="grade-nutri">${NUTRIENTES.map((n) => `<label>${n.rotulo} (${n.un})
        <input type="number" min="0" step="any" data-nutri="${n.k}" value="${doCatalogo ? "" : esc(item.nutrientes?.[n.k] || "")}"></label>`).join("")}
      </div>
    </div>
    <div class="nutri-preview"></div>`;

  const select = div.querySelector('[data-campo="alimento"]');
  const qtd = div.querySelector('[data-campo="quantidade"]');
  select.addEventListener("change", () => {
    const alimento = estado.alimentosPorId[select.value];
    if (alimento) qtd.value = alimento.porcao; // porção sugerida ao trocar de alimento
    atualizarIngrediente(div);
  });
  div.addEventListener("input", () => atualizarIngrediente(div));
  div.querySelector("[data-remover]").onclick = () => {
    div.remove();
    atualizarTotaisEditor();
  };
  atualizarIngrediente(div, false);
  return div;
}

/** Nutrientes do ingrediente (prévia local; o cálculo oficial é feito pela API Python). */
function nutrientesDaLinha(div) {
  const sel = div.querySelector('[data-campo="alimento"]').value;
  const alimento = estado.alimentosPorId[sel];
  if (alimento) {
    const qtd = Number(div.querySelector('[data-campo="quantidade"]').value) || 0;
    return Object.fromEntries(NUTRIENTES.map((n) => [n.k, (alimento.por100[n.k] * qtd) / 100]));
  }
  if (sel === "outro") {
    return Object.fromEntries(NUTRIENTES.map((n) => [n.k, Number(div.querySelector(`[data-nutri="${n.k}"]`).value) || 0]));
  }
  return null;
}

function atualizarIngrediente(div, recalcularTotais = true) {
  const sel = div.querySelector('[data-campo="alimento"]').value;
  const alimento = estado.alimentosPorId[sel];
  div.querySelector(".outro-campos").hidden = sel !== "outro";
  div.querySelector(".unidade").textContent = alimento?.unidade || "g";

  const preview = div.querySelector(".nutri-preview");
  const nutr = nutrientesDaLinha(div);
  preview.innerHTML = alimento
    ? `<small class="ajuda">Porção sugerida: ${esc(alimento.porcaoDescricao)} (${alimento.porcao} ${alimento.unidade})</small>${htmlMacros(nutr, "macros macros-mini")}`
    : "";
  if (recalcularTotais) atualizarTotaisEditor();
}

function atualizarTotaisEditor() {
  const caixa = $("#totais-editor");
  if (!edicao || edicao.tipo !== "refeicao") return (caixa.innerHTML = "");
  const linhas = [...document.querySelectorAll("#lista-itens .item-refeicao")];
  const total = somaNutrientes(linhas.map(nutrientesDaLinha).filter(Boolean));
  caixa.innerHTML = `<span>Total da refeição</span>${htmlMacros(total)}`;
}

function abrirEditor(tipo, card = null) {
  edicao = { tipo, id: card?.id ?? null, cor: card?.cor ?? "padrao", fixado: card?.fixado ?? false };
  const ehTreino = tipo === "treino";

  formCard.reset();
  formCard.className = ehTreino ? "modo-treino" : "modo-refeicao";
  $("#editor-titulo").textContent = `${card ? "Editar" : "Novo"} ${ehTreino ? "treino" : "refeição"}`;
  $("#titulo-itens").textContent = ehTreino ? "Exercícios" : "Ingredientes / preparo";
  $("#origem-api").textContent = ehTreino ? "Salvo na ☕ API Java" : "Salvo na 🐍 API Python";
  $("#erro-editor").textContent = "";

  formCard.titulo.value = card?.titulo ?? "";
  formCard.dia.value = card?.dia ?? (estado.filtroDia !== "todos" ? estado.filtroDia : diaDeHoje());
  formCard.notas.value = card?.notas ?? "";
  if (ehTreino) {
    formCard.grupoMuscular.value = card?.grupoMuscular ?? "";
    formCard.duracaoMin.value = card?.duracaoMin ?? "";
  } else {
    formCard.tipo.value = card?.tipo ?? "almoco";
    if (!estado.alimentos.length) toast("Catálogo de alimentos indisponível (API Python). Use \"Outro\".", true);
  }

  const lista = $("#lista-itens");
  lista.innerHTML = "";
  const itens = (ehTreino ? card?.exercicios : card?.itens) ?? [];
  (itens.length ? itens : [{}]).forEach((it) => lista.appendChild(linhaItem(tipo, it)));
  atualizarTotaisEditor();

  desenharSeletorCor();
  editor.showModal();
  formCard.titulo.focus();
}

function desenharSeletorCor() {
  $("#seletor-cor").innerHTML = CORES.map((c) =>
    `<button type="button" class="bolinha cor-${c} ${edicao.cor === c ? "selecionada" : ""}" data-cor="${c}" title="${c}"></button>`
  ).join("");
}

$("#seletor-cor").addEventListener("click", (e) => {
  if (!e.target.dataset.cor) return;
  edicao.cor = e.target.dataset.cor;
  desenharSeletorCor();
});

$("#add-item").onclick = () => {
  const linha = linhaItem(edicao.tipo);
  $("#lista-itens").appendChild(linha);
  linha.querySelector(".cresce").focus();
};
$("#cancelar").onclick = () => editor.close();

function numeroOuNulo(v) {
  return v === "" ? null : Number(v);
}

function lerFormulario() {
  const f = formCard;
  const linhas = [...document.querySelectorAll("#lista-itens .item-editor")];
  const campo = (linha, nome) => linha.querySelector(`[data-campo="${nome}"]`);
  const base = { titulo: f.titulo.value.trim(), dia: f.dia.value, cor: edicao.cor, fixado: edicao.fixado, notas: f.notas.value };

  if (edicao.tipo === "treino") {
    return {
      ...base,
      grupoMuscular: f.grupoMuscular.value.trim(),
      duracaoMin: numeroOuNulo(f.duracaoMin.value),
      exercicios: linhas
        .filter((l) => campo(l, "nome").value.trim())
        .map((l) => ({
          nome: campo(l, "nome").value.trim(),
          series: numeroOuNulo(campo(l, "series").value),
          repeticoes: campo(l, "repeticoes").value.trim(),
          carga: numeroOuNulo(campo(l, "carga").value),
          feito: campo(l, "feito").checked,
        })),
    };
  }
  return {
    ...base,
    tipo: f.tipo.value,
    itens: linhas
      .map((l) => {
        const sel = campo(l, "alimento").value;
        const feito = campo(l, "feito").checked;
        const quantidade = numeroOuNulo(campo(l, "quantidade").value);
        if (sel === "outro") {
          const nutrientes = Object.fromEntries(
            NUTRIENTES.map((n) => [n.k, numeroOuNulo(l.querySelector(`[data-nutri="${n.k}"]`).value) ?? 0])
          );
          return { texto: campo(l, "texto").value.trim(), quantidade, nutrientes, feito };
        }
        return sel ? { alimentoId: Number(sel), quantidade, feito } : null; // linha vazia é ignorada
      })
      .filter(Boolean),
  };
}

formCard.addEventListener("submit", async (e) => {
  e.preventDefault();
  const dados = lerFormulario();
  const { tipo, id } = edicao;
  try {
    let salvo;
    if (tipo === "treino") {
      salvo = id ? await apiJava.atualizarTreino(id, dados) : await apiJava.criarTreino(dados);
    } else {
      salvo = id ? await apiPython.atualizarRefeicao(id, dados) : await apiPython.criarRefeicao(dados);
    }
    substituirCard(tipo, salvo);
    editor.close();
    toast(id ? "Card atualizado." : "Card criado!");
    renderizar();
    recarregarResumos();
  } catch (erro) {
    $("#erro-editor").textContent = erro.message;
  }
});

// ---------------------------------------------------------------------
// Filtros, busca e inicialização
// ---------------------------------------------------------------------
function ativarChip(container, botao) {
  container.querySelectorAll(".chip").forEach((c) => c.classList.toggle("ativo", c === botao));
}

$("#filtro-dia").innerHTML =
  `<button class="chip ativo" data-dia="todos">Semana toda</button>` +
  DIAS.map(([c, n]) => `<button class="chip" data-dia="${c}">${n.slice(0, 3)}</button>`).join("");
formCard.dia.innerHTML = DIAS.map(([c, n]) => `<option value="${c}">${n}</option>`).join("");

document.querySelector(".barra").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  if (chip.dataset.tipo) estado.filtroTipo = chip.dataset.tipo;
  if (chip.dataset.dia) estado.filtroDia = chip.dataset.dia;
  if (chip.dataset.visao) estado.visao = chip.dataset.visao;
  ativarChip(chip.parentElement, chip);
  renderizar();
});

$("#busca").addEventListener("input", (e) => {
  estado.busca = e.target.value;
  renderizar();
});

$("#novo-treino").onclick = () => abrirEditor("treino");
$("#nova-refeicao").onclick = () => abrirEditor("refeicao");
$("#btn-sair").onclick = sair;
$("#nome-usuario").textContent = `Olá, ${usuario?.nome ?? ""}`;

carregarTudo();
setInterval(verificarApis, 15000);
