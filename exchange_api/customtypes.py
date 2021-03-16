from enum import Enum, auto


class ApiQueryError(Exception):
    def __init__(self, status_code: int = 0, data: str = ""):
        self.status_code = status_code
        if data:
            self.code = data['code']
            self.msg = data['msg']
        else:
            self.code = None
            self.msg = None
        message = f"{status_code} [{self.code}] {self.msg}"

        super().__init__(message)


class TimeInForceStatus(Enum):
    GOOD_TIL_CANCELED = auto()
    IMMEDIAGE_OR_CANCEL = auto()
    FILL_OR_KILL = auto()
