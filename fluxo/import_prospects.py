"""Importa a lista de prospects (CSV) para o banco. Idempotente pelo place_id."""
import csv
import sys

from . import db


def import_csv(path, conn=None):
    inserted = 0
    with db.connect() as c:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cur = c.execute(
                    """INSERT OR IGNORE INTO contacts
                       (place_id, name, address, phone, rating, rating_count)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        row["place_id"],
                        row["nome"],
                        row["endereco"],
                        row["telefone"],
                        float(row["nota"]) if row["nota"] else None,
                        int(row["avaliacoes"]) if row["avaliacoes"] else None,
                    ),
                )
                inserted += cur.rowcount
    return inserted


if __name__ == "__main__":
    print(f"contatos novos importados: {import_csv(sys.argv[1])}")
