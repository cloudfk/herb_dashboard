import requests
import re

url = "https://docs.google.com/spreadsheets/d/1YS2w6eQfULCpSCccQ2jjxoCTs0gJYt78vdt22Q4vZBU/edit?usp=sharing"

try:
    print(f"Fetching {url}...")
    response = requests.get(url)
    content = response.text
    
    print(f"Content length: {len(content)}")
    
    targets = ["Prescription_Input", "Herb_Library", "Pathology_Map"]
    
    for t in targets:
        print(f"\n--- Searching for {t} ---")
        indices = [m.start() for m in re.finditer(re.escape(t), content)]
        if not indices:
            print("Not found!")
        for idx in indices:
            # Print surrounding context
            start = max(0, idx - 100)
            end = min(len(content), idx + 100)
            snippet = content[start:end]
            print(f"Context: ...{snippet}...")
            
except Exception as e:
    print(e)
