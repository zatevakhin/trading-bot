import random
import socket
import time

import socks

from .baseworker import Worker, WorkerStatus


class ProxySwitcher(Worker):
    def __init__(self, proxy_list, lifetime):
        Worker.__init__(self, name="proxy-switcher")
        self.proxy_list = proxy_list
        self.lifetime = lifetime
        self.status = WorkerStatus.WORKING

    def get_random_proxy(self):
        return random.choice(self.proxy_list)

    def stop(self):
        self.status = WorkerStatus.STOPPED

    def run(self):

        while self.status in [WorkerStatus.WORKING]:
            ip, port = self.get_random_proxy()

            socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, ip, int(port))
            socket.socket = socks.socksocket

            for _ in range(self.lifetime + 1):
                if self.status not in [WorkerStatus.WORKING]:
                    socks.setdefaultproxy(None)
                    socket.socket = socks.socksocket
                    break

                time.sleep(1)
