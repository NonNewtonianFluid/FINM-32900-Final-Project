import pandas as pd
from pandas.testing import assert_frame_equal
import numpy as np

import derive_table

import config
from pathlib import Path
DATA_DIR = Path(config.DATA_DIR)

def test_derive_table_shape():
    all_df = pd.read_csv( Path(DATA_DIR) / "pulled" / 'daily.csv')
    res_df = derive_table.derive_table(all_df)
    assert res_df.shape[0] == 28
    assert res_df.shape[1] == 4


def test_compare_paper_manual():
    
    BID_ASK_BIAS_THRESHOLD = 10
    RETURN_THRESHOLD = 5
    BID_ASK_SPREAD_THRESHOLD = 10
    CREDIT_SPREAD_THRESHOLD = 500

    data = {
        'All': [
            0.148, 1.703, 35.13, 323.6,
            0.278, 1.374, 51.80, 314.7,
            0.323, -2.499, 59.04, 602.9,
            0.168, 6.899, 42.47, 440.6,
            0.081, 1.914, 29.52, 305.5,
            0.049, 0.768, 19.87, 238.0
        ],
        'A and above': [
            0.114, 1.022, 29.90, 137.5,
            0.202, -0.450, 42.00, 106.9,
            0.285, 1.538, 57.60, 318.0,
            0.149, 4.572, 40.98, 211.9,
            0.061, 1.356, 24.87, 141.3,
            0.029, 0.291, 14.86, 91.51
        ],
        'BBB': [
            0.138, 0.898, 34.23, 234.3,
            0.270, -1.424, 50.78, 218.2,
            0.287, -1.460, 53.03, 475.2,
            0.138, 6.194, 38.80, 297.6,
            0.075, 2.083, 29.96, 229.9,
            0.046, 0.420, 20.67, 173.7
        ],
        'Junk': [
            0.204, 1.665, 42.77, 691.3,
            0.373, 2.980, 63.32, 653.2,
            0.429, -11.23, 66.28, 1309.6,
            0.217, 10.50, 48.28, 835.1,
            0.113, 1.851, 36.26, 625.2,
            0.079, 0.375, 26.20, 555.3
        ]
    }

    index = pd.MultiIndex.from_product([
        ["Full sample", "Pre-crisis", 
        "Crisis", "Post-Crisis", 
        "Basel II.5 and III", "Post-Volcker"],
        ["Bid-ask bias bps", "Daily return bps", "Bid-ask spread bps", "Credit spread bps"]
    ], names=['category', 'variables'])

    df_corrected = pd.DataFrame(data, index=index)

    all_df = pd.read_csv( Path(DATA_DIR) / "pulled" / 'daily.csv')
    res_df = derive_table.derive_table(all_df)
    res_df_compare = res_df[res_df.index.get_level_values('category') != 'Up to latest']

    # TEST 1: Make sure that absolute difference is less than ~0.2% for the 
    # bid_ask_spread_data
    bid_ask_spread_data = res_df_compare.xs('Bid-ask spread bps', level='variables', drop_level=False)
    bid_ask_spread_data_expected = df_corrected.xs('Bid-ask spread bps', level='variables', drop_level=False)
    
    # bid_ask_bias_data
    bid_ask_bias_data = res_df_compare.xs('Bid-ask bias bps', level='variables', drop_level=False)
    bid_ask_bias_data_expected = df_corrected.xs('Bid-ask bias bps', level='variables', drop_level=False)

    # daily_return_data
    daily_return_data = res_df_compare.xs('Daily return bps', level='variables', drop_level=False)
    daily_return_data_expected = df_corrected.xs('Daily return bps', level='variables', drop_level=False)

    # credit_spread_data
    credit_spread_data = res_df_compare.xs('Credit spread bps', level='variables', drop_level=False)
    credit_spread_data_expected = df_corrected.xs('Credit spread bps', level='variables', drop_level=False)
    
    assert (bid_ask_spread_data - bid_ask_spread_data_expected).abs().mean().mean() < BID_ASK_SPREAD_THRESHOLD
    assert (bid_ask_bias_data - bid_ask_bias_data_expected).abs().mean().mean() < BID_ASK_BIAS_THRESHOLD
    assert (daily_return_data - daily_return_data_expected).abs().mean().mean() < RETURN_THRESHOLD
    assert (credit_spread_data - credit_spread_data_expected).abs().mean().mean() < CREDIT_SPREAD_THRESHOLD

    # TEST 2: Make sure the signs are the same at least 95% days.
    assert (np.array(bid_ask_spread_data) * np.array(bid_ask_spread_data_expected) > 0).mean() > 0.95
    assert (np.array(bid_ask_bias_data) * np.array(bid_ask_bias_data_expected) > 0).mean() > 0.95
    assert (np.array(daily_return_data) * np.array(daily_return_data_expected) > 0).mean() > 0.7
    assert (np.array(credit_spread_data) * np.array(credit_spread_data_expected) > 0).mean() > 0.95
