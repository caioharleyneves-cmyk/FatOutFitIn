"""Regressão HTTP dos catálogos por usuário, grupos, técnicas e cardio."""
import argparse
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--python-port', type=int, default=5000)
p.add_argument('--java-port', type=int, default=8080)
p.add_argument('--fixture', type=Path, required=True)
p.add_argument('--verify-persistence', action='store_true')
a = p.parse_args()
http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
total = 0

def request(port, route, method='GET', data=None, token=None):
    headers = {'Content-Type':'application/json'}
    if token: headers['Authorization'] = 'Bearer ' + token
    q = urllib.request.Request(f'http://127.0.0.1:{port}/api{route}', method=method,
        headers=headers, data=json.dumps(data).encode() if data is not None else None)
    try: response = http.open(q, timeout=10)
    except urllib.error.HTTPError as e: response = e
    return response.code, json.loads(response.read())

def check(name, result, code=200, rule=lambda x: True):
    global total
    total += 1
    assert result[0] == code and rule(result[1]), (name, result)
    print('PASS', name)
    return result[1]

def py(route, method='GET', data=None): return request(a.python_port, route, method, data)
def java(route, method='GET', data=None, token=None): return request(a.java_port, route, method, data, token)

if a.verify_persistence:
    f = json.loads(a.fixture.read_text(encoding='utf-8'))
    token = check('Login após reinício', py('/login','POST',{'email':f['email'],'senha':'Teste1234!'}))['token']
    c = check('Catálogo após reinício', java('/catalogo-treinos',token=token))
    check('Grupo personalizado persistiu', (200,c), rule=lambda d: f['grupo'] in d['personalizados']['grupos'])
    check('Exercício personalizado persistiu', (200,c), rule=lambda d: f['exercicio'] in d['personalizados']['exercicios'])
    check('Cardio persistiu', java('/cardios/'+str(f['cardioId']),token=token), rule=lambda d:d['concluido'] and d['distanciaKm']==5)
    check('Técnica e grupos persistiram', java('/treinos/'+str(f['treinoId']),token=token),
          rule=lambda d:d['exercicios'][0]['tecnica']=='Rest-pause' and len(d['gruposMusculares'])==3)
else:
    stamp = str(time.time_ns())
    email = f'catalogo.{stamp}@example.test'
    user = check('Cadastro A', py('/usuarios','POST',{'nome':'Teste catálogo','email':email,'senha':'Teste1234!'}),201)
    token = check('Login A', py('/login','POST',{'email':email,'senha':'Teste1234!'}))['token']
    email_b = f'outro.{stamp}@example.test'
    check('Cadastro B', py('/usuarios','POST',{'nome':'Outro','email':email_b,'senha':'Teste1234!'}),201)
    outro = check('Login B', py('/login','POST',{'email':email_b,'senha':'Teste1234!'}))['token']
    catalogo = check('Catálogo conhecido', java('/catalogo-treinos',token=token),
        rule=lambda d: all(g in d['grupos'] for g in ['Peito','Dorsal','Trapézio']) and len(d['exercicios'])>=25)
    check('Catálogo exige sessão', java('/catalogo-treinos'),401)
    grupo = 'Mobilidade ' + stamp[-6:]
    exercicio = 'Meu exercício ' + stamp[-6:]
    check('Salvar grupo próprio', java('/catalogo-treinos/personalizados','POST',{'tipo':'grupo','nome':grupo},token),201,
        lambda d:grupo in d['grupos'])
    check('Salvar exercício próprio', java('/catalogo-treinos/personalizados','POST',{'tipo':'exercicio','nome':exercicio},token),201,
        lambda d:any(e['nome']==exercicio for e in d['exercicios']))
    check('Evitar duplicado por caixa', java('/catalogo-treinos/personalizados','POST',{'tipo':'grupo','nome':grupo.upper()},token),201,
        lambda d:len(d['personalizados']['grupos'])==1)
    check('Opções pessoais isoladas', java('/catalogo-treinos',token=outro),
        rule=lambda d:grupo not in d['grupos'] and not any(e['nome']==exercicio for e in d['exercicios']))
    for data in [{'tipo':'outro','nome':'Teste'},{'tipo':'grupo','nome':''},{'tipo':'grupo','nome':None},
                 {'tipo':'grupo','nome':'x'*41},{'tipo':'exercicio','nome':'x'*121}]:
        check('Validar opção personalizada', java('/catalogo-treinos/personalizados','POST',data,token),400)
    treino = {'titulo':'Treino múltiplos grupos','dia':'seg','gruposMusculares':['Peito','Tríceps'],
        'duracaoMin':45,'exercicios':[{'nome':exercicio,'series':3,'repeticoes':'10','carga':20,'tecnica':'Drop set'}]}
    t = check('Criar treino com técnica e grupos', java('/treinos','POST',treino,token),201,
        lambda d:d['gruposMusculares']==['Peito','Tríceps'] and d['exercicios'][0]['tecnica']=='Drop set')
    treino['gruposMusculares'].append(grupo)
    treino['exercicios'][0]['tecnica']='Rest-pause'
    check('Editar técnica e grupos', java('/treinos/'+str(t['id']),'PUT',treino,token),
        rule=lambda d:len(d['gruposMusculares'])==3 and d['exercicios'][0]['tecnica']=='Rest-pause')
    check('Resumo dos grupos selecionados', java('/treinos/resumo',token=token),
        rule=lambda d:grupo in d['dias'][0]['grupos'] and 'Tríceps' in d['dias'][0]['grupos'])
    cardio = {'titulo':'Corrida de teste','dia':'qua','tipoCardio':'Corrida','duracaoMin':30,'distanciaKm':5,'intensidade':'moderada'}
    c = check('Criar cardio', java('/cardios','POST',cardio,token),201,lambda d:d['modalidade']=='cardio')
    path = '/cardios/'+str(c['id'])
    check('Ler cardio', java(path,token=token),rule=lambda d:d['distanciaKm']==5)
    check('Listar cardio sem musculação', java('/cardios',token=token),rule=lambda d:len(d)==1 and d[0]['id']==c['id'])
    check('Filtro cardio por dia', java('/cardios?dia=seg',token=token),rule=lambda d:d==[])
    check('Filtro inválido de cardio', java('/cardios?dia=xyz',token=token),400)
    check('Concluir cardio', java(path+'/concluir','PATCH',token=token),rule=lambda d:d['concluido'])
    check('Resumo inclui cardio', java('/treinos/resumo',token=token),
        rule=lambda d:d['totalCardios']==1 and d['cardiosConcluidos']==1 and d['minutosCardio']==30 and d['dias'][2]['progresso']==100)
    check('Cardio isolado por usuário', java(path,token=outro),404)
    check('Edição isolada por usuário', java(path,'PUT',cardio,outro),404)
    check('Exclusão isolada por usuário', java(path,'DELETE',token=outro),404)
    check('Rota cardio não aceita treino normal', java('/cardios/'+str(t['id']),token=token),404)
    for campo,valor in [('duracaoMin',None),('duracaoMin',0),('duracaoMin',601),('distanciaKm',-1),('intensidade','errada'),('tipoCardio','')]:
        check('Validar cardio '+campo,java('/cardios','POST',{**cardio,campo:valor},token),400)
    descartavel=check('Criar cardio para exclusão',java('/cardios','POST',{**cardio,'titulo':'Excluir teste'},token),201)
    check('Editar cardio',java('/cardios/'+str(descartavel['id']),'PUT',{**cardio,'titulo':'Atualizado'},token),
        rule=lambda d:d['titulo']=='Atualizado')
    check('Excluir cardio',java('/cardios/'+str(descartavel['id']),'DELETE',token=token))
    check('Cardio excluído retorna 404',java('/cardios/'+str(descartavel['id']),token=token),404)
    a.fixture.write_text(json.dumps({'email':email,'grupo':grupo,'exercicio':exercicio,'cardioId':c['id'],'treinoId':t['id']},ensure_ascii=False),encoding='utf-8')
print('TOTAL',total,'verificações aprovadas.')
