// =====================================================================
// Camada de comunicação com as duas APIs.
//   API Python (Flask)       -> http://localhost:5000  (usuários e refeições)
//   API Java   (Spring Boot) -> http://localhost:8080  (treinos)
// =====================================================================
const API_PYTHON = window.FOFI_CONFIG?.apiPython || "http://localhost:5000/api";
const API_JAVA = window.FOFI_CONFIG?.apiJava || "http://localhost:8080/api";

const SESSAO_KEY = "fofi-usuario";

function getUsuario() {
  try {
    const usuario = JSON.parse(localStorage.getItem(SESSAO_KEY));
    return usuario && typeof usuario.token === "string" && usuario.token ? usuario : null;
  } catch {
    return null;
  }
}

function setUsuario(usuario) {
  localStorage.setItem(SESSAO_KEY, JSON.stringify(usuario));
}

function sair() {
  localStorage.removeItem(SESSAO_KEY);
  window.location.href = "index.html";
}

/**
 * Faz a requisição, envia a sessão assinada no cabeçalho Authorization
 * e transforma respostas de erro ({ "erro": "..." }) em exceções.
 */
async function requisicao(baseUrl, caminho, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  const usuario = getUsuario();
  if (usuario) headers.Authorization = `Bearer ${usuario.token}`;

  let resposta;
  try {
    resposta = await fetch(baseUrl + caminho, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    const nome = `${baseUrl === API_JAVA ? "API Java" : "API Python"} (${new URL(baseUrl).origin})`;
    throw new Error(`Não foi possível conectar à ${nome}. Ela está rodando?`);
  }

  const dados = await resposta.json().catch(() => null);
  if (!resposta.ok) {
    if (resposta.status === 401 && usuario) sair();
    throw new Error(dados?.erro || `Erro ${resposta.status}`);
  }
  return dados;
}

// ---------------------------- API Python ----------------------------
const apiPython = {
  health: () => requisicao(API_PYTHON, "/health"),
  cadastrar: (dados) => requisicao(API_PYTHON, "/usuarios", { method: "POST", body: dados }),
  login: (dados) => requisicao(API_PYTHON, "/login", { method: "POST", body: dados }),
  listarAlimentos: () => requisicao(API_PYTHON, "/alimentos"),
  listarRefeicoes: () => requisicao(API_PYTHON, "/refeicoes"),
  criarRefeicao: (r) => requisicao(API_PYTHON, "/refeicoes", { method: "POST", body: r }),
  atualizarRefeicao: (id, r) => requisicao(API_PYTHON, `/refeicoes/${id}`, { method: "PUT", body: r }),
  excluirRefeicao: (id) => requisicao(API_PYTHON, `/refeicoes/${id}`, { method: "DELETE" }),
  resumoRefeicoes: () => requisicao(API_PYTHON, "/refeicoes/resumo"),
};

// ----------------------------- API Java -----------------------------
const apiJava = {
  health: () => requisicao(API_JAVA, "/health"),
  listarTreinos: () => requisicao(API_JAVA, "/treinos"),
  criarTreino: (t) => requisicao(API_JAVA, "/treinos", { method: "POST", body: t }),
  atualizarTreino: (id, t) => requisicao(API_JAVA, `/treinos/${id}`, { method: "PUT", body: t }),
  alternarExercicio: (id, i) => requisicao(API_JAVA, `/treinos/${id}/exercicios/${i}`, { method: "PATCH" }),
  excluirTreino: (id) => requisicao(API_JAVA, `/treinos/${id}`, { method: "DELETE" }),
  resumoTreinos: () => requisicao(API_JAVA, "/treinos/resumo"),
  catalogo: () => requisicao(API_JAVA, "/catalogo-treinos"),
  salvarPersonalizado: (tipo, nome) => requisicao(API_JAVA, "/catalogo-treinos/personalizados", { method: "POST", body: { tipo, nome } }),
  criarCardio: (c) => requisicao(API_JAVA, "/cardios", { method: "POST", body: c }),
  atualizarCardio: (id, c) => requisicao(API_JAVA, `/cardios/${id}`, { method: "PUT", body: c }),
  concluirCardio: (id) => requisicao(API_JAVA, `/cardios/${id}/concluir`, { method: "PATCH" }),
  excluirCardio: (id) => requisicao(API_JAVA, `/cardios/${id}`, { method: "DELETE" }),
};
