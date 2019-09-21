"""
Image analysis and web visualization

Author: Ebad Kamil <kamilebad@gmail.com>
Copyright (C) European X-Ray Free-Electron Laser Facility GmbH.
All rights reserved.
"""
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import functools
import numpy as np
import queue
from scipy import constants
from threading import Thread, Event

from karabo_bridge import Client
from karabo_data import stack_detector_data
from karabo_data.geometry2 import LPD_1MGeometry, AGIPD_1MGeometry
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator

from .config import config


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

