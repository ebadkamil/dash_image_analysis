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


def get_exp_tab():
    return html.Div(id="experimental-params")


def get_plot_tab(config):
    div = html.Div(
        children=[html.Br(),
            html.Div([
                html.Div(
                    [html.Label("Azimuthal Integration Set up"),
                     html.Hr(),
                     html.Label("Energy:", className="leftbox"),

                     dcc.Input(
                        id='energy',
                        type='number',
                        value=config["energy"],
                        className="rightbox"),
                     html.Label("Sample Distance:", className="leftbox"),
                     dcc.Input(
                        id='distance',
                        type='number',
                        value=config["distance"],
                        className="rightbox"),
                     html.Label("Pixel size:", className="leftbox"),
                     dcc.Input(
                        id='pixel-size',
                        type='number',
                        value=config["pixel_size"],
                        className="rightbox"),
                     html.Label("Cx (pixel):", className="leftbox"),
                     dcc.Input(
                        id='centrex',
                        type='number',
                        value=config["centerx"],
                        className="rightbox"),
                     html.Label("Cy (pixel)::", className="leftbox"),
                     dcc.Input(
                        id='centrey',
                        type='number',
                        value=config["centery"],
                        className="rightbox"),
                     html.Label("Integration Method:",
                                className="leftbox"),
                     dcc.Dropdown(
                        id='int-mthd',
                        options=[{'label': i, 'value': i}
                                 for i in config["int_mthds"]],
                        value=config["int_mthds"][0],
                        className="rightbox"),
                     html.Label("Integration points:",
                                className="leftbox"),
                     dcc.Input(
                        id='int-pts',
                        type='number',
                        value=config["int_pts"],
                        className="rightbox"),
                     html.Label("Integration range:",
                                className="leftbox"),
                     dcc.RangeSlider(
                        id='int-rng',
                        min=0,
                        max=10.0,
                        value=config["int_rng"],
                        className="rightbox"),
                     html.Label("Mask range:", className="leftbox"),
                     dcc.RangeSlider(
                        id='mask-rng',
                        min=0,
                        max=10000.0,
                        value=config["mask_rng"],
                        className="rightbox"),
                     html.Label("Geometry:", className="leftbox"),
                     dcc.Input(
                        id='geom-file',
                        type='text',
                        value=config["geom_file"],
                        className="rightbox"),

                     ], className="pretty_container six columns"),
                html.Div([
                    html.Label("Source:", className="leftbox"),
                    dcc.Dropdown(
                        id='source',
                        options=[{'label': i, 'value': i} for i in config["source_name"]],
                        value=config["source_name"][0]),
                    html.Hr(),
                    html.Label("Analysis Type:", className="leftbox"),
                    dcc.Dropdown(
                        id='analysis-type',
                        options=[{'label': i, 'value': i}
                                 for i in ["AzimuthalIntegration", "ROI"]],
                        value="AzimuthalIntegration",
                        className="rightbox"),
                    html.Label("Projection:", className="leftbox"),
                    dcc.Dropdown(
                        id='roi-projection',
                        options=[{'label': i, 'value': f"projection_{i}"} for i in ['x', 'y']],
                        value="projection_x",
                        className="rightbox"),
                    html.Div(id="logger")
                ], className="pretty_container six columns")

            ], className="row"),
            html.Div(
            [html.Div(
                [dcc.Dropdown(
                    id='color-scale',
                    options=[{'label': i, 'value': i}
                             for i in colors_map],
                    value=colors_map[0])],
                className="pretty_container six columns"),
             html.Div(
                [html.Label("Pulses: ", className="leftbox"),
                 dcc.Slider(
                    id='n-pulses',
                    min=1,
                    max=400,
                    value=10,
                    step=1,
                    className="rightbox")],
                className="pretty_container six columns")],
            className="row"),

            html.Div([
                html.Div(
                    [dcc.Graph(
                        id='mean-image')],
                    className="pretty_container six columns"),
                html.Div(
                    [dcc.Graph(
                        id='ai-integral')],
                    className="pretty_container six columns")],
            className="row"),

            html.Div([
                html.Div(
                    [dcc.Graph(
                        id='histogram')],
                    className="pretty_container four columns"),
                html.Div(
                    [dcc.Graph(
                        id='fom-plot')],
                    className="pretty_container eight columns")],
            className="row"),
        ])
    return div
