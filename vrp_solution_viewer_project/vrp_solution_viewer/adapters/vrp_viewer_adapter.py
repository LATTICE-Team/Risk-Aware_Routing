"""
Adapter für das aktuelle vrp2.py-Modell mit Variablen
x, y, firsttask, nexttask, lasttask, cont_start, cont_arrival,
cont_departure und cont_end.

Ziel:
    Erzeuge eine JSON-Datei, die im vrp_solution_viewer geöffnet werden kann.

Verwendung in vrp2.py nach erfolgreicher Optimierung:

    if status in (mip.OptimizationStatus.OPTIMAL, mip.OptimizationStatus.FEASIBLE):
        from vrp_viewer_adapter import export_viewer_json

        export_viewer_json(
            "solution_from_vrp2.json",
            graph=G,
            I=I,
            K=K,
            V=V,
            T=T,
            c=c,
            x=x,
            y=y,
            A=A,
            firsttask=firsttask,
            nexttask=nexttask,
            lasttask=lasttask,
            cont_start=cont_start,
            cont_arrival=cont_arrival,
            cont_departure=cont_departure,
            cont_end=cont_end,
        )

Danach im Viewer die erzeugte JSON-Datei öffnen.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import networkx as nx
from networkx.readwrite import json_graph


# Farben aus deiner bisherigen Palette, als Hex-Strings für den Viewer.
CONTAINER_COLORS = [
    "#ebac23", "#b80058", "#008cf9", "#006e00", "#00bbad",
    "#d163e6", "#b24502", "#ff9287", "#5954d6", "#00c6f8",
    "#878500", "#00a76c", "#bdbdbd",
]


def export_viewer_json(
    output_path: str | Path,
    *,
    graph: nx.Graph,
    I: Iterable[Any],
    K: Iterable[Any],
    V: Iterable[Any],
    T: list[list[float]],
    c: list[list[Any]] | None,
    x: list[list[list[Any]]],
    y: list[list[list[list[Any]]]],
    A: list[tuple[Any, Any, Any]],
    firsttask: list[list[Any]],
    nexttask: list[list[list[Any]]],
    lasttask: list[list[Any]],
    cont_start: list[Any],
    cont_arrival: list[list[Any]],
    cont_departure: list[list[Any]],
    cont_end: list[Any],
    tolerance: float = 0.5,
    include_zero_length_events: bool = False,
) -> dict[str, Any]:
    """Exportiert eine MIP-Lösung im JSON-Format des vrp_solution_viewers.

    Der Adapter liest direkt die `.x`-Werte der python-mip-Variablen aus.
    Binärvariablen gelten als aktiv, wenn ihr Wert größer als `tolerance` ist.

    Modellinterpretation:
    - Containerbewegung k: i -> j ist aktiv, falls x[k][i][j] = 1.
    - Geladene Roboterbewegung v mit Container k: i -> j ist aktiv, falls
      y[v][k][i][j] = 1.
    - Leere Roboterbewegungen werden aus firsttask, nexttask und lasttask
      rekonstruiert.

    Für Wartezeiten werden keine Events erzeugt. Der Viewer zeigt Agenten in
    Wartephasen automatisch an der zuletzt erreichten Position.
    """

    nodes = list(I)
    containers = [str(k) for k in K]
    robots = [str(v) for v in V]
    container_colors = {
        str(k): CONTAINER_COLORS[index % len(CONTAINER_COLORS)]
        for index, k in enumerate(K)
    }

    container_movements: list[dict[str, Any]] = []
    robot_movements: list[dict[str, Any]] = []

    # 1) Containerbewegungen und geladene Roboterbewegungen.
    for k in K:
        for i in nodes:
            for j in nodes:
                if i == j:
                    continue
                if _active(x[k][i][j], tolerance):
                    start = _container_arc_start(k, i, cont_start, cont_departure)
                    end = _container_arc_end(k, j, cont_arrival, cont_end)

                    _append_event(
                        container_movements,
                        agent_id=str(k),
                        source=i,
                        target=j,
                        start=start,
                        end=end,
                        color=container_colors[str(k)],
                        metadata={"kind": "container", "container": str(k)},
                        include_zero_length_events=include_zero_length_events,
                    )

                    # Exakt ein Roboter sollte diese aktive Containerkante fahren.
                    assigned_robots = []
                    for v in V:
                        if _active(y[v][k][i][j], tolerance):
                            assigned_robots.append(v)
                            _append_event(
                                robot_movements,
                                agent_id=str(v),
                                source=i,
                                target=j,
                                start=start,
                                end=end,
                                loaded=True,
                                container_id=str(k),
                                metadata={
                                    "kind": "robot_loaded",
                                    "robot": str(v),
                                    "container": str(k),
                                },
                                include_zero_length_events=include_zero_length_events,
                            )

                    if len(assigned_robots) != 1:
                        # Kein harter Abbruch, damit man auch Debug-JSONs erzeugen kann.
                        # Der Hinweis landet in metadata["warnings"].
                        pass

    # 2) Leere Roboterbewegungen aus firsttask, nexttask, lasttask.
    warnings: list[str] = []
    A_idx = range(len(A))

    for v in V:
        # Depot -> erste Aufgabe.
        for a in A_idx:
            if _active(firsttask[v][a], tolerance):
                _, pickup, _ = A[a]
                task_start_time = _task_start_value(a, A, cont_start, cont_departure)
                travel = _travel_time(T, 0, pickup)
                if pickup != 0 and _positive_duration(travel, include_zero_length_events):
                    # Darstellung: Der Roboter verlässt das Depot so spät wie möglich
                    # und kommt genau zum Start der ersten Aufgabe an.
                    start = max(0.0, task_start_time - travel)
                    end = task_start_time
                    _append_event(
                        robot_movements,
                        agent_id=str(v),
                        source=0,
                        target=pickup,
                        start=start,
                        end=end,
                        loaded=False,
                        metadata={
                            "kind": "robot_empty_start",
                            "robot": str(v),
                            "task": a,
                        },
                        include_zero_length_events=include_zero_length_events,
                    )

        # Aufgabe a -> Aufgabe b.
        for a in A_idx:
            for b in A_idx:
                if a == b:
                    continue
                if _active(nexttask[v][a][b], tolerance):
                    _, _, drop_a = A[a]
                    _, pickup_b, _ = A[b]
                    travel = _travel_time(T, drop_a, pickup_b)
                    start = _task_end_value(a, A, cont_arrival, cont_end)
                    end = start + travel
                    next_start = _task_start_value(b, A, cont_start, cont_departure)

                    if end > next_start + 1e-5:
                        warnings.append(
                            f"Roboter {v}: leere Fahrt Task {a}->{b} endet bei {end:.6g}, "
                            f"aber Task {b} startet bei {next_start:.6g}."
                        )

                    if drop_a != pickup_b or include_zero_length_events:
                        _append_event(
                            robot_movements,
                            agent_id=str(v),
                            source=drop_a,
                            target=pickup_b,
                            start=start,
                            end=end,
                            loaded=False,
                            metadata={
                                "kind": "robot_empty_between",
                                "robot": str(v),
                                "previous_task": a,
                                "next_task": b,
                            },
                            include_zero_length_events=include_zero_length_events,
                        )

        # letzte Aufgabe -> Depot.
        for a in A_idx:
            if _active(lasttask[v][a], tolerance):
                _, _, drop = A[a]
                travel = _travel_time(T, drop, 0)
                start = _task_end_value(a, A, cont_arrival, cont_end)
                end = start + travel
                if drop != 0 and _positive_duration(travel, include_zero_length_events):
                    _append_event(
                        robot_movements,
                        agent_id=str(v),
                        source=drop,
                        target=0,
                        start=start,
                        end=end,
                        loaded=False,
                        metadata={
                            "kind": "robot_empty_end",
                            "robot": str(v),
                            "task": a,
                        },
                        include_zero_length_events=include_zero_length_events,
                    )

    container_movements.sort(key=lambda e: (e["agent_id"], e["start"], e["end"]))
    robot_movements.sort(key=lambda e: (e["agent_id"], e["start"], e["end"], e["loaded"]))

    metadata: dict[str, Any] = {
        "source": "vrp_viewer_adapter.export_viewer_json",
        "time_interpretation": {
            "container_arc_start": "cont_start[k] if source=0 else cont_departure[k][source]",
            "container_arc_end": "cont_end[k] if target=0 else cont_arrival[k][target]",
            "loaded_robot_arc": "same interval as corresponding active y[v][k][i][j]",
            "empty_robot_arcs": "reconstructed from firsttask, nexttask, lasttask",
        },
        "warnings": warnings,
    }

    if c is not None:
        metadata["container_job_assignments"] = [
            {"container": str(k), "job": i}
            for k in K
            for i in nodes
            if i != 0 and _active(c[k][i], tolerance)
        ]

    payload = {
        "graph": _graph_to_viewer_json(graph),
        "containers": containers,
        "robots": robots,
        "container_colors": container_colors,
        "container_movements": container_movements,
        "robot_movements": robot_movements,
        "metadata": metadata,
    }

    output_path = Path(output_path)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def _graph_to_viewer_json(graph: nx.Graph) -> dict[str, Any]:
    """Konvertiert den Graphen robust in das vom Viewer geladene node-link-Format."""
    try:
        return json_graph.node_link_data(graph, edges="edges")
    except TypeError:
        # Kompatibilität mit älteren NetworkX-Versionen.
        data = json_graph.node_link_data(graph)
        if "links" in data and "edges" not in data:
            data["edges"] = data.pop("links")
        return data


def _append_event(
    events: list[dict[str, Any]],
    *,
    agent_id: str,
    source: Any,
    target: Any,
    start: float,
    end: float,
    loaded: bool | None = None,
    container_id: str | None = None,
    color: str | None = None,
    metadata: dict[str, Any] | None = None,
    include_zero_length_events: bool = False,
) -> None:
    start = float(start)
    end = float(end)

    if end < start - 1e-6:
        raise ValueError(
            f"Ungültiges Event für Agent {agent_id}: {source}->{target} hat end < start "
            f"({end} < {start})."
        )

    if not include_zero_length_events and abs(end - start) <= 1e-9:
        return

    event: dict[str, Any] = {
        "agent_id": str(agent_id),
        "source": source,
        "target": target,
        "start": start,
        "end": end,
    }
    if loaded is not None:
        event["loaded"] = bool(loaded)
    if container_id is not None:
        event["container_id"] = str(container_id)
    if color is not None:
        event["color"] = color
    if metadata:
        event["metadata"] = metadata
    events.append(event)


def _container_arc_start(k: Any, i: Any, cont_start: list[Any], cont_departure: list[list[Any]]) -> float:
    if i == 0:
        return _value(cont_start[k])
    return _value(cont_departure[k][i])


def _container_arc_end(k: Any, j: Any, cont_arrival: list[list[Any]], cont_end: list[Any]) -> float:
    if j == 0:
        return _value(cont_end[k])
    return _value(cont_arrival[k][j])


def _task_start_value(a: int, A: list[tuple[Any, Any, Any]], cont_start: list[Any], cont_departure: list[list[Any]]) -> float:
    k, i, _ = A[a]
    return _container_arc_start(k, i, cont_start, cont_departure)


def _task_end_value(a: int, A: list[tuple[Any, Any, Any]], cont_arrival: list[list[Any]], cont_end: list[Any]) -> float:
    k, _, j = A[a]
    return _container_arc_end(k, j, cont_arrival, cont_end)


def _travel_time(T: list[list[float]], i: Any, j: Any) -> float:
    return float(T[i][j])


def _active(var_or_value: Any, tolerance: float) -> bool:
    return _value(var_or_value) > tolerance


def _value(var_or_value: Any) -> float:
    """Liest den Wert einer python-mip-Variable oder eines numerischen Wertes."""
    if hasattr(var_or_value, "x"):
        value = var_or_value.x
        if value is None:
            raise ValueError("MIP-Variable hat keinen Lösungswert. Wurde das Modell erfolgreich gelöst?")
        return float(value)
    return float(var_or_value)


def _positive_duration(duration: float, include_zero_length_events: bool) -> bool:
    return include_zero_length_events or abs(float(duration)) > 1e-9
