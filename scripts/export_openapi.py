"""Build a public schema using a disposable credential, never deployment secrets."""

import json
from pathlib import Path

from demo_api.main import create_app

schema = create_app({"schema-build": "documentation-only-" + "x" * 32}).openapi()
Path("docs/openapi.json").write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
