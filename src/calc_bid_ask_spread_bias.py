import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import numpy as np
import datetime as dt
import zipfile

import config
from pathlib import Path

OUTPUT_DIR = Path(config.OUTPUT_DIR)
DATA_DIR = Path(config.DATA_DIR)
WRDS_USERNAME = config.WRDS_USERNAME

def calc_bid_ask_spread(df):
    pass





if __name__ == "__main__":

    all_illiqs = pd.read_csv(DATA_DIR / "pulled" /'Illiq.csv.gzip', compression='gzip')
    all_illiqs = all_illiqs.drop(columns=['Unnamed: 0'])

    rating = pd.read_csv(DATA_DIR / "pulled" / 'Bond Rating_with CUSIP.csv')
    rating = rating[rating['RATING_TYPE']=='SPR']
    

    