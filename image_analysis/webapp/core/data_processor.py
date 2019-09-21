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

from karabo_data import stack_detector_data
from karabo_data.geometry2 import LPD_1MGeometry, AGIPD_1MGeometry
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator

from .config import config

class DataProcessorWorker(Thread):
    def __init__(self, in_queue, out_queue):
        super().__init__()

        self._running = False
        self._out_queue = out_queue
        self._in_queue = in_queue
        self._analysis_type = None
        self._ai_params = None
        self._ai_integrator = None
        self._geom_file = None
        self._geom = None
        self._source_name = None
        self._fom = deque(maxlen=15)

    def run(self):
        self._running = True
        while self._running:
            try:
                data, meta = self._in_queue.get(timeout=config["TIME_OUT"])
            except queue.Empty:
                continue

            tid = next(iter(meta.values()))["timestamp.tid"]
            proc_data = ProcessedData(tid)

            assembled = self.assemble(data, proc_data)
            if assembled is not None and assembled.shape[0] != 0:
                if self._ai_params is not None:
                    threshold_mask = self._ai_params["mask_rng"]
                self.mask_image(assembled, threshold_mask=threshold_mask)
                mean_image = np.mean(assembled, axis=0)
                proc_data.image = mean_image
                self._process(self._analysis_type, assembled, proc_data)

            while self._running:
                try:
                    self._out_queue.put(proc_data, timeout=config["TIME_OUT"])
                    break
                except queue.Full:
                    continue

    def _process(self, analysis_type, data, processed):
        if analysis_type == "ROI":
            self.process_roi(data, processed)
        elif analysis_type == "AzimuthalIntegration":
            self.process_ai(data, processed)
        else:
            pass

    def mask_image(self, image, threshold_mask=None):

        def parallel(i):
            image[i][np.isnan(image[i])] = 0
            if threshold_mask is not None:
                a_min, a_max = threshold_mask
                np.clip(image[i], a_min, a_max, out=image[i])

        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(parallel, range(image.shape[0]))

    def assemble(self, data, processed):
        if config["DETECTOR"] == "JungFrau":
            try:
                img = np.copy(data[self._source_name]["data.adc"])
            except KeyError as ex:
                print(ex)
                return
        elif config["DETECTOR"] == "LPD":
            try:
                modules_data = stack_detector_data(
                    data, "image.data", only='LPD')
            except Exception as ex:
                print(ex)
                return
            if self._geom is not None:
                img, _ = self._geom.position_all_modules(modules_data)
            else:
                return
        elif config["DETECTOR"] == "AGIPD":
            try:
                modules_data = stack_detector_data(
                    data, "image.data", only='AGIPD')
            except Exception as ex:
                print(ex)
                return
            if self._geom is not None:
                img, _ = self._geom.position_all_modules(modules_data)
            else:
                return
        else:
            print("Unknown detector type")
            return

        return img

    def process_roi(self, assembled, processed):
        processed.projection_x = np.mean(assembled, axis=1)
        processed.projection_y = np.mean(assembled, axis=2)

    def process_ai(self, assembled, processed):
        integrator = self._update_integrator()
        itgt1d = functools.partial(integrator.integrate1d,
                                   method=self._ai_params["int_mthd"],
                                   radial_range=self._ai_params["int_rng"],
                                   correctSolidAngle=True,
                                   polarization_factor=1,
                                   unit="q_A^-1")
        integ_points = self._ai_params["int_pts"]

        def parallel(i):
            ret = itgt1d(assembled[i], integ_points)
            return ret.radial, ret.intensity

        with ThreadPoolExecutor(max_workers=5) as executor:
            rets = executor.map(parallel,
                                range(assembled.shape[0]))

        momentums, intensities = zip(*rets)
        momentum = momentums[0]
        foms = []
        for intensity in intensities:
            itgt = np.trapz(*slice_curve(
                intensity, momentum, *self._ai_params["int_rng"]))
            foms.append(itgt)

        self._fom.append((processed.tid, foms))
        processed.momentum = momentum
        processed.intensities = np.array(intensities)
        processed.fom = self._fom

    def _update_integrator(self):
        self._wavelength = energy2wavelength(self._ai_params["energy"])
        self._distance = self._ai_params["distance"]
        self._poni1 = \
            self._ai_params["centery"] * self._ai_params["pixel_size"]
        self._poni2 = \
            self._ai_params["centerx"] * self._ai_params["pixel_size"]

        if self._ai_integrator is None:
            self._ai_integrator = AzimuthalIntegrator(
                dist=self._ai_params["distance"],
                pixel1=self._ai_params["pixel_size"],
                pixel2=self._ai_params["pixel_size"],
                poni1=self._poni1,
                poni2=self._poni2,
                rot1=0,
                rot2=0,
                rot3=0,
                wavelength=self._wavelength)
        else:
            if self._ai_integrator.dist != self._distance \
                    or self._ai_integrator.wavelength != self._wavelength \
                    or self._ai_integrator.poni1 != self._poni1 \
                    or self._ai_integrator.poni2 != self._poni2:
                self._ai_integrator.set_param(
                    (self._distance,
                     self._poni1,
                     self._poni2,
                     0,
                     0,
                     0,
                     self._wavelength))
        return self._ai_integrator

    def onAnalysisTypeChange(self, value):
        if self._analysis_type != value:
            self._analysis_type = value
            self._fom.clear()

    def onAiParamsChange(self, value):
        if self._ai_params != value:
            self._ai_params = value

    def onGeomFileChange(self, value):
        if self._geom_file != value:
            self._geom_file = value
            try:
                if config["DETECTOR"] == 'LPD':
                    quad_positions = config["LPD"]["quad_positions"]
                    self._geom = LPD_1MGeometry.from_h5_file_and_quad_positions(
                        self._geom_file, quad_positions)
                elif config["DETECTOR"] == 'AGIPD':
                    self._geom = AGIPD_1MGeometry.from_crystfel_geom(filename)
            except Exception as ex:
                print(ex)

    def onSourceNameChange(self, value):
        self._source_name = value

    def terminate(self):
        self._running = False


class ProcessedData:
    def __init__(self, tid):
        self._tid = tid
        self.projection_x = None
        self.projection_y = None
        self.momentum = None
        self.intensities = None
        self.image = None
        self.fom = None

    @property
    def tid(self):
        return self._tid


def energy2wavelength(energy):
    # Plank-einstein relation (E=hv)
    HC_E = 1e-3 * constants.c * constants.h / constants.e
    return HC_E / energy


def slice_curve(y, x, x_min=None, x_max=None):
    """Slice an x-y plot based on the range of x values.

    x is assumed to be monotonically increasing.

    :param numpy.ndarray y: 1D array.
    :param numpy.ndarray x: 1D array.
    :param None/float x_min: minimum x value.
    :param None/float x_max: maximum x value.

    :return: (the sliced x and y)
    :rtype: (numpy.ndarray, numpy.ndarray)
    """
    if x_min is None:
        x_min = x.min()

    if x_max is None:
        x_max = x.max()

    indices = np.where(np.logical_and(x <= x_max, x >= x_min))
    return y[indices], x[indices]
