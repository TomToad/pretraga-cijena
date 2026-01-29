"""
Skripta za automatsko uploadanje CSV cjenika na Dropbox
Pokreni dnevno u 8:20 AM putem Task Schedulera ili cron
"""

import dropbox
import os
from datetime import datetime

# ----------------- KONFIGURACIJA -----------------
# Zamijenite s vašim Dropbox Access Tokenom
DROPBOX_TOKEN = "your_dropbox_access_token_here"

# Lokalni folder gdje se nalaze CSV cjenici
LOCAL_DIR = r"D:\Py_skripte\Cjenici_jucer"

# Dropbox folder (mora bit /Cjenici_jucer)
DROPBOX_DIR = "/Cjenici_jucer"

# Lista CSV datoteka koje se uploadaju
CSV_FILES = [
    "plodine_jucer.csv",
    "eurospin_jucer.csv",
    "kaufland_jucer.csv",
    "konzum_jucer.csv",
    "lidl_jucer.csv",
    "spar_jucer.csv"
]

# ----------------- FUNKCIJE -----------------

def upload_to_dropbox(local_path, dropbox_path, dbx):
    """Uploada datoteku na Dropbox"""
    try:
        with open(local_path, "rb") as f:
            dbx.files_upload(
                f.read(),
                dropbox_path,
                mode=dropbox.files.WriteMode.overwrite
            )
        return True
    except Exception as e:
        print(f"  ✗ Greška: {e}")
        return False

def main():
    print("="*60)
    print(f"DROPBOX UPLOAD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Provjeri postoji li token
    if DROPBOX_TOKEN == "your_dropbox_access_token_here":
        print("❌ GREŠKA: Nisi postavio DROPBOX_TOKEN!")
        print("   Otvori upload_to_dropbox.py i zamijeni token.")
        return
    
    # Provjeri postoji li lokalni folder
    if not os.path.exists(LOCAL_DIR):
        print(f"❌ GREŠKA: Folder {LOCAL_DIR} ne postoji!")
        return
    
    # Inicijaliziraj Dropbox
    try:
        dbx = dropbox.Dropbox(DROPBOX_TOKEN)
        # Test connection
        dbx.users_get_current_account()
        print("✓ Dropbox konekcija uspješna\n")
    except Exception as e:
        print(f"❌ GREŠKA: Ne mogu se spojiti na Dropbox!")
        print(f"   {e}")
        return
    
    # Upload CSV datoteka
    uploaded = 0
    failed = 0
    
    for filename in CSV_FILES:
        local_path = os.path.join(LOCAL_DIR, filename)
        dropbox_path = f"{DROPBOX_DIR}/{filename}"
        
        if not os.path.exists(local_path):
            print(f"⚠ {filename} - ne postoji lokalno, preskačem")
            failed += 1
            continue
        
        # Dobavi veličinu datoteke
        file_size = os.path.getsize(local_path)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"📤 Uploadam {filename} ({file_size_mb:.2f} MB)...", end=" ")
        
        if upload_to_dropbox(local_path, dropbox_path, dbx):
            print("✓")
            uploaded += 1
        else:
            failed += 1
    
    # Statistika
    print("\n" + "="*60)
    print(f"ZAVRŠENO:")
    print(f"  ✓ Uspješno: {uploaded}/{len(CSV_FILES)}")
    if failed > 0:
        print(f"  ✗ Neuspješno: {failed}/{len(CSV_FILES)}")
    print("="*60)
    
    # Log za Task Scheduler
    log_file = os.path.join(LOCAL_DIR, "upload_log.txt")
    with open(log_file, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"{timestamp} - Uploaded: {uploaded}/{len(CSV_FILES)}, Failed: {failed}\n")

if __name__ == "__main__":
    main()
