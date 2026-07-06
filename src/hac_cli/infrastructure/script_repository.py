"""Filesystem-backed script library with YAML frontmatter metadata."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from thefuzz import process as fuzzy_process

from hac_cli.domain.models import ScriptMeta
from hac_cli.domain.ports import IScriptRepository

_SCRIPTS_ROOT = Path(__file__).parents[4] / "scripts"
_META_PATTERN = re.compile(r"^// @meta\s*(.*?)^// @end", re.DOTALL | re.MULTILINE)
_FIELD_PATTERN = re.compile(r"^// (\w+):\s*(.+)$", re.MULTILINE)


class FilesystemScriptRepository(IScriptRepository):
    def __init__(self, scripts_root: Path = _SCRIPTS_ROOT) -> None:
        self._root = scripts_root

    def list_scripts(self, category: Optional[str] = None) -> list[ScriptMeta]:
        pattern = f"{category}/**/*.groovy" if category else "**/*.groovy"
        scripts = []
        for path in sorted(self._root.glob(pattern)):
            if path.name.startswith("_"):
                continue
            meta = self._parse_meta(path)
            if meta:
                scripts.append(meta)
        return scripts

    def get_script_content(self, path: str) -> str:
        full_path = self._resolve_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"Script not found: {path}")
        return full_path.read_text(encoding="utf-8")

    def search_scripts(self, query: str) -> list[ScriptMeta]:
        all_scripts = self.list_scripts()
        if not all_scripts:
            return []

        search_corpus = {
            s.path: f"{s.name} {s.description} {' '.join(s.tags)}"
            for s in all_scripts
        }

        results = fuzzy_process.extractBests(query, search_corpus, score_cutoff=40, limit=5)
        matched_paths = {r[2] for r in results}
        return [s for s in all_scripts if s.path in matched_paths]

    def _resolve_path(self, path: str) -> Path:
        clean = path.lstrip("/").removesuffix(".groovy")
        return self._root / f"{clean}.groovy"

    def _parse_meta(self, path: Path) -> Optional[ScriptMeta]:
        content = path.read_text(encoding="utf-8")
        match = _META_PATTERN.search(content)

        relative = path.relative_to(self._root).with_suffix("")
        category = relative.parts[0] if len(relative.parts) > 1 else "misc"
        lib_path = str(relative)

        if not match:
            return ScriptMeta(
                name=path.stem.replace("_", " ").title(),
                description="",
                category=category,
                path=lib_path,
            )

        fields: dict[str, str] = dict(_FIELD_PATTERN.findall(match.group(0)))

        raw_tags = fields.get("tags", "")
        tags = tuple(t.strip().strip("[]") for t in raw_tags.split(",") if t.strip())

        return ScriptMeta(
            name=fields.get("name", path.stem),
            description=fields.get("description", ""),
            category=fields.get("category", category),
            path=lib_path,
            tags=tags,
        )
