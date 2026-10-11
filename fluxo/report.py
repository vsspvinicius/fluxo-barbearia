"""Relatório diário: processo primeiro, financeiro depois."""
from . import db

QUERIES = [
    ("Contatos na lista", "SELECT COUNT(*) FROM contacts"),
    ("Com e-mail", "SELECT COUNT(*) FROM contacts WHERE email IS NOT NULL AND email != ''"),
    ("E-mails enviados (reais)", "SELECT COUNT(*) FROM sends WHERE dry_run = 0"),
    ("Simulações (dry-run)", "SELECT COUNT(*) FROM sends WHERE dry_run = 1"),
    ("Respostas recebidas", "SELECT COUNT(*) FROM replies"),
    ("Interessados", "SELECT COUNT(*) FROM replies WHERE classification = 'interessado'"),
    ("Descadastros", "SELECT COUNT(*) FROM unsubscribes"),
]


def build():
    lines = ["# Relatório Fluxo Barbearia", ""]
    with db.connect() as c:
        for label, sql in QUERIES:
            lines.append(f"{label}: {c.execute(sql).fetchone()[0]}")
    lines += ["", "Financeiro: R$ 0,00 (nenhuma venda registrada)"]
    return "\n".join(lines)


if __name__ == "__main__":
    print(build())
