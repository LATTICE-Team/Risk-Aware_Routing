from __future__ import annotations

import networkx as nx

from vrp_solution_viewer.model.events import MovementEvent
from vrp_solution_viewer.model.solution_data import SolutionData


def create_demo_solution() -> SolutionData:
    graph = nx.complete_graph(["D", "1", "2", "3", "4"], create_using=nx.DiGraph)
    positions = {
        "D": (0.0, 0.0),
        "1": (180.0, -80.0),
        "2": (340.0, 30.0),
        "3": (160.0, 160.0),
        "4": (420.0, 190.0),
    }
    labels = {"D": "Depot", "1": "Job 1", "2": "Job 2", "3": "Job 3", "4": "Job 4"}
    for node, pos in positions.items():
        graph.nodes[node]["pos"] = pos
        graph.nodes[node]["label"] = labels[node]
    for i, j in graph.edges:
        xi, yi = positions[i]
        xj, yj = positions[j]
        graph.edges[i, j]["weight"] = round(((xj - xi) ** 2 + (yj - yi) ** 2) ** 0.5 / 40.0, 2)

    container_colors = {"K1": "#e41a1c", "K2": "#377eb8", "K3": "#4daf4a"}
    container_movements = [
        MovementEvent("K1", "D", "1", 0.0, 5.0, color=container_colors["K1"]),
        MovementEvent("K1", "1", "2", 10.0, 16.0, color=container_colors["K1"]),
        MovementEvent("K2", "D", "3", 0.0, 6.0, color=container_colors["K2"]),
        MovementEvent("K2", "3", "4", 12.0, 19.0, color=container_colors["K2"]),
        MovementEvent("K3", "D", "1", 2.0, 7.0, color=container_colors["K3"]),
        MovementEvent("K3", "1", "3", 11.0, 18.0, color=container_colors["K3"]),
    ]
    robot_movements = [
        MovementEvent("R1", "D", "1", 0.0, 5.0, loaded=True, container_id="K1"),
        MovementEvent("R1", "1", "D", 5.0, 9.0, loaded=False),
        MovementEvent("R1", "D", "1", 2.0, 7.0, loaded=True, container_id="K3"),
        MovementEvent("R1", "1", "3", 11.0, 18.0, loaded=True, container_id="K3"),
        MovementEvent("R2", "D", "3", 0.0, 6.0, loaded=True, container_id="K2"),
        MovementEvent("R2", "3", "4", 12.0, 19.0, loaded=True, container_id="K2"),
        MovementEvent("R2", "4", "D", 19.0, 28.0, loaded=False),
    ]
    return SolutionData(
        graph=graph,
        containers=["K1", "K2", "K3"],
        robots=["R1", "R2"],
        container_colors=container_colors,
        container_movements=container_movements,
        robot_movements=robot_movements,
        metadata={"name": "Demo"},
    )
