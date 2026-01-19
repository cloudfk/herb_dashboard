import pandas as pd
from analysis import PrescriptionAnalyzer
import plotly.graph_objects as go

# Mock Data
df_pres = pd.DataFrame({
    'Prescription_Name': ['A', 'A'],
    'Herb_Name': ['H1', 'H2'],
    'Amount': [10, 20]
})

df_herb = pd.DataFrame({
    'Herb_Name': ['H1', 'H2'],
    'Compound_Name (성분)': ['C1', 'C2'],
    'Target_Protein': ['T1', 'T2'],
    'Pathway': ['P1', 'P2']
})

df_path = pd.DataFrame({
    'Target_Protein': ['T1', 'T2'],
    'Loop_Node': ['Loop1', 'Loop2'],
    'Action_Type': ['Activation', 'Inhibition'],
    'Action': ['Act1', 'Inh1']
})

# Initialize Analyzer
analyzer = PrescriptionAnalyzer(df_pres, df_herb, df_path, 'A', 'A')

# Test generate_inference_sunburst
try:
    fig = analyzer.generate_inference_sunburst('A')
    print("Sunburst generated successfully.")
    # Check if fig is a Plotly figure
    if isinstance(fig, go.Figure):
        print("Result is a valid Plotly Figure.")
    else:
        print("Result is NOT a Plotly Figure.")
except Exception as e:
    print(f"Error generating Sunburst: {e}")
