import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import numpy as np
import datetime as dt
import zipfile
import gzip
import warnings
warnings.filterwarnings("ignore")

import config
from pathlib import Path

OUTPUT_DIR = Path(config.OUTPUT_DIR)
DATA_DIR = Path(config.DATA_DIR)
WRDS_USERNAME = config.WRDS_USERNAME

def merge_rating(df,rating):

    df['source'] = 'A'
    rating['source'] = 'R'

    all_df = pd.concat([df,rating],axis=0)
    all_df = all_df.sort_values(by=['cusip_id','date','source'])

    all_df_filled = all_df.groupby('cusip_id').apply(lambda group: group.ffill())
    all_df_filled = all_df_filled.reset_index(drop=True)
    all_df_filled = all_df_filled[all_df_filled['source']=='A']
    all_df_filled = all_df_filled[all_df_filled['category'].notna()]
    all_df_filled = all_df_filled.reset_index(drop=True)

    return all_df_filled


def calc_bid_ask_spread(df):
    res_df = pd.DataFrame(df.groupby(['date','category'])['prc_bid'].mean())
    res_df = res_df.rename(columns={'prc_bid':'vw_prc_bid_mean'})
    res_df['vw_prc_ask_mean'] = df.groupby(['date','category'])['prc_ask'].mean().values
    res_df['bid_ask_spread'] = 2 * (res_df['vw_prc_bid_mean'] - res_df['vw_prc_ask_mean'])/(res_df['vw_prc_ask_mean'] + res_df['vw_prc_bid_mean'])*10000
    res_df['bid_ask_bias'] = ((res_df['vw_prc_ask_mean'] - res_df['vw_prc_bid_mean'])/(res_df['vw_prc_ask_mean'] + res_df['vw_prc_bid_mean']))**2 * 10000
    return res_df


def derive_table(res_df):
    df = res_df.copy().reset_index()
    df['date'] = pd.to_datetime(df['date'])

    # Define the subsample date ranges
    subsamples = {
        'Full sample': ('2002-07-01', '2022-09-30'),
        'Pre-crisis': ('2002-07-01', '2007-06-30'),
        'Crisis': ('2007-07-01', '2009-04-30'),
        'Post-Crisis': ('2009-05-01', '2012-05-31'),
        'Basel II.5 & III': ('2012-06-01', '2014-03-31'),
        'Post-Volcker': ('2014-04-01', '2022-09-30'),
        'All': (df['date'].min(), df['date'].max())  # Entire dataset range
    }

    # Initialize a dictionary to store the mean values
    mean_values = {}

    # Loop over each subsample and calculate the means
    for subsample, (start_date, end_date) in subsamples.items():
        # Filter the dataframe for the subsample date range
        subsample_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        # Calculate the mean of 'bid_ask_spread' and 'bid_ask_bias'
        mean_values[subsample] = {
        'bid_ask_spread_mean': [subsample_df['bid_ask_spread'].mean()] + subsample_df.groupby('category')['bid_ask_spread'].mean().values.tolist(),
        'bid_ask_bias_mean': [subsample_df['bid_ask_bias'].mean()] + subsample_df.groupby('category')['bid_ask_bias'].mean().values.tolist()
    }
        
    rating_categories = ['Full','A and above','BBB','Junk']

    df_samples = []
    for sample, metrics in mean_values.items():
        data = {}
        for metric, values in metrics.items():
            for rating, value in zip(rating_categories, values):
                data[(metric, rating)] = value
        df_sample = pd.DataFrame(data, index=[sample])
        df_samples.append(df_sample)

    # Combine all sample DataFrames into one final DataFrame
    df_final = pd.concat(df_samples)

    # Show the final DataFrame
    return df_final


if __name__ == "__main__":

    all_illiqs = pd.read_csv('..' / DATA_DIR / "pulled" /'Illiq.csv.gzip', compression='gzip')
    all_illiqs = all_illiqs.sort_values(by=['cusip_id','date']).reset_index(drop=True)
    all_illiqs = all_illiqs.rename(columns = {'trd_exctn_dt':'date'})

    rating = pd.read_csv('..' / DATA_DIR / "pulled" / 'sp_ratings_with_CUSIP.csv')
    rating = rating[['complete_cusip','rating_date', 'rating','category']].sort_values(by=['complete_cusip','rating_date']).reset_index(drop=True)
    rating = rating.rename(columns = {'complete_cusip':'cusip_id', 'rating_date':'date'})

    all_df_filled = merge_rating(all_illiqs, rating)
    res_df = calc_bid_ask_spread(all_df_filled)
    df_final = derive_table(res_df)

    