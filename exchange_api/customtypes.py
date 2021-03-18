from enum import Enum, auto


class PoloniexQueryError(Exception):
    def __init__(self, status_code: int = 0, data: str = ""):
        self.status_code = status_code
        if data:
            self.msg = data['error']
        else:
            self.msg = None
        message = f"{status_code} {self.msg}"

        super().__init__(message)


class BinanceQueryError(Exception):
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


class BinanceFilterError(Exception):
    def __init__(self, pair: str, checked_value: float, filter_name: str):
        message = f"{filter_name} for {pair} doesn't meet filter restrictions. {filter_name} value = {checked_value}"

        super().__init__(message)


class TimeInForceStatus(Enum):
    GOOD_TIL_CANCELED = auto()
    IMMEDIATE_OR_CANCEL = auto()
    FILL_OR_KILL = auto()
