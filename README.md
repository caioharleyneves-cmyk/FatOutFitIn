# 🔥 FatOutFitIn

Mural de notas no estilo Google Keep para organizar **rotinas de academia** e **preparo de refeições semanais**, usando um sistema baseado em cards.

Cada card representa um treino ou uma refeição de um dia da semana, com checklist (exercícios / ingredientes), cor, fixação no topo, notas e progresso. A plataforma também mostra um resumo da semana (treinos, séries, dias de descanso, calorias e proteínas).

## Planejamento mais simples

- Login e mural com visual claro e responsivo, sem o GIF de fundo.
- Um botão abre os sete dias em balões, tanto no filtro do mural quanto no editor.
- Musculação: selecione vários grupos musculares e exercícios conhecidos. Grupos e exercícios personalizados ficam salvos na conta.
- Cada exercício pode registrar uma técnica avançada opcional, como Drop set ou Rest-pause, ou uma técnica digitada pelo usuário.
- Cardio: cards próprios com atividade, duração, intensidade, distância opcional e conclusão.

O catálogo pessoal fica em `api-java/data/catalogo-personalizado.json`, separado por
usuário. Os cards de cardio são armazenados junto aos treinos no arquivo já
existente. Treinos anteriores continuam compatíveis com a nova versão.

Se uma versão antiga estiver aberta, pressione Enter na janela do iniciador para
encerrá-la e abra `INICIAR.cmd` novamente. A Java será recompilada automaticamente.

## 👥 Integrantes

| Nome | Responsabilidade |
|------|------------------|
| _Caio Harley_ | _ex.: API Python_ |
| _Guilherme Rodrigues_ | _ex.: API Java_ |
| _Serra_ | _ex.: Front-end_ |

## 🛠️ Tecnologias

| Parte | Tecnologias | Porta |
|-------|-------------|-------|
| `api-python/` | Python 3.10+, Flask, Flask-CORS, PyJWT, SQLite | **5000** |
| `api-java/` | Java 17+, Spring Boot 3.5, java-jwt (Maven Wrapper incluso) | **8080** |
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
| Cards de cardio, intensidade, distância e conclusão | ☕ Java |
| Catálogo de exercícios, grupos e opções personalizadas da conta | ☕ Java |

O login devolve um token de sessão JWT com duração de 8 horas. O front-end envia
`Authorization: Bearer <token>` nas duas APIs. Cada API verifica a assinatura,
o emissor, o público e a validade do token; o ID do usuário vem da sessão verificada.
Enviar somente `X-Usuario-Id` não autentica uma requisição.

Para executar localmente, a primeira API iniciada cria automaticamente a chave
em `.local/auth-secret`, na raiz do projeto; a outra usa a mesma chave. Esse arquivo
é privado e ignorado pelo Git. Inicie cada API a partir de sua pasta, como abaixo.
Se as APIs estiverem em máquinas diferentes, configure `FOFI_AUTH_SECRET` com o
mesmo segredo aleatório de pelo menos 32 bytes nos dois ambientes.
Ao atualizar de uma versão anterior, faça login novamente.

## ▶️ Como executar

### Forma mais fácil no Windows

1. Instale **Python 3.10+** e **JDK 17+**, caso ainda não estejam instalados.
2. Extraia o ZIP inteiro para uma pasta.
3. Dê dois cliques em **`INICIAR.cmd`**, na raiz do projeto.
4. Aguarde: as dependências são instaladas e o navegador abre automaticamente.
5. Para encerrar as duas APIs e a página, pressione **Enter** na janela do iniciador.

O iniciador escolhe portas livres e configura o front-end automaticamente. Não
é preciso editar endereços, ativar o ambiente virtual ou abrir três terminais.
Na primeira execução é necessário ter internet; nas seguintes, o ambiente e a
compilação são reaproveitados. O guia completo está em **GUIA-PARA-RODAR.md**.

Também é possível iniciar por um terminal na raiz do projeto:

```powershell
python iniciar.py
```

### Execução manual (alternativa)

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

Se a porta 8080 já estiver em uso, inicie com
`.\mvnw.cmd spring-boot:run "-Dspring-boot.run.arguments=--server.port=8081"`
e ajuste `API_JAVA` em `frontend/js/api.js` para `http://localhost:8081/api`.

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
| POST | `/api/login` | Login `{email, senha}` → `{id, nome, email, token}` |
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
| GET | `/api/catalogo-treinos` | Grupos, exercícios, técnicas, atividades de cardio e opções pessoais |
| POST | `/api/catalogo-treinos/personalizados` | Salva `{tipo: "grupo" ou "exercicio", nome}` para o usuário |
| GET | `/api/cardios` | Lista cardios; aceita filtro `?dia=seg` |
| GET | `/api/cardios/{id}` | Consulta um cardio da conta |
| POST | `/api/cardios` | Cria cardio |
| PUT | `/api/cardios/{id}` | Edita cardio |
| PATCH | `/api/cardios/{id}/concluir` | Alterna a conclusão do cardio |
| DELETE | `/api/cardios/{id}` | Exclui cardio |

Exemplo de corpo de treino:

```json
{
  "titulo": "Treino A",
  "dia": "seg",
  "gruposMusculares": ["Peito", "Tríceps"],
  "duracaoMin": 60,
  "cor": "laranja",
  "fixado": true,
  "exercicios": [
    { "nome": "Supino reto", "series": 4, "repeticoes": "8-10", "carga": 40, "feito": false, "tecnica": "Drop set" }
  ],
  "notas": "Descanso de 90s"
}
```

Exemplo com `curl`:

```bash
curl -H "Authorization: Bearer SEU_TOKEN" http://localhost:8080/api/treinos/resumo
curl -H "Authorization: Bearer SEU_TOKEN" http://localhost:5000/api/refeicoes/resumo
```

## Testes de integração

Com as duas APIs rodando, execute da raiz do repositório:

```powershell
api-python\.venv\Scripts\python.exe tests/test_api.py
# Se a API Java estiver na porta alternativa:
api-python\.venv\Scripts\python.exe tests/test_api.py --java-port 8081
# Catálogos, grupos, técnicas e cardio (use portas exibidas pelo iniciador):
api-python\.venv\Scripts\python.exe tests/test_catalogo_cardio.py --java-port 8081 --fixture teste-persistencia.json
# Reinicie as APIs e confirme que os registros personalizados foram preservados:
api-python\.venv\Scripts\python.exe tests/test_catalogo_cardio.py --java-port 8081 --fixture teste-persistencia.json --verify-persistence
```

Os testes criam contas e cards fictícios no banco local, verificam CRUD, cálculo
nutricional, isolamento entre contas, validações e sessões inválidas/expiradas.
Os cards válidos são excluídos ao final; as contas de teste ficam no banco.

A suíte adicional de catálogo/cardio deixa registros fictícios para permitir a
verificação após reiniciar as APIs. Execute em dados de teste. Ambas as suítes
aceitam `--python-port` e `--java-port` quando as portas padrão estiverem ocupadas.

### Exemplo de cardio

```json
{
  "titulo": "Caminhada no parque",
  "dia": "seg",
  "tipoCardio": "Caminhada",
  "duracaoMin": 30,
  "intensidade": "leve",
  "distanciaKm": 3,
  "concluido": false,
  "notas": "Percurso ao ar livre"
}
```

Todos os endpoints de catálogo e cardio exigem a mesma sessão assinada usada nos
treinos. As opções pessoais de uma conta não aparecem no catálogo de outra.

## 📁 Estrutura

```
FatOutFitIn/
├── INICIAR.cmd          # dois cliques no Windows
├── iniciar.py           # instalação, portas e inicialização automática
├── GUIA-PARA-RODAR.md   # guia passo a passo e solução de problemas
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
└── README.md
```
