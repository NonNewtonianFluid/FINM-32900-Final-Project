'''
Overview
-------------
This Python script downloads the S&P ratings and converts them
into numerical scores, i.e., AAA == 1, C ==21.
'''

import pandas as pd
from dateutil.relativedelta import *
from pandas.tseries.offsets import *
import datetime as datetime
import wrds
import warnings
warnings.filterwarnings("ignore")

import config
from pathlib import Path
OUTPUT_DIR = Path(config.OUTPUT_DIR)
DATA_DIR = Path(config.DATA_DIR)
WRDS_USERNAME = config.WRDS_USERNAME


# Define the mapping from SP ratings to numeric values
sp_rating_mapping = {
    "AAA": 1,
    "AA+": 2,
    "AA": 3,
    "AA/A-1+":3,
    "AA-": 4,
    "AA-/A-1+":4,
    "A+": 5,
    "A": 6,
    "A-": 7,
    "BBB+": 8,
    "BBB": 9,
    "BBB/A-2":9,
    "BBB-": 10,
    "BB+": 11,
    "BB": 12,
    "BB-": 13,
    "B+": 14,
    "B": 15,
    "B-": 16,
    "CCC+": 17,
    "CCC": 18,
    "CCC-": 19,
    "CC": 20,
    "C": 21,
    "D":22
}

def get_sp_rating(df):
    rat = df[  (df['rating_type'] == "SPR") ]
    # Replace the ratings in the "rating" column with numeric values
    rat["spr"] = rat["rating"].map(sp_rating_mapping)
    rat = rat.drop_duplicates(subset=['issue_id', 'rating_date'])
    rat['category'] = rat['spr'].apply(rating_to_category)
    return rat

    
def rating_to_category(rating):
    if pd.isna(rating):
        return None  # or 'Unknown' if you prefer to label NaN ratings
    # Define the rating thresholds for each category
    if 0 <= rating <= 6 :
        return 'A and above'
    elif 7 <= rating <= 9:
        return 'BBB'
    else:
        return 'Junk'


if __name__ == "__main__":

    db = wrds.Connection(wrds_username=WRDS_USERNAME)

    #* ************************************** */
    #* Download Mergent File                  */
    #* ************************************** */  
    rat_raw = db.raw_sql("""SELECT issue_id, rating_type, rating_date,rating               
                    FROM fisd.fisd_ratings
                    """)

    id = db.raw_sql("""SELECT complete_cusip, issue_id, offering_date                 
                    FROM fisd.fisd_mergedissue  
                    """)

    rat = pd.merge(rat_raw,id,how='inner',on='issue_id')

    # Keep SP Ratings
    rat = rat[rat['rating_type'] == "SPR"]

    # Remove from sample, ALL bonds with an "NR" (not rated) and the "NR",
    # derivatives category #
    rat = rat[rat['rating'] != "NR"]
    rat = rat[rat['rating'] != 'NR/NR']
    rat = rat[rat['rating'] != 'SUSP']
    rat = rat[rat['rating'] != 'P-1']
    rat = rat[rat['rating'] != '0']
    rat = rat[rat['rating'] != 'NAV']

    ratsp = get_sp_rating(rat)

    ratsp.to_csv( Path(DATA_DIR) / "pulled" / 'sp_ratings_with_CUSIP.csv', index=False)
