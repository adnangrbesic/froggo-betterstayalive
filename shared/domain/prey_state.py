from enum import Enum, auto

class PreyState(Enum):
    IDLE = auto()
    ALERT = auto()
    PANIC = auto()
