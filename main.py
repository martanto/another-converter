import os
import datetime
import pandas as pd
import numpy as np
from IPython.display import JSON
from models.SeismicData import SeismicData
from config.config import Configuration
from cores.files import Files
from cores.convert import Convert
from obspy import read, Stream
from numpy import ma

def main():
    Convert(
        save_to_database=False,
        save_to_csv=True,
        save_dayplot=True,
        save_spectogram=False
    ).to_mseed()

if __name__ == '__main__':
    main()
