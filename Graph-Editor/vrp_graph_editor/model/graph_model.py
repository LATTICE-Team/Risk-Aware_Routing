"""NetworkX-basierte Datenhaltung für den Editor.

Dieses Modul enthält bewusst keine Qt-Widgets. Damit kann dieselbe Graphstruktur
später auch vom VRP/MIP-Solver oder von Tests verwendet werden.
"""

from __future__ import annotations

import networkx as nx

from vrp_graph_editor.config.defaults import DEFAULT_EDGE_COLOR, DEFAULT_NODE_COLOR
from vrp_graph_editor.model.attributes import (
    edge_defaults,
    node_defaults,
    normalize_time_window,
    valid_color,
)


class GraphModel:
    """Kapselt den NetworkX-Graphen und elementare Modelloperationen."""

    def __init__(self, graph: nx.Graph | None = None) -> None:
        self.graph: nx.Graph = graph if graph is not None else nx.Graph()
        self.node_counter = 1
        self.normalize_loaded_graph()
        self.update_node_counter_from_graph()

    def clear(self) -> None:
        self.graph = nx.Graph()
        self.node_counter = 1

    def set_graph(self, graph: nx.Graph) -> None:
        if graph.is_multigraph():
            raise ValueError("MultiGraph-Dateien werden in dieser Version nicht unterstützt.")
        self.graph = nx.Graph(graph)
        self.normalize_loaded_graph()
        self.update_node_counter_from_graph()

    def next_node_id(self) -> str:
        while True:
            candidate = f"N{self.node_counter}"
            self.node_counter += 1
            if candidate not in self.graph.nodes:
                return candidate

    def add_node(self, pos) -> str:
        node_id = self.next_node_id()
        self.graph.add_node(node_id, **node_defaults(node_id, pos))
        return node_id

    def add_edge(self, u: str, v: str) -> None:
        if u == v:
            raise ValueError("Schleifen werden in dieser Version nicht unterstützt.")
        if self.graph.has_edge(u, v):
            raise ValueError(f"Zwischen {u} und {v} existiert bereits eine Kante.")
        self.graph.add_edge(u, v, **edge_defaults(u, v))

    def remove_edge(self, u: str, v: str) -> None:
        if self.graph.has_edge(u, v):
            self.graph.remove_edge(u, v)

    def remove_node(self, node_id: str) -> None:
        if node_id in self.graph:
            self.graph.remove_node(node_id)

    def normalize_loaded_graph(self) -> None:
        """Bringt geladene Graphen auf das erwartete Attributschema."""
        if any(not isinstance(n, str) for n in self.graph.nodes):
            self.graph = nx.relabel_nodes(self.graph, {n: str(n) for n in self.graph.nodes}, copy=True)

        if self.graph.number_of_nodes() > 0:
            fallback_positions = nx.spring_layout(self.graph, seed=7, scale=250.0)
        else:
            fallback_positions = {}

        for node_id, attrs in self.graph.nodes(data=True):
            fallback = fallback_positions.get(node_id, (0.0, 0.0))
            raw_pos = attrs.get("position", [float(fallback[0]), float(fallback[1])])
            try:
                x, y = float(raw_pos[0]), float(raw_pos[1])
            except Exception:
                x, y = float(fallback[0]), float(fallback[1])

            defaults = node_defaults(str(node_id), (x, y))
            defaults.update(attrs)
            defaults["time_window"] = normalize_time_window(defaults.get("time_window"))
            defaults["color"] = valid_color(str(defaults.get("color", DEFAULT_NODE_COLOR)), DEFAULT_NODE_COLOR)
            defaults["position"] = [x, y]
            attrs.clear()
            attrs.update(defaults)

        for u, v, attrs in self.graph.edges(data=True):
            defaults = edge_defaults(str(u), str(v))
            defaults.update(attrs)
            defaults["color"] = valid_color(str(defaults.get("color", DEFAULT_EDGE_COLOR)), DEFAULT_EDGE_COLOR)
            try:
                defaults["width"] = max(0.1, float(defaults.get("width", 2.0)))
            except (TypeError, ValueError):
                defaults["width"] = 2.0
            try:
                defaults["weight"] = float(defaults.get("weight", 0.0))
            except (TypeError, ValueError):
                defaults["weight"] = 0.0
            attrs.clear()
            attrs.update(defaults)

    def update_node_counter_from_graph(self) -> None:
        max_numeric = 0
        for node in self.graph.nodes:
            if isinstance(node, str) and node.startswith("N"):
                suffix = node[1:]
                if suffix.isdigit():
                    max_numeric = max(max_numeric, int(suffix))
        self.node_counter = max_numeric + 1
