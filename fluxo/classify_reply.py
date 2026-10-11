"""Classifica respostas de leads. Usa a API da Claude se houver chave; senão, regras simples."""
import json
import re
import urllib.request

from . import config

LABELS = ["interessado", "duvida", "recusou", "remover", "outro"]

_REMOVE = re.compile(r"\b(remover|remove|descadastr|parar de receber|não quero|nao quero)\b", re.I)
_REFUSE = re.compile(r"\b(não tenho interesse|nao tenho interesse|não obrigado|nao obrigado)\b", re.I)
_INTEREST = re.compile(r"\b(quero|tenho interesse|pode falar|como funciona|me explica|quanto custa|valor)\b", re.I)


def classify_rules(text):
    if _REMOVE.search(text):
        return "remover"
    if _REFUSE.search(text):
        return "recusou"
    if _INTEREST.search(text):
        return "interessado"
    if "?" in text:
        return "duvida"
    return "outro"


def classify_llm(text):
    prompt = (
        "Classifique a resposta de um dono de barbearia a um e-mail de oferta. "
        f"Responda só com uma destas palavras: {', '.join(LABELS)}.\n\nResposta:\n{text}"
    )
    body = json.dumps({
        "model": config.ANTHROPIC_MODEL,
        "max_tokens": 10,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": config.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        out = json.loads(r.read())["content"][0]["text"].strip().lower()
    return out if out in LABELS else "outro"


def classify(text):
    if config.ANTHROPIC_API_KEY:
        try:
            return classify_llm(text)
        except Exception:
            pass  # cai para regras se a API falhar
    return classify_rules(text)
