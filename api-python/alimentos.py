"""
Catálogo de alimentos comuns com informações nutricionais POR 100 g (ou 100 ml).

Valores aproximados baseados na Tabela Brasileira de Composição de Alimentos
(TACO/UNICAMP) e, quando ausentes nela, na USDA FoodData Central.

Campos:
  kcal, proteinas (g), carboidratos (g), gorduras (g), fibras (g), sodio (mg)
  porcao          -> quantidade sugerida (g ou ml) ao adicionar o alimento
  porcaoDescricao -> texto de ajuda para a porção sugerida
"""

NUTRIENTES = ["kcal", "proteinas", "carboidratos", "gorduras", "fibras", "sodio"]

_TABELA = [
    # (nome, categoria, unidade, porcao, porcaoDescricao, kcal, prot, carb, gord, fibras, sodio)
    # ---- Proteínas animais ----
    ("Peito de frango grelhado", "Proteínas", "g", 120, "1 filé médio", 159, 32.0, 0.0, 2.5, 0.0, 50),
    ("Coxa de frango assada (sem pele)", "Proteínas", "g", 100, "1 coxa", 191, 26.9, 0.0, 8.5, 0.0, 90),
    ("Patinho bovino grelhado", "Proteínas", "g", 120, "1 bife médio", 219, 35.9, 0.0, 7.3, 0.0, 60),
    ("Carne moída (acém) refogada", "Proteínas", "g", 100, "4 colheres de sopa", 212, 26.7, 0.0, 10.9, 0.0, 52),
    ("Lombo suíno assado", "Proteínas", "g", 100, "1 fatia grossa", 210, 35.7, 0.0, 6.4, 0.0, 39),
    ("Tilápia grelhada", "Proteínas", "g", 120, "1 filé", 128, 26.0, 0.0, 2.7, 0.0, 56),
    ("Salmão grelhado", "Proteínas", "g", 120, "1 posta", 229, 26.1, 0.0, 14.0, 0.0, 98),
    ("Atum em lata (em água)", "Proteínas", "g", 60, "1/2 lata drenada", 116, 25.5, 0.0, 0.8, 0.0, 247),
    ("Ovo de galinha cozido", "Proteínas", "g", 50, "1 unidade", 146, 13.3, 0.6, 9.5, 0.0, 146),
    ("Clara de ovo cozida", "Proteínas", "g", 33, "1 clara", 52, 10.9, 0.7, 0.2, 0.0, 166),
    ("Whey protein (pó)", "Proteínas", "g", 30, "1 scoop", 400, 80.0, 8.0, 6.0, 0.0, 200),

    # ---- Carboidratos ----
    ("Arroz branco cozido", "Carboidratos", "g", 150, "4 colheres de sopa", 128, 2.5, 28.1, 0.2, 1.6, 1),
    ("Arroz integral cozido", "Carboidratos", "g", 150, "4 colheres de sopa", 124, 2.6, 25.8, 1.0, 2.7, 1),
    ("Macarrão cozido", "Carboidratos", "g", 150, "1 escumadeira cheia", 158, 5.8, 30.9, 0.9, 1.8, 1),
    ("Batata-doce cozida", "Carboidratos", "g", 150, "1 unidade média", 77, 0.6, 18.4, 0.1, 2.2, 3),
    ("Batata inglesa cozida", "Carboidratos", "g", 150, "1 unidade média", 52, 1.2, 11.9, 0.0, 1.3, 2),
    ("Mandioca cozida", "Carboidratos", "g", 100, "2 pedaços", 125, 0.6, 30.1, 0.3, 1.6, 1),
    ("Cuscuz de milho cozido", "Carboidratos", "g", 100, "1 fatia", 113, 2.2, 25.3, 0.7, 2.1, 247),
    ("Pão francês", "Carboidratos", "g", 50, "1 unidade", 300, 8.0, 58.6, 3.1, 2.3, 648),
    ("Pão de forma integral", "Carboidratos", "g", 25, "1 fatia", 253, 9.4, 49.9, 3.7, 6.9, 506),
    ("Tapioca (goma)", "Carboidratos", "g", 50, "1 tapioca média", 240, 0.2, 59.5, 0.1, 0.4, 1),
    ("Aveia em flocos", "Carboidratos", "g", 30, "3 colheres de sopa", 394, 13.9, 66.6, 8.5, 9.1, 5),
    ("Granola", "Carboidratos", "g", 40, "4 colheres de sopa", 420, 10.0, 66.0, 13.0, 7.0, 30),

    # ---- Leguminosas ----
    ("Feijão carioca cozido", "Leguminosas", "g", 86, "1 concha", 76, 4.8, 13.6, 0.5, 8.5, 2),
    ("Feijão preto cozido", "Leguminosas", "g", 86, "1 concha", 77, 4.5, 14.0, 0.5, 8.4, 2),
    ("Lentilha cozida", "Leguminosas", "g", 86, "1 concha", 93, 6.3, 16.3, 0.5, 7.9, 1),
    ("Grão-de-bico cozido", "Leguminosas", "g", 80, "4 colheres de sopa", 164, 8.9, 27.4, 2.6, 7.6, 7),

    # ---- Frutas ----
    ("Banana prata", "Frutas", "g", 70, "1 unidade", 98, 1.3, 26.0, 0.1, 2.0, 0),
    ("Maçã", "Frutas", "g", 130, "1 unidade média", 56, 0.3, 15.2, 0.0, 1.3, 0),
    ("Mamão papaia", "Frutas", "g", 150, "1/2 unidade", 40, 0.5, 10.4, 0.1, 1.0, 3),
    ("Morango", "Frutas", "g", 100, "8 unidades", 30, 0.9, 6.8, 0.3, 1.7, 0),
    ("Laranja", "Frutas", "g", 140, "1 unidade", 37, 1.0, 8.9, 0.1, 0.8, 0),
    ("Abacate", "Frutas", "g", 100, "4 colheres de sopa", 96, 1.2, 6.0, 8.4, 6.3, 0),

    # ---- Vegetais ----
    ("Brócolis cozido", "Vegetais", "g", 60, "3 ramos", 25, 2.1, 4.4, 0.5, 3.4, 2),
    ("Alface", "Vegetais", "g", 30, "3 folhas", 11, 1.3, 1.7, 0.2, 1.8, 3),
    ("Tomate", "Vegetais", "g", 80, "1/2 unidade", 15, 1.1, 3.1, 0.2, 1.2, 1),
    ("Cenoura crua", "Vegetais", "g", 50, "1/2 unidade", 34, 1.3, 7.7, 0.2, 3.2, 3),
    ("Abobrinha cozida", "Vegetais", "g", 80, "3 colheres de sopa", 15, 1.1, 3.0, 0.2, 1.6, 1),
    ("Espinafre refogado", "Vegetais", "g", 60, "2 colheres de sopa", 67, 2.7, 4.2, 5.4, 2.5, 6),

    # ---- Laticínios ----
    ("Leite integral", "Laticínios", "ml", 200, "1 copo", 61, 3.2, 4.7, 3.3, 0.0, 46),
    ("Leite desnatado", "Laticínios", "ml", 200, "1 copo", 35, 3.4, 5.0, 0.1, 0.0, 51),
    ("Iogurte natural integral", "Laticínios", "g", 170, "1 pote", 51, 4.1, 1.9, 3.0, 0.0, 52),
    ("Queijo minas frescal", "Laticínios", "g", 30, "1 fatia", 264, 17.4, 3.2, 20.2, 0.0, 31),
    ("Queijo muçarela", "Laticínios", "g", 20, "1 fatia", 330, 22.6, 3.0, 25.2, 0.0, 581),
    ("Requeijão cremoso", "Laticínios", "g", 30, "1 colher de sopa", 257, 9.6, 2.4, 23.4, 0.0, 558),

    # ---- Gorduras e oleaginosas ----
    ("Azeite de oliva", "Gorduras", "ml", 13, "1 colher de sopa", 884, 0.0, 0.0, 100.0, 0.0, 0),
    ("Pasta de amendoim integral", "Gorduras", "g", 15, "1 colher de sopa", 588, 25.0, 20.0, 50.0, 6.0, 17),
    ("Castanha-do-pará", "Gorduras", "g", 10, "2 unidades", 643, 14.5, 15.1, 63.5, 7.9, 1),
    ("Castanha de caju torrada", "Gorduras", "g", 20, "10 unidades", 570, 18.5, 29.1, 46.3, 3.7, 125),
    ("Manteiga com sal", "Gorduras", "g", 10, "1 colher de chá", 726, 0.4, 0.1, 82.4, 0.0, 579),

    # ---- Outros ----
    ("Mel", "Outros", "g", 15, "1 colher de sopa", 309, 0.0, 84.0, 0.0, 0.0, 6),
    ("Chocolate amargo 70%", "Outros", "g", 25, "2 quadradinhos", 598, 7.8, 45.9, 42.6, 10.9, 20),
]

ALIMENTOS = [
    {
        "id": i,
        "nome": nome,
        "categoria": categoria,
        "unidade": unidade,
        "porcao": porcao,
        "porcaoDescricao": descricao,
        "por100": dict(zip(NUTRIENTES, valores)),
    }
    for i, (nome, categoria, unidade, porcao, descricao, *valores) in enumerate(_TABELA, start=1)
]

ALIMENTOS_POR_ID = {a["id"]: a for a in ALIMENTOS}
CATEGORIAS = list(dict.fromkeys(a["categoria"] for a in ALIMENTOS))
