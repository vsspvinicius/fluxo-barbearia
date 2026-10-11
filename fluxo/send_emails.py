"""Envio diário de e-mails. Padrão: dry-run (não envia). Limite diário e descadastro respeitados."""
import json
import sys
import urllib.request

from . import config, db, templates


def _send_resend(to, subject, text):
    payload = json.dumps({
        "from": f"{config.FROM_NAME} <{config.FROM_EMAIL}>",
        "to": [to],
        "subject": subject,
        "text": text,
    }).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {config.RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read()).get("id")


def run(limit=None):
    limit = limit or config.DAILY_EMAIL_LIMIT
    if not config.DRY_RUN and (not config.RESEND_API_KEY or not config.FROM_EMAIL):
        sys.exit("Envio real exige RESEND_API_KEY e FLUXO_FROM_EMAIL. Use FLUXO_DRY_RUN=1 para testar.")

    sent = 0
    with db.connect() as c:
        rows = c.execute(
            """SELECT * FROM contacts
               WHERE status = 'novo' AND email IS NOT NULL AND email != ''
                 AND email NOT IN (SELECT email FROM unsubscribes)
               ORDER BY rating_count DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        for contact in rows:
            subject, text = templates.render(contact)
            provider_id = None
            if not config.DRY_RUN:
                provider_id = _send_resend(contact["email"], subject, text)
            c.execute(
                "INSERT INTO sends (contact_id, channel, subject, dry_run, provider_id) VALUES (?,?,?,?,?)",
                (contact["id"], "email", subject, int(config.DRY_RUN), provider_id),
            )
            if not config.DRY_RUN:
                c.execute(
                    "UPDATE contacts SET status='contatado', updated_at=datetime('now') WHERE id=?",
                    (contact["id"],),
                )
            sent += 1
    return sent


if __name__ == "__main__":
    n = run()
    mode = "DRY-RUN (nada enviado)" if config.DRY_RUN else "ENVIADO"
    print(f"{mode}: {n} e-mail(s) processados, limite {config.DAILY_EMAIL_LIMIT}/dia")
