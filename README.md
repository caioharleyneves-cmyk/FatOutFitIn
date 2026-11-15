# 🔥 FatOutFitIn

Mural de notas no estilo Google Keep para organizar **rotinas de academia** e **preparo de refeições semanais**, usando um sistema baseado em cards.

Cada card representa um treino ou uma refeição de um dia da semana, com checklist (exercícios / ingredientes), cor, fixação no topo, notas e progresso. A plataforma também mostra um resumo da semana (treinos, séries, dias de descanso, calorias e proteínas).

## 👥 Integrantes

| Nome | Responsabilidade |
|------|------------------|
| _Integrante 1_ | _ex.: API Python_ |
| _Integrante 2_ | _ex.: API Java_ |
| _Integrante 3_ | _ex.: Front-end_ |

## 🛠️ Tecnologias

| Parte | Tecnologias | Porta |
|-------|-------------|-------|
| `api-python/` | Python 3.10+, Flask, Flask-CORS, SQLite | **5000** |
| `api-java/` | Java 17+, Spring Boot 3.5 (Maven Wrapper incluso) | **8080** |
| `frontend/` | HTML, CSS e JavaScript puro (fetch API) | **5500** |

### Quem faz o quê

| Ação no front-end | API chamada |
|-------------------|-------------|
| Login e cadastro | 🐍 Python |
| Criar / editar / excluir / fixar / colorir **refeições** | 🐍 Python |
| Marcar ingredientes como preparados | 🐍 Python |
| Catálogo de alimentos e cálculo de kcal/macros por ingrediente | 🐍 Python |
| Resumo nutricional (kcal, proteínas, carboidratos, gorduras, fibras e sódio por dia) | 🐍 Python |
| Criar / editar / excluir / fixar / colorir **treinos** | ☕ Java |
| Marcar exercícios como concluídos | ☕ Java |
| Resumo de treinos (séries, minutos, progresso, descanso) | ☕ Java |

O usuário logado é identificado nas duas APIs pelo cabeçalho `X-Usuario-Id` (o `id` devolvido pelo login da API Python).

## ▶️ Como executar

Abra **três terminais**, um para cada parte. Os comandos abaixo partem da raiz do repositório.

### 1. API Python (porta 5000)

Pré-requisito: Python 3.10 ou superior.

```bash
cd api-python
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

A API sobe em `http://localhost:5000`. O banco SQLite (`fatoutfitin.db`) é criado automaticamente.
Teste: `http://localhost:5000/api/health`.

### 2. API Java (porta 8080)

Pré-requisito: JDK 17 ou superior (não é necessário instalar o Maven; o wrapper baixa sozinho).

```bash
cd api-java

# Windows
.\mvnw.cmd spring-boot:run
# Linux / macOS
./mvnw spring-boot:run
```

A API sobe em `http://localhost:8080`. Os treinos ficam salvos em `api-java/data/treinos.json` (criado automaticamente).
Teste: `http://localhost:8080/api/health`.

### 3. Front-end (porta 5500)

```bash
cd frontend
python -m http.server 5500
```

Acesse **http://localhost:5500**, crie uma conta na aba "Criar conta" e comece a montar seu mural.

> Também funciona com a extensão *Live Server* do VS Code (porta 5500). Os indicadores **● Python** e **● Java** no topo do mural ficam verdes quando cada API está no ar.

## 📡 Endpoints

Todas as respostas são JSON. Erros seguem o formato `{"erro": "mensagem", "status": 400}` e não derrubam a aplicação
(400 dado inválido, 401 sem usuário, 404 não encontrado, 409 conflito, 500 erro interno).

### 🐍 API Python — `http://localhost:5000`

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/health` | Verifica se a API está no ar |
| POST | `/api/usuarios` | Cadastra usuário `{nome, email, senha}` |
| POST | `/api/login` | Login `{email, senha}` → `{id, nome, email}` |
| GET | `/api/alimentos` | Catálogo de alimentos com nutrientes por 100 g/ml (filtros `?busca=frango`, `?categoria=Frutas`) |
| GET | `/api/alimentos/{id}` | Detalhe de um alimento; com `?quantidade=150` calcula os nutrientes da porção |
| GET | `/api/refeicoes` | Lista as refeições do usuário (filtro opcional `?dia=seg`) |
| GET | `/api/refeicoes/{id}` | Busca uma refeição |
| POST | `/api/refeicoes` | Cria um card de refeição (a API calcula os nutrientes) |
| PUT | `/api/refeicoes/{id}` | Atualiza um card de refeição (inclui checklist, cor, fixado) |
| DELETE | `/api/refeicoes/{id}` | Exclui um card de refeição |
| GET | `/api/refeicoes/resumo` | Refeições e nutrientes por dia, total da semana e média diária |

**Nutrientes** calculados: `kcal`, `proteinas` (g), `carboidratos` (g), `gorduras` (g), `fibras` (g) e `sodio` (mg).
O catálogo (`api-python/alimentos.py`) tem ~50 alimentos comuns com valores aproximados da tabela TACO/UNICAMP (e USDA quando ausentes).

Cada ingrediente pode ser:
- **do catálogo**: envie `alimentoId` e `quantidade` (g ou ml; se omitida usa a porção sugerida). Nome e nutrientes são calculados pela API.
- **"Outro"**: envie `texto` e os `nutrientes` da quantidade usada, informados pelo usuário.

Exemplo de corpo de refeição:

```json
{
  "titulo": "Marmita de frango",
  "dia": "seg",
  "tipo": "almoco",
  "cor": "verde",
  "fixado": false,
  "itens": [
    { "alimentoId": 1, "quantidade": 150, "feito": false },
    { "alimentoId": 12, "quantidade": 120, "feito": false },
    { "texto": "Molho caseiro", "quantidade": 30, "feito": false,
      "nutrientes": { "kcal": 40, "proteinas": 1, "carboidratos": 5, "gorduras": 2, "fibras": 0.5, "sodio": 300 } }
  ],
  "notas": "Preparar no domingo"
}
```

A resposta traz cada item com seus `nutrientes` e o total da refeição em `nutrientes`.

Valores aceitos — `dia`: `seg, ter, qua, qui, sex, sab, dom` · `tipo`: `cafe, almoco, lanche, jantar, pre-treino, pos-treino, ceia` · `cor`: `padrao, vermelho, laranja, amarelo, verde, azul, roxo, rosa`.

### ☕ API Java — `http://localhost:8080`

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/health` | Verifica se a API está no ar |
| GET | `/api/treinos` | Lista os treinos do usuário (filtro opcional `?dia=seg`) |
| GET | `/api/treinos/{id}` | Busca um treino |
| POST | `/api/treinos` | Cria um card de treino |
| PUT | `/api/treinos/{id}` | Atualiza um card de treino |
| PATCH | `/api/treinos/{id}/exercicios/{indice}` | Marca/desmarca um exercício como concluído |
| DELETE | `/api/treinos/{id}` | Exclui um card de treino |
| GET | `/api/treinos/resumo` | Treinos, séries, minutos, grupos musculares e progresso por dia |

Exemplo de corpo de treino:

```json
{
  "titulo": "Treino A",
  "dia": "seg",
  "grupoMuscular": "Peito e tríceps",
  "duracaoMin": 60,
  "cor": "laranja",
  "fixado": true,
  "exercicios": [
    { "nome": "Supino reto", "series": 4, "repeticoes": "8-10", "carga": 40, "feito": false }
  ],
  "notas": "Descanso de 90s"
}
```

Exemplo com `curl`:

```bash
curl -H "X-Usuario-Id: 1" http://localhost:8080/api/treinos/resumo
curl -H "X-Usuario-Id: 1" http://localhost:5000/api/refeicoes/resumo
```

## 📁 Estrutura

```
FatOutFitIn/
├── api-python/          # Flask: usuários, catálogo de alimentos e refeições
│   ├── app.py
│   ├── alimentos.py     # catálogo nutricional
│   └── requirements.txt
├── api-java/            # Spring Boot: treinos
│   ├── pom.xml
│   ├── mvnw / mvnw.cmd
│   └── src/main/java/br/ime/fatoutfitin/
│       ├── controller/TreinoController.java
│       ├── service/TreinoService.java
│       ├── repository/TreinoRepository.java
│       ├── model/        (Treino, Exercicio)
│       ├── exception/    (ApiException, GlobalExceptionHandler)
│       └── config/CorsConfig.java
├── frontend/
│   ├── index.html       # login / cadastro
│   ├── principal.html   # mural de cards
│   ├── css/styles.css
│   ├── js/api.js        # chamadas às duas APIs
│   ├── js/login.js
│   ├── js/mural.js
│   └── img/
└── README.md
```
