# core/stats.py

import requests
import re

def get_dynamic_team_mapping():
    """Mengambil data tipe tim langsung dari API JKT48 Official"""
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

def calculate_pivoted_team_stats(event_data, photo_map):
    """Mengubah struktur data dari Sesi->Member menjadi Team->Member->Sesi (A-Z)"""
    team_mapping = get_dynamic_team_mapping()
    
    # Inisialisasi wadah tim
    teams = {"LOVE": {}, "DREAM": {}, "PASSION": {}, "TRAINEE": {}}
    
    sessions = event_data.get('session', [])
    for sesi in sessions:
        raw_label = sesi.get('label', 'Session')
        
        # Ekstrak angka sesi (misal "Sesi 1" atau "Session 1" -> "S1")
        sesi_num = re.search(r'\d+', raw_label)
        sesi_short = f"S{sesi_num.group(0)}" if sesi_num else raw_label[:5]
        
        for m in sesi.get('session_detail', []):
            name = m.get('jkt48_member_name', 'Unknown')
            sold = m.get('tickets_sold', 0)
            avail = m.get('available_quota', 0)
            total = sold + avail
            
            safe_name = name.strip().lower()
            team_type = team_mapping.get(safe_name, "TRAINEE")
            if team_type not in teams:
                team_type = "TRAINEE"
                
            if name not in teams[team_type]:
                teams[team_type][name] = {
                    "photo": photo_map.get(safe_name, ""),
                    "sessions": []
                }
            
            # Masukkan detail sesi penjualan member
            teams[team_type][name]["sessions"].append({
                "label": sesi_short,
                "sold": sold,
                "total": total,
                "is_sold_out": (avail <= 0)
            })
            
    # Urutkan nama member dari A sampai Z di setiap tim
    pivoted_data = {}
    for team, members in teams.items():
        if not members:
            continue
        sorted_names = sorted(members.keys())
        pivoted_data[team] = []
        for name in sorted_names:
            pivoted_data[team].append({
                "name": name,
                "photo": members[name]["photo"],
                "sessions": members[name]["sessions"]
            })
            
    return pivoted_data
