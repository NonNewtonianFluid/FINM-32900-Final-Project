# Calculate Corporate Bond Metrics from TRACE data

## Overview

This Python repository aims to replicate Table 1 from the research paper "Noisy prices and return-based anomalies in corporate bonds" authored by Alexander Dickerson, Cesare Robotti, and Giulio Rossetti. The primary references for data sourcing and cleaning are drawn from [Open Source Bond Asset Pricing](https://openbondassetpricing.com/).

## Requirements

- Python 3.9.13
- pandas 
- numpy
- quantLib 1.29
- joblib 1.1.1
- wrds 3.1.2 (and access to the WRDS database and cloud)

## Usage

Please make sure to update and install the required packages.

Run these scripts sequentially to produce table 1 from the paper.

1. Run ```calculate_bond_return.py```. This script uses the data downloaded from the file ```MakeBondDailyMetrics.py.py``` Open Source Bond Asset Pricing outputs the daily corporate bond prices filtering based on business days between trades (<= 5 days), filtering out bonds with less than five trades per month, calculating the daily returns, removing large return reversals and excluding returns with absolute value > 20%.

2. Run ```bond_return_with_rating.py```. This script use the data generated from ```calculate_bond_return.py``` and outputs the mean daily bond return based on different time period subsamples, conditioning on different ratings. 

   
