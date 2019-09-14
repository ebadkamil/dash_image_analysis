"""
Image analysis and web visualization

Author: Ebad Kamil <kamilebad@gmail.com>
Copyright (C) European X-Ray Free-Electron Laser Facility GmbH.
All rights reserved.
"""
import dash_html_components as html
import dash_core_components as dcc
import dash_daq as daq

colors_map = ['Blackbody', 'Reds', 'Viridis']

_SOURCE = {
    "JungFrau": ["FXE_XAD_JF1M1/DET/RECEIVER:daqOutput",
                 "FXE_XAD_JF1M1/DET/RECEIVER-1:daqOutput",
                 "FXE_XAD_JF1M1/DET/RECEIVER-2:daqOutput"],
    "LPD": ["FXE_DET_LPD1M-1/DET/detector"],
    "AGIPD": ["SPB_DET_AGIPD1M-1/DET/detector"]
}


def get_stream_tab(config):
    return html.Div(className='control-tab',
                    children=[
                        html.Br(), html.Div([

                            html.Div([
                                html.Label("Run Folder"),
                                dcc.Input(
                                    id='run-folder',
                                    placeholder="Enter run directory",
                                    type='text',
                                    value=config["run_folder"]),
                                html.Label("Port"),
                                dcc.Input(
                                    id='port',
                                    placeholder="Port",
                                    type='text',
                                    value=config["port"]),

                                html.Hr(),
                                daq.BooleanSwitch(
                                    id='stream',
                                    on=False
                                ),
                            ],
                                className="pretty_container one-third column"),
                            html.Div(id="stream-info",
                                     className="two-thirds column")], className="row")])
