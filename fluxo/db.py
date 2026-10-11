"""Armazenamento. Produção: Supabase via REST (SUPABASE_URL + SUPABASE_SERVICE_KEY).
Sem essas variáveis, usa SQLite local (testes e simulação)."""
import datetime as dt
import json
import sqlite3
import urllib.error
import urllib.parse
import urllib.request

from . import config

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT, place_id TEXT UNIQUE, name TEXT NOT NULL,
    address TEXT, phone TEXT, email TEXT, rating REAL, rating_count INTEGER,
    status TEXT NOT NULL DEFAULT 'novo', created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS sends (
    id INTEGER PRIMARY KEY AUTOINCREMENT, contact_id INTEGER NOT NULL REFERENCES contacts(id),
    channel TEXT NOT NULL, subject TEXT, dry_run INTEGER NOT NULL, provider_id TEXT,
    sent_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT, contact_id INTEGER NOT NULL REFERENCES contacts(id),
    body TEXT NOT NULL, classification TEXT, received_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS unsubscribes (
    email TEXT PRIMARY KEY, created_at TEXT DEFAULT (datetime('now')));
"""


class SQLiteStore:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SQLITE_SCHEMA)

    def _rows(self, sql, params=()):
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def _val(self, v):
        return int(v) if isinstance(v, bool) else v

    def add_contacts(self, rows):
        n = 0
        for r in rows:
            cur = self.conn.execute(
                "INSERT OR IGNORE INTO contacts (place_id,name,address,phone,rating,rating_count)"
                " VALUES (?,?,?,?,?,?)",
                (r["place_id"], r["name"], r.get("address"), r.get("phone"),
                 r.get("rating"), r.get("rating_count")))
            n += cur.rowcount
        self.conn.commit()
        return n

    def set_email(self, place_id, email):
        self.conn.execute("UPDATE contacts SET email=? WHERE place_id=?", (email, place_id))
        self.conn.commit()

    def candidates(self):
        return self._rows("SELECT * FROM contacts WHERE status='novo' AND email IS NOT NULL AND email != ''")

    def unsubscribed(self):
        return {r["email"] for r in self._rows("SELECT email FROM unsubscribes")}

    def mark_status(self, contact_id, status):
        self.conn.execute("UPDATE contacts SET status=?, updated_at=datetime('now') WHERE id=?",
                          (status, contact_id))
        self.conn.commit()

    def record_send(self, contact_id, subject, dry_run, provider_id=None):
        self.conn.execute(
            "INSERT INTO sends (contact_id,channel,subject,dry_run,provider_id) VALUES (?,?,?,?,?)",
            (contact_id, "email", subject, int(dry_run), provider_id))
        self.conn.commit()

    def record_reply(self, contact_id, body, classification):
        self.conn.execute("INSERT INTO replies (contact_id,body,classification) VALUES (?,?,?)",
                          (contact_id, body, classification))
        self.conn.commit()

    def add_unsubscribe(self, email):
        self.conn.execute("INSERT OR IGNORE INTO unsubscribes (email) VALUES (?)", (email,))
        self.conn.commit()

    def count(self, table, where=None, not_null=None):
        clauses, params = [], []
        for k, v in (where or {}).items():
            clauses.append(f"{k}=?")
            params.append(self._val(v))
        for k in (not_null or []):
            clauses.append(f"{k} IS NOT NULL AND {k} != ''")
        sql = f"SELECT COUNT(*) AS n FROM {table}" + (" WHERE " + " AND ".join(clauses) if clauses else "")
        return self.conn.execute(sql, params).fetchone()["n"]


class SupabaseStore:
    def __init__(self, url, key):
        self.base = url.rstrip("/") + "/rest/v1"
        self.key = key

    def _req(self, method, table, params=None, body=None, prefer=None):
        qs = ("?" + urllib.parse.urlencode(params, safe=".,()")) if params else ""
        headers = {"apikey": self.key, "Authorization": f"Bearer {self.key}",
                   "Content-Type": "application/json"}
        if prefer:
            headers["Prefer"] = prefer
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(f"{self.base}/{table}{qs}", data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                return (json.loads(raw) if raw else None), r.headers
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Supabase {method} {table} falhou: {e.code} {e.read().decode()[:300]}")

    def _pg(self, v):
        return ("true" if v else "false") if isinstance(v, bool) else str(v)

    def add_contacts(self, rows):
        if not rows:
            return 0
        data, _ = self._req("POST", "contacts", params={"on_conflict": "place_id"},
                            body=[{k: r.get(k) for k in ("place_id", "name", "address", "phone",
                                                         "rating", "rating_count")} for r in rows],
                            prefer="resolution=ignore-duplicates,return=representation")
        return len(data or [])

    def set_email(self, place_id, email):
        self._req("PATCH", "contacts", params={"place_id": f"eq.{place_id}"}, body={"email": email},
                  prefer="return=minimal")

    def candidates(self):
        data, _ = self._req("GET", "contacts", params={"status": "eq.novo", "email": "not.is.null",
                                                       "select": "*"})
        return [c for c in (data or []) if c.get("email")]

    def unsubscribed(self):
        data, _ = self._req("GET", "unsubscribes", params={"select": "email"})
        return {r["email"] for r in (data or [])}

    def mark_status(self, contact_id, status):
        self._req("PATCH", "contacts", params={"id": f"eq.{contact_id}"},
                  body={"status": status, "updated_at": dt.datetime.utcnow().isoformat() + "Z"},
                  prefer="return=minimal")

    def record_send(self, contact_id, subject, dry_run, provider_id=None):
        self._req("POST", "sends", body={"contact_id": contact_id, "channel": "email",
                                         "subject": subject, "dry_run": bool(dry_run),
                                         "provider_id": provider_id}, prefer="return=minimal")

    def record_reply(self, contact_id, body, classification):
        self._req("POST", "replies", body={"contact_id": contact_id, "body": body,
                                           "classification": classification}, prefer="return=minimal")

    def add_unsubscribe(self, email):
        self._req("POST", "unsubscribes", params={"on_conflict": "email"}, body={"email": email},
                  prefer="resolution=ignore-duplicates,return=minimal")

    def count(self, table, where=None, not_null=None):
        params = {"select": "id"}
        for k, v in (where or {}).items():
            params[k] = f"eq.{self._pg(v)}"
        for k in (not_null or []):
            params[k] = "not.is.null"
        _, headers = self._req("GET", table, params=params, prefer="count=exact")
        cr = headers.get("Content-Range", "*/0")
        return int(cr.split("/")[-1])


def get_store():
    if config.SUPABASE_URL and config.SUPABASE_SERVICE_KEY:
        return SupabaseStore(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
    return SQLiteStore(config.DB_PATH)
