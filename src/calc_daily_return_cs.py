'''
Overview
-------------
This Python script
1. Takes in the data generated from load_return_cs.py   
2. cleans the merged data based on the conditions mentioned from the paper
3. Output daily_return.csvcalculate daily returns and extract credit spread on corporate bonds.
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


def extract_price_cs(data):
    '''
    This functions takes in the data generated from load_return_cs.py.
    Input: data, dataframe generated from load_return_cs.py
    Output: df_return_cs, dataframe contains 'cusip_id','trd_exctn_dt','prclean','cs_dur'
    '''
    data.columns = data.columns.str.lower()
    if 'unnamed: 0' in data.columns:
        data.drop(columns=['unnamed: 0'], inplace=True)
        
    # Convert 'trd_exctn_dt' to datetime
    data['trd_exctn_dt'] = pd.to_datetime(data['trd_exctn_dt'])

    # Sort by 'cusip_id' and 'trd_exctn_dt'
    data.sort_values(by=['cusip_id', 'trd_exctn_dt'], inplace=True)
    
    # extract important information
    df_return_cs = data[['cusip_id','trd_exctn_dt','prclean','cs_dur']]
    
    return df_return_cs


def process_credit_spread(df):
    '''
    This function winsorize credit spread data
    '''
    df['cs_dur'] = df['cs_dur']*10000
    df['cs_dur'] = winsorize(df['cs_dur'], limits=[0.005, 0.005])
    df.rename(columns={'cs_dur': 'cs_dur_bps'}, inplace=True)
    return df


def get_trades_info(df, start_date = START_DATE, end_date = END_DATE):
    '''
    This function is used to process the illiquid data by adding 2 columns 
    to denote the business days count between 2 trades and the total number of trades of a bond winthin a month.
    '''
    calendar = USFederalHolidayCalendar()
    holidays = calendar.holidays(start_date, end_date)
    holiday_date_list = holidays.date.tolist()
    df = df.rename(columns={'trd_exctn_dt':'date'})

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


# def filter_less_than_five_busn_days(data):
#     '''
#     This function filter based on business days between trades (<= 5 days)
    
#     '''
#     # Calculate the number of calendar days between trades
#     data['days_since_last_trade'] = data.groupby('cusip_id')['trd_exctn_dt'].diff().dt.days.fillna(0).astype(int)

#     # Define a function to calculate the number of business days between two dates
#     def calculate_business_days(row):
#         if row['days_since_last_trade'] == 0:  # no difference means no business days
#             return 0
#         # Generate a date range that excludes weekends
#         business_days = pd.bdate_range(start=row['trd_exctn_dt'] - pd.Timedelta(days=row['days_since_last_trade']),
#                                     end=row['trd_exctn_dt'] - pd.Timedelta(days=1))
#         return len(business_days)

#     # Apply the function to each row
#     data['business_days_since_last_trade'] = data.apply(calculate_business_days, axis=1)

#     # filter the trades has less than five business days since last trade
#     data = data[data['business_days_since_last_trade'] <= 5]
#     return data


# def filter_less_than_five_trades_per_months(data):
#     '''
#     filter out bonds with less than five trades per month
#     '''
#     # Group by cusip_id and month, and filter out bonds with less than five trades per month
#     data['year_month'] = data['trd_exctn_dt'].dt.to_period('M')

#     monthly_trade_counts = data.groupby(['cusip_id', 'year_month']).size().reset_index(name='monthly_trades')

#     eligible_bonds = monthly_trade_counts[monthly_trade_counts['monthly_trades'] >= 5]

#     # Join the eligible bonds back to the data
#     data = data.merge(eligible_bonds[['cusip_id', 'year_month']], on=['cusip_id', 'year_month'], how='inner')
#     return data


def calc_daily_returns_remove_large_reversals(data):
    
    '''
    calculate the daily returns, remove large return reversals 
    and exclude returns with absolute value > 20%. 
    winsorize credit spread data at 95%
    returns and credit spread are in bps    
    '''
    # Calculate daily returns
    data['daily_return'] = data.groupby('cusip_id')['prclean'].pct_change()

    # Remove large return reversals (20% or more followed by 20% or more in the opposite direction)
    data['previous_return'] = data.groupby('cusip_id')['daily_return'].shift()
    data = data[~((abs(data['daily_return']) >= 0.2) & (data['daily_return'] * data['previous_return'] < 0))]

    # Exclude returns with absolute value > 20%
    data = data[abs(data['daily_return']) <= 0.2]
    
    # Multiply the 'daily_return' by 10,000
    data['daily_return'] = data['daily_return'] * 10000
    
    # Rename the 'daily_return' column to 'daily_return_bps'
    data.rename(columns={'daily_return': 'daily_return_bps'}, inplace=True)

    return data



if __name__ == "__main__":
    
    raw_price_cs = pd.read_csv( DATA_DIR / "pulled" /'BondDailyPublic.csv.gzip', compression='gzip')
    
    df = extract_price_cs(raw_price_cs)

    df_wcs = process_credit_spread(df)

    df_filter = get_trades_info(df_wcs)
    df_wo5 = df_filter[df_filter['trade_counts'] >= 5]
    df_wo5 = df_wo5[df_wo5['n'] <= 5]
    
    # df_filter_less_five = filter_less_than_five_busn_days(df_wcs)
    # df_less_five_trade = filter_less_than_five_trades_per_months(df_filter_less_five)
    
    df_final = calc_daily_returns_remove_large_reversals(df_wo5)
    
    df_final.to_csv( Path(DATA_DIR) / "pulled" / 'daily_return_cs.csv', index=False)
    

    





    
    
