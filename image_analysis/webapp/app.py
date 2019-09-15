"""
Image analysis and web visualization

Author: Ebad Kamil <kamilebad@gmail.com>
Copyright (C) European X-Ray Free-Electron Laser Facility GmbH.
All rights reserved.
"""
from math import ceil
import numpy as np
import queue
from queue import Queue

import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

from .layout import get_layout, _SOURCE
from ..helpers import get_virtual_memory


class DashApp:

    def __init__(self, detector, hostname, port):
        app = dash.Dash(__name__)
        app.config['suppress_callback_exceptions'] = True
        self._hostname = hostname
        self._port = port

        self._file_server = None
        config["DETECTOR"] = detector
        self._config = config[detector]
        self._app = app

        self.setLayout()
        self.register_callbacks()

    def setLayout(self):
        self._app.layout = get_layout(config["TIME_OUT"], self._config)

    def register_callbacks(self):
        """Register callbacks"""
        @self._app.callback(
            Output('train-id', 'value'),
            [Input('interval_component', 'n_intervals')])
        def update_train_id(n):
            self._update()
            if self._data is None:
                raise dash.exceptions.PreventUpdate
            return str(self._data.tid)

        @self._app.callback(
            [Output('virtual_memory', 'value'),
             Output('virtual_memory', 'max'),
             Output('swap_memory', 'value'),
             Output('swap_memory', 'max')],
            [Input('psutil_component', 'n_intervals')])
        def update_memory_info(n):
            try:
                virtual, swap = get_virtual_memory()
            except Exception:
                raise dash.exceptions.PreventUpdate
            return ((virtual.used/1024**3), ceil((virtual.total/1024**3)),
                    (swap.used/1024**3), ceil((swap.total/1024**3)))
