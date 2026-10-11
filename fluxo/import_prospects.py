"""Importa a lista de prospects (CSV) para o armazenamento. Idempotente pelo place_id."""
import csv
import sys

from . import db


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [{
            "place_id": row["place_id"],
            "name": row["nome"],
            "address": row["endereco"],
            "phone": row["telefone"],
            "rating": float(row["nota"]) if row["nota"] else None,
            "rating_count": int(row["avaliacoes"]) if row["avaliacoes"] else None,
        } for row in csv.DictReader(f)]


def import_csv(path):
    return db.get_store().add_contacts(read_csv(path))


if __name__ == "__main__":
    print(f"contatos novos importados: {import_csv(sys.argv[1])}")
