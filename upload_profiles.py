"""One-off: copy the local profiles in users/*.json to the Supabase table.

Needs .streamlit/secrets.toml with the [supabase] url and key (same values as on Streamlit Cloud):
    python upload_profiles.py
Profiles that already exist online are skipped, so it is safe to run twice.
"""
import json
import tomllib
from pathlib import Path

import storage

here = Path(__file__).parent
secrets = tomllib.loads((here / ".streamlit" / "secrets.toml").read_text(encoding="utf-8"))
store = storage.get_store(secrets, here / "users")
if not isinstance(store, storage.SupabaseStore):
    raise SystemExit("No [supabase] url/key in .streamlit/secrets.toml")
for path in sorted((here / "users").glob("*.json")):
    slug = path.stem
    if store.exists(slug):
        print(f"skip   {slug} (already online)")
        continue
    store.save(slug, json.loads(path.read_text(encoding="utf-8")))
    print(f"upload {slug}")
