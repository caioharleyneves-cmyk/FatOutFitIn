import json
import math
import argparse
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
import jwt

parser = argparse.ArgumentParser(description='Testes HTTP de integração; inicie as duas APIs antes.')
parser.add_argument('--java-port', type=int, default=8080)
parser.add_argument('--python-port', type=int, default=5000)
parser.add_argument('--output', type=Path)
args = parser.parse_args()

RESULTADOS = []
TOKENS = {}
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def req(porta, rota, metodo='GET', dados=None, usuario=None, raw=None, content_type='application/json', token=None, extra_headers=None):
    if porta == 8081:
        porta = args.java_port
    elif porta == 5000:
        porta = args.python_port
    headers = {'Content-Type': content_type}
    if usuario is not None:
        headers['X-Usuario-Id'] = str(usuario)
    sessao = token if token is not None else TOKENS.get(usuario)
    if sessao is not None:
        headers['Authorization'] = 'Bearer ' + sessao
    headers.update(extra_headers or {})
    corpo = raw if raw is not None else (json.dumps(dados).encode() if dados is not None else None)
    r = urllib.request.Request(f'http://127.0.0.1:{porta}/api{rota}', data=corpo, headers=headers, method=metodo)
    try:
        resp = opener.open(r, timeout=10)
    except urllib.error.HTTPError as e:
        resp = e
    text = resp.read().decode()
    try:
        obj = json.loads(text)
    except ValueError:
        obj = text
    return resp.code, obj

def check(nome, resposta, status, regra=lambda d: True):
    codigo, obj = resposta
    ok = codigo == status and regra(obj)
    seguro = {k: v for k, v in obj.items() if k != 'token'} if isinstance(obj, dict) else obj
    RESULTADOS.append({'teste': nome, 'ok': ok, 'esperado': status, 'recebido': codigo, 'resposta': seguro})
    print(('PASS' if ok else 'FAIL') + ' ' + nome + f' [{codigo}]')
    return obj

stamp = str(time.time_ns())
conta = {'nome': 'Teste API', 'email': f'api.{stamp}@example.test', 'senha': 'Teste1234!'}
u = check('Cadastro', req(5000, '/usuarios', 'POST', conta), 201)['id']
v = check('Segunda conta', req(5000, '/usuarios', 'POST', {**conta, 'email': f'outro.{stamp}@example.test'}), 201)['id']
check('Cadastro duplicado', req(5000, '/usuarios', 'POST', conta), 409)
TOKENS[u] = check('Login correto', req(5000, '/login', 'POST', conta), 200, lambda d: d['id'] == u and bool(d.get('token')))['token']
TOKENS[v] = check('Login segunda conta', req(5000, '/login', 'POST', {**conta, 'email': f'outro.{stamp}@example.test'}), 200)['token']
check('Login senha errada', req(5000, '/login', 'POST', {**conta, 'senha': 'errada'}), 401)
check('Cadastro email invalido', req(5000, '/usuarios', 'POST', {**conta, 'email': 'invalido'}), 400)
for porta in [5000, 8081]:
    prefixo = 'Python' if porta == 5000 else 'Java'
    raiz = '/refeicoes' if porta == 5000 else '/treinos'
    check(prefixo + ' health', req(porta, '/health'), 200)
    check(prefixo + ' sem usuario', req(porta, raiz), 401)
    check(prefixo + ' rota inexistente', req(porta, '/nao-existe', usuario=u), 404)
    check(prefixo + ' item inexistente', req(porta, raiz + '/99999999', usuario=u), 404)
    check(prefixo + ' dia invalido', req(porta, raiz + '?dia=xyz', usuario=u), 400)
    check(prefixo + ' JSON invalido', req(porta, raiz, 'POST', usuario=u, raw=b'{'), 400)
    check(prefixo + ' corpo vazio', req(porta, raiz, 'POST', {}, u), 400)
    check(prefixo + ' usuario inexistente', req(porta, raiz, usuario=999999999), 401)
    check(prefixo + ' token adulterado', req(porta, raiz, token=TOKENS[u] + 'x'), 401)
    check(prefixo + ' token malformado', req(porta, raiz, token='invalido'), 401)

chave = os.environ.get('FOFI_AUTH_SECRET') or (Path(__file__).resolve().parent.parent / '.local/auth-secret').read_text().strip()
claims = {'sub': str(u), 'iss': 'fatoutfitin-api-python', 'aud': 'fatoutfitin', 'iat': int(time.time()), 'exp': int(time.time()) + 60}
for porta, raiz in [(5000, '/refeicoes'), (8081, '/treinos')]:
    for descricao, payload, algoritmo in [
        ('expirado', {**claims, 'iat': int(time.time()) - 200, 'exp': int(time.time()) - 100}, 'HS256'),
        ('sem expiracao', {k:v for k,v in claims.items() if k != 'exp'}, 'HS256'),
        ('emissor errado', {**claims, 'iss': 'outro'}, 'HS256'),
        ('publico errado', {**claims, 'aud': 'outro'}, 'HS256'),
        ('algoritmo errado', claims, 'HS384'),
        ('usuario nulo', {**claims, 'sub': '0'}, 'HS256'),
        ('usuario enorme', {**claims, 'sub': '999999999999999999999999'}, 'HS256'),
    ]:
        check(f'{porta} token {descricao}', req(porta, raiz, token=jwt.encode(payload, chave, algorithm=algoritmo)), 401)

alimentos = check('Catalogo alimentos', req(5000, '/alimentos'), 200, lambda d: len(d) >= 40)
a = alimentos[0]
check('Calculo porcao 150g', req(5000, f"/alimentos/{a['id']}?quantidade=150"), 200, lambda d: d['nutrientes']['kcal'] == math.floor(a['por100']['kcal'] * 1.5 + 0.5))
check('Quantidade negativa', req(5000, f"/alimentos/{a['id']}?quantidade=-1"), 400)
refeicao = {'titulo': 'Marmita teste', 'dia': 'seg', 'tipo': 'almoco', 'itens': [{'alimentoId': a['id'], 'quantidade': 150, 'feito': False}]}
r = check('Criar refeicao', req(5000, '/refeicoes', 'POST', refeicao, u), 201)
check('Calculo meio para cima ao salvar', (201, r), 201, lambda d: d['nutrientes']['kcal'] == math.floor(a['por100']['kcal'] * 1.5 + 0.5))
rid = r['id']
check('Ler refeicao', req(5000, f'/refeicoes/{rid}', usuario=u), 200, lambda d: d['titulo'] == refeicao['titulo'])
check('Refeicao isolada segunda conta', req(5000, f'/refeicoes/{rid}', usuario=v), 404)
check('Python ID forjado nao troca identidade', req(5000, f'/refeicoes/{rid}', usuario=v, extra_headers={'X-Usuario-Id': str(u)}), 404)
refeicao.update(titulo='Marmita atualizada', fixado=True, cor='verde')
refeicao['itens'][0]['feito'] = True
check('Editar refeicao checklist fixacao cor', req(5000, f'/refeicoes/{rid}', 'PUT', refeicao, u), 200, lambda d: d['fixado'] and d['itens'][0]['feito'] and d['cor'] == 'verde')
check('Resumo nutricional', req(5000, '/refeicoes/resumo', usuario=u), 200, lambda d: d['totalRefeicoes'] == 1 and d['total']['kcal'] == r['nutrientes']['kcal'])
check('Filtro refeicoes vazio', req(5000, '/refeicoes?dia=ter', usuario=u), 200, lambda d: d == [])
check('Titulo nulo deve ser recusado', req(5000, '/refeicoes', 'POST', {**refeicao, 'titulo': None}, u), 400)
check('Nome e senha nulos devem ser recusados', req(5000, '/usuarios', 'POST', {'nome': None, 'email': f'nulo.{stamp}@example.test', 'senha': None}), 400)
for campo, valor in [('titulo', []), ('fixado', 'false'), ('notas', {}), ('itens', [None]), ('itens', [{'alimentoId': True}]), ('itens', [{'texto': None}]), ('itens', [{'texto': 'Molho', 'feito': 'false'}])]:
    check(f'Python tipo invalido {campo}={valor}', req(5000, '/refeicoes', 'POST', {**refeicao, campo: valor}, u), 400)

treino = {'titulo': 'Treino API', 'dia': 'seg', 'duracaoMin': 60, 'grupoMuscular': 'Peito', 'exercicios': [{'nome': 'Supino', 'series': 4, 'repeticoes': '8-10', 'carga': 40, 'feito': False}]}
t = check('Criar treino', req(8081, '/treinos', 'POST', treino, u), 201)
tid = t['id']
check('Ler treino', req(8081, f'/treinos/{tid}', usuario=u), 200, lambda d: d['titulo'] == treino['titulo'])
check('Treino isolado segunda conta', req(8081, f'/treinos/{tid}', usuario=v), 404)
check('Java ID forjado nao troca identidade', req(8081, f'/treinos/{tid}', usuario=v, extra_headers={'X-Usuario-Id': str(u)}), 404)
treino.update(titulo='Treino atualizado', cor='azul', fixado=True)
check('Editar treino fixacao cor', req(8081, f'/treinos/{tid}', 'PUT', treino, u), 200, lambda d: d['fixado'] and d['cor'] == 'azul')
check('Concluir exercicio PATCH', req(8081, f'/treinos/{tid}/exercicios/0', 'PATCH', usuario=u), 200, lambda d: d['exercicios'][0]['feito'])
check('Resumo treino', req(8081, '/treinos/resumo', usuario=u), 200, lambda d: d['totalTreinos'] == 1 and d['progressoSemana'] == 100 and d['dias'][0]['series'] == 4)
check('Duracao negativa', req(8081, '/treinos', 'POST', {**treino, 'duracaoMin': -1}, u), 400)
check('Exercicio nulo', req(8081, '/treinos', 'POST', {**treino, 'exercicios': [None]}, u), 400)
check('Indice exercicio inexistente', req(8081, f'/treinos/{tid}/exercicios/99', 'PATCH', usuario=u), 404)
check('Filtro treinos vazio', req(8081, '/treinos?dia=ter', usuario=u), 200, lambda d: d == [])
check('Content-Type invalido Java', req(8081, '/treinos', 'POST', usuario=u, raw=b'texto', content_type='text/plain'), 415)
check('Excluir refeicao', req(5000, f'/refeicoes/{rid}', 'DELETE', usuario=u), 200)
check('Refeicao excluida', req(5000, f'/refeicoes/{rid}', usuario=u), 404)
check('Excluir treino', req(8081, f'/treinos/{tid}', 'DELETE', usuario=u), 200)
check('Treino excluido', req(8081, f'/treinos/{tid}', usuario=u), 404)

if args.output:
    args.output.write_text(json.dumps(RESULTADOS, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'TOTAL {len(RESULTADOS)}; PASS {sum(r["ok"] for r in RESULTADOS)}; FAIL {sum(not r["ok"] for r in RESULTADOS)}')
sys.exit(0 if all(r['ok'] for r in RESULTADOS) else 1)
