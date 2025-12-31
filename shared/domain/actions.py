from enum import Enum


class Action(Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3

    def opposite(self):
        if self == Action.UP:
            return Action.DOWN
        if self == Action.DOWN:
            return Action.UP
        if self == Action.LEFT:
            return Action.RIGHT
        if self == Action.RIGHT:
            return Action.LEFT
