"""
Image analysis and web visualization

Author: Ebad Kamil <kamilebad@gmail.com>
All rights reserved.
"""
import argparse

from .webapp import DashApp


def run_dashservice():
    ap = argparse.ArgumentParser(prog="webImageAnalyis")
    ap.add_argument("detector", help="detector name (case insensitive)",
                    choices=[det.upper()
                             for det in ["jungfrau", "LPD", "AGIPD"]],
                    type=lambda s: s.upper())
    ap.add_argument("hostname", help="Hostname")
    ap.add_argument("port", help="TCP port to run server on")
    args = ap.parse_args()

    detector = args.detector
    if detector == 'JUNGFRAU':
        detector = 'JungFrau'

    hostname = args.hostname
    port = args.port

    app = DashApp(detector, hostname, port)
    app.recieve()
    app.process()

    app._app.run_server(debug=False)
