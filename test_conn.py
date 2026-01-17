import requests

sheet_id = "1YS2w6eQfULCpSCccQ2jjxoCTs0gJYt78vdt22Q4vZBU"
gids = {
    "Prescription": "0",
    "Herb": "1414851403",
    "Pathology": "108192910"
}

endpoints = [
    # Format 1: Standard export
    lambda gid: f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}",
    # Format 2: GViz
    lambda gid: f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}",
]

print("Testing connections...")

for name, gid in gids.items():
    print(f"\n--- Testing {name} (GID: {gid}) ---")
    for i, ep in enumerate(endpoints):
        url = ep(gid)
        try:
            resp = requests.get(url)
            print(f"Format {i+1}: Status {resp.status_code}")
            if resp.status_code == 200:
                print(f"  Success! Preview: {resp.text[:50]}...")
            else:
                print(f"  Failed.")
        except Exception as e:
            print(f"  Error: {e}")
