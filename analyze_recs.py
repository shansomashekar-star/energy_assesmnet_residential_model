import pandas as pd
import numpy as np

# Load Data
print("Loading RECS 2020 Data...")
try:
    df = pd.read_csv('recs2020_public_v7.csv', low_memory=False)
except FileNotFoundError:
    print("Error: csv file not found.")
    exit()

# Feature Engineering
df['EUI'] = df['TOTALBTU'] / df['TOTSQFT_EN'] # Energy Use Intensity (kBTU/sqft)

# 1. geographic benchmarks
print("\n--- Benchmarks by Census Division ---")
benchmarks = df.groupby('DIVISION')['EUI'].agg(['mean', 'median', 'count'])
print(benchmarks)

# 2. Correlation Analysis
print("\n--- Correlation with Total Energy ---")
corrs = df[['TOTSQFT_EN', 'HDD65', 'CDD65', 'NHSLDMEM', 'YEARMADERANGE', 'TOTALBTU']].corr()['TOTALBTU']
print(corrs)

# 3. Simple Mock Audit Logic
# Pick a random "client" from the dataset
client = df.sample(1).iloc[0]
print(f"\n--- Mock Audit for Home ID: {client['DOEID']} ---")
print(f"Location (Div): {client['DIVISION']}")
print(f"Size: {client['TOTSQFT_EN']} sqft")
print(f"Actual Usage: {client['TOTALBTU']:.2f} million BTU")

# Compare to peers in same Division
peer_group = df[df['DIVISION'] == client['DIVISION']]
percentile = (peer_group['TOTALBTU'] < client['TOTALBTU']).mean() * 100
print(f"Peer Percentile: {percentile:.1f}% (Higher is worse)")

if percentile > 75:
    print("INSIGHT: High Usage Alert! You use more energy than 75% of neighbors.")
else:
    print("INSIGHT: Good Efficiency. You are better than average.")
