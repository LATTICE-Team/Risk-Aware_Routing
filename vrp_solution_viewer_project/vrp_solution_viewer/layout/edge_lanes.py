from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from vrp_solution_viewer.config.defaults import LANE_GAP
from vrp_solution_viewer.model.events import MovementEvent


@dataclass(frozen=True)
class LaneAssignment:
    event: MovementEvent
    offset: float
    lane_index: int
    lane_count: int


def assign_lanes_for_overlapping_edges(
    events: list[MovementEvent], *, lane_gap: float = LANE_GAP
) -> list[LaneAssignment]:
    """Ordnet parallelen/überdeckten Routen seitliche Zeichenversätze zu.

    In dieser ersten Fassung werden Kanten mit identischem ungeordnetem
    Endpunktpaar gruppiert, also i->j und j->i gemeinsam. Dadurch werden
    mehrfach genutzte Kanten nebeneinander gezeichnet.
    """

    groups: dict[tuple[str, str], list[MovementEvent]] = defaultdict(list)
    for event in events:
        key = tuple(sorted((str(event.source), str(event.target))))
        groups[key].append(event)

    assignments: list[LaneAssignment] = []
    for group_events in groups.values():
        unique_routes = sorted(
            {(e.agent_id, str(e.source), str(e.target)) for e in group_events},
            key=lambda item: (item[1], item[2], item[0]),
        )
        route_to_index = {route: index for index, route in enumerate(unique_routes)}
        n = max(1, len(unique_routes))
        center = (n - 1) / 2.0
        for event in group_events:
            route = (event.agent_id, str(event.source), str(event.target))
            index = route_to_index[route]
            assignments.append(
                LaneAssignment(
                    event=event,
                    offset=(index - center) * lane_gap,
                    lane_index=index,
                    lane_count=n,
                )
            )
    return assignments
