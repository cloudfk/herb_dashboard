import pandas as pd
import plotly.graph_objects as go

class PrescriptionAnalyzer:
    def __init__(self, df_pres, df_herb, df_path, pres_a, pres_b):
        self.raw_pres = df_pres
        self.raw_herb = df_herb
        self.raw_path = df_path
        self.pres_a = pres_a
        self.pres_b = pres_b
        
        # Column mapping based on actual data inspection (User confirmed English headers)
        self.col_pres_name = 'Prescription_Name'
        self.col_pres_herb = 'Herb_Name'
        self.col_pres_amount = 'Amount'
        
        # Herb Library
        # Debug output: ['Herb_Name', 'Compound_Name (성분)', 'Target_Protein', 'Pathway']
        self.col_herb_name = 'Herb_Name'
        self.col_herb_ing = 'Compound_Name (성분)'
        self.col_herb_target = 'Target_Protein'
        
        # Pathology Map
        # Debug output: ['Target_Protein', 'Loop_Node', 'Action_Type', 'Action']
        self.col_path_target = 'Target_Protein'
        self.col_path_loop = 'Loop_Node'

    def get_filtered_data(self):
        # Filter for A and B
        df = self.raw_pres[self.raw_pres[self.col_pres_name].isin([self.pres_a, self.pres_b])].copy()
        
        # Merge with Herb Library (Herb -> Herb)
        # Note: Herb Library has multiple rows per Herb (one per compound/target)
        df = pd.merge(df, self.raw_herb, left_on=self.col_pres_herb, right_on=self.col_herb_name, how='left')
        
        # Merge with Pathology (Target -> Target)
        # Herb Lib 'Target_Protein (타겟)' matches Pathology 'Target_Protein'
        df = pd.merge(df, self.raw_path, left_on=self.col_herb_target, right_on=self.col_path_target, how='left')
        
        return df

    def get_structure(self):
        # We need nodes and links
        # Levels: Prescription -> Herb -> Ingredient -> Loop/Pathway (using Loop as final node for now, or Target)
        # User asked: [Prescription] -> [Herb] -> [Ingredient] -> [Pathway/Loop Node]
        
        df = self.get_filtered_data()
        
        # Determine unique sets for coloring
        # For each Herb, Ingredient, Loop: Is it in A? Is it in B?
        
        # Helpers to get sets
        def get_items(pres_name, col):
            return set(df[df[self.col_pres_name] == pres_name][col].dropna())
        
        herbs_a = get_items(self.pres_a, self.col_pres_herb)
        herbs_b = get_items(self.pres_b, self.col_pres_herb)
        
        ings_a = get_items(self.pres_a, self.col_herb_ing)
        ings_b = get_items(self.pres_b, self.col_herb_ing)
        
        loops_a = get_items(self.pres_a, self.col_path_loop)
        loops_b = get_items(self.pres_b, self.col_path_loop)
        
        # Assign colors
        def get_color(item, set_a, set_b):
            in_a = item in set_a
            in_b = item in set_b
            if in_a and in_b:
                return "purple"
            elif in_a:
                return "red"
            elif in_b:
                return "blue"
            else:
                return "grey"
        
        # Build Node List
        # We need unique nodes with indices
        
        # Prescriptions
        nodes = []
        nodes.append({'label': self.pres_a, 'color': 'red', 'type': 'Prescription'})
        nodes.append({'label': self.pres_b, 'color': 'blue', 'type': 'Prescription'})
        
        # Map keys: (Level, Name) -> Index
        node_map = {('Prescription', self.pres_a): 0, ('Prescription', self.pres_b): 1}
        
        def add_nodes(items, set_a, set_b, n_type):
            sorted_items = sorted(list(set_a | set_b))
            start_idx = len(nodes)
            for i, item in enumerate(sorted_items):
                 nodes.append({
                     'label': item,
                     'color': get_color(item, set_a, set_b),
                     'type': n_type
                 })
                 node_map[(n_type, item)] = start_idx + i
        
        add_nodes(herbs_a | herbs_b, herbs_a, herbs_b, 'Herb')
        add_nodes(ings_a | ings_b, ings_a, ings_b, 'Ingredient')
        add_nodes(loops_a | loops_b, loops_a, loops_b, 'Pathway')
        
        # Build Links
        links = []
        
        # 1. Pres -> Herb
        # Group by Pres, Herb to get summed Amount
        grp1 = df.groupby([self.col_pres_name, self.col_pres_herb])[self.col_pres_amount].sum().reset_index()
        for _, row in grp1.iterrows():
            src_name = row[self.col_pres_name]
            tgt_name = row[self.col_pres_herb]
            val = row[self.col_pres_amount]
            
            src_key = ('Prescription', src_name)
            tgt_key = ('Herb', tgt_name)
            
            if pd.notna(src_name) and pd.notna(tgt_name) and val > 0:
                # Link color based on Source (Prescription) is easiest, or relationship.
                # Requirement: "Prescription A related paths are Red..."
                # Link color usually matches source for flow clarity in this case.
                c = 'red' if src_name == self.pres_a else 'blue'
                if src_key in node_map and tgt_key in node_map:
                    links.append({'source': node_map[src_key], 'target': node_map[tgt_key], 'value': val, 'color': c})

        # 2. Herb -> Ingredient
        # Problem: Amounts are definitions. We should propagate the "Flow" from the specific prescription.
        # But Sankey in Plotly sums incoming. 
        # If we just link Herb(Purple) -> Ing(Purple), what color?
        # The prompt says: "Two prescription shared path -> Purple".
        # So strictly, we should have separate links if we want to show the 'Red flow' vs 'Blue flow' through a shared node.
        # However, standard Sankey merges flows at nodes. 
        # To strictly show separate Red/Blue paths, we'd need to duplicate nodes (Herb_A, Herb_B), but that defeats the purpose of "Shared Node".
        # So we stick to standard Sankey: Shared Node = Purple. 
        # Links: If the node is Shared, the outgoing link color is tricky.
        # usually we make the link color semi-transparent grey or purple if both contribute.
        # Simply: 
        # If Link connects (Red -> Red) -> Red
        # (Blue -> Blue) -> Blue
        # (Purple -> Purple) -> Purple?
        # (Red -> Purple) -> Red
        # (Purple -> Red) -> Red (Shouldn't happen)
        # (Purple -> Purple) -> Purple.
        
        # Let's aggregate flows.
        # Actually, best way to calculate flow volume for (Herb -> Ing) is to sum the Amounts of that Herb from A and B.
        # But wait, Herb X has Amount 10 in A, 20 in B. Total 30.
        # Herb X contains Ing Y, Ing Z.
        # We flow 30 to Y and 30 to Z? Or split?
        # I will just default to count or sum. 
        # Let's just create defined links based on existence.
        # Weight/Value: The user said "Line thickness reflects Amount".
        # So for Herb -> Ing, use Sum(Amount of Herb).
        
        # Iterate over all Unique (Herb, Ing) pairs in the library (that are in our subset)
        # Value = Sum of Amounts of this Herb in our filtered DF.
        
        grp2 = df.groupby([self.col_pres_herb, self.col_herb_ing])[self.col_pres_amount].sum().reset_index()
        for _, row in grp2.iterrows():
            src_name = row[self.col_pres_herb]
            tgt_name = row[self.col_herb_ing]
            val = row[self.col_pres_amount]
            
            src_key = ('Herb', src_name)
            tgt_key = ('Ingredient', tgt_name)
            
            if pd.notna(src_name) and pd.notna(tgt_name) and val > 0:
                # Color logic for link
                # If src is Red (only A), link is Red.
                # If src is Blue (only B), link is Blue.
                # If src is Purple (Both), check Target.
                # Actually simpler: check if this specific (Herb->Ing) connection exists in A-chain? 
                # Yes, if Herb is present in A.
                # Is it in B-chain? Yes, if Herb is present in B.
                # Herb is the determinant because Ingredient is intrinsic to Herb.
                src_color = get_color(src_name, herbs_a, herbs_b)
                # If src is purple, the link carries both flows. Color it purple? 
                # Or maybe gradient? Plotly supports 'scales'.
                # Let's use src color.
                if src_key in node_map and tgt_key in node_map:
                    links.append({'source': node_map[src_key], 'target': node_map[tgt_key], 'value': val, 'color': src_color.replace('grey', 'silver')})

        # 3. Ingredient -> Pathway
        # Value = Sum of Amounts of Herbs containing this Ingredient.
        grp3 = df.groupby([self.col_herb_ing, self.col_path_loop])[self.col_pres_amount].sum().reset_index()
        for _, row in grp3.iterrows():
            src_name = row[self.col_herb_ing]
            tgt_name = row[self.col_path_loop]
            val = row[self.col_pres_amount]
            
            src_key = ('Ingredient', src_name)
            tgt_key = ('Pathway', tgt_name)
            
            if pd.notna(src_name) and pd.notna(tgt_name) and val > 0:
                src_color = get_color(src_name, ings_a, ings_b)
                if src_key in node_map and tgt_key in node_map:
                    links.append({'source': node_map[src_key], 'target': node_map[tgt_key], 'value': val, 'color': src_color.replace('grey', 'silver')})
                
        return nodes, links

    def generate_sankey(self):
        nodes, links = self.get_structure()
        
        # Plotly format
        # node = dict(label=[...], color=[...])
        # link = dict(source=[...], target=[...], value=[...], color=[...])
        
        node_dict = {
            'label': [n['label'] for n in nodes],
            'color': [n['color'] for n in nodes],
            'pad': 15,
            'thickness': 20,
            'line': dict(color="black", width=0.5)
        }
        
        link_dict = {
            'source': [l['source'] for l in links],
            'target': [l['target'] for l in links],
            'value': [l['value'] for l in links],
            'color': [l['color'].replace('red', 'rgba(255,0,0,0.4)').replace('blue', 'rgba(0,0,255,0.4)').replace('purple', 'rgba(128,0,128,0.4)') for l in links] # Add transparency
        }
        
        fig = go.Figure(data=[go.Sankey(
            node=node_dict,
            link=link_dict
        )])
        
        fig.update_layout(title_text=f"{self.pres_a} vs {self.pres_b} Comparison", font_size=10)
        return fig

    def get_common_insights(self):
        df = self.get_filtered_data()
        
        # Filter for Prescription A and B separately
        df_a = df[df[self.col_pres_name] == self.pres_a]
        df_b = df[df[self.col_pres_name] == self.pres_b]
        
        # Common Loops
        loops_a = set(df_a[self.col_path_loop].dropna())
        loops_b = set(df_b[self.col_path_loop].dropna())
        common_loops = list(loops_a.intersection(loops_b))
        
        # Common Targets (Using Herb Target column or Path Target column - they are merged)
        # Using col_herb_target (from Herb library side) as it's the source of truth for ingredients
        targets_a = set(df_a[self.col_herb_target].dropna())
        targets_b = set(df_b[self.col_herb_target].dropna())
        common_targets = list(targets_a.intersection(targets_b))
        
        return common_targets, common_loops
