"""
Image analysis and web visualization

Author: Ebad Kamil <kamilebad@gmail.com>
All rights reserved.
"""
import queue
from threading import Thread, Event

from karabo_bridge import Client


class DaqWorker(Thread):
    def __init__(self, hostname, port, daq_queue):
        super().__init__()

        self._daq_queue = daq_queue
        self._running = False
        self._bind_address = f"tcp://{hostname}:{port}"

    def run(self):
        self._running = True
        with Client(self._bind_address) as client:
            while self._running:
                data = client.next()
                try:
                    self._daq_queue.put(data)
                except queue.Full:
                    continue

    def terminate(self):
        self._running = False
