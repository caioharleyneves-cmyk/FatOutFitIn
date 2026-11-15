"""
FatOutFitIn - API Python (Flask)

Responsável por:
  * Usuários (cadastro e login)
  * Cards de refeições (preparo de refeições semanais)
  * Resumo nutricional da semana

Roda na porta 5000. Os dados ficam em um banco SQLite local (fatoutfitin.db).
"""
import json
import os
import re
import sqlite3

from flask import Flask, g, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("FOFI_DB", os.path.join(BASE_DIR, "fatoutfitin.db"))

DIAS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
TIPOS = ["cafe", "almoco", "lanche", "jantar", "pre-treino", "pos-treino", "ceia"]
CORES = ["padrao", "vermelho", "laranja", "amarelo", "verde", "azul", "roxo", "rosa"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

app = Flask(__name__)
app.json.ensure_ascii = False
app.json.sort_keys = False
CORS(app)


# --------------------------------------------------------------------------- #
# Banco de dados
# --------------------------------------------------------------------------- #
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        # Garante as tabelas mesmo que o arquivo do banco seja apagado com a API rodando
        criar_tabelas(g.db)
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    criar_tabelas(db)
    db.close()


def criar_tabelas(db):
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nome        TEXT NOT NULL,
            email       TEXT NOT NULL UNIQUE,
            senha_hash  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS refeicoes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            titulo      TEXT NOT NULL,
            dia         TEXT NOT NULL,
            tipo        TEXT NOT NULL,
            cor         TEXT NOT NULL DEFAULT 'padrao',
            fixado      INTEGER NOT NULL DEFAULT 0,
            calorias    INTEGER NOT NULL DEFAULT 0,
            proteinas   INTEGER NOT NULL DEFAULT 0,
            itens       TEXT NOT NULL DEFAULT '[]',
            notas       TEXT NOT NULL DEFAULT ''
        );
        """
    )
    db.commit()


# --------------------------------------------------------------------------- #
# Erros: sempre devolvem JSON, nunca derrubam a aplicação
# --------------------------------------------------------------------------- #
class ApiError(Exception):
    def __init__(self, status, mensagem):
        super().__init__(mensagem)
        self.status = status
        self.mensagem = mensagem


@app.errorhandler(ApiError)
def handle_api_error(err):
    return jsonify({"erro": err.mensagem, "status": err.status}), err.status


@app.errorhandler(HTTPException)
def handle_http_error(err):
    mensagens = {404: "Rota não encontrada.", 405: "Método não permitido nesta rota."}
    msg = mensagens.get(err.code, err.description)
    return jsonify({"erro": msg, "status": err.code}), err.code


@app.errorhandler(Exception)
def handle_unexpected(err):
    app.logger.exception(err)
    return jsonify({"erro": "Erro interno no servidor.", "status": 500}), 500


# --------------------------------------------------------------------------- #
# Helpers de validação
# --------------------------------------------------------------------------- #
def corpo_json():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise ApiError(400, "O corpo da requisição deve ser um JSON válido (objeto).")
    return dados


def usuario_atual():
    """Lê o usuário logado do cabeçalho X-Usuario-Id e confere se existe."""
    bruto = request.headers.get("X-Usuario-Id", "")
    if not bruto.isdigit():
        raise ApiError(401, "Cabeçalho X-Usuario-Id ausente ou inválido. Faça login.")
    usuario = get_db().execute("SELECT id FROM usuarios WHERE id = ?", (int(bruto),)).fetchone()
    if usuario is None:
        raise ApiError(401, "Usuário não encontrado. Faça login novamente.")
    return usuario["id"]


def inteiro_nao_negativo(valor, campo):
    if valor is None or valor == "":
        return 0
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ApiError(400, f"O campo '{campo}' deve ser um número inteiro.")
    if numero < 0 or numero > 100000:
        raise ApiError(400, f"O campo '{campo}' deve estar entre 0 e 100000.")
    return numero


def validar_refeicao(dados):
    titulo = str(dados.get("titulo", "")).strip()
    if not titulo:
        raise ApiError(400, "O campo 'titulo' é obrigatório.")
    if len(titulo) > 80:
        raise ApiError(400, "O 'titulo' deve ter no máximo 80 caracteres.")

    dia = dados.get("dia")
    if dia not in DIAS:
        raise ApiError(400, f"'dia' inválido. Use um destes: {', '.join(DIAS)}.")

    tipo = dados.get("tipo")
    if tipo not in TIPOS:
        raise ApiError(400, f"'tipo' inválido. Use um destes: {', '.join(TIPOS)}.")

    cor = dados.get("cor") or "padrao"
    if cor not in CORES:
        raise ApiError(400, f"'cor' inválida. Use uma destas: {', '.join(CORES)}.")

    itens_brutos = dados.get("itens", [])
    if not isinstance(itens_brutos, list):
        raise ApiError(400, "'itens' deve ser uma lista.")
    itens = []
    for item in itens_brutos:
        if not isinstance(item, dict) or not str(item.get("texto", "")).strip():
            raise ApiError(400, "Cada item precisa ter um 'texto' não vazio.")
        itens.append({"texto": str(item["texto"]).strip()[:120], "feito": bool(item.get("feito", False))})

    return {
        "titulo": titulo,
        "dia": dia,
        "tipo": tipo,
        "cor": cor,
        "fixado": 1 if dados.get("fixado") else 0,
        "calorias": inteiro_nao_negativo(dados.get("calorias"), "calorias"),
        "proteinas": inteiro_nao_negativo(dados.get("proteinas"), "proteinas"),
        "itens": json.dumps(itens, ensure_ascii=False),
        "notas": str(dados.get("notas", "") or "")[:500],
    }


def refeicao_para_json(row):
    return {
        "id": row["id"],
        "titulo": row["titulo"],
        "dia": row["dia"],
        "tipo": row["tipo"],
        "cor": row["cor"],
        "fixado": bool(row["fixado"]),
        "calorias": row["calorias"],
        "proteinas": row["proteinas"],
        "itens": json.loads(row["itens"]),
        "notas": row["notas"],
    }


def buscar_refeicao(refeicao_id, usuario_id):
    row = get_db().execute(
        "SELECT * FROM refeicoes WHERE id = ? AND usuario_id = ?", (refeicao_id, usuario_id)
    ).fetchone()
    if row is None:
        raise ApiError(404, f"Refeição {refeicao_id} não encontrada.")
    return row


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "api": "python", "porta": 5000})


# ---- Usuários ------------------------------------------------------------- #
@app.post("/api/usuarios")
def cadastrar_usuario():
    dados = corpo_json()
    nome = str(dados.get("nome", "")).strip()
    email = str(dados.get("email", "")).strip().lower()
    senha = str(dados.get("senha", ""))

    if not nome:
        raise ApiError(400, "O campo 'nome' é obrigatório.")
    if not EMAIL_RE.match(email):
        raise ApiError(400, "Informe um e-mail válido.")
    if len(senha) < 4:
        raise ApiError(400, "A senha deve ter pelo menos 4 caracteres.")

    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
            (nome, email, generate_password_hash(senha)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise ApiError(409, "Já existe um usuário com este e-mail.")

    return jsonify({"id": cur.lastrowid, "nome": nome, "email": email}), 201


@app.post("/api/login")
def login():
    dados = corpo_json()
    email = str(dados.get("email", "")).strip().lower()
    senha = str(dados.get("senha", ""))
    if not email or not senha:
        raise ApiError(400, "Informe e-mail e senha.")

    row = get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row is None or not check_password_hash(row["senha_hash"], senha):
        raise ApiError(401, "E-mail ou senha incorretos.")

    return jsonify({"id": row["id"], "nome": row["nome"], "email": row["email"]})


# ---- Refeições ------------------------------------------------------------ #
@app.get("/api/refeicoes")
def listar_refeicoes():
    usuario_id = usuario_atual()
    sql = "SELECT * FROM refeicoes WHERE usuario_id = ?"
    params = [usuario_id]

    dia = request.args.get("dia")
    if dia:
        if dia not in DIAS:
            raise ApiError(400, f"Filtro 'dia' inválido. Use um destes: {', '.join(DIAS)}.")
        sql += " AND dia = ?"
        params.append(dia)

    sql += " ORDER BY fixado DESC, id DESC"
    rows = get_db().execute(sql, params).fetchall()
    return jsonify([refeicao_para_json(r) for r in rows])


@app.get("/api/refeicoes/<int:refeicao_id>")
def obter_refeicao(refeicao_id):
    return jsonify(refeicao_para_json(buscar_refeicao(refeicao_id, usuario_atual())))


@app.post("/api/refeicoes")
def criar_refeicao():
    usuario_id = usuario_atual()
    r = validar_refeicao(corpo_json())
    db = get_db()
    cur = db.execute(
        """INSERT INTO refeicoes
           (usuario_id, titulo, dia, tipo, cor, fixado, calorias, proteinas, itens, notas)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (usuario_id, r["titulo"], r["dia"], r["tipo"], r["cor"], r["fixado"],
         r["calorias"], r["proteinas"], r["itens"], r["notas"]),
    )
    db.commit()
    return jsonify(refeicao_para_json(buscar_refeicao(cur.lastrowid, usuario_id))), 201


@app.put("/api/refeicoes/<int:refeicao_id>")
def atualizar_refeicao(refeicao_id):
    usuario_id = usuario_atual()
    buscar_refeicao(refeicao_id, usuario_id)
    r = validar_refeicao(corpo_json())
    db = get_db()
    db.execute(
        """UPDATE refeicoes SET titulo=?, dia=?, tipo=?, cor=?, fixado=?, calorias=?,
           proteinas=?, itens=?, notas=? WHERE id=? AND usuario_id=?""",
        (r["titulo"], r["dia"], r["tipo"], r["cor"], r["fixado"], r["calorias"],
         r["proteinas"], r["itens"], r["notas"], refeicao_id, usuario_id),
    )
    db.commit()
    return jsonify(refeicao_para_json(buscar_refeicao(refeicao_id, usuario_id)))


@app.delete("/api/refeicoes/<int:refeicao_id>")
def excluir_refeicao(refeicao_id):
    usuario_id = usuario_atual()
    buscar_refeicao(refeicao_id, usuario_id)
    db = get_db()
    db.execute("DELETE FROM refeicoes WHERE id = ? AND usuario_id = ?", (refeicao_id, usuario_id))
    db.commit()
    return jsonify({"mensagem": f"Refeição {refeicao_id} excluída."})


@app.get("/api/refeicoes/resumo")
def resumo_refeicoes():
    """Totais de calorias, proteínas e refeições por dia da semana."""
    usuario_id = usuario_atual()
    rows = get_db().execute(
        """SELECT dia, COUNT(*) AS qtd, SUM(calorias) AS kcal, SUM(proteinas) AS prot
           FROM refeicoes WHERE usuario_id = ? GROUP BY dia""",
        (usuario_id,),
    ).fetchall()
    por_dia = {d: {"dia": d, "refeicoes": 0, "calorias": 0, "proteinas": 0} for d in DIAS}
    for row in rows:
        por_dia[row["dia"]] = {
            "dia": row["dia"],
            "refeicoes": row["qtd"],
            "calorias": row["kcal"] or 0,
            "proteinas": row["prot"] or 0,
        }
    dias = [por_dia[d] for d in DIAS]
    total_kcal = sum(d["calorias"] for d in dias)
    return jsonify({
        "dias": dias,
        "totalRefeicoes": sum(d["refeicoes"] for d in dias),
        "totalCalorias": total_kcal,
        "totalProteinas": sum(d["proteinas"] for d in dias),
        "mediaCaloriasDia": round(total_kcal / 7),
    })


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
