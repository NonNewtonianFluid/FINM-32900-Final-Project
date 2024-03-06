'''
Overview
-------------
This Python script
1. downloads the ratings from WRDS,
2. cleans them by only keeping the Moody's and SP's rating
3. converts them into numerical scores
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

# Define the mapping from Moody ratings to numeric values
moody_rating_mapping = {
    "Aaa": 1,
    "Aa1": 2,
    "Aa2": 3,
    "Aa3": 4,
    "A1": 5,
    "A2": 6,
    "A3": 7,
    "Baa1": 8,
    "Baa2": 9,
    "Baa3": 10,
    "Ba1": 11,
    "Ba2": 12,
    "Ba3": 13,
    "B1": 14,
    "B2": 15,
    "B3": 16,
    "Caa1": 17,
    "Caa2": 18,
    "Caa3": 19,
    "Ca": 20,
    "C": 21,
}



def rating_to_category(rating):
    '''
    This function converts numeric ratings into categories ('A and above', 'BBB', or 'Junk') 
    based on predefined thresholds, and handling NaN values as None.
    '''
    if pd.isna(rating):
        return None 
    # Define the rating thresholds for each category
    if 0 <= rating <= 6 :
        return 'A and above'
    elif 7 <= rating <= 9:
        return 'BBB'
    else:
        return 'Junk'
    

def get_sp_rating(df):
    '''
    This function Filters the DataFrame to retain rows where `rating_type` is "SPR", 
    converts ratings to numeric values, removes duplicates, 
    and assigns categories based on numeric ratings.
    '''
    rat = df[(df['rating_type'] == "SPR")]
    # Replace the ratings in the "rating" column with numeric values
    rat["spr"] = rat["rating"].map(sp_rating_mapping)
    rat = rat.drop_duplicates(subset=['issue_id', 'rating_date'])
    rat['category'] = rat['spr'].apply(rating_to_category)
    return rat


def get_moody_rating(df):
    '''
    This function filters the DataFrame to retain rows where `rating_type` is "MR",
    converts ratings to numeric values, removes duplicates, 
    and assigns categories based on numeric ratings.
    '''
    rat = df[(df['rating_type'] == "MR") ]
    # Replace the ratings in the "rating" column with numeric values
    rat["mr"] = rat["rating"].map(moody_rating_mapping)
    rat = rat.drop_duplicates(subset=['issue_id', 'rating_date'])
    rat['category'] = rat['mr'].apply(rating_to_category)
    return rat


def concat_moody_sp(ratsp, ratsmd):
    '''
    This function concat the moody and sp ratings together, 
    and inplace the sp ratings with moody ratings if the rating is missing
    '''
    df = pd.concat([ratsp, ratsmd], axis=0)
    df = df.sort_values(by=['complete_cusip', 'rating_date'])
    df['spr'] = df['spr'].fillna(df['mr'])
    df = df.drop_duplicates(subset=['issue_id', 'rating_date'])
    return df


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

    rat1 = rat[rat['rating_type'] == "SPR"]
    rat2 = rat[rat['rating_type'] == "MR"]

    ratsp = get_sp_rating(rat1)
    ratsmd = get_moody_rating(rat2)
    
    rating = concat_moody_sp(ratsp, ratsmd)

    # Remove from sample, ALL bonds with an "NR" (not rated) and the "NR",
    # derivatives category #
    rating = rating[rating['rating'] != "NR"]
    rating = rating[rating['rating'] != 'NR/NR']
    rating = rating[rating['rating'] != 'SUSP']
    rating = rating[rating['rating'] != 'P-1']
    rating = rating[rating['rating'] != '0']
    rating = rating[rating['rating'] != 'NAV']
    
    # rating['rating_date'] = pd.to_datetime('rating_date', format='%Y-%m-%d')
    rating.sort_values(['complete_cusip', 'rating_date'], inplace=True)
    
    rating.to_csv( Path(DATA_DIR) / "pulled" / 'rating.csv', index=False)
