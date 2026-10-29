"""Engine backends.

Use :func:`get_engine` to obtain a backend by name. New backends register
themselves in :data:`REGISTRY`; the XG backend will live beside gnubg here.
"""

from __future__ import annotations

from typing import Callable

from bgcoach.engines.base import (
    CubeEval,
    Engine,
    EngineError,
    Evaluation,
    MoveEval,
    Probs,
    StaticEval,
)

REGISTRY: dict[str, Callable[[], Engine]] = {}


def register(name: str):
    def deco(factory: Callable[[], Engine]):
        REGISTRY[name] = factory
        return factory
    return deco


@register("gnubg")
def _gnubg() -> Engine:
    from bgcoach.engines.gnubg import GnubgEngine

    return GnubgEngine()


def get_engine(name: str = "gnubg") -> Engine:
    try:
        factory = REGISTRY[name]
    except KeyError:
        raise EngineError(f"unknown engine {name!r}; known: {sorted(REGISTRY)}") from None
    return factory()


__all__ = [
    "CubeEval",
    "Engine",
    "EngineError",
    "Evaluation",
    "MoveEval",
    "Probs",
    "StaticEval",
    "REGISTRY",
    "get_engine",
    "register",
]
