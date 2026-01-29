import pandas as pd
from analysis import PrescriptionAnalyzer
import plotly.graph_objects as go
import os

# Mock Data
df_pres = pd.DataFrame({
    'Prescription_Name': ['A'],
    'Herb_Name': ['H1'],
    'Amount': [10]
})

df_herb = pd.DataFrame({
    'Herb_Name': ['H1'],
    'Compound_Name (성분)': ['C1'],
    'Target_Protein': ['T1'],
    'Pathway': ['P1']
})

df_path = pd.DataFrame({
    'Target_Protein': ['T1'],
    'Loop_Node': ['Energy Loop'],
    'Action_Type': ['Activation'],
    'Action': ['Test Action']
})

# Mock Mechanism Mapping (Simulating Google Sheet data)
df_mech_map = pd.DataFrame({
    'Action_Key': ['Test Action'],
    'Source_System': ['Mitochondria'],
    'Initial_State': ['Low'],
    'Mechanism': ['Act'],
    'Target_System': ['Cell'],
    'Final_State': ['High']
})

# Initialize Analyzer with 4 dfs
analyzer = PrescriptionAnalyzer(df_pres, df_herb, df_path, df_mech_map, 'A', 'A')

# Test
try:
    fig = analyzer.generate_mechanism_flow('A')
    print("Mechanism Flow generated successfully.")
    
    if isinstance(fig, go.Figure):
         if len(fig.data) > 0 and len(fig.data[0].link.source) > 0:
             print("Links found in Sankey.")
         else:
             print("Warning: Figure generated but no links found (Mapping match failed?).")
    else:
        print("Result is NOT a Plotly figure.")

except Exception as e:
    print(f"Error: {e}")
