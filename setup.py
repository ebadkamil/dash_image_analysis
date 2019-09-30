import os.path as osp
import re
import sys
from setuptools import setup, find_packages


def find_version():
    with open(osp.join('image_analysis', '__init__.py'), 'r') as f:
        match = re.search(r'^__version__ = "(\d+\.\d+\.\d+)"', f.read(), re.M)
        if match is not None:
            return match.group(1)
        raise RuntimeError("Unable to find version string.")


setup(name="image_analysis",
      version=find_version(),
      author="Ebad Kamil",
      author_email="kamilebad@gmail.com",
      maintainer="Ebad Kamil",
      packages=find_packages(),
      package_data={
        'image_analysis.geometries': ['*.h5']
      },
      entry_points={
          "console_scripts": [
              "web_image_analysis = image_analysis.application:run_dashservice",
          ],
      },
      install_requires=[
           'karabo_data>=0.7.0',
           'dash>=1.6.1',
           'dash-daq>=0.3.1',
           'pyFAI>0.16.0'
      ],
      extras_require={
        'test': [
          'pytest',
        ]
      },
      python_requires='>=3.6',
)
