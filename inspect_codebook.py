import pandas as pd

# Load Codebook
print("Reading Codebook...")
try:
    # Skip the title rows. Usually row 4 (0-indexed -> 3) is the header
    df_code = pd.read_excel("recs2020_codebook_v7.xlsx", header=3)
    print("Columns found:", df_code.columns.tolist())
    
    # Rename columns for clarity
    df_code.columns = ['Variable Name', 'Type', 'Variable Label', 'Response Codes', 'Section_']
    
    print("Columns (renamed):", df_code.columns.tolist())
    
    # Filter for useful structural vars
    keywords = ['wall', 'roof', 'window', 'insulat', 'heat', 'cool', 'thermostat', 'year', 'age']
    
    print("\n--- Potential Feature Candidates ---")
    
    for idx, row in df_code.iterrows():
        label = str(row['Variable Label']).lower()
        if any(k in label for k in keywords):
            print(f"{row['Variable Name']}: {row['Variable Label']}")

except Exception as e:
    print(f"Error: {e}")
