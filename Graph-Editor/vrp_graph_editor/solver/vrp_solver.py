"""Platzhalter für die spätere VRP/MIP-Anbindung.

Dieses Modul ist absichtlich unabhängig von PySide6. Der Solver sollte nur den
NetworkX-Graphen oder aus ihm extrahierte Arrays/Matrizen kennen, nicht jedoch
QGraphicsItem, MainWindow oder andere GUI-Klassen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import networkx as nx


@dataclass(frozen=True)
class VRPInstance:
    """Minimale extrahierte VRP-Datenstruktur für spätere MIP-Modelle."""

    nodes: list[str]
    demands: dict[str, float]
    time_windows: dict[str, tuple[float, float]]
    edge_weights: dict[tuple[str, str], float]


def extract_vrp_instance(graph: nx.Graph) -> VRPInstance:
    """Extrahiert eine solverfreundliche Struktur aus dem NetworkX-Graphen."""
    nodes = [str(n) for n in graph.nodes]
    demands = {str(n): float(attrs.get("demand", 0.0)) for n, attrs in graph.nodes(data=True)}
    time_windows: dict[str, tuple[float, float]] = {}
    for n, attrs in graph.nodes(data=True):
        tw = attrs.get("time_window", [0.0, 0.0])
        time_windows[str(n)] = (float(tw[0]), float(tw[1]))

    edge_weights: dict[tuple[str, str], float] = {}
    for u, v, attrs in graph.edges(data=True):
        weight = float(attrs.get("weight", 0.0))
        edge_weights[(str(u), str(v))] = weight
        edge_weights[(str(v), str(u))] = weight

    return VRPInstance(
        nodes=nodes,
        demands=demands,
        time_windows=time_windows,
        edge_weights=edge_weights,
    )


def solve_vrp_with_mip(graph: nx.Graph, **kwargs: Any) -> Any:
    """Hook für ein späteres python-mip-Modell.

    Noch nicht implementiert, weil Kapazitäten, Fahrzeuganzahl, Depotmodell,
    Servicezeiten und Zielfunktion fachlich spezifiziert werden müssen.
    """
    _ = extract_vrp_instance(graph)
    raise NotImplementedError("VRP/MIP-Solver ist als Erweiterungspunkt vorbereitet, aber noch nicht implementiert.")
