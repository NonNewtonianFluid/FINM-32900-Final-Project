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

1.  load_trace.py: This Python script is designed to streamline the process of extracting, cleaning, and analyzing bond data from the WRDS TRACE database. The script focuses on three key areas of bond market analysis: price, volume, and illiquidity metrics. By leveraging data directly from WRDS, the script ensures access to comprehensive and accurate bond trading information, enabling a detailed examination of market dynamics.
   
2.  load_rating.py: This Python script automates fetching bond ratings from the WRDS (Wharton Research Data Services) database, specifically targeting Moody's and Standard & Poor's (S&P) ratings. Instead of converting these ratings into numeric scores, it categorizes them into three broad quality categories: 'A and above', 'BBB', or 'Junk'. The script then cleans and saves the processed data for subsequent analysis.

3.  load_return_cs.py: This script automates the process of downloading a compressed dataset of bond market transactions for December 2023 from a public source, extracting the contents, and preparing the data for analysis. The data is then loaded into a pandas DataFrame, with some initial cleaning applied to standardize column names and formats.
   
4.  calc_spread_bias.py: 

5.  calc_daily_return_cs.py: This Python script plays an integral role in a comprehensive workflow designed for bond market analysis. It takes in bond market data produced by a prior script named load_return_cs.py, then proceeds to clean and filter this data according to conditions grounded in academic research. Following this, it calculates daily returns and credit spreads for corporate bonds, thereby preparing the refined data for subsequent stages of analysis.

6.  derive_table.py: This Python script performs advanced processing on bond market data, integrating various sources including trading data, bid-ask spread, returns, and bond ratings. The goal is to prepare a comprehensive dataset for in-depth analysis, specifically focusing on calculating daily returns, credit spreads, and correlating these with bond ratings. The final output includes a LaTeX table summarizing key statistics across different market periods.

7.  summary_stats.ipynb:
8.  
9.  pandas_to_latex.py


   
