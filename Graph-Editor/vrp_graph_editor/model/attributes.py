"""Attribut-Defaultwerte und robuste Normalisierung für Graphdaten.

Dieses Modul bleibt bewusst unabhängig von PySide6, damit Graphdaten und Solver
auch ohne GUI-Kontext getestet und genutzt werden können.
"""

from __future__ import annotations

import re
from typing import Any, Sequence

from vrp_graph_editor.config.defaults import (
    DEFAULT_CLASSIFICATIONS,
    DEFAULT_EDGE_COLOR,
    DEFAULT_NODE_COLOR,
)

_HEX_COLOR_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def valid_color(value: str, fallback: str) -> str:
    """Gibt einen validen Hex-Farbwert zurück oder nutzt `fallback`.

    Akzeptiert `#RRGGBB`, `RRGGBB`, `#RGB` und `RGB`. Die Rückgabe ist immer
    ein normalisierter sechsstelliger Hexwert in Kleinschreibung.
    """
    raw = str(value).strip()
    match = _HEX_COLOR_RE.match(raw)
    if not match:
        return fallback.lower()

    hex_value = match.group(1).lower()
    if len(hex_value) == 3:
        hex_value = "".join(ch * 2 for ch in hex_value)
    return f"#{hex_value}"


def normalize_time_window(value: Any) -> list[float]:
    """Normalisiert Listen, Tupel oder einfache Strings zu [start, end]."""
    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            return [float(value[0]), float(value[1])]
        except (TypeError, ValueError):
            return [0.0, 0.0]

    if isinstance(value, str):
        cleaned = value.replace("[", "").replace("]", "").replace(";", ",").replace("-", ",")
        parts = [p.strip() for p in cleaned.split(",") if p.strip()]
        if len(parts) >= 2:
            try:
                return [float(parts[0]), float(parts[1])]
            except ValueError:
                return [0.0, 0.0]

    return [0.0, 0.0]


def normalize_position(pos: Any) -> tuple[float, float]:
    """Normalisiert QPointF-ähnliche Objekte oder Sequenzen zu `(x, y)`."""
    if hasattr(pos, "x") and hasattr(pos, "y"):
        return float(pos.x()), float(pos.y())
    if isinstance(pos, Sequence) and len(pos) >= 2:
        return float(pos[0]), float(pos[1])
    return 0.0, 0.0


def node_defaults(node_id: str, pos: Any) -> dict:
    """Defaultattribute für einen VRP-Knoten."""
    x, y = normalize_position(pos)
    return {
        "label": node_id,
        "demand": 0.0,
        "time_window": [0.0, 0.0],
        "color": DEFAULT_NODE_COLOR,
        "classification": DEFAULT_CLASSIFICATIONS[0],
        "position": [x, y],
    }


def edge_defaults(u: str, v: str) -> dict:
    """Defaultattribute für eine VRP-Kante."""
    return {
        "label": f"{u}–{v}",
        "weight": 0.0,
        "color": DEFAULT_EDGE_COLOR,
        "width": 2.0,
    }
