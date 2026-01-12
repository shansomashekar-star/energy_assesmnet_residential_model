
import pandas as pd
import os
import json
import warnings

# Suppress openpyxl warnings about conditional formatting
warnings.simplefilter(action='ignore', category=UserWarning)

DATA_DIR = "data"
BENCHMARK_FILE = "models_advanced/benchmark_data.json"

def parse_hc_table(filename):
    """
    Parses a typical RECS HC table.
    Note: These tables have complex headers (rows 3-6 usually).
    We look for specific rows like 'Northeast', 'Midwest', etc.
    """
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        print(f"File not found: {filename}")
        return None
        
    try:
        # Load, skipping header fluff
        df = pd.read_excel(filepath, skiprows=2, engine='openpyxl') 
        # Structure is usually: Col A = Label (e.g. Region), Col B = Total Homes, Col C+ = Metrics?
        # Actually HC tables are often: "Total U.S.", "Northeast", etc. in first column.
        
        # Let's extract Region / Census Division rows.
        # Key Rows to identify:
        # "Northeast Census Region"
        # "Midwest Census Region"
        # "South Census Region"
        # "West Census Region"
        
        # We need to map row labels to standard keys.
        benchmarks = {}
        
        # Clean col 0
        df.iloc[:,0] = df.iloc[:,0].astype(str).str.strip()
        
        # Iterate rows to find regions
        for idx, row in df.iterrows():
            label = str(row.iloc[0])
            
            # Simple keyword matching for regions
            region = None
            if "Northeast Census Region" in label: region = "Northeast"
            elif "Midwest Census Region" in label: region = "Midwest"
            elif "South Census Region" in label: region = "South"
            elif "West Census Region" in label: region = "West"
            elif "Total U.S." in label: region = "National"
            
            if region:
                # Value extraction depends on table type.
                # HC 1.1 is "Fuels Used". This might not have "Total BTU".
                # To get Total Energy benchmarks, we ideally want CE (Consumption & Expenditures) tables.
                # CE 1.1? We downloaded ce7.1.xlsx...
                # Let's check CE 1.1 equivalent? Actually we have 'ce7.1.xlsx'.
                pass
                
        return benchmarks
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
        return None


def extract_sqft_benchmarks():
    """Parses HC 10.9 (Avg SqFt)"""
    filename = "HC_10.9.xlsx"
    filepath = os.path.join(DATA_DIR, filename)
    
    defaults = {"National": 2300, "Northeast": 2500, "Midwest": 2400, "South": 2200, "West": 2100}
    
    if not os.path.exists(filepath):
        print(f"{filename} not found. Using defaults.")
        return defaults

    print(f"Parsing {filename} for SqFt Benchmarks...")
    try:
        # Load with openpyxl
        df = pd.read_excel(filepath, skiprows=2, engine='openpyxl')
        
        # Structure: Col A = Region/Row, Col B = Total U.S. Avg?
        # We need to hunt.
        benchmarks = {}
        
        # Iterate rows looking for regions
        for idx, row in df.iterrows():
            label = str(row.iloc[0]).strip()
            val = row.iloc[1] # Assume Column B is the "All Homes" average for that row
            
            try:
                val = float(val)
            except:
                continue
                
            if "Total U.S." in label: benchmarks["National"] = val
            elif "Northeast Census Region" in label: benchmarks["Northeast"] = val
            elif "Midwest Census Region" in label: benchmarks["Midwest"] = val
            elif "South Census Region" in label: benchmarks["South"] = val
            elif "West Census Region" in label: benchmarks["West"] = val
            
        # Merge with defaults if missing
        for k, v in defaults.items():
            if k not in benchmarks: benchmarks[k] = v
            
        return benchmarks
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
        return defaults


def parse_all_files():
    """Iterates ALL .xlsx files in data/ and extracts National Totals"""
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".xlsx")]
    print(f"Processing {len(files)} files...")
    
    knowledge_base = {}
    
    for fname in files:
        if fname.startswith("HC_10.9"): continue # Handled specifically
        
        path = os.path.join(DATA_DIR, fname)
        try:
            # Load
            df = pd.read_excel(path, skiprows=2, engine='openpyxl')
            
            # Find Total U.S. Row (Relaxed Search)
            found = False
            # Search first 20 rows
            for idx, row in df.head(50).iterrows():
                # specific check: First column often has labels
                label = str(row.iloc[0]).strip()
                
                # Some tables use "Total U.S." or just "Total" if table is national
                if "Total U.S." in label or "All homes" in label:
                    vals = row.values.tolist()
                    clean_vals = [x for x in vals if isinstance(x, (int, float)) and not pd.isna(x)]
                    if clean_vals:
                       knowledge_base[fname] = clean_vals[:5]
                       found = True
                    break
            if not found:
                 # Check if the FILE itself is regional, maybe the first row is just totals?
                 # Let's try row 3-6
                 pass
            if not found:
                print(f"[{fname}] 'Total U.S.' row not found.")
        except Exception as e:
            print(f"Failed to parse {fname}: {e}")
            continue
            
    return knowledge_base

def main():
    # 1. Extract SqFt Benchmarks (High Precision)
    sqft_bench = extract_sqft_benchmarks()
    
    # 2. Extract All Other Stats (Broad Coverage)
    national_stats = parse_all_files()
    
    # 3. Create Composite Database
    db = {
        "sqft": sqft_bench,
        "eui": { # Fallback
            "National": 35.0,
            "Northeast": 42.0,
            "Midwest": 38.0, 
            "South": 30.0,
            "West": 25.0
        },
        "national_stats": national_stats,
        "source": f"EIA RECS 2020 ({len(national_stats)} files processed)"
    }
    
    # 4. Save to JSON
    with open(BENCHMARK_FILE, "w") as f:
        json.dump(db, f, indent=2)
    
    print(f"Analysis complete. Processed {len(national_stats)} files.")
    print(f"Benchmark data saved to {BENCHMARK_FILE}")

if __name__ == "__main__":
    main()
