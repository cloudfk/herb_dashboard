import pandas as pd
from analysis import PrescriptionAnalyzer
import graphviz

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

# Initialize Analyzer (reverted signature, only 5 args)
analyzer = PrescriptionAnalyzer(df_pres, df_herb, df_path, 'A', 'A')

# Test
try:
    dot = analyzer.generate_network_graph('A')
    print("Network Graph generated successfully.")
    
    if isinstance(dot, graphviz.Digraph):
         print("Result is a valid Graphviz Digraph.")
         # Render source to check content
         # print(dot.source) 
    else:
        print("Result is NOT a Graphviz Digraph.")

except Exception as e:
    print(f"Error: {e}")
