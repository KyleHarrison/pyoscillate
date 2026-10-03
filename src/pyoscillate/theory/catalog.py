"""The base for every dropdown-backed lookup: a class whose attributes are
its members, each with a stable string `id`, a display `label` and a
`category` to group a large list under."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, eq=False, kw_only=True)
class CatalogItem:
    """One member of a `Catalog`. `id` and an unset `label`/`category` are
    filled in when the member's `Catalog` is defined: `id` is the attribute
    name lower-cased, `label` its capitalised words, `category` the catalog's
    own. Members compare by identity."""

    id: str = ""
    label: str = ""
    category: str = ""


class Catalog:
    """Base for a class that lists its members as class attributes:

        class Chords(Catalog):
            TRIAD = Chord(offsets=(0, 2, 4), unit=ChordUnit.DEGREES)

    Order is definition order. A `Param` stores a member's position (a number
    a slider can hold) and persists its `id`, which survives reordering. A
    catalog can also gather other catalogs through `sources` to list their
    members together; their ids must not collide."""

    # catalogs whose members this one lists after its own
    sources: ClassVar[tuple[type[Catalog], ...]] = ()
    # the category a member that names none takes
    category: ClassVar[str] = ""

    _members: ClassVar[tuple[CatalogItem, ...]] = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        members: list[CatalogItem] = []
        for name, value in vars(cls).items():
            if isinstance(value, CatalogItem):
                object.__setattr__(value, "id", name.lower())
                if not value.label:
                    object.__setattr__(
                        value, "label", name.replace("_", " ").capitalize()
                    )
                if not value.category:
                    object.__setattr__(value, "category", cls.category)
                members.append(value)
        for source in cls.sources:
            members.extend(source.members())
        ids = [member.id for member in members]
        if len(set(ids)) != len(ids):
            raise ValueError(f"{cls.__name__} has duplicate member ids")
        cls._members = tuple(members)

    @classmethod
    def members(cls) -> tuple[CatalogItem, ...]:
        """Every member, in dropdown order."""
        return cls._members

    @classmethod
    def subset(cls, members: Iterable[CatalogItem]) -> type[Catalog]:
        """A new catalog of just `members` (each keeps its id, label and
        category), in the order given."""
        return type(
            f"{cls.__name__}Subset",
            (Catalog,),
            {member.id.upper(): member for member in members},
        )

    @classmethod
    def ids(cls) -> tuple[str, ...]:
        """Each member's stable id, in dropdown order."""
        return tuple(member.id for member in cls._members)

    @classmethod
    def labels(cls) -> tuple[str, ...]:
        """Display text for each member, in dropdown order."""
        return tuple(member.label for member in cls._members)

    @classmethod
    def categories(cls) -> tuple[str, ...]:
        """Each member's category, in dropdown order."""
        return tuple(member.category for member in cls._members)

    @classmethod
    def by_id(cls, member_id: str) -> CatalogItem:
        """The member with `member_id`."""
        for member in cls._members:
            if member.id == member_id:
                return member
        raise KeyError(f"{cls.__name__} has no member {member_id!r}")

    @classmethod
    def by_index(cls, index: int) -> CatalogItem:
        """The member at dropdown position `index`, clamped to the range."""
        return cls._members[max(0, min(index, len(cls._members) - 1))]

    @classmethod
    def index_of(cls, member: CatalogItem) -> int:
        """`member`'s dropdown position, the number a `Param` stores."""
        if member not in cls._members:
            raise ValueError(f"{member.id!r} is not a member of {cls.__name__}")
        return cls._members.index(member)

    @classmethod
    def grouped(cls) -> dict[str, tuple[CatalogItem, ...]]:
        """Members by category, categories in order of first appearance."""
        groups: dict[str, list[CatalogItem]] = {}
        for member in cls._members:
            groups.setdefault(member.category, []).append(member)
        return {category: tuple(items) for category, items in groups.items()}
