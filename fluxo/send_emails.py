"""Envio diário de e-mails. Padrão: dry-run (não envia). Limite diário e descadastro respeitados."""
import json
import sys
import urllib.request

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


def run(limit=None):
    limit = limit or config.DAILY_EMAIL_LIMIT
    if not config.DRY_RUN and (not config.RESEND_API_KEY or not config.FROM_EMAIL):
        sys.exit("Envio real exige RESEND_API_KEY e FLUXO_FROM_EMAIL. Use FLUXO_DRY_RUN=1 para testar.")
    store = db.get_store()
    unsub = store.unsubscribed()
    targets = [c for c in store.candidates() if c["email"] not in unsub]
    targets.sort(key=lambda c: c.get("rating_count") or 0, reverse=True)
    sent = 0
    for contact in targets[:limit]:
        subject, text = templates.render(contact)
        provider_id = None
        if not config.DRY_RUN:
            provider_id = _send_resend(contact["email"], subject, text)
            store.mark_status(contact["id"], "contatado")
        store.record_send(contact["id"], subject, config.DRY_RUN, provider_id)
        sent += 1
    return sent


if __name__ == "__main__":
    n = run()
    mode = "DRY-RUN (nada enviado)" if config.DRY_RUN else "ENVIADO"
    print(f"{mode}: {n} e-mail(s) processados, limite {config.DAILY_EMAIL_LIMIT}/dia")
