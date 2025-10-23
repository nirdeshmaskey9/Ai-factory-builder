from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ai_factory.builders.base import Builder


class WebBuilder(Builder):
    def build_domain(self, *, blueprint: Mapping[str, Any], options: Mapping[str, Any], ctx: Mapping[str, Any], outputs_dir: Path, warnings: list[str]) -> None:
        name = str(blueprint.get("name") or blueprint.get("title") or "web_app").replace(" ", "_")
        text_fields = " ".join(
            str(blueprint.get(k, "")) for k in ("description", "title", "summary", "goal")
        ).lower()
        md = ctx.get("metadata", {}) if isinstance(ctx, dict) else {}
        is_dynamic = bool(
            blueprint.get("routes")
            or md.get("dynamic")
            or ("fastapi" in text_fields or "/hello" in text_fields)
        )
        # Multi-route full-app signal: mentions of history/summary/sqlite/jinja/templates
        is_full_app = bool(
            md.get("full_app")
            or any(k in text_fields for k in ["/history", "/summary", "sqlite", "jinja", "templates", "multi-route", "multiple routes"])  # noqa: E501
        )

        if is_full_app:
            self._build_full_app(name=name, blueprint=blueprint, outputs_dir=outputs_dir, warnings=warnings)
        elif is_dynamic:
            context = {
                "app_name": name,
                "hello_text": blueprint.get("hello_text", f"Hello from {name}"),
                "route_path": blueprint.get("route", "/hello"),
                "description": blueprint.get("description", "A generated FastAPI app."),
            }
            base = outputs_dir / name
            self.render_to_file("dynamic/app.py.j2", context, base / "app.py")
            self.render_to_file("dynamic/README.md.j2", context, base / "README.md")
            self.render_to_file("dynamic/Dockerfile.j2", context, base / "Dockerfile")
        else:
            context = {
                "app_name": name,
                "title": blueprint.get("title", name),
                "description": blueprint.get("description", "A generated web app."),
            }
            # Static HTML + minimal README (paths relative to web template root)
            self.render_to_file("index.html.j2", context, outputs_dir / name / "index.html")
            self.render_to_file("README.md.j2", context, outputs_dir / name / "README.md")

    def _build_full_app(self, *, name: str, blueprint: Mapping[str, Any], outputs_dir: Path, warnings: list[str]) -> None:
        """Render a universal FastAPI+Jinja2+SQLite multi-route app from template bank.

        Uses simple token replacement on .tmpl files under web/fastapi_full_app.
        """
        root_candidates = []
        try:
            # obtain template root from env loader
            loader = getattr(self.env, "loader", None)
            searchpath = getattr(loader, "searchpath", []) or []
            root_candidates = [Path(p) for p in searchpath]
        except Exception:
            pass
        # Fallback to repository-relative path
        root_candidates.append(Path("ai_factory") / "templates" / "web")
        tpl_root = None
        for cand in root_candidates:
            p = cand / "fastapi_full_app"
            if p.exists():
                tpl_root = p
                break
        if tpl_root is None:
            warnings.append("fastapi_full_app template missing")
            return

        base = outputs_dir / name
        (base / "routes").mkdir(parents=True, exist_ok=True)
        (base / "templates").mkdir(parents=True, exist_ok=True)
        (base / "static").mkdir(parents=True, exist_ok=True)

        # Heuristic defaults (mood-tracker friendly) unless provided
        model_name = str(blueprint.get("model_name") or name.title().replace("_", ""))
        table_name = str(blueprint.get("table") or "entries")
        fields_sql = str(blueprint.get("fields_sql") or "id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT UNIQUE, mood INTEGER, note TEXT")

        # HTML and route placeholders (date handled via SQLite date('now'))
        form_fields_html = """
  <label for=\"mood\">Mood (1–5)</label>
  <input type=\"number\" id=\"mood\" name=\"mood\" min=\"1\" max=\"5\" required>
  <label for=\"note\">Note</label>
  <textarea id=\"note\" name=\"note\" rows=\"3\" placeholder=\"Reflection (optional)\"></textarea>
""".strip()
        list_headers = "<th>date</th><th>mood</th><th>note</th>"
        list_rows_html = (
            "{% for r in rows %}<tr><td>{{ r[1] }}</td><td>{{ r[2] }}</td><td>{{ r[3] }}</td></tr>{% else %}"
            "<tr><td colspan='3'>No entries</td></tr>{% endfor %}"
        )
        summary_logic_py_lines = [
            "from datetime import date, timedelta",
            "today = date.today()",
            "start = today - timedelta(days=6)",
            "with get_conn() as conn:",
            "    rows = conn.execute(\"SELECT mood FROM \" + TABLE_NAME + \" WHERE date >= ? AND date <= ? ORDER BY date ASC\", (start.isoformat(), today.isoformat())).fetchall()",
            "moods = [int(r[0]) for r in rows]",
            "avg = round(sum(moods)/len(moods), 2) if moods else 0.0",
            "# ASCII emoticons to avoid encoding issues on some consoles",
            "emoji = ':D' if avg>=4.5 else (':)' if avg>=3.5 else (':|' if avg>=2.5 else (':(' if avg>=1.5 else ':/')))",
            "count = len(moods)",
        ]
        summary_logic_py = "\n".join("    "+ln for ln in summary_logic_py_lines)
        form_args = "mood: int = Form(...), note: str = Form('')"
        column_names = "date, mood, note"
        placeholders = "date('now'), ?, ?"
        column_values = "mood, note"

        tokens = {
            "__APP_NAME__": name,
            "__MODEL_NAME__": model_name,
            "__TABLE_NAME__": table_name,
            "__FIELDS_SQL__": fields_sql,
            "__FORM_FIELDS_HTML__": form_fields_html,
            "__LIST_HEADERS__": list_headers,
            "__LIST_ROWS_HTML__": list_rows_html,
            "__SUMMARY_LOGIC_PY__": summary_logic_py,
            "__FORM_ARGS__": form_args,
            "__COLUMN_NAMES__": column_names,
            "__PLACEHOLDERS__": placeholders,
            "__COLUMN_VALUES_LIST__": column_values,
        }

        def render_tmpl(rel: str, dest: Path) -> None:
            src = tpl_root / rel
            text = src.read_text(encoding="utf-8")
            for k, v in tokens.items():
                text = text.replace(k, v)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")

        # Core modules
        render_tmpl("main.py.tmpl", base / "main.py")
        render_tmpl("database.py.tmpl", base / "database.py")
        render_tmpl("models.py.tmpl", base / "models.py")
        # Routes
        (base / "routes" / "__init__.py").write_text("", encoding="utf-8")
        render_tmpl("routes/home.py.tmpl", base / "routes" / "home.py")
        render_tmpl("routes/log.py.tmpl", base / "routes" / "log.py")
        render_tmpl("routes/history.py.tmpl", base / "routes" / "history.py")
        render_tmpl("routes/summary.py.tmpl", base / "routes" / "summary.py")
        # Templates and static
        for rel in ["templates/base.html", "templates/index.html", "templates/history.html", "templates/summary.html"]:
            render_tmpl(rel, base / rel)
        render_tmpl("static/style.css", base / "static" / "style.css")
        # Preview compatibility wrapper
        (base / "app.py").write_text("from main import app\n", encoding="utf-8")
