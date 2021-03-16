from enum import IntEnum, auto
from threading import Thread


class WorkerStatus(IntEnum):
    WORKING = auto()
    STOPPED = auto()


class Worker(Thread):
    def __init__(self, name=None):
        Thread.__init__(self, name=name)

    def stop(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError
