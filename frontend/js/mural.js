(() => {
  const usuario = getUsuario();
  if (!usuario) { location.replace("index.html"); return; }
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => [...document.querySelectorAll(s)];
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" })[c]);
  const normalizar = (s) => String(s).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
  const DIAS = [["seg","Segunda"],["ter","Terça"],["qua","Quarta"],["qui","Quinta"],["sex","Sexta"],["sab","Sábado"],["dom","Domingo"]];
  const NOME_DIA = Object.fromEntries(DIAS);
  const NOMES = { treino:"treino", cardio:"cardio", refeicao:"refeição" };
  const TIPOS_REFEICAO = { cafe:"Café da manhã",almoco:"Almoço",lanche:"Lanche",jantar:"Jantar","pre-treino":"Pré-treino","pos-treino":"Pós-treino",ceia:"Ceia" };
  const CORES = ["padrao","vermelho","laranja","amarelo","verde","azul","roxo","rosa"];
  const NUTRIENTES = [
    {k:"kcal",rotulo:"Calorias",curto:"",un:"kcal"},{k:"proteinas",rotulo:"Proteínas",curto:"P",un:"g"},
    {k:"carboidratos",rotulo:"Carboidratos",curto:"C",un:"g"},{k:"gorduras",rotulo:"Gorduras",curto:"G",un:"g"},
    {k:"fibras",rotulo:"Fibras",curto:"Fib",un:"g"},{k:"sodio",rotulo:"Sódio",curto:"Na",un:"mg"}
  ];
  const estado = { treinos:[],refeicoes:[],alimentos:[],alimentosPorId:{},resumoTreinos:null,resumoRefeicoes:null,
    catalogo:{grupos:[],exercicios:[],tecnicas:[],tiposCardio:[],personalizados:{grupos:[],exercicios:[]}},
    filtroTipo:"todos",filtroDia:"todos",visao:"mural",busca:"",falhas:[] };
  const editor = $("#editor"), f = $("#form-card");
  let edicao = null;
  const hoje = () => ["dom","seg","ter","qua","qui","sex","sab"][new Date().getDay()];
  const tipoDe = (t) => t.modalidade === "cardio" ? "cardio" : "treino";
  const gruposDe = (t) => t?.gruposMusculares?.length ? t.gruposMusculares : t?.grupoMuscular ? t.grupoMuscular.split(/,\s*|\s+e\s+/).map(s => s.trim()).filter(Boolean) : [];
  const numero = (v) => v === "" ? null : Number(v);
  const fmt = (v,k) => new Intl.NumberFormat("pt-BR",{maximumFractionDigits:k==="kcal"||k==="sodio"?0:1}).format(Number(v)||0);
  const arredondar = (v,k) => Math.round(v*(k==="kcal"||k==="sodio"?1:10))/(k==="kcal"||k==="sodio"?1:10);

  function toast(texto,erro=false) {
    const t=$("#toast"); t.textContent=texto;t.className="toast"+(erro?" erro":"");t.hidden=false;
    clearTimeout(toast.timer);toast.timer=setTimeout(()=>t.hidden=true,4500);
  }
  function htmlMacros(nutr,completo=false) {
    return '<div class="macros">'+NUTRIENTES.filter((_,i)=>completo||i<4).map(n=>'<span class="macro m-'+n.k+'" title="'+n.rotulo+'">'+(n.curto?'<b>'+n.curto+'</b> ':'')+fmt(nutr?.[n.k],n.k)+' '+n.un+'</span>').join("")+'</div>';
  }
  async function verificarApis() {
    const resultados=await Promise.allSettled([apiPython.health(),apiJava.health()]);
    ["python","java"].forEach((nome,i)=>$("#status-"+nome).classList.toggle("online",resultados[i].status==="fulfilled"));
  }
  async function carregarTudo() {
    $("#erro-carregamento").hidden=true;
    const r=await Promise.allSettled([apiJava.listarTreinos(),apiPython.listarRefeicoes(),apiJava.resumoTreinos(),apiPython.resumoRefeicoes(),apiPython.listarAlimentos(),apiJava.catalogo()]);
    estado.falhas=[];
    const campos=["treinos","refeicoes","resumoTreinos","resumoRefeicoes","alimentos","catalogo"];
    r.forEach((res,i)=>{
      if(res.status==="fulfilled")estado[campos[i]]=res.value;
      else if(i===0||i===1||i===5)estado.falhas.push(res.reason.message);
    });
    estado.alimentosPorId=Object.fromEntries(estado.alimentos.map(a=>[a.id,a]));
    if(estado.falhas.length) {
      $("#erro-carregamento").hidden=false;
      $("#erro-carregamento").innerHTML=esc(estado.falhas.join(" "))+' <button type="button" id="tentar-novamente">Tentar novamente</button>';
      $("#tentar-novamente").onclick=carregarTudo;
    }
    await verificarApis();renderizar();
  }
  async function atualizarResumos() {
    const r=await Promise.allSettled([apiJava.resumoTreinos(),apiPython.resumoRefeicoes()]);
    if(r[0].status==="fulfilled")estado.resumoTreinos=r[0].value;
    if(r[1].status==="fulfilled")estado.resumoRefeicoes=r[1].value;
    renderizarResumo();if(estado.visao==="semana")renderizarSemana();
  }
  function todosCards() {
    const busca=normalizar(estado.busca);
    return [...estado.treinos.map(t=>({...t,_tipo:tipoDe(t)})),...estado.refeicoes.map(r=>({...r,_tipo:"refeicao"}))]
      .filter(c=>estado.filtroTipo==="todos"||estado.filtroTipo===c._tipo)
      .filter(c=>estado.filtroDia==="todos"||estado.filtroDia===c.dia)
      .filter(c=>!busca||normalizar([c.titulo,c.notas,c.grupoMuscular,c.tipoCardio,...(c.exercicios||[]).map(e=>e.nome),...(c.itens||[]).map(i=>i.texto)].join(" ")).includes(busca))
      .sort((a,b)=>DIAS.findIndex(d=>d[0]===a.dia)-DIAS.findIndex(d=>d[0]===b.dia)||b.id-a.id);
  }
  function htmlItens(card) {
    const treino=card._tipo==="treino", itens=treino?card.exercicios:card.itens;
    return '<ul class="checklist">'+itens.map((it,i)=>{
      const detalhe=treino?[it.series?it.series+" séries":"",it.repeticoes?it.repeticoes+" reps":"",it.carga!=null?fmt(it.carga)+" kg":""].filter(Boolean).join(" · "):
        [it.quantidade!=null?fmt(it.quantidade)+" "+(it.unidade||"g"):"",it.nutrientes?.kcal!=null?fmt(it.nutrientes.kcal,"kcal")+" kcal":""].filter(Boolean).join(" · ");
      return '<li class="'+(it.feito?"feito":"")+'"><label><input type="checkbox" data-acao="marcar" data-indice="'+i+'" '+(it.feito?"checked":"")+'><span>'+esc(treino?it.nome:it.texto)+'</span></label><small>'+esc(detalhe)+'</small>'+(it.tecnica?'<span class="technique">'+esc(it.tecnica)+'</span>':"")+'</li>';
    }).join("")+'</ul>';
  }
  function htmlCard(card) {
    const tipo=card._tipo, cardio=tipo==="cardio", treino=tipo==="treino";
    const itens=treino?(card.exercicios||[]):card.itens||[];
    const feitos=cardio?(card.concluido?1:0):itens.filter(i=>i.feito).length;
    const total=cardio?1:itens.length, progresso=total?Math.round(feitos*100/total):0;
    const meta=treino?[...gruposDe(card),card.duracaoMin?card.duracaoMin+" min":""].filter(Boolean).join(" · "):
      cardio?card.tipoCardio+" · "+({leve:"Leve",moderada:"Moderada",intensa:"Intensa"}[card.intensidade]||"Moderada"):TIPOS_REFEICAO[card.tipo];
    const conteudo=cardio?'<div class="cardio-numbers"><div><b>'+fmt(card.duracaoMin)+'</b><span>minutos</span></div>'+(card.distanciaKm!=null?'<div><b>'+fmt(card.distanciaKm)+'</b><span>quilômetros</span></div>':"")+'</div><label class="cardio-done"><input type="checkbox" data-acao="concluir-cardio" '+(card.concluido?"checked":"")+'> Cardio concluído</label>':
      (tipo==="refeicao"&&itens.length?htmlMacros(card.nutrientes):"")+(itens.length?htmlItens(card):'<p class="ajuda">Seu planejamento está salvo.</p>');
    return '<article class="card cor-'+esc(card.cor||"padrao")+'" data-tipo="'+tipo+'" data-id="'+card.id+'"><header><span class="etiqueta tipo">'+({treino:"🏋️ Musculação",cardio:"🏃 Cardio",refeicao:"🍽️ Refeição"}[tipo])+'</span><span class="etiqueta">'+NOME_DIA[card.dia]+'</span><button type="button" class="icon-button pin '+(card.fixado?"ativo":"")+'" data-acao="fixar" title="'+(card.fixado?"Desafixar":"Fixar")+'" aria-label="'+(card.fixado?"Desafixar":"Fixar")+' '+esc(card.titulo)+'">⌖</button></header><h3><button type="button" class="title-button" data-acao="editar">'+esc(card.titulo)+'</button></h3><p class="meta">'+esc(meta)+'</p>'+conteudo+(total?'<div class="progresso" aria-label="'+progresso+'% concluído"><span style="width:'+progresso+'%"></span></div><span class="progress-caption">'+feitos+' de '+total+' '+(cardio?"atividade concluída":"itens concluídos")+'</span>':"")+(card.notas?'<p class="notas">'+esc(card.notas)+'</p>':"")+'<footer><span class="card-date">'+(cardio?"Movimento faz bem":treino?"No seu ritmo":"Cuidado em cada refeição")+'</span><button type="button" class="btn-card" data-acao="editar" aria-label="Editar '+esc(card.titulo)+'">Editar</button><button type="button" class="btn-card" data-acao="excluir" aria-label="Excluir '+esc(card.titulo)+'">Excluir</button></footer></article>';
  }
  function renderizarResumo() {
    const t=estado.resumoTreinos,r=estado.resumoRefeicoes;
    const bloco=(icone,valor,rotulo,detalhe)=>'<div class="indicador"><span class="indicator-icon" aria-hidden="true">'+icone+'</span><div><b>'+valor+'</b><span>'+rotulo+'</span><small>'+esc(detalhe)+'</small></div></div>';
    $("#resumo").innerHTML=bloco("🏋️",t?fmt(t.totalTreinos):"—","atividades na semana",t?(t.totalMusculacao??t.totalTreinos)+" musculação e "+(t.totalCardios??0)+" cardio":"Aguardando conexão")+
      bloco("⏱️",t?fmt(t.totalMinutos):"—","minutos de movimento",t?(t.progressoSemana||0)+"% do planejamento concluído":"Aguardando conexão")+
      bloco("🍽️",r?fmt(r.totalRefeicoes):"—","refeições planejadas",r?fmt(r.total.kcal,"kcal")+" kcal na semana":"Aguardando conexão");
  }
  function renderizarSemana() {
    const cards=todosCards();
    const dias=estado.filtroDia==="todos"?DIAS:DIAS.filter(d=>d[0]===estado.filtroDia);
    $("#visao-semana").style.gridTemplateColumns=dias.length===1?"minmax(270px,420px)":"";
    $("#visao-semana").innerHTML=dias.map(([dia,nome])=>{
      const doDia=cards.filter(c=>c.dia===dia);
      return '<div class="coluna-dia '+(dia===hoje()?"hoje":"")+'"><h3>'+nome+(dia===hoje()?" <small>Hoje</small>":"")+'</h3><p class="totais">'+doDia.length+' '+(doDia.length===1?"planejamento":"planejamentos")+'</p>'+ (doDia.map(htmlCard).join("")||'<p class="vazio">Um espaço livre na sua semana.</p>')+'</div>';
    }).join("");
  }
  function renderizar() {
    renderizarResumo();
    const cards=todosCards(),fixados=cards.filter(c=>c.fixado),outros=cards.filter(c=>!c.fixado);
    $("#contagem-cards").textContent=cards.length;
    $("#titulo-mural").textContent=({todos:"Meu mural",treino:"Musculação",cardio:"Meus cardios",refeicao:"Minhas refeições"})[estado.filtroTipo];
    $("#visao-mural").hidden=estado.visao!=="mural";$("#visao-semana").hidden=estado.visao!=="semana";
    if(estado.visao==="semana")renderizarSemana();
    else {
      $("#mural-fixados").innerHTML=fixados.map(htmlCard).join("");$("#mural").innerHTML=outros.map(htmlCard).join("");
      $("#titulo-fixados").hidden=!fixados.length;$("#titulo-outros").hidden=!fixados.length||!outros.length;
      $("#vazio").hidden=cards.length>0;
      const filtrado=!!estado.busca||estado.filtroDia!=="todos"||estado.filtroTipo!=="todos";
      $("#vazio").innerHTML='<span class="empty-icon" aria-hidden="true">'+(filtrado?"⌕":"▦")+'</span><h3>'+(filtrado?"Nenhum resultado por aqui":"Sua próxima semana começa aqui.")+'</h3><p>'+(filtrado?"Tente outro dia, categoria ou palavra na busca.":"Adicione seu primeiro treino, cardio ou refeição e organize sua rotina do seu jeito.")+'</p><button type="button" class="btn-secundario" id="acao-vazio">'+(filtrado?"Limpar filtros":"Criar meu primeiro treino")+'</button>';
      $("#acao-vazio").onclick=()=>{if(filtrado){estado.busca="";estado.filtroDia="todos";estado.filtroTipo="todos";$("#busca").value="";atualizarFiltros();renderizar();}else abrirEditor("treino");};
    }
  }
  function substituir(tipo,salvo) {
    const lista=tipo==="refeicao"?estado.refeicoes:estado.treinos;
    const i=lista.findIndex(c=>c.id===salvo.id);if(i<0)lista.unshift(salvo);else lista[i]=salvo;
  }
  function salvar(tipo,id,dados) {
    return tipo==="refeicao"?apiPython.atualizarRefeicao(id,dados):tipo==="cardio"?apiJava.atualizarCardio(id,dados):apiJava.atualizarTreino(id,dados);
  }
  $("#conteudo").addEventListener("click",async e=>{
    const alvo=e.target.closest("[data-acao]"),el=e.target.closest(".card");if(!alvo||!el)return;
    const tipo=el.dataset.tipo,id=Number(el.dataset.id),lista=tipo==="refeicao"?estado.refeicoes:estado.treinos,card=lista.find(c=>c.id===id);
    if(!card)return;
    const acao=alvo.dataset.acao;if(acao==="editar"){abrirEditor(tipo,card);return;}
    if(alvo.disabled)return;alvo.disabled=true;
    try {
      if(acao==="excluir"){
        if(!confirm('Excluir "'+card.titulo+'"?'))return;
        if(tipo==="refeicao")await apiPython.excluirRefeicao(id);else if(tipo==="cardio")await apiJava.excluirCardio(id);else await apiJava.excluirTreino(id);
        lista.splice(lista.indexOf(card),1);toast("Planejamento excluído.");
      } else if(acao==="fixar")substituir(tipo,await salvar(tipo,id,{...card,fixado:!card.fixado}));
      else if(acao==="concluir-cardio")substituir(tipo,await apiJava.concluirCardio(id));
      else if(acao==="marcar"){
        if(tipo==="treino")substituir(tipo,await apiJava.alternarExercicio(id,Number(alvo.dataset.indice)));
        else substituir(tipo,await salvar(tipo,id,{...card,itens:card.itens.map((it,i)=>i===Number(alvo.dataset.indice)?{...it,feito:!it.feito}:it)}));
      }
      renderizar();await atualizarResumos();
    }catch(erro){toast(erro.message,true);renderizar();}
    finally{alvo.disabled=false;}
  });

  function desenharDias(container,selecionado,atributo) {
    $(container).innerHTML=DIAS.map(([dia,nome])=>'<button type="button" class="day-balloon '+(dia===selecionado?"ativo":"")+'" '+atributo+'="'+dia+'" aria-label="'+nome+'" aria-pressed="'+(dia===selecionado)+'" title="'+nome+'">'+nome.slice(0,3)+'</button>').join("");
  }
  function diaEditor(dia) {
    f.dia.value=dia;$("#dia-editor-label").textContent=NOME_DIA[dia];desenharDias("#dias-editor",dia,"data-dia-editor");
  }
  document.addEventListener("click",e=>{
    const escolhido=e.target.closest("[data-dia-editor]");
    if(escolhido){diaEditor(escolhido.dataset.diaEditor);$("#editor-dia").open=false;}
    const filtro=e.target.closest("[data-dia-filtro]");
    if(filtro){estado.filtroDia=filtro.dataset.diaFiltro;$("#filtro-dia").open=false;atualizarFiltros();renderizar();}
    $$("details.day-picker[open]").forEach(d=>{if(!d.contains(e.target))d.open=false;});
  });
  document.addEventListener("keydown",e=>{
    const abertos=$$("details.day-picker[open]");
    if(e.key==="Escape"&&abertos.length){e.preventDefault();abertos.forEach(d=>d.open=false);}
  });
  function atualizarFiltros() {
    $$("#filtro-tipo button").forEach(b=>{b.classList.toggle("ativo",b.dataset.tipo===estado.filtroTipo);b.setAttribute("aria-pressed",b.dataset.tipo===estado.filtroTipo);});
    $$("#filtro-visao button").forEach(b=>{b.classList.toggle("ativo",b.dataset.visao===estado.visao);b.setAttribute("aria-pressed",b.dataset.visao===estado.visao);});
    $("#dia-filtro-label").textContent=estado.filtroDia==="todos"?"Semana toda":NOME_DIA[estado.filtroDia];
    desenharDias("#dias-filtro",estado.filtroDia,"data-dia-filtro");
  }
  const gruposSelecionados=()=> $$("#grupos-musculares input:checked").map(i=>i.value);
  function desenharGrupos(selecionados=[]) {
    const vistos=new Set();
    const grupos=[...estado.catalogo.grupos,...selecionados].filter(g=>{
      const chave=normalizar(g);if(vistos.has(chave))return false;vistos.add(chave);return true;
    });
    $("#grupos-musculares").innerHTML=grupos.map(g=>'<label class="choice-pill"><input type="checkbox" value="'+esc(g)+'" '+(selecionados.some(s=>normalizar(s)===normalizar(g))?"checked":"")+'><span>'+esc(g)+'</span></label>').join("");
  }
  async function salvarGrupo() {
    const input=$("#nome-grupo-personalizado"),nome=input.value.trim();if(!nome)throw new Error("Informe o nome do grupo personalizado.");
    const selecionados=gruposSelecionados();
    estado.catalogo=await apiJava.salvarPersonalizado("grupo",nome);
    const canonico=estado.catalogo.grupos.find(g=>normalizar(g)===normalizar(nome))||nome;
    desenharGrupos([...selecionados,canonico]);input.value="";toast("Grupo salvo na sua conta.");
  }
  $("#salvar-grupo").onclick=async()=>{
    const b=$("#salvar-grupo");b.disabled=true;try{await salvarGrupo();}catch(e){$("#erro-editor").textContent=e.message;}finally{b.disabled=false;}
  };

  function opcoesExercicios(selecionado="") {
    const lista=estado.catalogo.exercicios;
    const grupos=[...new Set(lista.map(e=>e.grupo))];
    let html='<option value="">Escolha um exercício</option>';
    if(selecionado&&selecionado!=="__custom__"&&!lista.some(e=>e.nome===selecionado))html+='<option value="'+esc(selecionado)+'" selected>'+esc(selecionado)+'</option>';
    html+=grupos.map(g=>'<optgroup label="'+esc(g)+'">'+lista.filter(e=>e.grupo===g).map(e=>'<option value="'+esc(e.nome)+'" '+(e.nome===selecionado?"selected":"")+'>'+esc(e.nome)+'</option>').join("")+'</optgroup>').join("");
    return html+'<option value="__custom__" '+(selecionado==="__custom__"?"selected":"")+'>+ Exercício personalizado</option>';
  }
  function linhaExercicio(ex={}) {
    const div=document.createElement("div");div.className="item-editor item-exercicio";
    const tecnica=ex.tecnica||"",outra=tecnica&&!estado.catalogo.tecnicas.includes(tecnica);
    div.innerHTML='<div class="exercise-heading"><span>Exercício</span><button type="button" class="icon-button remover" aria-label="Remover exercício">×</button></div><label>Nome do exercício<select data-campo="nome">'+opcoesExercicios(ex.nome)+'</select></label><div class="custom-exercise" hidden><div class="custom-row"><input data-campo="nome-custom" maxlength="120" placeholder="Nome do exercício" aria-label="Nome do exercício personalizado"><button type="button" class="btn-secundario salvar-exercicio">Salvar exercício</button></div><small>Fica disponível nos seus próximos treinos.</small></div><div class="exercise-fields"><label>Séries<input data-campo="series" type="number" min="0" max="50" placeholder="3" value="'+esc(ex.series)+'"></label><label>Repetições<input data-campo="repeticoes" maxlength="40" placeholder="8–12" value="'+esc(ex.repeticoes)+'"></label><label>Carga (kg)<input data-campo="carga" type="number" min="0" max="1000" step="0.5" placeholder="Opcional" value="'+esc(ex.carga)+'"></label></div><div class="exercise-technique"><label>Técnica avançada <small>Opcional</small><select data-campo="tecnica"><option value="">Sem técnica avançada</option>'+estado.catalogo.tecnicas.map(t=>'<option '+(t===tecnica?"selected":"")+'>'+esc(t)+'</option>').join("")+'<option value="__outra__" '+(outra?"selected":"")+'>Outra técnica</option></select></label><input data-campo="outra-tecnica" maxlength="120" placeholder="Nome da técnica" aria-label="Técnica personalizada" value="'+esc(outra?tecnica:"")+'" '+(outra?"":"hidden")+'></div><label class="check-row"><input data-campo="feito" type="checkbox" '+(ex.feito?"checked":"")+'> Exercício concluído</label>';
    div.querySelector(".remover").onclick=()=>div.remove();
    div.querySelector('[data-campo="nome"]').onchange=e=>div.querySelector(".custom-exercise").hidden=e.target.value!=="__custom__";
    div.querySelector('[data-campo="tecnica"]').onchange=e=>div.querySelector('[data-campo="outra-tecnica"]').hidden=e.target.value!=="__outra__";
    div.querySelector(".salvar-exercicio").onclick=async()=>{
      const b=div.querySelector(".salvar-exercicio");b.disabled=true;
      try{await salvarExercicioPersonalizado(div);toast("Exercício salvo na sua conta.");}catch(e){$("#erro-editor").textContent=e.message;}finally{b.disabled=false;}
    };
    return div;
  }
  async function salvarExercicioPersonalizado(div) {
    const nome=div.querySelector('[data-campo="nome-custom"]').value.trim();
    if(!nome)throw new Error("Informe o nome do exercício personalizado.");
    estado.catalogo=await apiJava.salvarPersonalizado("exercicio",nome);
    const canonico=estado.catalogo.exercicios.find(e=>normalizar(e.nome)===normalizar(nome))?.nome||nome;
    $$("#lista-itens .item-exercicio").forEach(l=>{
      const s=l.querySelector('[data-campo="nome"]'),valor=l===div?canonico:s.value;
      s.innerHTML=opcoesExercicios(valor);s.value=valor;
    });
    div.querySelector(".custom-exercise").hidden=true;
  }
  function opcoesAlimentos(id) {
    const grupos=[...new Set(estado.alimentos.map(a=>a.categoria))];
    return '<option value="">Escolha um alimento</option>'+grupos.map(g=>'<optgroup label="'+esc(g)+'">'+estado.alimentos.filter(a=>a.categoria===g).map(a=>'<option value="'+a.id+'" '+(String(a.id)===String(id)?"selected":"")+'>'+esc(a.nome)+'</option>').join("")+'</optgroup>').join("")+'<option value="outro" '+(id==="outro"?"selected":"")+'>Outro alimento</option>';
  }
  function nutrientesDaLinha(div) {
    const sel=div.querySelector('[data-campo="alimento"]').value,a=estado.alimentosPorId[sel];
    if(a){const v=div.querySelector('[data-campo="quantidade"]').value,q=v===""?a.porcao:Number(v);return Object.fromEntries(NUTRIENTES.map(n=>[n.k,arredondar(a.por100[n.k]*(q/100),n.k)]));}
    if(sel==="outro")return Object.fromEntries(NUTRIENTES.map(n=>[n.k,arredondar(Number(div.querySelector('[data-nutri="'+n.k+'"]').value)||0,n.k)]));
    return null;
  }
  function atualizarIngrediente(div) {
    const sel=div.querySelector('[data-campo="alimento"]').value,a=estado.alimentosPorId[sel];
    div.querySelector(".outro-campos").hidden=sel!=="outro";
    div.querySelector(".unidade").textContent=a?.unidade||"g";
    div.querySelector(".nutri-preview").innerHTML=a?'<small>Porção sugerida: '+esc(a.porcaoDescricao)+'</small>'+htmlMacros(nutrientesDaLinha(div)):"";
    atualizarTotaisEditor();
  }
  function linhaIngrediente(it={}) {
    const div=document.createElement("div");div.className="item-editor item-refeicao";
    const catalogo=it.alimentoId!=null&&estado.alimentosPorId[it.alimentoId],selecionado=catalogo?it.alimentoId:it.texto?"outro":"";
    div.innerHTML='<div class="linha-item"><label>Alimento<select data-campo="alimento">'+opcoesAlimentos(selecionado)+'</select></label><label>Quantidade<input data-campo="quantidade" type="number" min="0" max="5000" step="any" placeholder="Qtd." value="'+esc(it.quantidade)+'"></label><span class="unidade">g</span><button type="button" class="icon-button remover" aria-label="Remover ingrediente">×</button></div><div class="outro-campos" hidden><label>Nome do alimento<input data-campo="texto" maxlength="120" placeholder="Ex.: Molho caseiro" value="'+esc(catalogo?"":it.texto)+'"></label><p class="ajuda">Valores nutricionais para a quantidade usada:</p><div class="grade-nutri">'+NUTRIENTES.map(n=>'<label>'+n.rotulo+' ('+n.un+')<input data-nutri="'+n.k+'" type="number" min="0" step="any" value="'+esc(catalogo?"":it.nutrientes?.[n.k]??"")+'"></label>').join("")+'</div></div><div class="nutri-preview"></div><label class="check-row"><input data-campo="feito" type="checkbox" '+(it.feito?"checked":"")+'> Ingrediente preparado</label>';
    div.querySelector(".remover").onclick=()=>{div.remove();atualizarTotaisEditor();};
    div.querySelector('[data-campo="alimento"]').onchange=e=>{const a=estado.alimentosPorId[e.target.value];if(a)div.querySelector('[data-campo="quantidade"]').value=a.porcao;atualizarIngrediente(div);};
    div.addEventListener("input",()=>atualizarIngrediente(div));
    atualizarIngrediente(div);return div;
  }
  function atualizarTotaisEditor() {
    if(edicao?.tipo!=="refeicao")return;
    const nutrientes=$$("#lista-itens .item-refeicao").map(nutrientesDaLinha).filter(Boolean);
    const total=Object.fromEntries(NUTRIENTES.map(n=>[n.k,nutrientes.reduce((s,v)=>s+(v[n.k]||0),0)]));
    $("#totais-editor").innerHTML='<span>Total da refeição</span>'+htmlMacros(total,true);
  }
  function abrirEditor(tipo,card=null) {
    edicao={tipo,id:card?.id??null,fixado:card?.fixado??false,cor:card?.cor||"padrao"};
    f.reset();f.className="modo-"+tipo;$("#erro-editor").textContent="";
    $("#editor-titulo").textContent=(card?"Editar ":"Nov"+(tipo==="refeicao"?"a ":"o "))+NOMES[tipo];
    f.titulo.value=card?.titulo||"";
    f.titulo.placeholder={treino:"Ex.: Treino A · Peito e tríceps",cardio:"Ex.: Corrida no parque",refeicao:"Ex.: Marmita da semana"}[tipo];
    f.notas.value=card?.notas||"";
    f.notas.placeholder={treino:"Descanso entre séries, ajustes de carga ou observações do treino...",cardio:"Percurso, ritmo ou observações do seu cardio...",refeicao:"Modo de preparo, ingredientes ou dicas para a refeição..."}[tipo];
    diaEditor(card?.dia||(estado.filtroDia!=="todos"?estado.filtroDia:hoje()));
    $("#editor-dia").open=false;$("#nome-grupo-personalizado").value="";
    $$("#form-card .custom-add, #form-card .card-customization").forEach(d=>d.open=false);
    f.duracaoMin.value=card?.duracaoMin??"";f.tipo.value=card?.tipo||"almoco";
    desenharGrupos(gruposDe(card));
    const tipos=estado.catalogo.tiposCardio.length?estado.catalogo.tiposCardio:["Caminhada","Corrida","Bicicleta","Elíptico","Escada","Remo","Pular corda","Natação"];
    $("#tipo-cardio").innerHTML=tipos.map(t=>'<option>'+esc(t)+'</option>').join("")+'<option value="outro">Outra atividade</option>';
    const conhecido=!card?.tipoCardio||tipos.includes(card.tipoCardio);
    f.tipoCardio.value=conhecido?(card?.tipoCardio||"Caminhada"):"outro";f.outraAtividade.value=conhecido?"":card.tipoCardio;
    $("#outra-atividade-wrap").hidden=f.tipoCardio.value!=="outro";f.intensidade.value=card?.intensidade||"moderada";f.distanciaKm.value=card?.distanciaKm??"";f.concluido.checked=card?.concluido??false;
    $("#titulo-itens").textContent=tipo==="treino"?"Exercícios":"Ingredientes";
    $("#add-item").textContent=tipo==="treino"?"+ Adicionar exercício":"+ Adicionar ingrediente";
    const lista=$("#lista-itens");lista.innerHTML="";
    if(tipo!=="cardio"){
      const itens=(tipo==="treino"?card?.exercicios:card?.itens)||[];
      (itens.length?itens:[{}]).forEach(it=>lista.appendChild(tipo==="treino"?linhaExercicio(it):linhaIngrediente(it)));
    }
    atualizarTotaisEditor();
    desenharCores();$("#origem-api").textContent="Salvo na sua conta";f.querySelector('[type="submit"]').textContent="Salvar "+NOMES[tipo];
    editor.showModal();f.titulo.focus();
  }
  function desenharCores() {
    $("#seletor-cor").innerHTML=CORES.map(c=>'<button type="button" class="bolinha cor-'+c+' '+(edicao.cor===c?"selecionada":"")+'" data-cor="'+c+'" title="'+c+'" aria-label="Cor '+c+'" aria-pressed="'+(edicao.cor===c)+'"></button>').join("");
  }
  $("#seletor-cor").onclick=e=>{const b=e.target.closest("[data-cor]");if(b){edicao.cor=b.dataset.cor;desenharCores();}};
  $("#tipo-cardio").onchange=()=>$("#outra-atividade-wrap").hidden=f.tipoCardio.value!=="outro";
  $("#add-item").onclick=()=>{$("#lista-itens").appendChild(edicao.tipo==="treino"?linhaExercicio():linhaIngrediente());};
  $("#cancelar").onclick=$("#fechar-editor").onclick=()=>editor.close();
  function lerFormulario() {
    const base={titulo:f.titulo.value.trim(),dia:f.dia.value,cor:edicao.cor,fixado:edicao.fixado,notas:f.notas.value};
    if(!base.titulo)throw new Error("Dê um título ao seu planejamento.");
    if(edicao.tipo==="cardio")return {...base,modalidade:"cardio",tipoCardio:f.tipoCardio.value==="outro"?f.outraAtividade.value.trim():f.tipoCardio.value,intensidade:f.intensidade.value,duracaoMin:numero(f.duracaoMin.value),distanciaKm:numero(f.distanciaKm.value),concluido:f.concluido.checked};
    const campo=(l,n)=>l.querySelector('[data-campo="'+n+'"]');
    if(edicao.tipo==="treino"){
      const grupos=gruposSelecionados();
      return {...base,modalidade:"musculacao",gruposMusculares:grupos,grupoMuscular:grupos.join(", "),duracaoMin:numero(f.duracaoMin.value),
        exercicios:$$("#lista-itens .item-exercicio").filter(l=>campo(l,"nome").value).map(l=>({nome:campo(l,"nome").value,series:numero(campo(l,"series").value),repeticoes:campo(l,"repeticoes").value.trim(),carga:numero(campo(l,"carga").value),tecnica:campo(l,"tecnica").value==="__outra__"?campo(l,"outra-tecnica").value.trim():campo(l,"tecnica").value,feito:campo(l,"feito").checked}))};
    }
    return {...base,tipo:f.tipo.value,itens:$$("#lista-itens .item-refeicao").map(l=>{
      const sel=campo(l,"alimento").value,quantidade=numero(campo(l,"quantidade").value),feito=campo(l,"feito").checked;
      if(sel==="outro")return {texto:campo(l,"texto").value.trim(),quantidade,feito,nutrientes:Object.fromEntries(NUTRIENTES.map(n=>[n.k,Number(l.querySelector('[data-nutri="'+n.k+'"]').value)||0]))};
      return sel?{alimentoId:Number(sel),quantidade,feito}:null;
    }).filter(Boolean)};
  }
  f.addEventListener("submit",async e=>{
    e.preventDefault();const b=f.querySelector('[type="submit"]');if(b.disabled)return;b.disabled=true;$("#erro-editor").textContent="";
    try{
      if(edicao.tipo==="treino"){
        if($("#nome-grupo-personalizado").value.trim())await salvarGrupo();
        for(const linha of $$("#lista-itens .item-exercicio"))if(linha.querySelector('[data-campo="nome"]').value==="__custom__")await salvarExercicioPersonalizado(linha);
      }
      const dados=lerFormulario(),{tipo,id}=edicao;
      const salvo=id?await salvar(tipo,id,dados):tipo==="refeicao"?await apiPython.criarRefeicao(dados):tipo==="cardio"?await apiJava.criarCardio(dados):await apiJava.criarTreino(dados);
      substituir(tipo,salvo);editor.close();toast(id?"Planejamento atualizado.":tipo==="refeicao"?"Sua refeição foi salva.":"Seu "+NOMES[tipo]+" foi salvo.");renderizar();await atualizarResumos();
    }catch(erro){$("#erro-editor").textContent=erro.message;}finally{b.disabled=false;}
  });
  $("#filtro-tipo").onclick=e=>{const b=e.target.closest("[data-tipo]");if(!b)return;estado.filtroTipo=b.dataset.tipo;atualizarFiltros();renderizar();};
  $("#filtro-visao").onclick=e=>{const b=e.target.closest("[data-visao]");if(!b)return;estado.visao=b.dataset.visao;atualizarFiltros();renderizar();};
  $("#busca").oninput=e=>{estado.busca=e.target.value;renderizar();};
  $("#novo-treino").onclick=()=>abrirEditor("treino");$("#novo-cardio").onclick=()=>abrirEditor("cardio");$("#nova-refeicao").onclick=()=>abrirEditor("refeicao");$("#btn-sair").onclick=sair;
  $("#nome-usuario").textContent=usuario.nome;$("#avatar").textContent=usuario.nome.trim().slice(0,2).toUpperCase();
  $("#saudacao").textContent="Olá, "+usuario.nome.split(" ")[0]+". Vamos cuidar da sua semana?";
  $("#status-python").title=API_PYTHON;$("#status-java").title=API_JAVA;
  atualizarFiltros();carregarTudo();setInterval(verificarApis,15000);
})();
