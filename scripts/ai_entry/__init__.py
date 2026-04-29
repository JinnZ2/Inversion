"""AI entry point package.

One Python handler module per markdown document in this repository.
Handlers share a common ``MarkdownDoc`` base (see ``_common.py``) and are
registered lazily in ``REGISTRY`` so that a single CLI (``ai_entry.py`` at
the repository root) can list, dump, and analyze the whole corpus.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._common import MarkdownDoc, parse_frontmatter, REPO_ROOT

# Slug -> dotted module path (lazy: avoids re-importing a submodule when the
# submodule is also run as __main__ via ``python3 -m scripts.ai_entry.<slug>``).
_HANDLER_MODULES: dict[str, str] = {
    "readme": "scripts.ai_entry.readme",
    "institutional-inversion": "scripts.ai_entry.institutional_inversion",
    "documentation": "scripts.ai_entry.documentation",
    "harm-reduction": "scripts.ai_entry.harm_reduction",
    "middle-men": "scripts.ai_entry.middle_men",
    "survival": "scripts.ai_entry.survival",
    "reconstitution-protocol": "scripts.ai_entry.reconstitution_protocol",
    "meta-framework-note": "scripts.ai_entry.meta_framework_note",
    "scope-collapse": "scripts.ai_entry.scope_collapse",
}


class _Registry:
    """Mapping-like view that imports handler modules on first access."""

    def __init__(self, modules: dict[str, str]) -> None:
        self._modules = modules
        self._cache: dict[str, MarkdownDoc] = {}

    def _load(self, slug: str) -> MarkdownDoc:
        if slug in self._cache:
            return self._cache[slug]
        import importlib

        module = importlib.import_module(self._modules[slug])
        doc = getattr(module, "DOC")
        self._cache[slug] = doc
        return doc

    def __contains__(self, slug: object) -> bool:
        return slug in self._modules

    def __getitem__(self, slug: str) -> MarkdownDoc:
        if slug not in self._modules:
            raise KeyError(slug)
        return self._load(slug)

    def __iter__(self):
        return iter(self._modules)

    def keys(self):
        return self._modules.keys()

    def values(self):
        for slug in self._modules:
            yield self._load(slug)

    def items(self):
        for slug in self._modules:
            yield slug, self._load(slug)

    def __len__(self) -> int:
        return len(self._modules)


REGISTRY: _Registry = _Registry(_HANDLER_MODULES)

if TYPE_CHECKING:  # for type-checkers that want a concrete Mapping
    REGISTRY: dict[str, MarkdownDoc]  # type: ignore[no-redef]

__all__ = ["MarkdownDoc", "parse_frontmatter", "REPO_ROOT", "REGISTRY"]
