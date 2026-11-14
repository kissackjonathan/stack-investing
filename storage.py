"""Where player profiles are stored.

- Locally (default): one JSON file per player in users/<slug>.json.
- Online: a Supabase table, used automatically when Streamlit secrets contain a [supabase] section:

    [supabase]
    url = "https://xxxx.supabase.co"
    key = "service_role key"     # server-side only: never shown to visitors

  Table (run once in the Supabase SQL editor):
    create table profiles (slug text primary key, data jsonb not null, updated_at timestamptz not null default now());
    alter table profiles enable row level security;   -- no policies: only the server key can read/write

Every store has the same 4 methods: exists(slug), load(slug) -> dict | None, save(slug, data) -> version,
version(slug) -> a value that changes on every save (used to pick up changes made in another tab).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


class FileStore:
    def __init__(self, folder):
        self.folder = Path(folder)

    def _path(self, slug):
        return self.folder / f"{slug}.json"

    def exists(self, slug):
        return self._path(slug).is_file()

    def load(self, slug):
        try:
            return json.loads(self._path(slug).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def save(self, slug, data):
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self._path(slug)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)                     # atomic: a crash never leaves half a file
        return self.version(slug)

    def version(self, slug):
        try:
            return self._path(slug).stat().st_mtime_ns
        except OSError:
            return None


class SupabaseStore:
    TIMEOUT = 10

    def __init__(self, url, key):
        self.endpoint = url.rstrip("/") + "/rest/v1/profiles"
        self.session = requests.Session()
        self.session.headers.update({"apikey": key, "Content-Type": "application/json"})
        if key.startswith("eyJ"):             # legacy service_role key (a JWT) also goes in Authorization;
            self.session.headers["Authorization"] = f"Bearer {key}"   # new sb_secret_ keys use apikey only

    def _get(self, slug, columns):
        r = self.session.get(self.endpoint, params={"slug": f"eq.{slug}", "select": columns}, timeout=self.TIMEOUT)
        r.raise_for_status()
        rows = r.json()
        return rows[0] if rows else None

    def exists(self, slug):
        return self._get(slug, "slug") is not None

    def load(self, slug):
        row = self._get(slug, "data")
        return row["data"] if row else None

    def save(self, slug, data):
        stamp = datetime.now(timezone.utc).isoformat()
        r = self.session.post(self.endpoint, json={"slug": slug, "data": data, "updated_at": stamp},
                              headers={"Prefer": "resolution=merge-duplicates,return=representation"},
                              params={"select": "updated_at"}, timeout=self.TIMEOUT)
        r.raise_for_status()
        rows = r.json()
        return rows[0]["updated_at"] if rows else None

    def version(self, slug):
        row = self._get(slug, "updated_at")
        return row["updated_at"] if row else None


def get_store(secrets, folder):
    """SupabaseStore when secrets hold [supabase] url + key, else FileStore(folder)."""
    try:
        conf = secrets.get("supabase") if secrets is not None else None
    except Exception:                         # no secrets.toml at all
        conf = None
    if conf and conf.get("url") and conf.get("key"):
        return SupabaseStore(conf["url"], conf["key"])
    return FileStore(folder)
