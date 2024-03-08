'''
Overview
-------------
This Python script downloads the latest data(Dec 2023) from https://openbondassetpricing.com
It contains daily TRACE panel data including clean and invoice (dirty) prices, 
accrued interest, daily bond yields, bond credit spreads, duration and convexity. 
'''
import pandas as pd

import requests
import warnings
import zipfile
import os

warnings.filterwarnings("ignore")

import config
from pathlib import Path


OUTPUT_DIR = Path(config.OUTPUT_DIR)
DATA_DIR = Path(config.DATA_DIR)
WRDS_USERNAME = config.WRDS_USERNAME


file_url = 'https://openbondassetpricing.com/wp-content/uploads/2023/12/BondDailyPublicDec2023.csv.zip'

response = requests.get(file_url)

with open(Path(DATA_DIR) / "pulled" / 'BondDailyPublicDec2023.csv.zip', 'wb') as file:
    file.write(response.content)

print('Download completed!')

with zipfile.ZipFile(Path(DATA_DIR) / "pulled" / 'BondDailyPublicDec2023.csv.zip', 'r') as zip_ref:
    zip_ref.extractall(Path(DATA_DIR) / "pulled" )

print(r"Extraction completed! The file is now under folder \data\pulled")

path = Path(DATA_DIR) / "pulled" / 'BondDailyPublicDec2023.csv.zip'

if os.path.exists(path):
    os.remove(path)
    print(f"File {path} has been deleted.")
else:
    print(f"The file {path} does not exist.")
