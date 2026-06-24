# core/stats.py

import requests

def get_dynamic_team_mapping():
    """Mengambil data tim langsung dari API JKT48 Official"""
    url = "https://jkt48.com/api/v1/members?lang=id"
    team_mapping = {}
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status"):
                for m in data.get("data", []):
                    safe_name = m.get("name", "").strip().lower()
                    team_type = m.get("type", "TRAINEE")
                    team_mapping[safe_name] = team_type
    except:
        pass
    return team_mapping

def calculate_team_visual_stats(event_data, photo_map):
    """Menghitung dan mengelompokkan SELURUH member per tim"""
    team_mapping = get_dynamic_team_mapping()
    
    teams = {"LOVE": [], "DREAM": [], "PASSION": [], "TRAINEE": []}
    member_accumulator = {}
    
    sessions = event_data.get('session', [])
    for sesi in sessions:
        for m in sesi.get('session_detail', []):
            name = m.get('jkt48_member_name', 'Unknown')
            sold = m.get('tickets_sold', 0)
            avail = m.get('available_quota', 0)
            
            safe_name = name.strip().lower()
            
            if safe_name not in member_accumulator:
                team_type = team_mapping.get(safe_name, "TRAINEE")
                if team_type not in teams:
                    team_type = "TRAINEE"
                    
                member_accumulator[safe_name] = {
                    "name": name,
                    "team": team_type,
                    "sold": 0,
                    "total": 0,
                    "photo": photo_map.get(safe_name, "")
                }
            
            member_accumulator[safe_name]["sold"] += sold
            member_accumulator[safe_name]["total"] += (sold + avail)
            
    for data in member_accumulator.values():
        total = data["total"]
        sold = data["sold"]
        rate = (sold / total * 100) if total > 0 else 0
        
        teams[data["team"]].append({
            "name": data["name"],
            "sold_rate": rate,
            "sold": sold,
            "total": total,
            "photo": data["photo"]
        })
        
    # Urutkan berdasarkan persentase tertinggi (Tanpa batasan [:4])
    for team in teams:
        teams[team] = sorted(teams[team], key=lambda x: (x["sold_rate"], x["sold"]), reverse=True)
        
    return teams
