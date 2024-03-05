'''
Overview
-------------
This Python script
1. merges the ratings data with the illiquid data (value-weighted bid and ask price)
2. cleans the merged data
3. generates the bid ask spread and bid ask bias
'''

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay
import numpy as np
from scipy.stats.mstats import winsorize
import datetime as dt
import warnings
warnings.filterwarnings("ignore")

import config
from pathlib import Path

OUTPUT_DIR = Path(config.OUTPUT_DIR)
DATA_DIR = Path(config.DATA_DIR)
WRDS_USERNAME = config.WRDS_USERNAME
START_DATE = config.START_DATE
END_DATE = config.END_DATE


def process_illiquid_data(df):
    '''
    This function process the raw illiquid data retreived through load_trace.py
    1. rename the trading date column
    2. sort the data in the order of bond id and date
    '''
    df = df.rename(columns = {'trd_exctn_dt':'date'})
    df = df.sort_values(by=['cusip_id','date']).reset_index(drop=True)
    return df


def process_rating_data(df):
    '''
    This function process the raw rating data retreived through load_rating.py
    1. rename the trading date and bond id column for merging
    2. sort the data in the order of bond id and date
    '''
    df = df[['complete_cusip','rating_date', 'rating','category']].sort_values(by=['complete_cusip','rating_date']).reset_index(drop=True)
    df = df.rename(columns = {'complete_cusip':'cusip_id', 'rating_date':'date'})
    return df


def merge_rating_illiquid(illiqs, rating):
    '''
    This function merges the illiquid data and rating data in the aim of functioning as the merge_asof function.
    It matches the illiquid data with the rating for each bond by forward-filling mis-matched rating date and trading date,  for each cusip_id group, 
    and only includes rows originally from illiquid data.
    '''
    illiqs['source'] = 'A'
    rating['source'] = 'R'

    df = pd.concat([illiqs,rating],axis=0)
    df = df.sort_values(by=['cusip_id','date','source'])

    df_filled = df.groupby('cusip_id').apply(lambda group: group.ffill())
    df_filled = df_filled.reset_index(drop=True)
    df_filled = df_filled[df_filled['source']=='A']
    df_filled = df_filled[df_filled['category'].notna()]
    df_filled = df_filled.reset_index(drop=True)

    return df_filled


def get_trades_info(df, start_date = START_DATE, end_date = END_DATE):
    '''
    This function is used to process the illiquid data by adding 2 columns 
    to denote the business days count between 2 trades and the total number of trades of a bond winthin a month.
    '''
    calendar = USFederalHolidayCalendar()
    holidays = calendar.holidays(start_date, end_date)
    holiday_date_list = holidays.date.tolist()

    df['date_lag'] = df.groupby('cusip_id')['date'].shift(1)
    dfDC = df.dropna()
    dfDC['n']  = np.busday_count(dfDC['date_lag'].values.astype('M8[D]') , 
                                      dfDC['date'].values.astype('M8[D]'),
                                      holidays = holiday_date_list)

    df = df.merge(dfDC[['cusip_id','date','n']], left_on = ['cusip_id','date'], right_on = ['cusip_id','date'] ,how = "left")
    
    df = df.dropna()
    df['month_year']   = pd.to_datetime(df['date']).dt.to_period('M') 
    df['trade_counts'] = df.groupby(['cusip_id',
                                    'month_year'] )['date'].transform("count")    
    return df


def calc_spread_bias(df):
    '''
    This function is used to calculate the bid and ask spread and bid ask bias,
    also, as denoted in the paper, the bias should be winsorized
    '''
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['cusip_id','date'])

    df['spread'] = (df['prc_bid'] - df['prc_ask'])/(df['prc_bid'] + df['prc_ask']) * 10000 * 2
    df['bias'] = (((df['prc_bid'] - df['prc_ask']) / (df['prc_bid'] + df['prc_ask'])) ** 2) * 10000
    df['winsorized_bias'] = winsorize(df['bias'], limits=[0.005, 0.005])

    return df


if __name__ == "__main__":
    
    raw_illiqs = pd.read_csv('..' / DATA_DIR / "pulled" /'Illiq.csv.gzip', compression='gzip')
    raw_rating = pd.read_csv('..' / DATA_DIR / "pulled" /'rating.csv')

    illiqs = process_illiquid_data(raw_illiqs)
    rating = process_rating_data(raw_rating)

    df = merge_rating_illiquid(illiqs, rating)
    df = get_trades_info(df)

    df_wo5 = df[df['trade_counts'] >= 5]

    df_wo5 = df_wo5[df_wo5['n'] <= 7]

    df_final = calc_spread_bias(df_wo5)

    df_final['date'] = pd.to_datetime(df_final['date'])
    df_final.sort_vaues(['cusip_id', 'date'], inplace = True)

    df_final.to_csv( Path(DATA_DIR) / "pulled" / 'Illiqs_with_spread_bias.csv', index=False)
    


