import streamlit as st
import pandas as pd
import re
import urllib.parse

@st.cache_data(ttl=3600)
def load_data():
    """
    Loads data from Google Sheets using direct CSV export (GViz API).
    This bypasses st-gsheets-connection to avoid SSL/Env issues.
    Cached for 1 hour to support concurrent users.
    """
    try:
        # Configuration
        sheet_url = "https://docs.google.com/spreadsheets/d/1YS2w6eQfULCpSCccQ2jjxoCTs0gJYt78vdt22Q4vZBU"
        
        # Hardcoded GIDs to ensure robust connection without fragile scraping
        # Extracted from live sheet metadata
        gids = {
            "Prescription_Input": "221744534",      # Correct GID from user
            "Herb_Library": "1414851403",           # Confirmed (Integrated)
            "Prescription_script": "1443852241"     # Clinical scripts
        }

        # 2. Load Data using Export URL
        dfs = {}
        for name, gid in gids.items():
            # Use GViz API endpoint which is more robust for public access than /export
            csv_url = f"{sheet_url}/gviz/tq?tqx=out:csv&gid={gid}"
            # For Prescription_script, it might not have headers, but we'll try to read it
            if name == "Prescription_script":
                dfs[name] = pd.read_csv(csv_url, on_bad_lines='skip', header=None)
                # Assign manual headers based on structure: Prescription, Symptom, Explanation
                dfs[name].columns = ['Prescription_Name', 'Symptom_Status', 'Explanation'] + [f'extra_{i}' for i in range(len(dfs[name].columns)-3)]
            else:
                dfs[name] = pd.read_csv(csv_url, on_bad_lines='skip')

        return preprocess_data(dfs.get("Prescription_Input"), 
                             dfs.get("Herb_Library"), 
                             dfs.get("Prescription_script"))

    except Exception as e:
        st.error(f"Live data loading failed: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def preprocess_data(df_pres, df_herb, df_script):
    """
    Preprocesses the dataframes:
    2. Convert Amount to float using regex.
    3. Explode Herb_Library ingredients.
    4. Clean Prescription_script.
    """
    
    # Helper to strip strings
    def strip_strings(df):
        # Filter out "Unnamed" columns (empty columns in Sheet)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Strip column names checks
        df.columns = df.columns.str.strip()
        
        df_obj = df.select_dtypes(['object'])
        df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
        return df

    df_pres = strip_strings(df_pres.copy())
    df_herb = strip_strings(df_herb.copy())
    if df_script is not None:
        df_script = strip_strings(df_script.copy())
    
    # Validation: Check keys match expectations
    required_cols = ['Prescription_Name']
    if not all(col in df_pres.columns for col in required_cols):
        st.error(f"Data Connection Successful, but column structure does not match.")
        st.write("Found Columns:", df_pres.columns.tolist())
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Convert Amount to float
    amount_col = 'Amount'
    if amount_col in df_pres.columns:
        df_pres[amount_col] = df_pres[amount_col].astype(str).apply(lambda x: re.sub(r'[^0-9.]', '', x))
        df_pres[amount_col] = pd.to_numeric(df_pres[amount_col], errors='coerce').fillna(0.0)
    
    # Explode Herb_Library ingredients
    # Debug output: 'Compound_Name'
    ingredient_col = 'Compound_Name'
            
    if ingredient_col in df_herb.columns:
        # Split by comma (handling optional whitespace around it)
        df_herb[ingredient_col] = df_herb[ingredient_col].astype(str).str.split(r'\s*,\s*')
        # Handle cases where nulls might become 'nan' strings
        df_herb = df_herb.explode(ingredient_col)
        df_herb[ingredient_col] = df_herb[ingredient_col].str.strip()
    
    return df_pres, df_herb, df_script
