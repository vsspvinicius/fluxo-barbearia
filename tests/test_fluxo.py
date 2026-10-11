import csv
import os
import tempfile
import unittest

os.environ["FLUXO_DRY_RUN"] = "1"
os.environ["FLUXO_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

from fluxo import classify_reply, config, db, import_prospects, report, send_emails  # noqa: E402


class FluxoTests(unittest.TestCase):
    def setUp(self):
        config.DB_PATH = os.path.join(tempfile.mkdtemp(), "t.db")  # banco novo por teste
        self.csv_path = os.path.join(tempfile.mkdtemp(), "p.csv")
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["nome", "endereco", "telefone", "nota", "avaliacoes", "place_id"])
            w.writerow(["Barbearia A", "Rua 1", "+5519", "4.9", "100", "id1"])
            w.writerow(["Barbearia B", "Rua 2", "+5519", "5.0", "50", "id2"])

    def test_import_is_idempotent(self):
        self.assertEqual(import_prospects.import_csv(self.csv_path), 2)
        self.assertEqual(import_prospects.import_csv(self.csv_path), 0)

    def test_classify_rules(self):
        self.assertEqual(classify_reply.classify_rules("Pode remover meu contato"), "remover")
        self.assertEqual(classify_reply.classify_rules("Quanto custa isso?"), "interessado")
        self.assertEqual(classify_reply.classify_rules("Como funciona a agenda?"), "interessado")
        self.assertEqual(classify_reply.classify_rules("Não tenho interesse, obrigado"), "recusou")

    def test_dry_run_sends_nothing_and_respects_limit(self):
        import_prospects.import_csv(self.csv_path)
        with db.connect() as c:
            c.execute("UPDATE contacts SET email='a@x.com' WHERE place_id='id1'")
            c.execute("UPDATE contacts SET email='b@x.com' WHERE place_id='id2'")
        self.assertEqual(send_emails.run(limit=1), 1)
        with db.connect() as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM sends WHERE dry_run=0").fetchone()[0], 0)
            self.assertEqual(c.execute("SELECT status FROM contacts WHERE place_id='id1'").fetchone()[0], "novo")

    def test_unsubscribed_is_skipped(self):
        import_prospects.import_csv(self.csv_path)
        with db.connect() as c:
            c.execute("UPDATE contacts SET email='a@x.com' WHERE place_id='id1'")
            c.execute("INSERT INTO unsubscribes (email) VALUES ('a@x.com')")
        self.assertEqual(send_emails.run(limit=10), 0)

    def test_report_renders(self):
        self.assertIn("Relatório Fluxo Barbearia", report.build())


if __name__ == "__main__":
    unittest.main()
