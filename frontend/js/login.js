// Tela de login / cadastro -> API Python
if (getUsuario()) window.location.href = "principal.html";

const form = document.getElementById("form-acesso");
const campoNome = form.querySelector(".campo-nome");
const botao = document.getElementById("login");
const mensagem = document.getElementById("mensagem");
let modo = "login";

document.querySelectorAll(".aba").forEach((aba) => {
  aba.addEventListener("click", () => {
    modo = aba.dataset.modo;
    document.querySelectorAll(".aba").forEach((a) => a.classList.toggle("ativa", a === aba));
    campoNome.hidden = modo !== "cadastro";
    botao.textContent = modo === "login" ? "Entrar" : "Criar conta";
    form.senha.autocomplete = modo === "login" ? "current-password" : "new-password";
    mensagem.textContent = "";
    document.querySelector(".login-heading h2").textContent = modo === "login" ? "Sua rotina te espera." : "Comece no seu ritmo.";
    document.querySelector(".login-heading p").textContent = modo === "login" ? "Entre para continuar de onde parou." : "Crie sua conta e organize sua primeira semana.";
    if (modo === "cadastro") form.nome.focus();
  });
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  mensagem.textContent = "";
  mensagem.className = "mensagem";
  botao.disabled = true;

  const email = form.email.value.trim();
  const senha = form.senha.value;

  try {
    if (modo === "cadastro") {
      await apiPython.cadastrar({ nome: form.nome.value.trim(), email, senha });
    }
    const usuario = await apiPython.login({ email, senha });
    setUsuario(usuario);
    window.location.href = "principal.html";
  } catch (erro) {
    mensagem.textContent = erro.message;
    mensagem.classList.add("erro");
  } finally {
    botao.disabled = false;
  }
});
