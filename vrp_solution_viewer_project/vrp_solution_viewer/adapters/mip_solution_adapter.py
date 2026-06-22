from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import networkx as nx

from vrp_solution_viewer.config.defaults import CONTAINER_PALETTE
from vrp_solution_viewer.model.events import MovementEvent
from vrp_solution_viewer.model.solution_data import SolutionData

NumericMap = Mapping[tuple[Any, ...], float | int | bool]
TimeMap = Mapping[Any, float | int]
RobotTimeMap = Mapping[tuple[Any, Any], float | int]


def build_solution_from_active_variables(
    graph: nx.Graph,
    c: NumericMap | None,
    x: NumericMap,
    r_empty: NumericMap,
    r_loaded: NumericMap,
    t_a_job: TimeMap,
    t_d_job: TimeMap,
    t_a_robot: RobotTimeMap,
    t_d_robot: RobotTimeMap,
    *,
    container_ids: list[Any] | None = None,
    robot_ids: list[Any] | None = None,
    tolerance: float = 0.5,
) -> SolutionData:
    """Erzeugt eine normalisierte Viewer-Lösung aus aktiven MIP-Variablen.

    Erwartete Dictionary-Schlüssel:

    - c[(k, i)]
    - x[(k, i, j)]
    - r_empty[(v, i, j)] für r_{v,i,j,0}
    - r_loaded[(v, i, j)] für r_{v,i,j,1}
    - t_a_job[i], t_d_job[i]
    - t_a_robot[(v, i)], t_d_robot[(v, i)]

    Zeitliche Interpretation:

    - Containerbewegung i -> j: [t_d_job[i], t_a_job[j]]
    - Roboterbewegung i -> j: [t_d_robot[(v, i)], t_a_robot[(v, j)]]

    Diese Interpretation passt zu den von dir genannten Zeitvariablen. Wenn dein
    Modell zusätzliche Umschlag-, Warte- oder Depotzeitvariablen besitzt, sollte
    nur diese Adapterfunktion erweitert werden.
    """

    containers = [str(k) for k in (container_ids or _ids_from_first_position(x, 0))]
    robots = [str(v) for v in (robot_ids or sorted({str(key[0]) for key in [*r_empty.keys(), *r_loaded.keys()]}))]
    container_colors = {k: CONTAINER_PALETTE[index % len(CONTAINER_PALETTE)] for index, k in enumerate(containers)}

    container_movements: list[MovementEvent] = []
    for key, value in x.items():
        if not _active(value, tolerance):
            continue
        if len(key) != 3:
            raise ValueError(f"x-Schlüssel muss (k, i, j) sein, erhalten: {key!r}")
        k, i, j = key
        start = _time(t_d_job, i, f"t_d_job[{i!r}]")
        end = _time(t_a_job, j, f"t_a_job[{j!r}]")
        container_movements.append(
            MovementEvent(
                agent_id=str(k),
                source=i,
                target=j,
                start=start,
                end=end,
                color=container_colors.get(str(k)),
                metadata={"variable": "x", "key": tuple(map(str, key))},
            )
        )

    robot_movements: list[MovementEvent] = []
    robot_movements.extend(
        _robot_movements_from_r(r_empty, t_d_robot, t_a_robot, loaded=False, tolerance=tolerance)
    )
    robot_movements.extend(
        _robot_movements_from_r(r_loaded, t_d_robot, t_a_robot, loaded=True, tolerance=tolerance)
    )

    metadata: dict[str, Any] = {"source": "mip_solution_adapter"}
    if c is not None:
        metadata["container_job_assignments"] = [
            {"container": str(k), "job": i}
            for (k, i), value in c.items()
            if _active(value, tolerance)
        ]

    solution = SolutionData(
        graph=graph,
        containers=containers,
        robots=robots,
        container_colors=container_colors,
        container_movements=container_movements,
        robot_movements=robot_movements,
        metadata=metadata,
    )
    solution.validate()
    return solution


def _robot_movements_from_r(
    r: NumericMap,
    t_d_robot: RobotTimeMap,
    t_a_robot: RobotTimeMap,
    *,
    loaded: bool,
    tolerance: float,
) -> list[MovementEvent]:
    result: list[MovementEvent] = []
    variable_name = "r_loaded" if loaded else "r_empty"
    for key, value in r.items():
        if not _active(value, tolerance):
            continue
        if len(key) != 3:
            raise ValueError(f"r-Schlüssel muss (v, i, j) sein, erhalten: {key!r}")
        v, i, j = key
        result.append(
            MovementEvent(
                agent_id=str(v),
                source=i,
                target=j,
                start=_time(t_d_robot, (v, i), f"t_d_robot[{v!r}, {i!r}]") ,
                end=_time(t_a_robot, (v, j), f"t_a_robot[{v!r}, {j!r}]") ,
                loaded=loaded,
                metadata={"variable": variable_name, "key": tuple(map(str, key))},
            )
        )
    return result


def _active(value: float | int | bool, tolerance: float) -> bool:
    return float(value) > tolerance


def _time(mapping: Mapping[Any, float | int], key: Any, label: str) -> float:
    if key not in mapping:
        raise KeyError(f"Zeitwert {label} fehlt.")
    return float(mapping[key])


def _ids_from_first_position(mapping: NumericMap, position: int) -> list[Any]:
    return sorted({key[position] for key in mapping.keys()}, key=str)
