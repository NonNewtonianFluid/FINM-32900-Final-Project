FINM 32900 Final Project: Replicating Tables from Noisy Prices and Return-based Anomalies in Corporate Bonds
==================

# About this project

This study endeavors to replicate Table 1 from the research article "Noisy Prices and Return-based Anomalies in Corporate Bonds" authored by Alexander Dickerson, Cesare Robotti, and Giulio Rossetti. Utilizing the TRACE database, we extracted data on corporate bonds and computed various metrics, including bid-ask bias, return, bid-ask spread, and credit spread, across different time periods and bond ratings. Our findings indicate that the replication results for Table 1 closely align with the statistics reported in the original study. However, it is imperative to acknowledge several challenges encountered during our analysis, which may have contributed to slight discrepancies between our results and those presented in the original paper.

# Quick Start

To quickest way to run code in this repo is to use the following steps. First, note that you must have TexLive installed on your computer and available in your path.
You can do this by downloading and installing it from here ([windows](https://tug.org/texlive/windows.html#install) and [mac](https://tug.org/mactex/mactex-download.html) installers).
Having installed LaTeX, open a terminal and navigate to the root directory of the project and create a conda environment using the following command:
```
conda create -n blank python=3.12
conda activate finm
```
and then install the dependencies with pip
```
pip install -r requirements.txt
```
You can then run 
```
dodo.py
```
# General Directory Structure

 - The `reports` folder contains the pdf version of the report that was not generated from code. It cannot be easily recreated if it is deleted.

 - The `output` folder, on the other hand, contains the replicated "Table 1" and "Summary Statistics" in tex files that are generated from code. The files should be able to be deleted, because the code can be run again, which would again generate all of the contents.

# Data

The data source of Table 1 is the Wharton Research Data Services (WRDS) bond database, which integrates information from the Enhanced Trade Reporting and Compliance Engine (TRACE). We also utilize data from Mergent Fixed Income Securities Database (FISD) for details on bond issues. 
