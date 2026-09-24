from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PyoParamRef:
    owner: type[Any]
    name: str


@dataclass(frozen=True)
class SliderSpec:
    name: str
    minimum: float
    maximum: float
    step: float
    default: float
    description: str
    help_text: str
    pyo_refs: tuple[PyoParamRef, ...] = ()
