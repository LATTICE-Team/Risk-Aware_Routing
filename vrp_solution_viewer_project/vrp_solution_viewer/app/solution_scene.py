from __future__ import annotations

from typing import Any

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsScene

from vrp_solution_viewer.config.defaults import (
    CONTAINER_PALETTE,
    CONTAINER_RADIUS,
    LANE_GAP,
    NODE_RADIUS,
    ROBOT_HALF_SIZE,
    ROBOT_ROUTE_WIDTH,
    ROUTE_WIDTH,
    SYMBOL_AUTO_SCALE_MAX,
    SYMBOL_AUTO_SCALE_MIN,
    SYMBOL_REFERENCE_GRAPH_SPAN,
    SYMBOL_USER_SCALE_DEFAULT,
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
        self.auto_symbol_scale = 1.0
        self.user_symbol_scale = SYMBOL_USER_SCALE_DEFAULT

    @property
    def symbol_scale(self) -> float:
        return self.auto_symbol_scale * self.user_symbol_scale

    def set_solution(self, solution: SolutionData, initial_time: float = 0.0) -> None:
        self.solution = solution
        self.current_time = float(initial_time)
        self.auto_symbol_scale = self._compute_auto_symbol_scale(solution)
        self.redraw()
        self.set_time(self.current_time)

    def set_user_symbol_scale(self, scale: float) -> None:
        """Apply the user-controlled visual multiplier and redraw the scene.

        The automatic multiplier is recomputed when a new solution is loaded;
        this method only changes the additional manual multiplier.
        """
        self.user_symbol_scale = max(0.01, float(scale))
        current_time = self.current_time
        self.redraw()
        self.set_time(current_time)

    def reset_user_symbol_scale(self) -> None:
        self.set_user_symbol_scale(SYMBOL_USER_SCALE_DEFAULT)

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

        # Zuerst Roboter aktualisieren und dabei feststellen, welche Container
        # gerade getragen werden.  Diese Container werden anschließend nicht als
        # separates freies ContainerItem gezeichnet, sondern ausschließlich als
        # farbiger Kreis auf dem Roboter.
        carried_container_ids: set[str] = set()
        for robot_id, item in self.robot_items.items():
            state = self.solution.robot_state(robot_id, time_value)
            item.setVisible(state is not None)
            if state is not None:
                item.set_position_tuple(state.position)
                if state.active_event and state.active_event.loaded:
                    container_id = state.active_event.container_id
                    if container_id is not None:
                        carried_container_ids.add(str(container_id))
                    item.set_loaded_container(
                        container_id,
                        self._container_color(container_id) if container_id is not None else None,
                    )
                else:
                    item.set_loaded_container(None, None)

        for container_id, item in self.container_items.items():
            state = self.solution.container_state(container_id, time_value)
            item.setVisible(state is not None and str(container_id) not in carried_container_ids)
            if state is not None:
                item.set_position_tuple(state.position)

    def _draw_nodes(self) -> None:
        assert self.solution is not None
        if not self.show_nodes:
            return
        scale = self.symbol_scale
        for node, data in self.solution.graph.nodes(data=True):
            position = self.solution.node_position(node)
            label = str(data.get("label", node))
            item = NodeItem(
                node,
                position,
                label,
                radius=NODE_RADIUS * scale,
                pen_width=0.0,
                fill_color="#f7f7f7",
                label_gap=max(2.0 * scale, 0.5),
            )
            self.addItem(item)
            self.node_items[node] = item
        self._place_node_labels()

    def _draw_routes(self) -> None:
        assert self.solution is not None
        scale = self.symbol_scale
        lane_gap = LANE_GAP * scale
        node_radius = NODE_RADIUS * scale
        container_route_width = max(0.01, ROUTE_WIDTH * scale)
        robot_route_width = max(0.01, ROBOT_ROUTE_WIDTH * scale)
        lane_assignments = assign_lanes_for_overlapping_edges(
            self.solution.container_movements,
            lane_gap=lane_gap,
        )
        for assignment in lane_assignments:
            event = assignment.event
            color = event.color or self._container_color(event.agent_id)
            item = RouteEdgeItem(
                self.solution.node_position(event.source),
                self.solution.node_position(event.target),
                color=color,
                width=container_route_width,
                offset=assignment.offset,
                dashed=False,
                show_arrow=True,
                arrow_scale=scale,
                source_trim=node_radius,
                target_trim=node_radius,
            )
            item.setToolTip(
                f"Container {event.agent_id}: {event.source} → {event.target}, "
                f"t=[{event.start:g}, {event.end:g}]"
            )
            self.addItem(item)

        if self.show_robot_routes:
            robot_lane_assignments = assign_lanes_for_overlapping_edges(
                self.solution.robot_movements,
                lane_gap=lane_gap,
            )
            for assignment in robot_lane_assignments:
                event = assignment.event
                item = RouteEdgeItem(
                    self.solution.node_position(event.source),
                    self.solution.node_position(event.target),
                    color="#555555" if event.loaded else "#999999",
                    width=robot_route_width,
                    offset=assignment.offset,
                    dashed=not event.loaded,
                    show_arrow=True,
                    arrow_scale=scale,
                    source_trim=node_radius,
                    target_trim=node_radius,
                )
                item.setToolTip(
                    f"Roboter {event.agent_id}: {event.source} → {event.target}, "
                    f"beladen={event.loaded}, t=[{event.start:g}, {event.end:g}]"
                )
                self.addItem(item)

    def _place_node_labels(self) -> None:
        """Place node labels outside the circles with a simple collision heuristic.

        The first candidates are below and above the node.  If those would
        overlap already placed labels or nearby node circles, the method tries
        lateral and diagonal alternatives.  This is intentionally lightweight;
        it improves readability without introducing a full label-placement
        optimization problem.
        """
        if not self.node_items:
            return

        scale = self.symbol_scale
        gap_extra = max(1.5 * scale, 0.25)
        occupied_node_rects = [item.circle_scene_rect(extra=gap_extra) for item in self.node_items.values()]
        placed_label_rects: list[QRectF] = []

        # Stable order: depot first, then numerical node ids where possible.
        def sort_key(node_item: tuple[Any, NodeItem]) -> tuple[int, str]:
            node, _ = node_item
            if str(node) == "0":
                return (0, str(node))
            return (1, str(node))

        for _, item in sorted(self.node_items.items(), key=sort_key):
            best_offset: tuple[float, float] | None = None
            best_score: tuple[float, float] | None = None
            for dx, dy in self._label_candidate_offsets(item):
                candidate = item.label_scene_rect_for_offset(dx, dy)
                score = self._label_collision_score(candidate, occupied_node_rects, placed_label_rects)
                if best_score is None or score < best_score:
                    best_score = score
                    best_offset = (dx, dy)
                    if score == (0.0, 0.0):
                        break
            if best_offset is None:
                item.place_label_below()
                placed_label_rects.append(item.text.mapRectToScene(item.text.boundingRect()))
                continue

            item.set_label_offset(*best_offset)
            placed_label_rects.append(item.label_scene_rect_for_offset(*best_offset))

    def _label_candidate_offsets(self, item: NodeItem) -> list[tuple[float, float]]:
        w, h = item.label_size()
        r = item.radius
        gap = item.label_gap
        return [
            (-w / 2.0, r + gap),               # below: preferred
            (-w / 2.0, -r - gap - h),          # above
            (r + gap, -h / 2.0),               # right
            (-r - gap - w, -h / 2.0),          # left
            (r + gap, r + gap),                # lower right
            (-r - gap - w, r + gap),           # lower left
            (r + gap, -r - gap - h),           # upper right
            (-r - gap - w, -r - gap - h),      # upper left
        ]

    @staticmethod
    def _label_collision_score(
        candidate: QRectF,
        node_rects: list[QRectF],
        label_rects: list[QRectF],
    ) -> tuple[float, float]:
        hard_collision_area = 0.0
        soft_collision_count = 0.0
        for rect in node_rects:
            inter = candidate.intersected(rect)
            if not inter.isNull():
                hard_collision_area += inter.width() * inter.height()
                soft_collision_count += 1.0
        for rect in label_rects:
            inter = candidate.intersected(rect)
            if not inter.isNull():
                hard_collision_area += inter.width() * inter.height()
                soft_collision_count += 1.0
        return hard_collision_area, soft_collision_count

    def _create_agent_items(self) -> None:
        assert self.solution is not None
        scale = self.symbol_scale
        for index, container_id in enumerate(self.solution.containers):
            color = self._container_color(container_id, index)
            item = ContainerItem(
                container_id,
                color,
                radius=CONTAINER_RADIUS * scale,
                pen_width=0.10 * CONTAINER_RADIUS * scale,
            )
            self.addItem(item)
            self.container_items[container_id] = item
        for robot_id in self.solution.robots:
            item = RobotItem(
                robot_id,
                half_size=ROBOT_HALF_SIZE * scale,
                pen_width=0.12 * ROBOT_HALF_SIZE * scale,
                load_radius=CONTAINER_RADIUS * scale,
                load_pen_width=0.10 * CONTAINER_RADIUS * scale,
            )
            self.addItem(item)
            self.robot_items[robot_id] = item

    def _container_color(self, container_id: str, fallback_index: int | None = None) -> str:
        assert self.solution is not None
        if container_id in self.solution.container_colors:
            return self.solution.container_colors[container_id]
        if fallback_index is None:
            fallback_index = abs(hash(container_id))
        return CONTAINER_PALETTE[fallback_index % len(CONTAINER_PALETTE)]

    def _compute_auto_symbol_scale(self, solution: SolutionData) -> float:
        """Derive a scene-coordinate scale from the loaded graph extent.

        The base constants are suitable for a graph with a coordinate span of
        SYMBOL_REFERENCE_GRAPH_SPAN.  If positions are e.g. in [0, 10], the
        symbols are scaled down accordingly; if positions are in a larger
        coordinate system, they are scaled up.  Clamping prevents degenerate
        graphics for very tiny or very large coordinate ranges.
        """
        positions = [solution.node_position(node) for node in solution.graph.nodes]
        if not positions:
            return 1.0

        xs = [pos[0] for pos in positions]
        ys = [pos[1] for pos in positions]
        span_x = max(xs) - min(xs)
        span_y = max(ys) - min(ys)
        graph_span = max(span_x, span_y)
        if graph_span <= 1e-9:
            return 1.0

        raw_scale = graph_span / SYMBOL_REFERENCE_GRAPH_SPAN
        return min(SYMBOL_AUTO_SCALE_MAX, max(SYMBOL_AUTO_SCALE_MIN, raw_scale))

    def _update_scene_rect(self) -> None:
        if not self.items():
            self.setSceneRect(QRectF(-100, -100, 200, 200))
            return
        margin = max(20.0 * self.symbol_scale, 2.0)
        rect = self.itemsBoundingRect().adjusted(-margin, -margin, margin, margin)
        self.setSceneRect(rect)
