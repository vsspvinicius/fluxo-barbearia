import csv
import os
import tempfile
import unittest

os.environ["FLUXO_DRY_RUN"] = "1"

from fluxo import classify_reply, config, db, import_prospects, report, send_emails  # noqa: E402


class FluxoTests(unittest.TestCase):
    def setUp(self):
        # Testes sempre usam SQLite local, mesmo que o ambiente tenha Supabase configurado.
        config.SUPABASE_URL = ""
        config.SUPABASE_SERVICE_KEY = ""
        config.DRY_RUN = True
        config.DB_PATH = os.path.join(tempfile.mkdtemp(), "t.db")
        self.csv_path = os.path.join(tempfile.mkdtemp(), "p.csv")
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["nome", "endereco", "telefone", "nota", "avaliacoes", "place_id"])
            w.writerow(["Barbearia A", "Rua 1", "+5519", "4.9", "100", "id1"])
            w.writerow(["Barbearia B", "Rua 2", "+5519", "5.0", "50", "id2"])

    def _seed_with_emails(self):
        import_prospects.import_csv(self.csv_path)
        store = db.get_store()
        store.set_email("id1", "a@x.com")
        store.set_email("id2", "b@x.com")
        return store

    def test_import_is_idempotent(self):
        self.assertEqual(import_prospects.import_csv(self.csv_path), 2)
        self.assertEqual(import_prospects.import_csv(self.csv_path), 0)

    def test_classify_rules(self):
        self.assertEqual(classify_reply.classify_rules("Pode remover meu contato"), "remover")
        self.assertEqual(classify_reply.classify_rules("Quanto custa isso?"), "interessado")
        self.assertEqual(classify_reply.classify_rules("Como funciona a agenda?"), "interessado")
        self.assertEqual(classify_reply.classify_rules("Não tenho interesse, obrigado"), "recusou")

    def test_dry_run_sends_nothing_and_respects_limit(self):
        store = self._seed_with_emails()
        self.assertEqual(send_emails.run(limit=1), 1)
        self.assertEqual(store.count("sends", where={"dry_run": False}), 0)
        self.assertEqual(store.count("sends", where={"dry_run": True}), 1)
        self.assertEqual(store.count("contacts", where={"status": "novo"}), 2)

    def test_gmail_used_when_app_password_set(self):
        from unittest import mock
        store = self._seed_with_emails()
        config.DRY_RUN = False
        config.FROM_EMAIL = "eu@gmail.com"
        config.GMAIL_APP_PASSWORD = "abcdabcdabcdabcd"
        try:
            with mock.patch("smtplib.SMTP_SSL") as smtp:
                self.assertEqual(send_emails.run(limit=1), 1)
                server = smtp.return_value.__enter__.return_value
                server.login.assert_called_once_with("eu@gmail.com", "abcdabcdabcdabcd")
                msg = server.send_message.call_args[0][0]
                self.assertIn("remover", msg["List-Unsubscribe"])
            self.assertEqual(store.count("sends", where={"dry_run": False}), 1)
            self.assertEqual(store.count("contacts", where={"status": "contatado"}), 1)
        finally:
            config.DRY_RUN = True
            config.FROM_EMAIL = ""
            config.GMAIL_APP_PASSWORD = ""

    def test_template_personal_no_links_no_prices(self):
        from fluxo import templates
        subj, body = templates.render({"name": "Barbearia A", "rating": 4.9, "rating_count": 100})
        self.assertIn("Barbearia A", subj)
        self.assertIn("4,9 estrelas e 100 avaliações", body)
        self.assertNotIn("http", body)
        self.assertNotIn("R$", body)
        self.assertIn("remover", body)
        _, body2 = templates.render({"name": "Barbearia B", "rating": None, "rating_count": None})
        self.assertNotIn("estrelas", body2)

    def test_unsubscribed_is_skipped(self):
        store = self._seed_with_emails()
        store.add_unsubscribe("a@x.com")
        self.assertEqual(send_emails.run(limit=10), 1)

    def test_report_renders_with_counts(self):
        self._seed_with_emails()
        text = report.build()
        self.assertIn("Relatório Fluxo Barbearia", text)
        self.assertIn("Contatos na lista: 2", text)
        self.assertIn("Com e-mail: 2", text)


if __name__ == "__main__":
    unittest.main()
