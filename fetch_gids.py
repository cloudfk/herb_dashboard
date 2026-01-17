import requests
import re

url = "https://docs.google.com/spreadsheets/d/1YS2w6eQfULCpSCccQ2jjxoCTs0gJYt78vdt22Q4vZBU/edit?usp=sharing"

try:
    response = requests.get(url)
    response.raise_for_status()
    html = response.text
    
    # Regex to find (gid and name)
    # The pattern usually looks like: ,"name":"Sheet1","gid":"0",
    # Or strict JSON structures in the HTML
    
    # Let's look for simple patterns first
    matches = re.findall(r'"name":"([^"]+)","gid":"(\d+)"', html)
    
    print("Found sheets:")
    for name, gid in matches:
        print(f"Name: {name}, GID: {gid}")
        
    # Also try alternative pattern just in case
    if not matches:
        print("No standard JSON matches found. Trying loose pattern...")
        # sometimes it's gid: "..."
        matches = re.findall(r'gid=(\d+)', html)
        print("Found possible GIDs in links:", set(matches))

except Exception as e:
    print(f"Error: {e}")
