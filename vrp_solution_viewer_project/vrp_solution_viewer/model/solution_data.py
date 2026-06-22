from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

import networkx as nx

from vrp_solution_viewer.model.events import MovementEvent

Point = tuple[float, float]


@dataclass
class AgentState:
    agent_id: str
    position: Point
    active_event: MovementEvent | None


@dataclass
class SolutionData:
    """Normalisiertes Datenmodell für Visualisierung und Animation.

    Das Modell ist absichtlich unabhängig von python-mip. Solver-spezifische
    Variablen werden vorher durch einen Adapter in MovementEvent-Objekte
    überführt.
    """

    graph: nx.Graph
    containers: list[str]
    robots: list[str]
    container_movements: list[MovementEvent] = field(default_factory=list)
    robot_movements: list[MovementEvent] = field(default_factory=list)
    container_colors: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.container_movements.sort(key=lambda e: (e.agent_id, e.start, e.end))
        self.robot_movements.sort(key=lambda e: (e.agent_id, e.start, e.end))

    @property
    def start_time(self) -> float:
        events = [*self.container_movements, *self.robot_movements]
        return min((e.start for e in events), default=0.0)

    @property
    def end_time(self) -> float:
        events = [*self.container_movements, *self.robot_movements]
        return max((e.end for e in events), default=1.0)

    def node_position(self, node: Any) -> Point:
        data = self.graph.nodes[node]
        if "pos" in data:
            return _as_point(data["pos"])
        if "position" in data:
            return _as_point(data["position"])
        if "x" in data and "y" in data:
            return float(data["x"]), float(data["y"])
        raise ValueError(
            f"Knoten {node!r} hat keine Position. Erwartet wird 'pos', 'position' oder 'x'/'y'."
        )

    def validate(self) -> None:
        for node in self.graph.nodes:
            self.node_position(node)
        graph_nodes = set(self.graph.nodes)
        for event in [*self.container_movements, *self.robot_movements]:
            if event.source not in graph_nodes:
                raise ValueError(f"Quelle {event.source!r} aus Event {event!r} liegt nicht im Graphen.")
            if event.target not in graph_nodes:
                raise ValueError(f"Ziel {event.target!r} aus Event {event!r} liegt nicht im Graphen.")
            if event.end < event.start:
                raise ValueError(f"Event hat end < start: {event!r}")

    def container_state(self, container_id: str, time_value: float) -> AgentState | None:
        return self._agent_state(container_id, time_value, self._events_for(container_id, self.container_movements))

    def robot_state(self, robot_id: str, time_value: float) -> AgentState | None:
        return self._agent_state(robot_id, time_value, self._events_for(robot_id, self.robot_movements))

    def _events_for(self, agent_id: str, events: Iterable[MovementEvent]) -> list[MovementEvent]:
        return sorted((e for e in events if e.agent_id == agent_id), key=lambda e: (e.start, e.end))

    def _agent_state(
        self, agent_id: str, time_value: float, events: list[MovementEvent]
    ) -> AgentState | None:
        if not events:
            return None

        previous: MovementEvent | None = None
        for event in events:
            if event.contains(time_value):
                p0 = self.node_position(event.source)
                p1 = self.node_position(event.target)
                alpha = event.progress(time_value)
                return AgentState(agent_id, _interpolate(p0, p1, alpha), event)
            if time_value < event.start:
                if previous is None:
                    return AgentState(agent_id, self.node_position(event.source), None)
                return AgentState(agent_id, self.node_position(previous.target), None)
            previous = event

        assert previous is not None
        return AgentState(agent_id, self.node_position(previous.target), None)


def _as_point(value: Any) -> Point:
    if isinstance(value, str):
        parts = value.replace(";", ",").split(",")
        if len(parts) != 2:
            raise ValueError(f"Positionsstring {value!r} ist nicht zweidimensional.")
        return float(parts[0]), float(parts[1])
    if len(value) != 2:
        raise ValueError(f"Position {value!r} ist nicht zweidimensional.")
    return float(value[0]), float(value[1])


def _interpolate(p0: Point, p1: Point, alpha: float) -> Point:
    return p0[0] + alpha * (p1[0] - p0[0]), p0[1] + alpha * (p1[1] - p0[1])
