import pandas as pd
from analysis import PrescriptionAnalyzer
import plotly.graph_objects as go
import plotly.express as px

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

# Initialize Analyzer 
analyzer = PrescriptionAnalyzer(df_pres, df_herb, df_path, 'A', 'A')

# Test
try:
    fig = analyzer.generate_interaction_sunburst('A')
    print("Sunburst Chart generated successfully.")
    
    if isinstance(fig, go.Figure):
         # fig.data[0] should be Sunburst
         if fig.data and fig.data[0].type == 'sunburst':
             print("Result is a valid Plotly Sunburst.")
         else:
             print("Warning: Figure generated but type is not sunburst.")
    else:
        print("Result is NOT a Plotly figure.")

except Exception as e:
    print(f"Error: {e}")
