"""Envio diário de e-mails. Padrão: dry-run (não envia). Limite diário e descadastro respeitados."""
import json
import smtplib
import sys
import urllib.request
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from . import config, db, templates


def _send_resend(to, subject, text):
    payload = json.dumps({
        "from": f"{config.FROM_NAME} <{config.FROM_EMAIL}>",
        "to": [to], "subject": subject, "text": text,
    }).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails", data=payload,
        headers={"Authorization": f"Bearer {config.RESEND_API_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read()).get("id")


def _send_gmail(to, subject, text):
    msg = EmailMessage()
    msg["From"] = formataddr((config.FROM_NAME, config.FROM_EMAIL))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid(domain="gmail.com")
    unsub = [f"<mailto:{config.FROM_EMAIL}?subject=remover>"]
    if config.UNSUBSCRIBE_URL:
        unsub.insert(0, f"<{config.UNSUBSCRIBE_URL}>")
    msg["List-Unsubscribe"] = ", ".join(unsub)
    msg.set_content(text)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
        s.login(config.FROM_EMAIL, config.GMAIL_APP_PASSWORD)
        s.send_message(msg)
    return msg["Message-ID"]


def provider():
    """Gmail se houver senha de app; senão Resend; senão nenhum."""
    if config.GMAIL_APP_PASSWORD:
        return "gmail"
    if config.RESEND_API_KEY:
        return "resend"
    return None


def run(limit=None):
    limit = limit or config.DAILY_EMAIL_LIMIT
    prov = provider()
    if not config.DRY_RUN and (not prov or not config.FROM_EMAIL):
        sys.exit("Envio real exige FLUXO_FROM_EMAIL e GMAIL_APP_PASSWORD (ou RESEND_API_KEY). "
                 "Use FLUXO_DRY_RUN=1 para testar.")
    send = _send_gmail if prov == "gmail" else _send_resend
    store = db.get_store()
    unsub = store.unsubscribed()
    targets = [c for c in store.candidates() if c["email"] not in unsub]
    targets.sort(key=lambda c: c.get("rating_count") or 0, reverse=True)
    sent = 0
    for contact in targets[:limit]:
        subject, text = templates.render(contact)
        provider_id = None
        if not config.DRY_RUN:
            provider_id = send(contact["email"], subject, text)
            store.mark_status(contact["id"], "contatado")
        store.record_send(contact["id"], subject, config.DRY_RUN, provider_id)
        sent += 1
    return sent


if __name__ == "__main__":
    n = run()
    mode = "DRY-RUN (nada enviado)" if config.DRY_RUN else "ENVIADO"
    print(f"{mode}: {n} e-mail(s) processados, limite {config.DAILY_EMAIL_LIMIT}/dia")
