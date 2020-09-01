# Dash based Image Analysis
  - Multi-threaded DASH application that mimics experiments from EuXFEL HDF5 files
    - ZMQ server streams data stored in files in a sub-process.
    - **DASH** app receives data through ZMQ client
    - Data Processor perform Azimuthal integration and ROI analysis.

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
