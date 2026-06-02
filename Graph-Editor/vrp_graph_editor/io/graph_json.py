"""Persistenzfunktionen für NetworkX Node-Link-JSON."""

from __future__ import annotations

import json
from pathlib import Path

import networkx as nx
from networkx.readwrite import json_graph


def graph_to_node_link_data(graph: nx.Graph) -> dict:
    """Kompatibilitätswrapper für NetworkX 2.x/3.x."""
    try:
        return json_graph.node_link_data(graph, edges="edges")
    except TypeError:  # NetworkX < 3.4
        return json_graph.node_link_data(graph)


def node_link_data_to_graph(data: dict) -> nx.Graph:
    """Kompatibilitätswrapper für NetworkX 2.x/3.x."""
    try:
        return json_graph.node_link_graph(data, edges="edges")
    except TypeError:  # NetworkX < 3.4
        return json_graph.node_link_graph(data)


def load_graph_json(path: str | Path) -> nx.Graph:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return node_link_data_to_graph(data)


def save_graph_json(graph: nx.Graph, path: str | Path) -> None:
    data = graph_to_node_link_data(graph)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
