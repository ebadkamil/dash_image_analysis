# Dash based Image Analysis

Installing
==========

`dash_image_analysis` 

Create conda environment with Python 3.5 or later:

    conda create -n {env_name} python=3.6

Activate conda environment:

    conda activate {env_name}
    pip install -e .

Usage:
    
    web_image_analysis {detector} {hostname} {port}
    detector: LPD, JungFrau, AGIPD
    hostname, port: tcp://{hostname}:{port} address for ZMQ streaming of data from files.
