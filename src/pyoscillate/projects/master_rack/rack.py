# Run: uv run flet run src/flet/master_rack/app.py

"""Master rack: one selectable group per patch category directory, each
offering every concrete patch found there."""

from __future__ import annotations

import importlib
import inspect
import pkgutil

import pyoscillate.patches as patches_root
from pyoscillate.controller import GroupController, Slot
from pyoscillate.patches.base import Patch
from pyoscillate.projects.base import Rack


def discover_patches() -> dict[str, list[type[Patch]]]:
    """Every playable `Patch` subclass under `pyoscillate.patches`, keyed by
    its category (the directory under `patches/`), categories and classes in
    alphabetical order. A class that another discovered class extends is a
    style family's shared base, not a playable voice, so it is left out."""
    found: dict[type[Patch], str] = {}
    for category in pkgutil.iter_modules(patches_root.__path__):
        if not category.ispkg:
            continue  # shared framework modules (base, common, fx, ...)
        package = importlib.import_module(f"{patches_root.__name__}.{category.name}")
        modules = [package.__name__] + [
            info.name for info in pkgutil.walk_packages(package.__path__, f"{package.__name__}.")
        ]
        for name in modules:
            module = importlib.import_module(name)
            for value in vars(module).values():
                if (
                    inspect.isclass(value)
                    and issubclass(value, Patch)
                    and value.__module__ == module.__name__
                    and not inspect.isabstract(value)
                ):
                    found.setdefault(value, category.name)
    bases = {base for cls in found for base in cls.__mro__[1:]}
    categories: dict[str, list[type[Patch]]] = {}
    for cls, category in found.items():
        if cls not in bases:
            categories.setdefault(category, []).append(cls)
    return {
        category: sorted(classes, key=lambda cls: cls.name)
        for category, classes in sorted(categories.items())
    }


def _category_title(category: str) -> str:
    return category.replace("_", " ").title()


def _build_rack() -> type[Rack]:
    attributes: dict[str, object] = {
        "__doc__": (
            "Every patch in the repo, one group per category. Each group's "
            "menu adds or removes patches; adding never switches one on."
        ),
        "bpm": 120,
    }
    names: set[str] = set()
    for category, classes in discover_patches().items():
        slots = []
        for cls in classes:
            if cls.name in names:
                raise ValueError(f"Duplicate patch name '{cls.name}'")
            names.add(cls.name)
            slot = Slot(cls)
            attributes[f"{cls.name}_slot"] = slot
            slots.append(slot)
        attributes[f"{category}_group"] = GroupController(
            _category_title(category),
            tuple(slots),
            f"{len(slots)} {category.replace('_', ' ')} patches to add.",
            selectable=True,
        )
    return type("MasterRack", (Rack,), attributes)


MasterRack = _build_rack()
