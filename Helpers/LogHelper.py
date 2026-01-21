from enum import Enum, auto

class LogStatus(Enum):
    INFO = auto()
    WARNING = auto()
    ERROR = auto()

class LogHelper:
    def __init__(self):
        pass

    def matchLog(self, matchId):
        pass