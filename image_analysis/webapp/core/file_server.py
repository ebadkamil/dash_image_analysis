"""
File server.

Author: Ebad Kamil <ebad.kamil@xfel.eu>
Copyright (C) European X-Ray Free-Electron Laser Facility GmbH.
All rights reserved.
"""
import datetime
import os.path as osp
from multiprocessing import Process
import re
from time import time

from karabo_data import RunDirectory, ZMQStreamer
from .config import config


def generate_meta(sources, tid):
    """Generate metadata in case of repeat stream"""

    time_now = int(time() * 10**18)
    sec = time_now // 10**18
    frac = time_now % 10**18
    meta = {key:
            {'source': key, 'timestamp.sec': sec, 'timestamp.frac': frac,
             'timestamp.tid': tid} for key in sources}
    return meta


def serve_files(path, port, fast_devices=None,
                require_all=False, repeat_stream=True, **kwargs):
    """Stream data from files through a TCP socket.

    Parameters
    ----------
    path: str
        Path to the HDF5 file or file folder.
    port: int
        Local TCP port to bind socket to.
    slow_devices: list of tuples
        [('src', 'prop')]
    fast_devices: list of tuples
        [('src', 'prop')]
    require_all: bool
        If set to True, will stream only trainIDs that has data
        corresponding to keys specified in fast_devices.
        Default: False
    repeat_stream: bool
        If set to True, will continue streaming when trains()
        iterator is empty. Trainids will be monotonically increasing.
        Default: False
    """
    try:
        corr_data = RunDirectory(path)
        num_trains = len(corr_data.train_ids)
    except Exception as ex:
        print(repr(ex))
        return

    streamer = ZMQStreamer(port, **kwargs)
    streamer.start()

    counter = 0
    repeat_stream = False
    while True:
        for tid, train_data in corr_data.trains(devices=fast_devices,
                                                require_all=require_all):
            # loop over corrected DataCollection
            if train_data:
                # Generate fake meta data with monotically increasing
                # trainids only after the actual trains in corrected data
                meta = generate_meta(
                    train_data.keys(), tid+counter) if counter > 0 else None
                streamer.feed(train_data, metadata=meta)
        if not repeat_stream:
            break
        # increase the counter by total number of trains in a run
        counter += num_trains

    streamer.stop()


class FileServer(Process):
    """Stream the file data in another process."""

    def __init__(self, folder, port):
        """Initialization."""
        super().__init__()
        self._folder = folder
        self._port = port

    def run(self):
        """Override."""
        detector = config["DETECTOR"]
        if detector in ["LPD", "AGIPD", "DSSC"]:
            fast_devices = [("*DET/*CH0:xtdf", "image.data")]
        elif detector == "JungFrau":
            fast_devices = [("*/DET/*:daqOutput", "data.adc")]
        elif detector == "FastCCD":
            fast_devices = [("*/DAQ/*:daqOutput", "data.image.pixels")]
        else:
            raise NotImplementedError(f"Unknown Detector: {detector}")

        serve_files(self._folder, self._port,
                    fast_devices=fast_devices, require_all=True)
