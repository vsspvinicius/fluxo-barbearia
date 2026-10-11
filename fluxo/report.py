"""Relatório diário: processo primeiro, financeiro depois."""
from . import db

LINES = [
    ("Contatos na lista", lambda s: s.count("contacts")),
    ("Com e-mail", lambda s: s.count("contacts", not_null=["email"])),
    ("E-mails enviados (reais)", lambda s: s.count("sends", where={"dry_run": False})),
    ("Simulações (dry-run)", lambda s: s.count("sends", where={"dry_run": True})),
    ("Respostas recebidas", lambda s: s.count("replies")),
    ("Interessados", lambda s: s.count("replies", where={"classification": "interessado"})),
    ("Descadastros", lambda s: s.count("unsubscribes")),
]


def build():
    store = db.get_store()
    lines = ["# Relatório Fluxo Barbearia", ""]
    lines += [f"{label}: {fn(store)}" for label, fn in LINES]
    lines += ["", "Financeiro: R$ 0,00 (nenhuma venda registrada)"]
    return "\n".join(lines)


if __name__ == "__main__":
    print(build())
