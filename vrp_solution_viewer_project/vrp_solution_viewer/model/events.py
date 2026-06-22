from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MovementEvent:
    """Zeitabhängige Bewegung eines Containers oder Roboters entlang einer Kante."""

    agent_id: str
    source: Any
    target: Any
    start: float
    end: float
    loaded: bool = False
    container_id: str | None = None
    color: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def contains(self, time_value: float) -> bool:
        return self.start <= time_value <= self.end

    def progress(self, time_value: float) -> float:
        if self.end <= self.start:
            return 1.0
        alpha = (time_value - self.start) / (self.end - self.start)
        return max(0.0, min(1.0, alpha))
