"""Interaktionsmodi des Editors."""

from enum import Enum, auto


class EditorMode(Enum):
    SELECT = auto()
    ADD_NODE = auto()
    ADD_EDGE = auto()
