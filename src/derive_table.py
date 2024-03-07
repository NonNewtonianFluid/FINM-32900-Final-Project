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


def process_rating_data(df):
    '''
    This function process the raw rating data retreived through load_rating.py
    1. rename the trading date and bond id column for merging
    2. sort the data in the order of bond id and date
    '''
    df = df[['complete_cusip','rating_date', 'rating','category']].sort_values(by=['complete_cusip','rating_date']).reset_index(drop=True)
    df = df.rename(columns = {'complete_cusip':'cusip_id', 'rating_date':'date'})
    return df


def merge_df(df1, df2):
    '''
    This function merges two processed data (eg: bid-ask spread and returns) together.
    It matches the processed data by cusip_id and date, and only includes rows occurs in both dataframe.
    '''
    try:
        df1 = df1.rename(columns = {'trd_exctn_dt':'date'})
        df2 = df2.rename(columns = {'trd_exctn_dt':'date'})
    except Exception as e:
        print(e)

    res_df = pd.merge(df1,df2,on=['cusip_id','date'],how='inner')
    return res_df



def merge_rating(data, rating):
    '''
    This function merges processed data and rating data in the aim of functioning as the merge_asof function.
    It matches the processed data with the rating for each bond by forward-filling mis-matched rating date and trading date,  for each cusip_id group, 
    and only includes rows originally from processed data.
    '''
    data['source'] = 'A'
    rating['source'] = 'R'

    df = pd.concat([data,rating],axis=0)
    df = df.sort_values(by=['cusip_id','date','source'])

    df_filled = df.groupby('cusip_id').apply(lambda group: group.ffill())
    df_filled = df_filled.reset_index(drop=True)
    df_filled = df_filled[df_filled['source']=='A']
    df_filled = df_filled[df_filled['category'].notna()]
    df_filled = df_filled.reset_index(drop=True)
    df_filled = df_filled.drop(columns = ['source','rating'])

    return df_filled


def derive_table(res_df):
    df = res_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.rename(columns={'spread':'Bid-ask spread bps',
                       'winsorized_bias':'Bid-ask bias bps',
                       'daily_return_bps':'Daily return bps',
                       'cs_dur_bps':'Credit spread bps',
                       })

    # Define the subsample date ranges
    subsamples = {
        'Full sample': ('2002-07-01', '2022-09-30'),
        'Pre-crisis': ('2002-07-01', '2007-06-30'),
        'Crisis': ('2007-07-01', '2009-04-30'),
        'Post-Crisis': ('2009-05-01', '2012-05-31'),
        'Basel II.5 and III': ('2012-06-01', '2014-03-31'),
        'Post-Volcker': ('2014-04-01', '2022-09-30'),
        'Up to latest': ('2002-07-01', df['date'].max())
    }

    # Initialize a dictionary to store the mean values
    mean_values = {}

    for subsample, (start_date, end_date) in subsamples.items():
        # Filter the dataframe for the subsample date range
        subsample_df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
        # Calculate means for each category
        category_means = subsample_df.groupby('category').agg({
            'Bid-ask bias bps': 'mean',
            'Daily return bps': 'mean',
            'Bid-ask spread bps': 'mean',
            'Credit spread bps': 'mean'
        })#.add_prefix(subsample + '_')
        # Calculate the overall mean for all categories in the subsample
        overall_mean = subsample_df.agg({
            'Bid-ask bias bps': 'mean',
            'Daily return bps': 'mean',
            'Bid-ask spread bps': 'mean',
            'Credit spread bps': 'mean'
        }).to_frame('All').T#.add_prefix(subsample + '_').to_frame('All').T
        # Combine the overall mean with the category means
        combined_means = pd.concat([overall_mean, category_means], axis=0).T
        combined_means['category'] = subsample
        # Store the combined means in the mean_values dictionary with the subsample as the key
        mean_values[subsample] = combined_means

    for k,v in mean_values.items():
        if k == list(mean_values.keys())[0]:
            res_df = v
        else:
            res_df = pd.concat([res_df,v],axis=0)
    
    res_df['variables'] = res_df.index
    res_df = res_df.set_index(['category','variables'])

    return res_df
    


if __name__ == "__main__":
    
    spreadbias = pd.read_csv( DATA_DIR / "pulled" /'spread_bias.csv')
    ret = pd.read_csv( DATA_DIR / "pulled" /'daily_return_cs.csv')
    ret_cs = ret[['cusip_id', 'date','daily_return_bps', 'cs_dur_bps']]

    rating = pd.read_csv( DATA_DIR / "pulled" /'rating.csv')
    rating = process_rating_data(rating)

    all_df = merge_df(spreadbias, ret_cs)
    all_df = merge_rating(all_df, rating)

    all_df.to_csv( Path(DATA_DIR) / "pulled" / 'daily.csv', index=False)

    res_df = derive_table(all_df)
    
    float_format_func = lambda x: '{:.3f}'.format(x)
    latex_table_string = res_df.to_latex(float_format=float_format_func)

    path = OUTPUT_DIR / f'derived_table.tex'
    with open(path, "w") as text_file:
        text_file.write(latex_table_string)


