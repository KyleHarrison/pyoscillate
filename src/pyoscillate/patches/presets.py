from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ipywidgets import HTML, Dropdown, HBox

Preset = dict[str, dict[str, Any]]


def load_catalog(catalog_dir: Path) -> dict[str, Preset]:
    return {path.stem: json.loads(path.read_text()) for path in sorted(catalog_dir.glob("*.json"))}


def save_preset(catalog_dir: Path, name: str, values: Preset) -> Path:
    catalog_dir.mkdir(parents=True, exist_ok=True)
    path = catalog_dir / f"{name}.json"
    path.write_text(json.dumps(values, indent=2) + "\n")
    return path


class PresetController:
    def __init__(self, catalog_dir: Path) -> None:
        self.catalog_dir = catalog_dir
        self.catalog = load_catalog(catalog_dir)
        self.current: Preset = {}
        self._bindings: dict[str, tuple[dict[str, Any], Callable[[], None]]] = {}
        self._applying = False
        self.selector = Dropdown(
            options=list(self.catalog),
            value=next(iter(self.catalog), None),
            description="preset",
        )
        self.selector.observe(self._select, names="value")
        if self.selector.value is not None:
            self._select({"new": self.selector.value})

    @property
    def applying(self) -> bool:
        return self._applying

    def display(self) -> HBox:
        return HBox([self.selector, HTML("Select a saved patch catalog preset.")])

    def register(
        self,
        patch_name: str,
        widgets: dict[str, Any],
        refresh: Callable[[], None],
    ) -> None:
        self._bindings[patch_name] = (widgets, refresh)
        self._apply_patch(patch_name)

    def values(self) -> Preset:
        return {
            patch_name: {name: widget.value for name, widget in widgets.items()}
            for patch_name, (widgets, _) in self._bindings.items()
        }

    def _select(self, change: dict[str, Any]) -> None:
        self.current = self.catalog.get(change["new"], {})
        self._applying = True
        try:
            for patch_name in self._bindings:
                self._apply_patch(patch_name)
        finally:
            self._applying = False
        for _, refresh in self._bindings.values():
            refresh()

    def _apply_patch(self, patch_name: str) -> None:
        patch_values = self.current.get(patch_name, {})
        binding = self._bindings.get(patch_name)
        if binding is None:
            return
        widgets, _ = binding
        for name, widget in widgets.items():
            if name in patch_values:
                widget.value = patch_values[name]
