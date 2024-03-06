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

1.  load_trace
2.  load_rating
3.  load_return_cs (Carol)
4.  calc_spread_bias.py
5.  calc_daily_return_cs.py
6.  merge_metrics.py(output daily.csv, ultimate_table)
7.  summary_stats.ipynb
8.  pandas_to_latex.py


   
