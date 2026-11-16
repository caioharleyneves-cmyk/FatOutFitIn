"""Instala as dependências locais e inicia as três partes do FatOutFitIn."""
import argparse
import functools
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

RAIZ = Path(__file__).resolve().parent
LOCAL = RAIZ / ".local"
LOGS = LOCAL / "logs"
SEM_JANELA = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def porta_livre(preferida, reservadas=()):
    for porta in range(preferida, min(preferida + 100, 65536)):
        if porta in reservadas:
            continue
        with socket.socket() as teste:
            try:
                teste.bind(("127.0.0.1", porta))
                return porta
            except OSError:
                continue
    raise RuntimeError(f"Não há porta livre próxima de {preferida}.")


def executar(comando, pasta, log, ambiente=None):
    with log.open("w", encoding="utf-8") as saida:
        resultado = subprocess.run(comando, cwd=pasta, env=ambiente, stdout=saida,
                                   stderr=subprocess.STDOUT, creationflags=SEM_JANELA)
    if resultado.returncode:
        raise RuntimeError(f"Etapa de preparação falhou. Consulte {log}")


def localizar_java():
    candidatos = []
    if os.environ.get("JAVA_HOME"):
        candidatos.append(Path(os.environ["JAVA_HOME"]) / "bin" / ("java.exe" if os.name == "nt" else "java"))
    if shutil.which("java"):
        candidatos.append(Path(shutil.which("java")).resolve())
    for java in candidatos:
        javac = java.with_name("javac.exe" if os.name == "nt" else "javac")
        if not java.is_file() or not javac.is_file():
            continue
        versao = subprocess.run([str(java), "-version"], capture_output=True, text=True,
                                creationflags=SEM_JANELA)
        numero = re.search(r'version\s+"(\d+)', versao.stderr + versao.stdout)
        if versao.returncode == 0 and numero and int(numero.group(1)) >= 17:
            return java
    raise RuntimeError("JDK 17 ou superior não encontrado. Instale o JDK (não apenas JRE), "
                       "reabra a pasta e tente novamente. Veja GUIA-PARA-RODAR.md.")


def preparar_python(reinstalar=False):
    pasta = RAIZ / "api-python"
    python = pasta / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        print("[1/4] Criando ambiente Python...", flush=True)
        executar([sys.executable, "-m", "venv", str(pasta / ".venv")], RAIZ, LOGS / "ambiente-python.log")
    requisitos = pasta / "requirements.txt"
    assinatura = hashlib.sha256(requisitos.read_bytes() + str(python).encode()).hexdigest()
    marcador = LOCAL / "dependencias-python.sha256"
    pronto = marcador.exists() and marcador.read_text() == assinatura
    if pronto and not reinstalar:
        pronto = subprocess.run([str(python), "-c", "import flask, flask_cors, jwt"],
                                capture_output=True, creationflags=SEM_JANELA).returncode == 0
    if reinstalar or not pronto:
        print("[1/4] Instalando dependências Python (internet na primeira vez)...", flush=True)
        executar([str(python), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(requisitos)],
                 pasta, LOGS / "dependencias-python.log")
        marcador.write_text(assinatura)
    else:
        print("[1/4] Python pronto; usando dependências já instaladas.", flush=True)
    return python


def assinatura_java():
    pasta = RAIZ / "api-java"
    arquivos = [pasta / "pom.xml", *sorted((pasta / "src").rglob("*"))]
    resumo = hashlib.sha256()
    for arquivo in arquivos:
        if arquivo.is_file():
            resumo.update(arquivo.relative_to(pasta).as_posix().encode())
            resumo.update(arquivo.read_bytes())
    return resumo.hexdigest()


def preparar_java(java, reconstruir=False):
    pasta = RAIZ / "api-java"
    marcador = LOCAL / "compilacao-java.sha256"
    assinatura = assinatura_java()
    # Uma compilação por versão evita substituir um JAR aberto no Windows.
    pasta_build = LOCAL / "java-build" / assinatura[:16]
    jar = pasta_build / "fatoutfitin-api-java-1.0.0.jar"
    if reconstruir or not jar.is_file() or not marcador.exists() or marcador.read_text() != assinatura:
        print("[2/4] Preparando Java; a primeira compilação pode levar alguns minutos...", flush=True)
        ambiente = os.environ.copy()
        ambiente["JAVA_HOME"] = str(java.parent.parent)
        ambiente["MAVEN_USER_HOME"] = str(LOCAL / "maven")
        wrapper = pasta / ("mvnw.cmd" if os.name == "nt" else "mvnw")
        comando = [str(wrapper), "-B", "-ntp", "-q", f"-Dmaven.repo.local={LOCAL / 'maven/repository'}",
                   f"-Dfofi.build.directory={pasta_build}", "package"]
        if os.name != "nt":
            comando.insert(0, "sh")
        executar(comando, pasta, LOGS / "compilacao-java.log", ambiente)
        if not jar.is_file():
            raise RuntimeError("O Maven terminou sem gerar o programa Java. Consulte .local/logs/compilacao-java.log.")
        marcador.write_text(assinatura)
    else:
        print("[2/4] Java pronto; usando a compilação já existente.", flush=True)
    return jar


class ServidorFrontend(ThreadingHTTPServer):
    allow_reuse_address = False
    daemon_threads = True


class Paginas(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?", 1)[0] == "/js/config.js":
            corpo = ("window.FOFI_CONFIG = " + json.dumps(self.server.config_apis) + ";\n").encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
        else:
            super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, formato, *args):
        # A janela principal mostra somente o estado de inicialização.
        pass


def aguardar_api(processo, porta, nome, log):
    limite = time.monotonic() + 90
    while time.monotonic() < limite:
        if processo.poll() is not None:
            raise RuntimeError(f"API {nome} encerrou antes de iniciar. Consulte {log}")
        try:
            with HTTP.open(f"http://127.0.0.1:{porta}/api/health", timeout=1) as resposta:
                if json.load(resposta).get("api") == nome:
                    return
        except (OSError, ValueError, urllib.error.URLError):
            pass
        time.sleep(0.2)
    raise RuntimeError(f"API {nome} não ficou pronta no tempo esperado. Consulte {log}")


def main():
    parser = argparse.ArgumentParser(description="Inicia Python, Java e a página com um comando.")
    parser.add_argument("--no-browser", action="store_true", help="Não abrir o navegador automaticamente")
    parser.add_argument("--smoke-test", action="store_true", help="Verificar a inicialização e encerrar")
    parser.add_argument("--reparar", action="store_true", help="Reinstalar dependências e recompilar")
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        raise RuntimeError("Instale Python 3.10 ou superior para iniciar o projeto.")
    LOGS.mkdir(parents=True, exist_ok=True)
    java = localizar_java()
    # Impede duas inicializações de alterarem a compilação/ambiente ao mesmo tempo.
    lock = LOCAL / "inicializacao.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        raise RuntimeError("O iniciador desta pasta já está aberto. Use a janela existente. "
                           "Se ela foi fechada à força, veja a seção de problemas do guia.")
    processos = []
    arquivos_log = []
    servidor = None
    try:
        python = preparar_python(args.reparar)
        jar = preparar_java(java, args.reparar)
        porta_python = porta_livre(5000)
        porta_java = porta_livre(8080, [porta_python])
        porta_frontend = porta_livre(5500, [porta_python, porta_java])
        print(f"[3/4] Iniciando APIs: Python {porta_python} | Java {porta_java}...", flush=True)
        ambiente = os.environ.copy()
        ambiente["FOFI_PORT"] = str(porta_python)
        comandos = [
            ([str(python), "app.py"], RAIZ / "api-python", ambiente, porta_python, "python"),
            ([str(java), "-jar", str(jar), f"--server.port={porta_java}", "--server.address=127.0.0.1"],
             RAIZ / "api-java", os.environ.copy(), porta_java, "java"),
        ]
        for comando, pasta, env, porta, nome in comandos:
            log = LOGS / f"api-{nome}.log"
            saida = log.open("w", encoding="utf-8")
            arquivos_log.append(saida)
            processo = subprocess.Popen(comando, cwd=pasta, env=env, stdout=saida,
                                        stderr=subprocess.STDOUT, creationflags=SEM_JANELA)
            processos.append(processo)
            aguardar_api(processo, porta, nome, log)
        servidor = ServidorFrontend(("127.0.0.1", porta_frontend),
                                   functools.partial(Paginas, directory=str(RAIZ / "frontend")))
        servidor.config_apis = {"apiPython": f"http://127.0.0.1:{porta_python}/api",
                               "apiJava": f"http://127.0.0.1:{porta_java}/api"}
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{porta_frontend}"
        # Confere que a página e as URLs dinâmicas estão sendo servidas.
        with HTTP.open(url + "/js/config.js", timeout=5) as resposta:
            assert str(porta_java) in resposta.read().decode()
        with HTTP.open(url, timeout=5) as resposta:
            assert resposta.status == 200
        print(f"[4/4] Tudo pronto! Acesse: {url}", flush=True)
        print("As portas são escolhidas automaticamente; não é preciso editar arquivos.", flush=True)
        if args.smoke_test:
            print("TESTE OK: duas APIs, página e configuração de portas verificadas.", flush=True)
            return
        if not args.no_browser:
            webbrowser.open(url)
        input("\nMantenha esta janela aberta. Pressione ENTER aqui para encerrar tudo.\n")
    finally:
        if servidor:
            servidor.shutdown()
            servidor.server_close()
        for processo in reversed(processos):
            if processo.poll() is None:
                processo.terminate()
                try:
                    processo.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    processo.kill()
                    processo.wait()
        for arquivo in arquivos_log:
            arquivo.close()
        lock.rmdir()
        print("Serviços iniciados por esta janela foram encerrados.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInicialização interrompida.")
        sys.exit(130)
    except Exception as erro:
        print(f"\nERRO: {erro}", file=sys.stderr, flush=True)
        sys.exit(1)
