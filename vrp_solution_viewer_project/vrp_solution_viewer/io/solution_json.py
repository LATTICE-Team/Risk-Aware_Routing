from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx
from networkx.readwrite import json_graph

from vrp_solution_viewer.model.events import MovementEvent
from vrp_solution_viewer.model.solution_data import SolutionData


def load_solution_json(path: str | Path) -> SolutionData:
    with Path(path).open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return solution_from_dict(payload)


def save_solution_json(solution: SolutionData, path: str | Path) -> None:
    payload = solution_to_dict(solution)
    with Path(path).open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)


def solution_from_dict(payload: dict[str, Any]) -> SolutionData:
    if "graph" not in payload:
        raise ValueError("JSON enthält keinen Schlüssel 'graph'.")

    graph = json_graph.node_link_graph(payload["graph"], edges="edges")

    solution = SolutionData(
        graph=graph,
        containers=[str(k) for k in payload.get("containers", [])],
        robots=[str(v) for v in payload.get("robots", [])],
        container_colors={str(k): str(c) for k, c in payload.get("container_colors", {}).items()},
        container_movements=[_movement_from_dict(item) for item in payload.get("container_movements", [])],
        robot_movements=[_movement_from_dict(item) for item in payload.get("robot_movements", [])],
        metadata=dict(payload.get("metadata", {})),
    )
    solution.validate()
    return solution


def solution_to_dict(solution: SolutionData) -> dict[str, Any]:
    return {
        "graph": json_graph.node_link_data(solution.graph, edges="edges"),
        "containers": solution.containers,
        "robots": solution.robots,
        "container_colors": solution.container_colors,
        "container_movements": [_movement_to_dict(e) for e in solution.container_movements],
        "robot_movements": [_movement_to_dict(e) for e in solution.robot_movements],
        "metadata": solution.metadata,
    }


def _movement_from_dict(item: dict[str, Any]) -> MovementEvent:
    return MovementEvent(
        agent_id=str(item["agent_id"]),
        source=item["source"],
        target=item["target"],
        start=float(item["start"]),
        end=float(item["end"]),
        loaded=bool(item.get("loaded", False)),
        container_id=None if item.get("container_id") is None else str(item.get("container_id")),
        color=item.get("color"),
        metadata=dict(item.get("metadata", {})),
    )


def _movement_to_dict(event: MovementEvent) -> dict[str, Any]:
    data = {
        "agent_id": event.agent_id,
        "source": event.source,
        "target": event.target,
        "start": event.start,
        "end": event.end,
    }
    if event.loaded:
        data["loaded"] = event.loaded
    if event.container_id is not None:
        data["container_id"] = event.container_id
    if event.color is not None:
        data["color"] = event.color
    if event.metadata:
        data["metadata"] = event.metadata
    return data


def normalize_node_ids_to_strings(graph: nx.Graph) -> nx.Graph:
    """Hilfsfunktion für konsistente JSON-IDs bei gemischt typisierten Knoten."""

    mapping = {node: str(node) for node in graph.nodes}
    return nx.relabel_nodes(graph, mapping, copy=True)
