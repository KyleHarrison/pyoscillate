# Run: uv run flet run src/flet/master_rack/app.py

"""Master rack: a group per patch directory, nested the way the directories
are, each offering every concrete patch found directly in that directory."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from dataclasses import dataclass, field

import pyoscillate.patches as patches_root
from pyoscillate.controller import GroupController, Slot
from pyoscillate.patches.base import Patch
from pyoscillate.projects.base import Rack


def discover_directories() -> dict[tuple[str, ...], list[type[Patch]]]:
    """Every playable `Patch` subclass under `pyoscillate.patches`, keyed by
    the directory it lives in (a path of directory names below `patches/`;
    a package's own `__init__` is in the package's directory). Directories and
    classes are in alphabetical order. A class that another discovered class
    extends is a style family's shared base, not a playable voice, so it is
    left out."""
    found: dict[type[Patch], tuple[str, ...]] = {}
    for category in pkgutil.iter_modules(patches_root.__path__):
        if not category.ispkg:
            continue  # shared framework modules (base, common, fx, ...)
        package = importlib.import_module(f"{patches_root.__name__}.{category.name}")
        modules = [package.__name__] + [
            info.name
            for info in pkgutil.walk_packages(package.__path__, f"{package.__name__}.")
        ]
        for name in modules:
            module = importlib.import_module(name)
            parts = tuple(name.removeprefix(f"{patches_root.__name__}.").split("."))
            directory = parts if hasattr(module, "__path__") else parts[:-1]
            for value in vars(module).values():
                if (
                    inspect.isclass(value)
                    and issubclass(value, Patch)
                    and value.__module__ == module.__name__
                    and not inspect.isabstract(value)
                ):
                    found.setdefault(value, directory)
    bases = {base for cls in found for base in cls.__mro__[1:]}
    directories: dict[tuple[str, ...], list[type[Patch]]] = {}
    for cls, directory in found.items():
        if cls not in bases:
            directories.setdefault(directory, []).append(cls)
    return {
        directory: sorted(classes, key=lambda cls: cls.name)
        for directory, classes in sorted(directories.items())
    }


def discover_patches() -> dict[str, list[type[Patch]]]:
    """Every playable `Patch` subclass keyed by its top-level category (the
    first directory below `patches/`), subdirectories included, categories and
    classes in alphabetical order."""
    categories: dict[str, list[type[Patch]]] = {}
    for directory, classes in discover_directories().items():
        categories.setdefault(directory[0], []).extend(classes)
    return {
        category: sorted(classes, key=lambda cls: cls.name)
        for category, classes in categories.items()
    }


@dataclass
class _Directory:
    """One directory of the patch tree: the patches directly in it and the
    directories directly below it."""

    path: tuple[str, ...]
    classes: list[type[Patch]] = field(default_factory=list)
    children: dict[str, _Directory] = field(default_factory=dict)

    def count(self) -> int:
        return len(self.classes) + sum(c.count() for c in self.children.values())


def _title(name: str) -> str:
    """A directory name as a group title: `drums` -> "Drums", `fm` -> "FM"."""
    return name.upper() if len(name) <= 2 else name.replace("_", " ").title()


def _build_rack() -> type[Rack]:
    root = _Directory(())
    for path, classes in discover_directories().items():
        node = root
        for depth, name in enumerate(path, start=1):
            node = node.children.setdefault(name, _Directory(path[:depth]))
        node.classes.extend(classes)

    attributes: dict[str, object] = {
        "__doc__": (
            "Every patch in the repo, one group per directory, nested like the "
            "directories. A group's menu adds or removes the patches directly in "
            "it; adding never switches one on."
        ),
        "bpm": 120,
    }
    names: set[str] = set()

    def group(node: _Directory) -> GroupController:
        # inner groups first: a rack declares a group after the ones it holds
        inner = tuple(group(child) for _, child in sorted(node.children.items()))
        slots = []
        for cls in node.classes:
            if cls.name in names:
                raise ValueError(f"Duplicate patch name '{cls.name}'")
            names.add(cls.name)
            slot = Slot(cls)
            attributes[f"{cls.name}_slot"] = slot
            slots.append(slot)
        if inner:
            summary = (
                f"{node.count()} {'patch' if node.count() == 1 else 'patches'} "
                f"in {len(inner)} {'group' if len(inner) == 1 else 'groups'}."
            )
        else:
            summary = (
                f"{len(slots)} {'patch' if len(slots) == 1 else 'patches'} to add."
            )
        controller = GroupController(
            _title(node.path[-1]),
            (*slots, *inner),
            summary,
            selectable=bool(slots),
        )
        attributes[f"{'_'.join(node.path)}_group"] = controller
        return controller

    for _, top in sorted(root.children.items()):
        group(top)
    return type("MasterRack", (Rack,), attributes)


MasterRack = _build_rack()
