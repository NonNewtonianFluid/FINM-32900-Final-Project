#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from scipy.stats.mstats import winsorize
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns

from itertools import chain
import datetime as dt
import zipfile
import gzip
import warnings
warnings.filterwarnings("ignore")
import matplotlib.dates as mdates
import config
from pathlib import Path

OUTPUT_DIR = Path(config.OUTPUT_DIR)
DATA_DIR = Path(config.DATA_DIR)
START_DATE = config.START_DATE
END_DATE = config.END_DATE


# In[ ]:


# Change default pandas display options
pd.options.display.max_columns = 25
pd.options.display.max_rows = 500
pd.options.display.max_colwidth = 100
pd.set_option('display.float_format', lambda x: '%.4f' % x)

# Change default figure size
plt.rcParams['figure.figsize'] = 6, 5


# # Import Cleaned Data
# 
# - We are going to use the cleaned data to derive the table1. This dataframe contains the daily data of different bonds about bid ask spread, bid ask (cross-sectional winsorized) bias, daily return, credit spread, and ratong category.

# In[ ]:


daily_data = pd.read_csv(Path(DATA_DIR) / 'pulled' / 'daily.csv')


# In[ ]:


SUBSAMPLES = {
    'Full sample': ('2002-07-01', '2022-09-30'),
    'Pre-crisis': ('2002-07-01', '2007-06-30'),
    'Crisis': ('2007-07-01', '2009-04-30'),
    'Post-Crisis': ('2009-05-01', '2012-05-31'),
    'Basel II.5 & III': ('2012-06-01', '2014-03-31'),
    'Post-Volcker': ('2014-04-01', '2022-09-30'),
    'Recent':('2022-10-01', '2023-06-30'),
}


# In[ ]:


daily_data.head(5)


# ## Summary Statistics
# 
# - Note that all metrics has large range between the min and max, indicating that there are extreme values, and all the standard deviations indicate considerable variability among the data.
# 
# - 1. Bid Ask Spread:
# 
#     - Note that we did not exclude the negative bid ask spread, so the min of spread reaches to -13.38 bps. However, from the quantiles, we can see that most spreads are positive.
# 
#     - 25% of the spreads are less than or equal to 18.1036, 50% (median) are less than or equal to 30.3522, and 75% are less than or equal to 43.6666, showing that most spreads are concentrated in the lower range, which corresponds to the fact that the cleaned data tilts the daily sample toward a more **liquid** subset of corporate bond price.
# 
# - 2. Return
#     - The average daily return is small at 1.9293 bps.
#     - A very high standard deviation relative to the mean (35.8667) indicates large fluctuations in daily returns.
#     - The min daily return is significantly negative (-410.4720 bps), which could signify a substantial loss.
#     - The maximum daily return is exceptionally high (1250.0001 bps), pointing to some days with very large gains.
# 
# - 3. Bid ask Bias
#     - A small average value of mean 0.1387 suggests a slight bias after winsorizing the data to reduce the influence of extreme values. 
#     - The standard deviation is small (0.1501), indicating that the winsorized biases are generally close to the mean.
#     - The max is 1.8348, showing that even after winsorization, there can be considerable positive bias.
# 
# - 4. Credit Spread
#     - A mean of 329.0970 bps suggests that on average, the credit risk is regarded as moderate but significant.
#     - The large standard deviation indicates a wide variation in credit spread across different bonds, which is reasonable since our data captured both the investment grades bond as well as junk bonds.
#     - The very high max of 6053.5415 bps suggests that for some bonds, the crdit risk is extremely high, which might reflect high yield or distressed bonds.

# In[ ]:


# Group by date
summary_stats = daily_data.groupby('date')[['spread', 'winsorized_bias', 'daily_return_bps', 'cs_dur_bps']].mean()
summary_stats.describe()


# In[ ]:


# Write to Latex
float_format_func = lambda x: '{:.3f}'.format(x)
latex_table_string = summary_stats.describe().to_latex(float_format=float_format_func)
path = f'{OUTPUT_DIR}/summary_stats.tex'
with open(path, "w") as text_file:
    text_file.write(latex_table_string)


# In[ ]:


# Groupby date and category
data_categorized = daily_data.groupby(['category','date'])[['spread', 'winsorized_bias', 'daily_return_bps', 'cs_dur_bps']].mean()
data_categorized


# In[ ]:


def plot_summary_stats(summary_stats, name, subsamples=SUBSAMPLES):
    '''
    Since the data is cross-sectional, 
    we are going to use the average of all bonds on a specific date.
    This function is used to plot the time series of metrics (mean) across bonds
    '''
    df = summary_stats[[name]]
    df.index = pd.to_datetime(df.index)
    fig, ax = plt.subplots(figsize=(10,5), dpi=200)
    ax.plot(df, label = name)
    ax.set_xlabel('Date')
    ax.set_ylabel(f'Cross Bonds {name}')
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth = None, interval=30))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.set_title(f'Time Series of {name} across bonds')

    for subsample, (start, end) in subsamples.items():
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)
        ax.axvline(x=start, color='black', linestyle='--', lw=1, label=f'Start of {subsample}')
        ax.axvline(x=end, color='red', linestyle='--', lw=1, label=f'End of {subsample}')
    
    # Improve layout to accommodate the legends
    fig.autofmt_xdate()
    fig.tight_layout()


# In[ ]:


def plot_categorized(data_categorized, name, subsamples=SUBSAMPLES):
    '''
    This function is used to plot the time series of metrics (mean) across bonds 
    with the bonds being categorized into different rating groups
    '''
    summary_pivoted = data_categorized.reset_index().pivot(index='date', columns='category', values=['spread', 'winsorized_bias', 'daily_return_bps', 'cs_dur_bps'])
    df = summary_pivoted[[name]]
    df.index = pd.to_datetime(df.index)
    fig, ax = plt.subplots(figsize=(10,5), dpi=200)
    ax.plot(df, label = ['A and above', 'BBB', 'Junk'])
    ax.set_xlabel('Date')
    ax.set_ylabel(f'Cross Bonds {name}')
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth = None, interval=30))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.set_title(f'Time Series of {name} across bonds')
    ax.legend()
    for subsample, (start, end) in subsamples.items():
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)
        ax.axvline(x=start, color='black', linestyle='--', lw=1, label=f'Start of {subsample}')
        ax.axvline(x=end, color='red', linestyle='--', lw=1, label=f'End of {subsample}')
    
    # Improve layout to accommodate the legends
    fig.autofmt_xdate()
    fig.tight_layout()
    filepath = Path(OUTPUT_DIR) / f'{name}_categorized.png'
    plt.savefig(filepath)


# # 1 Bid and Ask Spread

# In[ ]:


plot_summary_stats(summary_stats, 'spread')


# - Higher bid-ask spreads typically indicate lower liquidity, meaning there are fewer buyers and sellers. This can make it more difficult to trade without impacting the price. Conversely, lower spreads suggest better liquidity, where bonds can be bought and sold more easily with less impact on the price.
# - From the time series, we can see several spikes. Peaks in the bid-ask spread can correspond to times of financial stress or uncertainty, when liquidity providers increase their spreads to compensate for higher risk. Periods with consistently higher spreads may align with economic downturns, financial crises, or other market disruptions.
# - During the Crisis period, the spread arises, which is consistent with our assumptions above. 
# - Oeverall, the spread has a decreasing tendency, with huge spikes occuring less frequently, indicating a more liquid and stable credit market in recent times
# 

# In[ ]:


plot_categorized(data_categorized, 'spread', subsamples=SUBSAMPLES)


# - Most spikes can be accounted for Junk bonds, while A-and-above bonds have fewer and smaller spikes.
# - Overall, the trends of bid and ask spread among the 3 rating categories are extremely similar. However, generally, higher-rated bonds (A-and-above and BBB) have narrower spreads, indicating lower risk and higher liquidity. Meanwhile, Junk bonds typically have wider spreads, signifying higher risk and lower liquidity.

# # 2 Daily Return

# In[ ]:


plot_summary_stats(summary_stats, 'daily_return_bps')


# - The plot illustrates the volatility of daily returns across bonds. The returns fluctuate around the zero line (which is quite reasonable), with few noticeable spikes both above and below it. 
# - During the crisis period, the returns experience higher volatility, which is consistent with a streassful market at that time.

# In[ ]:


plot_categorized(data_categorized, 'daily_return_bps', subsamples=SUBSAMPLES)


# - Spikes in daily returns might correlate with economic news, earnings reports, interest rate changes, or other market-moving events.
# Large positive spikes could indicate favorable market conditions or news for the bonds, while negative spikes could point to adverse events.
# - Junk bonds show the most significant swings, which is consistent with the higher risk and return volatility associated with lower credit quality. A and above' bonds appear to have the smallest fluctuations, suggesting lower volatility typically associated with higher-rated, more stable bonds.

# # 3 Bid and Ask Bias

# In[ ]:


plot_summary_stats(summary_stats, 'winsorized_bias')


# In[ ]:


plot_categorized(data_categorized, 'winsorized_bias', subsamples=SUBSAMPLES)


# - The results are similar to bid ask spead.

# # 4 Credit Spread

# In[ ]:


plot_summary_stats(summary_stats, 'cs_dur_bps')


# - Credit spreads fluctuate over time but appear relatively stable with occasional spikes, suggesting episodic periods of market stress or increased risk perception. The huge spike in recent times is likely due to extreme outliers.
# - The rising of credit spread around 2008 corresponds to the global financial crisis, where credit spreads typically widened significantly due to increased credit risk and market uncertainty.

# In[ ]:


plot_categorized(data_categorized, 'cs_dur_bps', subsamples=SUBSAMPLES)


# - The A-and-above category shows consistently lower credit spreads over time, indicative of higher creditworthiness and lower perceived risk by the market. BBB rated bonds have moderate credit spreads, suggesting medium risk. Junk bonds exhibit the highest credit spreads, reflecting their lower credit quality and higher risk.
# - Across all bond categories, there are periods where spreads widen significantly, likely indicating systemic market stresses affecting all bond types, albeit to different extents. Junk bonds, which are the most sensitive to economic changes and investor sentiment, show the most significant and frequent spikes. The global financial crisis around 2007-2008 and subsequent European debt crisis are likely to correspond with the spikes in the credit spreads seen in the plot.
# - Over the long term, credit spreads for 'A and above' and 'BBB' categories appear to remain relatively stable with fewer and less pronounced spikes, while 'Junk' bonds exhibit more volatility.

# # 5 Rating

# In[ ]:


def get_category_stats(df, subsamples, start_date=None, end_date=None, clean=False):
    '''
    This function is used to calculate the ratios of the 3 rating categories,
    i.e. A and above, BBB, Junk in different periods
    as well as the total counts of the rating dates
    '''
    if clean == True:
        df['date'] = pd.to_datetime(df['date'])
    else:
        df['rating_date'] = pd.to_datetime(df['rating_date'])
        
    if not start_date:
        start_date = START_DATE
    if not end_date:
        if clean == True:
            end_date = df['date'].max()
        else:
            end_date = df['rating_date'].max()
    subsamples['Up to latest'] = (start_date, end_date)

    category_ratios = pd.DataFrame()
    rating_nums_dict = {}

    for subsample_name, (start_date, end_date) in subsamples.items():
        if clean == True:
            subsample_df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
        else:
            subsample_df = df[(df['rating_date'] >= pd.to_datetime(start_date)) & (df['rating_date'] <= pd.to_datetime(end_date))]
            
        category_counts = subsample_df['category'].value_counts()
        category_ratio = category_counts / category_counts.sum()
        category_ratios[subsample_name] = category_ratio
        rating_nums_dict[subsample_name] = subsample_df.shape[0]

    rating_nums_df = pd.DataFrame(list(rating_nums_dict.items())).rename(columns={0:'category',1:'Total Counts'}).set_index('category')
    rating_stats = pd.concat([category_ratios.T, rating_nums_df], axis=1)

    rating_stats = rating_stats[['A and above', 'BBB', 'Junk', 'Total Counts']]
    
    return rating_stats


# In[ ]:


def plot_rating(df, clean=False):
    '''
    This function is used to plot the proportions of the 3 rating categories,
    i.e. A and above, BBB, Junk in different periods
    and the total counts of the rating dates
    '''

    fig, ax1 = plt.subplots(figsize=(10, 6), dpi=200)

    for column in df.columns[:-1]: 
        ax1.plot(df.index, df[column], label=column)

    ax1.set_xlabel('Category')
    ax1.set_ylabel('Proportion', color='tab:red')
    ax1.tick_params(axis='y', labelcolor='tab:red')

    ax2 = ax1.twinx()

    ax2.bar(df.index, df['Total Counts'], color='grey', alpha=0.6, label='Total Counts')

    ax2.set_ylabel('Total Counts', color='tab:grey')
    ax2.tick_params(axis='y', labelcolor='tab:grey')


    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left')

    if clean == True:
        plt.title('Rating Category Proportions and Total Counts with Cleaned Data')
    else:
        plt.title('Rating Category Proportions and Total Counts with Rating Data')
    
    if clean == True:
        filepath = f'..'/ Path(OUTPUT_DIR) / 'rating_cleaned.png'
    else:
        filepath = f'..'/ Path(OUTPUT_DIR) / 'rating.png'
    plt.savefig(filepath)
    
    plt.show()

    


# In[ ]:


rating = pd.read_csv(Path(DATA_DIR) / 'pulled' / 'rating.csv')
rating.head()


# In[ ]:


rating_stats = get_category_stats(rating, subsamples=SUBSAMPLES, clean=False)
rating_stats


# In[ ]:


plot_rating(rating_stats,clean=False)


# In[ ]:


rating_stats_clean = get_category_stats(daily_data, subsamples=SUBSAMPLES, clean=True)
rating_stats_clean


# In[ ]:


plot_rating(rating_stats_clean,clean=True)


# ### Conclusion:
# 
# - Note that ```rating``` is the rating data retreived from WRDS and processed by ```load_rating.py```, thus ```rating_stats``` is derived from a much larger sample while the cleaned data ```daily.csv``` tilts toward a more liquid sample by filtering out less frequntly traded bonds. However, the ratios show similar tendencies along the timeframe, with a decreasing ratio of A-and-above and an increasing ratio of BBB during the Post-Crisis to Post-Volcker periods.
# 
# - In cleaned data, the proportion of BBB category is higher than raw data, which might indicate that the our data focuses more on BBB category bonds. However, as the cleaned data is derived trading data, which naturally has more trade dates than the rating dates form the rating data, it could also indicates for a higher frequency of trading in BBB category bonds.
# 
# - In raw rating data, the proportion remains rather steady, but it is noticeable that an increasing ratio of BBB is accompnied by a decreasing ratio of A-and-above, which might indicates that the bond is more likely to transform between these 2 categories.
# 

# 

# 
