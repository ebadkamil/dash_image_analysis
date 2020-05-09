"""
Image analysis and web visualization

Author: Ebad Kamil <kamilebad@gmail.com>
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

from .core import (
    config, DaqWorker, DataProcessorWorker, FileServer, ProcessedData)
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

        self._data = None
        self._data_queue = Queue(maxsize=1)
        self._proc_queue = Queue(maxsize=1)
        self.reciever = DaqWorker(
            self._hostname, self._port, self._data_queue)
        self.processor = DataProcessorWorker(
            self._data_queue, self._proc_queue)

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

        @self._app.callback(
            Output('stream-info', 'children'),
            [Input('stream', 'on')],
            [State('run-folder', 'value'),
             State('port', 'value')])
        def stream(state, folder, port):
            info = ""
            if state:
                if not (folder and port):
                    info = f"Either Folder or port number missing"
                    return [info]
                self._file_server = FileServer(folder, port)
                try:
                    print("Start ", self._file_server)
                    self._file_server.start()
                    info = f"Serving file in the folder {folder} through port {port}"
                except Exception as ex:
                    info = repr(ex)
            elif not state:
                print("Shutdown ", self._file_server)
                if self._file_server is not None and self._file_server.is_alive():
                    info = "Shutdown File Server"
                    self._file_server.terminate()
                if self._file_server is not None:
                    self._file_server.join()

            return [info]

        @self._app.callback(Output('mean-image', 'figure'),
                            [Input('color-scale', 'value'),
                             Input('train-id', 'value')])
        def update_image_figure(color_scale, tid):
            if self._data.tid != int(tid) or self._data.image is None:
                raise dash.exceptions.PreventUpdate

            traces = [go.Heatmap(
                z=self._data.image[::3, ::3], colorscale=color_scale)]
            figure = {
                'data': traces,
                'layout': go.Layout(
                    margin={'l': 40, 'b': 40, 't': 40, 'r': 10},
                )
            }

            return figure

        @self._app.callback(Output('histogram', 'figure'),
                            [Input('train-id', 'value')])
        def update_histogram_figure(tid):
            if self._data.tid != int(tid) or self._data.image is None:
                raise dash.exceptions.PreventUpdate
            hist, bins = np.histogram(self._data.image.ravel(), bins=10)
            bin_center = (bins[1:] + bins[:-1])/2.0
            traces = [{'x': bin_center, 'y': hist,
                       'type': 'bar'}]
            figure = {
                'data': traces,
                'layout': go.Layout(
                    margin={'l': 40, 'b': 40, 't': 40, 'r': 10},
                )
            }

            return figure

        @self._app.callback(Output('ai-integral', 'figure'),
                            [Input('train-id', 'value')],
                            [State('analysis-type', 'value'),
                             State('roi-projection', 'value'),
                             State('n-pulses', 'value')]
                            )
        def update_correlation_figure(tid, analysis_type, projection, pulses):
            if self._data.tid != int(tid):
                raise dash.exceptions.PreventUpdate
            if analysis_type == "ROI":
                try:
                    y = getattr(self._data, f"{projection}")
                    traces = [go.Scatter(
                        x=np.arange(y.shape[1]), y=y[i]) for i in range(
                            y[:pulses, ...].shape[0])]
                except Exception:
                    raise dash.exceptions.PreventUpdate
            elif analysis_type == "AzimuthalIntegration":
                try:
                    y = getattr(self._data, "intensities")
                    x = getattr(self._data, "momentum")
                    traces = [go.Scatter(x=x, y=y[i])
                              for i in range(y[:pulses, ...].shape[0])]
                except Exception as ex:
                    raise dash.exceptions.PreventUpdate
            else:
                raise dash.exceptions.PreventUpdate

            figure = {
                'data': traces,
                'layout': go.Layout(
                    xaxis={'title': 'q'},
                    yaxis={'title': 'I(q)'},
                    margin={'l': 40, 'b': 40, 't': 40, 'r': 10},
                    hovermode='closest',
                    showlegend=False)}

            return figure

        @self._app.callback(Output('fom-plot', 'figure'),
                            [Input('train-id', 'value')])
        def update_fom_figure(tid):
            if self._data.tid != int(tid):
                raise dash.exceptions.PreventUpdate

            data = self._data.fom
            if data is None:
                raise dash.exceptions.PreventUpdate
            data = list(data)
            traces = [go.Box(
                y=foms,
                name=str(tid), marker_color='lightseagreen',
                boxmean='sd') for tid, foms in data]
            figure = {
                'data': traces,
                'layout': go.Layout(
                    margin={'l': 40, 'b': 40, 't': 40, 'r': 10},
                    showlegend=False,
                )
            }

            return figure

        @self._app.callback(Output('logger', 'children'),
                            [Input('train-id', 'value')],
                            [State('analysis-type', 'value'),
                             State('energy', 'value'),
                             State('distance', 'value'),
                             State('pixel-size', 'value'),
                             State('centrex', 'value'),
                             State('centrey', 'value'),
                             State('int-mthd', 'value'),
                             State('int-pts', 'value'),
                             State('int-rng', 'value'),
                             State('mask-rng', 'value'),
                             State('geom-file', 'value'),
                             State('source', 'value')
                             ]
                            )
        def update_params(tid,
                          analysis_type,
                          energy,
                          distance,
                          pixel_size,
                          centerx,
                          centery,
                          int_mthd,
                          int_pts,
                          int_rng,
                          mask_rng,
                          geom_file,
                          source):
            self.processor.onAnalysisTypeChange(analysis_type)
            ai_params = dict(
                energy=energy,
                distance=distance,
                pixel_size=pixel_size,
                centerx=centerx,
                centery=centery,
                int_mthd=int_mthd,
                int_pts=int_pts,
                int_rng=int_rng,
                mask_rng=mask_rng
            )
            self.processor.onAiParamsChange(ai_params)
            self.processor.onSourceNameChange(source)
            self.processor.onGeomFileChange(geom_file)

            return f"{analysis_type} registered"

    def _update(self):
        try:
            self._data = self._proc_queue.get_nowait()
        except queue.Empty:
            self._data = None

    def recieve(self):
        self.reciever.daemon = True
        self.reciever.start()

    def process(self):
        self.processor.daemon = True
        self.processor.start()
