from __future__ import annotations

from typing import Any

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsScene

from vrp_solution_viewer.config.defaults import (
    CONTAINER_PALETTE,
    ROBOT_ROUTE_WIDTH,
    ROUTE_WIDTH,
)
from vrp_solution_viewer.graphics.agent_item import ContainerItem, RobotItem
from vrp_solution_viewer.graphics.node_item import NodeItem
from vrp_solution_viewer.graphics.route_edge_item import RouteEdgeItem
from vrp_solution_viewer.layout.edge_lanes import assign_lanes_for_overlapping_edges
from vrp_solution_viewer.model.solution_data import SolutionData


class SolutionScene(QGraphicsScene):
    def __init__(self) -> None:
        super().__init__()
        self.solution: SolutionData | None = None
        self.node_items: dict[Any, NodeItem] = {}
        self.container_items: dict[str, ContainerItem] = {}
        self.robot_items: dict[str, RobotItem] = {}
        self.show_robot_routes = False
        self.show_nodes = True
        self.current_time = 0.0

    def set_solution(self, solution: SolutionData) -> None:
        self.solution = solution
        self.current_time = solution.start_time
        self.redraw()
        self.set_time(self.current_time)

    def redraw(self) -> None:
        self.clear()
        self.node_items.clear()
        self.container_items.clear()
        self.robot_items.clear()
        if self.solution is None:
            return
        self._draw_routes()
        self._draw_nodes()
        self._create_agent_items()
        self._update_scene_rect()

    def set_time(self, time_value: float) -> None:
        self.current_time = time_value
        if self.solution is None:
            return
        for container_id, item in self.container_items.items():
            state = self.solution.container_state(container_id, time_value)
            item.setVisible(state is not None)
            if state is not None:
                item.set_position_tuple(state.position)
        for robot_id, item in self.robot_items.items():
            state = self.solution.robot_state(robot_id, time_value)
            item.setVisible(state is not None)
            if state is not None:
                item.set_position_tuple(state.position)
                item.set_loaded(bool(state.active_event and state.active_event.loaded))

    def _draw_nodes(self) -> None:
        assert self.solution is not None
        if not self.show_nodes:
            return
        for node, data in self.solution.graph.nodes(data=True):
            position = self.solution.node_position(node)
            label = str(data.get("label", node))
            item = NodeItem(node, position, label)
            self.addItem(item)
            self.node_items[node] = item

    def _draw_routes(self) -> None:
        assert self.solution is not None
        lane_assignments = assign_lanes_for_overlapping_edges(self.solution.container_movements)
        for assignment in lane_assignments:
            event = assignment.event
            color = event.color or self._container_color(event.agent_id)
            item = RouteEdgeItem(
                self.solution.node_position(event.source),
                self.solution.node_position(event.target),
                color=color,
                width=ROUTE_WIDTH,
                offset=assignment.offset,
                dashed=False,
                show_arrow=True,
            )
            item.setToolTip(
                f"Container {event.agent_id}: {event.source} → {event.target}, "
                f"t=[{event.start:g}, {event.end:g}]"
            )
            self.addItem(item)

        if self.show_robot_routes:
            robot_lane_assignments = assign_lanes_for_overlapping_edges(self.solution.robot_movements)
            for assignment in robot_lane_assignments:
                event = assignment.event
                item = RouteEdgeItem(
                    self.solution.node_position(event.source),
                    self.solution.node_position(event.target),
                    color="#555555" if event.loaded else "#999999",
                    width=ROBOT_ROUTE_WIDTH,
                    offset=assignment.offset,
                    dashed=not event.loaded,
                    show_arrow=True,
                )
                item.setToolTip(
                    f"Roboter {event.agent_id}: {event.source} → {event.target}, "
                    f"beladen={event.loaded}, t=[{event.start:g}, {event.end:g}]"
                )
                self.addItem(item)

    def _create_agent_items(self) -> None:
        assert self.solution is not None
        for index, container_id in enumerate(self.solution.containers):
            color = self._container_color(container_id, index)
            item = ContainerItem(container_id, color)
            self.addItem(item)
            self.container_items[container_id] = item
        for robot_id in self.solution.robots:
            item = RobotItem(robot_id)
            self.addItem(item)
            self.robot_items[robot_id] = item

    def _container_color(self, container_id: str, fallback_index: int | None = None) -> str:
        assert self.solution is not None
        if container_id in self.solution.container_colors:
            return self.solution.container_colors[container_id]
        if fallback_index is None:
            fallback_index = abs(hash(container_id))
        return CONTAINER_PALETTE[fallback_index % len(CONTAINER_PALETTE)]

    def _update_scene_rect(self) -> None:
        if not self.items():
            self.setSceneRect(QRectF(-100, -100, 200, 200))
            return
        rect = self.itemsBoundingRect().adjusted(-80, -80, 80, 80)
        self.setSceneRect(rect)
