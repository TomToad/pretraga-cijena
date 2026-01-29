# 🛒 Pretraga Cijena - Price Finder

Moderna web aplikacija za pretragu i usporedbu cijena u hrvatskim trgovačkim lancima.

## 🌟 Značajke

- ✅ Pretraga u 6 trgovačkih lanaca: Plodine, Eurospin, Kaufland, Konzum, Lidl, Spar
- ✅ Wildcard pretraga (`*` i `?`)
- ✅ Automatsko sortiranje po cijeni (od najjeftinije)
- ✅ Export rezultata u Excel
- ✅ Responsive dizajn
- ✅ Dnevno ažuriranje cijena s Dropboxa

## 📋 Preduvjeti

- Python 3.8+
- Dropbox Account (za automatsko ažuriranje cijena)

## 🚀 Lokalno pokretanje (testiranje)

### 1. Instalacija

```bash
# Kloniraj repozitorij
git clone <your-repo-url>
cd pretraga-cijena

# Instaliraj dependencies
pip install -r requirements.txt
```

### 2. Priprema podataka (lokalno testiranje bez Dropboxa)

Kreiraj `data/` folder i stavi CSV cjenike:

```
pretraga-cijena/
├── app.py
├── requirements.txt
├── data/                    # Kreiraj ovaj folder
│   ├── plodine_jucer.csv
│   ├── eurospin_jucer.csv
│   ├── kaufland_jucer.csv
│   ├── konzum_jucer.csv
│   ├── lidl_jucer.csv
│   └── spar_jucer.csv
```

### 3. Pokreni aplikaciju

```bash
streamlit run app.py
```

Otvori browser na `http://localhost:8501`

---

## ☁️ Deploy na Streamlit Cloud

### Korak 1: Pripremi Dropbox

#### 1.1 Kreiraj Dropbox App

1. Idi na: https://www.dropbox.com/developers/apps
2. Klikni **"Create app"**
3. Odaberi:
   - **Scoped access**
   - **Full Dropbox** (ili App folder)
   - Daj ime: `Pretraga-Cijena-App`
4. Klikni **Create app**

#### 1.2 Konfiguriraj Permissions

1. U app postavkama idi na **Permissions** tab
2. Omogući: `files.content.read`
3. Spremi promjene

#### 1.3 Generiraj Access Token

1. Idi na **Settings** tab
2. Scroll do **"Generated access token"**
3. Klikni **"Generate"**
4. **Kopiraj token** (čuvaj ga sigurnim!)

#### 1.4 Uploadaj CSV cjenike

Kreiraj folder `/Cjenici_jucer/` u svom Dropboxu i uploadaj:
- `plodine_jucer.csv`
- `eurospin_jucer.csv`
- `kaufland_jucer.csv`
- `konzum_jucer.csv`
- `lidl_jucer.csv`
- `spar_jucer.csv`

**Struktura:**
```
Dropbox/
└── Cjenici_jucer/
    ├── plodine_jucer.csv
    ├── eurospin_jucer.csv
    ├── kaufland_jucer.csv
    ├── konzum_jucer.csv
    ├── lidl_jucer.csv
    └── spar_jucer.csv
```

---

### Korak 2: Pripremi GitHub repozitorij

#### 2.1 Kreiraj GitHub repo

1. Idi na: https://github.com/new
2. Ime: `pretraga-cijena` (ili bilo koje)
3. **Javno** (Public)
4. Kreiraj repo

#### 2.2 Uploadaj kod

```bash
# Inicijaliziraj git
git init

# Dodaj .gitignore
echo "data/
.streamlit/secrets.toml
*.pyc
__pycache__/" > .gitignore

# Commit
git add .
git commit -m "Initial commit"

# Push na GitHub
git remote add origin https://github.com/YOUR_USERNAME/pretraga-cijena.git
git branch -M main
git push -u origin main
```

**VAŽNO:** Nemoj commitati `.streamlit/secrets.toml` - to ide samo na Streamlit Cloud!

---

### Korak 3: Deploy na Streamlit Cloud

#### 3.1 Prijavi se na Streamlit Cloud

1. Idi na: https://share.streamlit.io/
2. Prijavi se s GitHub accountom

#### 3.2 Kreiraj novu app

1. Klikni **"New app"**
2. Odaberi:
   - **Repository:** `your-username/pretraga-cijena`
   - **Branch:** `main`
   - **Main file path:** `app.py`
3. Klikni **"Advanced settings"**

#### 3.3 Dodaj Dropbox token (SECRETS)

U **"Secrets"** sekciji, upiši:

```toml
DROPBOX_ACCESS_TOKEN = "tvoj_dropbox_token_ovdje"
```

**Zamijeni `tvoj_dropbox_token_ovdje` s tokenom iz Koraka 1.3!**

#### 3.4 Deploy

1. Klikni **"Deploy!"**
2. Pričekaj 2-3 minute
3. Aplikacija je live! 🎉

URL će biti: `https://your-username-pretraga-cijena.streamlit.app`

---

## 🔄 Automatsko ažuriranje cijena

### Skripta za upload na Dropbox

Kreiraj `upload_to_dropbox.py`:

```python
import dropbox
import os

# Tvoj Dropbox Access Token
DROPBOX_TOKEN = "tvoj_token"

# Lokalni folder s cjenicima
LOCAL_DIR = r"D:\Py_skripte\Cjenici_jucer"

# Dropbox folder
DROPBOX_DIR = "/Cjenici_jucer"

dbx = dropbox.Dropbox(DROPBOX_TOKEN)

for filename in os.listdir(LOCAL_DIR):
    if filename.endswith(".csv"):
        local_path = os.path.join(LOCAL_DIR, filename)
        dropbox_path = f"{DROPBOX_DIR}/{filename}"
        
        with open(local_path, "rb") as f:
            print(f"Uploadam {filename}...")
            dbx.files_upload(
                f.read(), 
                dropbox_path, 
                mode=dropbox.files.WriteMode.overwrite
            )
            print(f"✓ {filename} uploadan!")

print("\n✓ Svi cjenici su uploadani!")
```

### Pokreni dnevno u 8:20

**Windows Task Scheduler:**
1. Otvori Task Scheduler
2. Create Basic Task
3. Trigger: Daily, 8:20 AM
4. Action: Start a program
   - Program: `python`
   - Arguments: `"C:\path\to\upload_to_dropbox.py"`

**Linux cron:**
```bash
20 8 * * * /usr/bin/python3 /path/to/upload_to_dropbox.py
```

---

## 🎨 Wildcard pretraga

Aplikacija podržava wildcards u pretrazi:

| Wildcard | Značenje | Primjer | Pronalazi |
|----------|----------|---------|-----------|
| `*` | Bilo koji broj znakova | `mlijeko*` | "mlijeko dukat", "mlijeko meggle 1L" |
| `?` | Točno jedan znak | `sir ?0%` | "sir 20%", "sir 30%" |

**Primjeri:**
- `*čokolada` → sve što završava na "čokolada"
- `jogurt*vocal` → "jogurt vocal", "jogurt čvrsti vocal"
- `kava ???` → "kava illy", "kava bck"

---

## 📊 Struktura CSV cjenika

Aplikacija očekuje sljedeće kolone (nazivi se razlikuju po dućanu):

| Podatak | Plodine | Eurospin | Kaufland |
|---------|---------|----------|----------|
| Naziv | "Naziv proizvoda" | "NAZIV_PROIZVODA" | "naziv proizvoda" |
| Šifra | "Sifra proizvoda" | "ŠIFRA_PROIZVODA" | "šifra proizvoda" |
| Barkod | "Barkod" | "BARKOD" | "barkod" |
| Cijena | "Maloprodajna cijena" | "MALOPROD.CIJENA(EUR)" | "maloprodajna cijena..." |

---

## 🛠️ Troubleshooting

### Aplikacija ne učitava CSV-ove

**Problem:** `❌ Greška pri učitavanju plodine_jucer.csv`

**Rješenje:**
1. Provjeri je li Dropbox token ispravan
2. Provjeri strukturu foldera na Dropboxu (`/Cjenici_jucer/`)
3. Provjeri permissions na Dropbox app-u (`files.content.read`)

### Encoding problemi

Ako se pojave čudni znakovi (Ã, Å¡, Ä‡):
- Provjeri encoding u `DUCANI_CONFIG` u `app.py`
- Plodine/Eurospin/Lidl: `windows-1250`
- Kaufland/Konzum: `utf-8`

### Streamlit Cloud ne učitava app

1. Provjeri je li `requirements.txt` ispravan
2. Provjeri logs na Streamlit Cloud dashboardu
3. Provjeri je li `DROPBOX_ACCESS_TOKEN` dodan u Secrets

---

## 📝 License

MIT License - slobodno koristi i modificiraj!

---

## 🤝 Kontakt

Za pitanja i probleme, otvori Issue na GitHubu.

---

**Made with ❤️ in Croatia**
