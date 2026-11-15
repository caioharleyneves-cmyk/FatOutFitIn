"""
FatOutFitIn - API Python (Flask)

Responsável por:
  * Usuários (cadastro e login)
  * Catálogo de alimentos com informações nutricionais
  * Cards de refeições (preparo de refeições semanais), com cálculo de
    kcal, proteínas, carboidratos, gorduras, fibras e sódio por ingrediente
  * Resumo nutricional da semana

Roda na porta 5000. Os dados ficam em um banco SQLite local (fatoutfitin.db).
"""
import json
import os
import re
import sqlite3
import unicodedata

from flask import Flask, g, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from alimentos import ALIMENTOS, ALIMENTOS_POR_ID, CATEGORIAS, NUTRIENTES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("FOFI_DB", os.path.join(BASE_DIR, "fatoutfitin.db"))

DIAS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
TIPOS = ["cafe", "almoco", "lanche", "jantar", "pre-treino", "pos-treino", "ceia"]
CORES = ["padrao", "vermelho", "laranja", "amarelo", "verde", "azul", "roxo", "rosa"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Nutriente -> coluna no banco (kcal fica na coluna "calorias", que já existia)
COLUNAS = {"kcal": "calorias", "proteinas": "proteinas", "carboidratos": "carboidratos",
           "gorduras": "gorduras", "fibras": "fibras", "sodio": "sodio"}
# Limites aceitos para valores informados manualmente (ingrediente "Outro")
LIMITES = {"kcal": 10000, "proteinas": 1000, "carboidratos": 1000, "gorduras": 1000,
           "fibras": 500, "sodio": 50000}

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
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id    INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            titulo        TEXT NOT NULL,
            dia           TEXT NOT NULL,
            tipo          TEXT NOT NULL,
            cor           TEXT NOT NULL DEFAULT 'padrao',
            fixado        INTEGER NOT NULL DEFAULT 0,
            calorias      REAL NOT NULL DEFAULT 0,
            proteinas     REAL NOT NULL DEFAULT 0,
            carboidratos  REAL NOT NULL DEFAULT 0,
            gorduras      REAL NOT NULL DEFAULT 0,
            fibras        REAL NOT NULL DEFAULT 0,
            sodio         REAL NOT NULL DEFAULT 0,
            itens         TEXT NOT NULL DEFAULT '[]',
            notas         TEXT NOT NULL DEFAULT ''
        );
        """
    )
    # Migração: bancos criados pela versão anterior não tinham estas colunas
    existentes = {row[1] for row in db.execute("PRAGMA table_info(refeicoes)")}
    for coluna in ("carboidratos", "gorduras", "fibras", "sodio"):
        if coluna not in existentes:
            db.execute(f"ALTER TABLE refeicoes ADD COLUMN {coluna} REAL NOT NULL DEFAULT 0")
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


def numero(valor, campo, minimo, maximo, padrao=0.0):
    """Converte para float validando o intervalo; vazio/None vira o padrão."""
    if valor is None or valor == "":
        return padrao
    if isinstance(valor, bool):
        raise ApiError(400, f"O campo '{campo}' deve ser numérico.")
    try:
        n = float(valor)
    except (TypeError, ValueError):
        raise ApiError(400, f"O campo '{campo}' deve ser numérico.")
    if n != n or n < minimo or n > maximo:  # n != n detecta NaN
        raise ApiError(400, f"O campo '{campo}' deve estar entre {minimo:g} e {maximo:g}.")
    return n


def arredondar(nutriente, valor):
    # kcal e sódio (mg) inteiros; gramas com 1 casa decimal
    return round(valor) if nutriente in ("kcal", "sodio") else round(valor, 1)


def nutrientes_zerados():
    return {n: 0 for n in NUTRIENTES}


def calcular_nutrientes(alimento, quantidade):
    fator = quantidade / 100
    return {n: arredondar(n, alimento["por100"][n] * fator) for n in NUTRIENTES}


def validar_item(item, posicao):
    """
    Dois formatos de ingrediente:
      * do catálogo:  {"alimentoId": 5, "quantidade": 150, "feito": false}
                      -> nome e nutrientes são calculados pela API
      * "Outro":      {"texto": "Molho caseiro", "quantidade": 50,
                       "nutrientes": {"kcal": 40, "proteinas": 1, ...}, "feito": false}
                      -> valores informados pelo usuário para aquela quantidade
    """
    if not isinstance(item, dict):
        raise ApiError(400, f"O item {posicao} deve ser um objeto.")
    feito = bool(item.get("feito", False))
    alimento_id = item.get("alimentoId")

    if alimento_id not in (None, ""):
        try:
            alimento = ALIMENTOS_POR_ID.get(int(alimento_id))
        except (TypeError, ValueError):
            alimento = None
        if alimento is None:
            raise ApiError(400, f"Item {posicao}: alimento {alimento_id} não existe no catálogo.")
        quantidade = numero(item.get("quantidade"), f"itens[{posicao}].quantidade", 1, 5000,
                            padrao=alimento["porcao"])
        return {
            "alimentoId": alimento["id"],
            "texto": alimento["nome"],
            "quantidade": round(quantidade, 1),
            "unidade": alimento["unidade"],
            "feito": feito,
            "nutrientes": calcular_nutrientes(alimento, quantidade),
        }

    texto = str(item.get("texto", "")).strip()
    if not texto:
        raise ApiError(400, f"Item {posicao}: informe um alimento do catálogo ou o nome do ingrediente.")
    quantidade = numero(item.get("quantidade"), f"itens[{posicao}].quantidade", 0, 5000, padrao=None)
    informados = item.get("nutrientes") or {}
    if not isinstance(informados, dict):
        raise ApiError(400, f"Item {posicao}: 'nutrientes' deve ser um objeto.")
    nutrientes = {
        n: arredondar(n, numero(informados.get(n), f"itens[{posicao}].nutrientes.{n}", 0, LIMITES[n]))
        for n in NUTRIENTES
    }
    return {
        "alimentoId": None,
        "texto": texto[:120],
        "quantidade": None if quantidade is None else round(quantidade, 1),
        "unidade": "g",
        "feito": feito,
        "nutrientes": nutrientes,
    }


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
    if len(itens_brutos) > 50:
        raise ApiError(400, "Uma refeição pode ter no máximo 50 itens.")
    itens = [validar_item(item, i + 1) for i, item in enumerate(itens_brutos)]

    # Totais da refeição = soma dos ingredientes
    totais = {n: arredondar(n, sum(i["nutrientes"][n] for i in itens)) for n in NUTRIENTES}

    return {
        "titulo": titulo,
        "dia": dia,
        "tipo": tipo,
        "cor": cor,
        "fixado": 1 if dados.get("fixado") else 0,
        "itens": json.dumps(itens, ensure_ascii=False),
        "notas": str(dados.get("notas", "") or "")[:500],
        **{COLUNAS[n]: v for n, v in totais.items()},
    }


def item_compativel(item):
    """Itens salvos pela versão antiga só tinham texto/feito."""
    if "nutrientes" not in item:
        item = {"alimentoId": None, "texto": item.get("texto", ""), "quantidade": None,
                "unidade": "g", "feito": bool(item.get("feito")), "nutrientes": nutrientes_zerados()}
    return item


def refeicao_para_json(row):
    return {
        "id": row["id"],
        "titulo": row["titulo"],
        "dia": row["dia"],
        "tipo": row["tipo"],
        "cor": row["cor"],
        "fixado": bool(row["fixado"]),
        "nutrientes": {n: arredondar(n, row[COLUNAS[n]] or 0) for n in NUTRIENTES},
        "itens": [item_compativel(i) for i in json.loads(row["itens"])],
        "notas": row["notas"],
    }


def buscar_refeicao(refeicao_id, usuario_id):
    row = get_db().execute(
        "SELECT * FROM refeicoes WHERE id = ? AND usuario_id = ?", (refeicao_id, usuario_id)
    ).fetchone()
    if row is None:
        raise ApiError(404, f"Refeição {refeicao_id} não encontrada.")
    return row


def sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


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


# ---- Catálogo de alimentos ------------------------------------------------ #
@app.get("/api/alimentos")
def listar_alimentos():
    """Lista o catálogo (valores por 100 g/ml). Filtros: ?busca=frango&categoria=Proteínas"""
    resultado = ALIMENTOS
    categoria = request.args.get("categoria")
    if categoria:
        if categoria not in CATEGORIAS:
            raise ApiError(400, f"Categoria inválida. Use uma destas: {', '.join(CATEGORIAS)}.")
        resultado = [a for a in resultado if a["categoria"] == categoria]
    busca = sem_acento(request.args.get("busca", "").strip())
    if busca:
        resultado = [a for a in resultado if busca in sem_acento(a["nome"])]
    return jsonify(resultado)


@app.get("/api/alimentos/<int:alimento_id>")
def obter_alimento(alimento_id):
    """Detalhe do alimento; com ?quantidade=150 devolve também os nutrientes para essa quantidade."""
    alimento = ALIMENTOS_POR_ID.get(alimento_id)
    if alimento is None:
        raise ApiError(404, f"Alimento {alimento_id} não encontrado.")
    resposta = dict(alimento)
    if "quantidade" in request.args:
        quantidade = numero(request.args.get("quantidade"), "quantidade", 1, 5000)
        resposta["quantidade"] = quantidade
        resposta["nutrientes"] = calcular_nutrientes(alimento, quantidade)
    return jsonify(resposta)


# ---- Refeições ------------------------------------------------------------ #
def _colunas_refeicao():
    return ["titulo", "dia", "tipo", "cor", "fixado", "itens", "notas", *COLUNAS.values()]


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
    colunas = _colunas_refeicao()
    db = get_db()
    cur = db.execute(
        f"INSERT INTO refeicoes (usuario_id, {', '.join(colunas)}) "
        f"VALUES (?, {', '.join('?' for _ in colunas)})",
        (usuario_id, *[r[c] for c in colunas]),
    )
    db.commit()
    return jsonify(refeicao_para_json(buscar_refeicao(cur.lastrowid, usuario_id))), 201


@app.put("/api/refeicoes/<int:refeicao_id>")
def atualizar_refeicao(refeicao_id):
    usuario_id = usuario_atual()
    buscar_refeicao(refeicao_id, usuario_id)
    r = validar_refeicao(corpo_json())
    colunas = _colunas_refeicao()
    db = get_db()
    db.execute(
        f"UPDATE refeicoes SET {', '.join(f'{c} = ?' for c in colunas)} WHERE id = ? AND usuario_id = ?",
        (*[r[c] for c in colunas], refeicao_id, usuario_id),
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
    """Totais de kcal e macronutrientes por dia da semana, total e média diária."""
    usuario_id = usuario_atual()
    somas = ", ".join(f"SUM({c}) AS {n}" for n, c in COLUNAS.items())
    rows = get_db().execute(
        f"SELECT dia, COUNT(*) AS qtd, {somas} FROM refeicoes WHERE usuario_id = ? GROUP BY dia",
        (usuario_id,),
    ).fetchall()

    por_dia = {d: {"dia": d, "refeicoes": 0, "nutrientes": nutrientes_zerados()} for d in DIAS}
    for row in rows:
        por_dia[row["dia"]] = {
            "dia": row["dia"],
            "refeicoes": row["qtd"],
            "nutrientes": {n: arredondar(n, row[n] or 0) for n in NUTRIENTES},
        }
    dias = [por_dia[d] for d in DIAS]
    total = {n: arredondar(n, sum(d["nutrientes"][n] for d in dias)) for n in NUTRIENTES}
    return jsonify({
        "dias": dias,
        "totalRefeicoes": sum(d["refeicoes"] for d in dias),
        "total": total,
        "mediaDiaria": {n: arredondar(n, v / 7) for n, v in total.items()},
    })


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
