"""Sessões assinadas, verificáveis pelas APIs Python e Java de forma independente."""
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt

ISSUER = "fatoutfitin-api-python"
AUDIENCE = "fatoutfitin"


def carregar_chave():
    configurada = os.environ.get("FOFI_AUTH_SECRET")
    if configurada is not None:
        chave = configurada
    else:
        arquivo = Path(__file__).resolve().parent.parent / ".local" / "auth-secret"
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        # mkdir é atômico: impede que as duas APIs gerem chaves diferentes ao iniciar juntas.
        lock = arquivo.with_suffix(".lock")
        for tentativa in range(100):
            try:
                lock.mkdir()
                break
            except FileExistsError:
                if tentativa == 99:
                    raise RuntimeError("Não foi possível obter o bloqueio da chave de sessão.")
                time.sleep(0.05)
        try:
            if not arquivo.exists():
                temporario = arquivo.with_suffix(".tmp")
                temporario.write_text(secrets.token_hex(32), encoding="utf-8")
                temporario.replace(arquivo)
            chave = arquivo.read_text(encoding="utf-8").strip()
        finally:
            lock.rmdir()
    if len(chave.encode("utf-8")) < 32:
        raise RuntimeError("FOFI_AUTH_SECRET precisa ter pelo menos 32 bytes.")
    return chave


CHAVE = carregar_chave()


def criar_token(usuario_id):
    agora = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(usuario_id), "iss": ISSUER, "aud": AUDIENCE,
                       "iat": agora, "exp": agora + timedelta(hours=8)}, CHAVE, algorithm="HS256")


def validar_token(cabecalho):
    esquema, _, token = cabecalho.partition(" ")
    if esquema.lower() != "bearer" or not token.strip():
        raise jwt.InvalidTokenError("Token ausente")
    claims = jwt.decode(token.strip(), CHAVE, algorithms=["HS256"], issuer=ISSUER,
                        audience=AUDIENCE, options={"require": ["sub", "exp", "iat", "iss", "aud"]})
    if not claims["sub"].isdigit() or not 0 < int(claims["sub"]) <= 9223372036854775807:
        raise jwt.InvalidTokenError("Usuário inválido")
    return int(claims["sub"])
