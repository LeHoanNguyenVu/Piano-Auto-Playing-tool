import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from library.cloud_database import CloudDatabase

db = CloudDatabase()
print(f"Connected: {db.is_connected}")
print(f"Songs: {len(db.catalog)}")

for s in db.catalog:
    sid = s.get('id')
    pc = s.get('play_count', 0) or 0
    print(f"  id={sid} (type={type(sid).__name__}) play_count={pc}")

if db.catalog:
    song = db.catalog[0]
    sid = song.get('id')
    old = song.get('play_count', 0) or 0
    print(f"\nTesting increment for id={sid}...")
    db.increment_play_count(sid)
    
    db.refresh_catalog()
    for s in db.catalog:
        if s.get('id') == sid:
            new = s.get('play_count', 0) or 0
            print(f"Before={old} After={new} Changed={new > old}")
            if new <= old:
                print("FAILED: play_count did NOT increase.")
                print("Check RLS policies on songs_catalog table.")
            break
