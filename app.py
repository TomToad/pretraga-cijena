import streamlit as st
import pandas as pd
import re
import os
from io import BytesIO
import dropbox
from dropbox.exceptions import AuthError

# ----------------- KONFIGURACIJA -----------------
st.set_page_config(
    page_title="Pretraga Cijena | Price Finder",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS za tamni elegantni dizajn
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Work+Sans:wght@400;500;600&display=swap');
    
    /* Global Styles - DARK THEME */
    .main {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
    }
    
    /* Override Streamlit defaults */
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
    }
    
    /* Header */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
    }
    
    .main-title {
        font-family: 'Playfair Display', serif;
        font-size: 3rem;
        font-weight: 700;
        color: white;
        margin: 0;
        text-align: center;
        letter-spacing: -1px;
    }
    
    .subtitle {
        font-family: 'Work Sans', sans-serif;
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.9);
        text-align: center;
        margin-top: 0.5rem;
    }
    
    /* Section Headers */
    h3 {
        font-family: 'Work Sans', sans-serif;
        color: #e2e8f0 !important;
        font-weight: 600;
    }
    
    /* Input Section */
    .stTextInput > div > div > input {
        background-color: #1e1e3f;
        border-radius: 12px;
        border: 2px solid #2d3748;
        color: #e2e8f0;
        padding: 0.75rem 1rem;
        font-family: 'Work Sans', sans-serif;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3);
        background-color: #252547;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #718096;
    }
    
    /* Input Labels */
    .stTextInput > label {
        color: #cbd5e0 !important;
        font-family: 'Work Sans', sans-serif;
        font-weight: 500;
    }
    
    /* Button */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-family: 'Work Sans', sans-serif;
        font-weight: 600;
        font-size: 1.1rem;
        padding: 0.75rem 3rem;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.5);
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* Results Section */
    .results-header {
        font-family: 'Playfair Display', serif;
        font-size: 2rem;
        color: #e2e8f0;
        margin: 2rem 0 1rem 0;
        font-weight: 700;
    }
    
    .stats-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #1e1e3f 0%, #252547 100%);
        padding: 1.5rem;
        border-radius: 15px;
        flex: 1;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        border-left: 4px solid #667eea;
    }
    
    .stat-value {
        font-family: 'Playfair Display', serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #667eea;
        margin: 0;
    }
    
    .stat-label {
        font-family: 'Work Sans', sans-serif;
        font-size: 0.9rem;
        color: #a0aec0;
        margin-top: 0.25rem;
    }
    
    /* Table Styling */
    .stDataFrame {
        background-color: #1e1e3f;
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Info Box */
    .info-box {
        background: linear-gradient(135deg, #1e1e3f 0%, #2d2d5f 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 4px solid #667eea;
        margin-bottom: 2rem;
    }
    
    .info-box p {
        font-family: 'Work Sans', sans-serif;
        color: #cbd5e0;
        margin: 0;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    .info-box code {
        background-color: rgba(102, 126, 234, 0.2);
        color: #a5b4fc;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
    }
    
    /* Download Button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        font-family: 'Work Sans', sans-serif;
        font-weight: 600;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        box-shadow: 0 4px 15px rgba(72, 187, 120, 0.4);
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(72, 187, 120, 0.5);
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background-color: #667eea;
    }
    
    /* Warnings and Errors */
    .stAlert {
        background-color: #1e1e3f;
        color: #e2e8f0;
        border-radius: 12px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #718096;
        font-family: 'Work Sans', sans-serif;
        font-size: 0.9rem;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- KONFIGURACIJA DUĆANA -----------------
DUCANI_CONFIG = {
    "Plodine": {
        "filename": "plodine_jucer.csv",
        "separator": ";",
        "encoding": "windows-1250",
        "columns": {
            "naziv": "Naziv proizvoda",
            "sifra": "Sifra proizvoda",
            "barkod": "Barkod",
            "kategorija": "Kategorija proizvoda",
            "maloprodajna": "Maloprodajna cijena",
            "akcijska": "MPC za vrijeme posebnog oblika prodaje",
            "jedinica": "Jedinica mjere"
        },
        "price_logic": "fillna"
    },
    "Eurospin": {
        "filename": "eurospin_jucer.csv",
        "separator": ";",
        "encoding": "windows-1250",
        "columns": {
            "naziv": "NAZIV_PROIZVODA",
            "sifra": "ŠIFRA_PROIZVODA",
            "barkod": "BARKOD",
            "kategorija": "KATEGORIJA_PROIZVODA",
            "maloprodajna": "MALOPROD.CIJENA(EUR)",
            "akcijska": "MPC_POSEB.OBLIK_PROD",
            "jedinica": "JEDINICA_MJERE"
        },
        "price_logic": "eurospin"
    },
    "Kaufland": {
        "filename": "kaufland_jucer.csv",
        "separator": "\t",
        "encoding": "utf-8",
        "columns": {
            "naziv": "naziv proizvoda",
            "sifra": "šifra proizvoda",
            "barkod": "barkod",
            "kategorija": "kategorija proizvoda",
            "maloprodajna": None,
            "akcijska": None,
            "jedinica": "jedinica mjere"
        },
        "price_logic": "fillna"
    },
    "Konzum": {
        "filename": "konzum_jucer.csv",
        "separator": ",",
        "encoding": "utf-8",
        "columns": {
            "naziv": "NAZIV PROIZVODA",
            "sifra": "ŠIFRA PROIZVODA",
            "barkod": "BARKOD",
            "kategorija": "KATEGORIJA PROIZVODA",
            "maloprodajna": "MALOPRODAJNA CIJENA",
            "akcijska": "MPC ZA VRIJEME POSEBNOG OBLIKA PRODAJE",
            "jedinica": "JEDINICA MJERE"
        },
        "price_logic": "fillna"
    },
    "Lidl": {
        "filename": "lidl_jucer.csv",
        "separator": ",",
        "encoding": "windows-1250",
        "columns": {
            "naziv": "NAZIV",
            "sifra": "ŠIFRA",
            "barkod": "BARKOD",
            "kategorija": "KATEGORIJA_PROIZVODA",
            "maloprodajna": "MALOPRODAJNA_CIJENA",
            "akcijska": "MPC_ZA_VRIJEME_POSEBNOG_OBLIKA_PRODAJE",
            "jedinica": "JEDINICA_MJERE"
        },
        "price_logic": "fillna"
    },
    "Spar": {
        "filename": "spar_jucer.csv",
        "separator": ";",
        "encoding": "windows-1250",
        "columns": {
            "naziv": "naziv",
            "sifra": "šifra",
            "barkod": "barkod",
            "kategorija": "kategorija proizvoda",
            "maloprodajna": "MPC (EUR)",
            "akcijska": "MPC za vrijeme posebnog oblika prodaje (EUR)",
            "jedinica": "jedinica mjere"
        },
        "price_logic": "spar"
    }
}

# ----------------- HELPER FUNKCIJE -----------------

def wildcard_to_regex(pattern):
    """Pretvara wildcard pattern (* i ?) u regex"""
    pattern = re.escape(pattern)
    pattern = pattern.replace(r'\*', '.*')
    pattern = pattern.replace(r'\?', '.')
    pattern = '^' + pattern
    return pattern

def convert_price(val):
    """Konvertuje cijenu u float"""
    if pd.isna(val) or val == '':
        return None
    try:
        return float(str(val).replace(',', '.').replace(' ', ''))
    except:
        return None

@st.cache_data(ttl=3600)
def load_csv_from_dropbox(filename):
    try:
        dbx = dropbox.Dropbox(st.secrets["DROPBOX_ACCESS_TOKEN"])

        # 🔍 Debug – vidi što Dropbox stvarno vidi
        try:
            folder = dbx.files_list_folder("")
            available = [e.name for e in folder.entries]
            st.info(f"📂 Dropbox root sadrži: {available}")
        except Exception:
            pass

        path = f"/Cjenici_jucer/{filename}"

        metadata, response = dbx.files_download(path)
        return response.content

    except AuthError:
        st.error("❌ Dropbox token nije valjan ili je istekao.")
        return None

    except dropbox.exceptions.ApiError as e:
        if "not_found" in str(e):
            st.error(f"❌ Datoteka ne postoji: {filename}")
        else:
            st.error(f"❌ Dropbox greška: {e}")
        return None

    except Exception as e:
        st.error(f"❌ Neočekivana greška: {e}")
        return None

@st.cache_data(ttl=3600)
def load_csv_local(filepath, separator, encoding):
    """Učitava CSV s lokalnog diska (za development)"""
    try:
        if not os.path.exists(filepath):
            return None
        df = pd.read_csv(filepath, sep=separator, encoding=encoding, on_bad_lines='skip')
        return df
    except Exception as e:
        st.error(f"❌ Greška: {str(e)}")
        return None

def pretrazi_ducan(ducan_naziv, config, pojmovi, use_dropbox=False):
    """Pretražuje cjenik jednog dućana"""
    rezultati = []
    
    try:
        # Učitaj CSV
        if use_dropbox:
            csv_content = load_csv_from_dropbox(config["filename"])
            if csv_content is None:
                return rezultati
            from io import StringIO
            df = pd.read_csv(
                StringIO(csv_content.decode(config["encoding"])),
                sep=config["separator"],
                on_bad_lines='skip'
            )
        else:
            # Lokalni mod (za testiranje)
            local_path = os.path.join("data", config["filename"])
            df = load_csv_local(local_path, config["separator"], config["encoding"])
            if df is None:
                return rezultati
        
        df.columns = df.columns.str.strip()
        
        # Za Kaufland - pronađi kolonu sa "maloprod"
        if config["columns"]["maloprodajna"] is None:
            cijena_cols = [col for col in df.columns if "maloprod" in col.lower()]
            if cijena_cols:
                config["columns"]["maloprodajna"] = cijena_cols[0]
        
        # Pripremi cijene
        df[config["columns"]["maloprodajna"]] = df[config["columns"]["maloprodajna"]].apply(convert_price)
        
        if config["columns"]["akcijska"]:
            df[config["columns"]["akcijska"]] = df[config["columns"]["akcijska"]].apply(convert_price)
        
        # Odaberi cijenu prema logici
        if config["price_logic"] == "eurospin":
            df["CIJENA"] = df[[config["columns"]["maloprodajna"], config["columns"]["akcijska"]]].apply(
                lambda x: x[config["columns"]["akcijska"]] if x[config["columns"]["akcijska"]] and x[config["columns"]["akcijska"]] > 0 
                else x[config["columns"]["maloprodajna"]], 
                axis=1
            )
        elif config["price_logic"] == "spar":
            df["CIJENA"] = df[[config["columns"]["maloprodajna"], config["columns"]["akcijska"]]].apply(
                lambda x: x[config["columns"]["akcijska"]] 
                if pd.notna(x[config["columns"]["akcijska"]]) and x[config["columns"]["akcijska"]] > 0 
                else x[config["columns"]["maloprodajna"]], 
                axis=1
            )
        else:
            df["CIJENA"] = df[config["columns"]["maloprodajna"]].fillna(
                df[config["columns"]["akcijska"]] if config["columns"]["akcijska"] else 0
            )
        
        # Pretraga po pojmovima s wildcard podrškom
        for pojam_original in pojmovi:
            if not pojam_original or pojam_original.strip() == "":
                continue
                
            regex_pattern = wildcard_to_regex(pojam_original.lower())
            mask = df[config["columns"]["naziv"]].astype(str).str.lower().str.contains(regex_pattern, na=False, regex=True)
            pronadeni = df[mask].copy()
            
            for _, row in pronadeni.iterrows():
                jedinica = row.get(config["columns"]["jedinica"], "") if config["columns"]["jedinica"] else ""
                barkod = row.get(config["columns"]["barkod"], "") if config["columns"]["barkod"] else ""
                
                rezultati.append({
                    "Trgovački lanac": ducan_naziv,
                    "Traženi pojam": pojam_original,
                    "Šifra": row[config["columns"]["sifra"]],
                    "Barkod": str(barkod).replace('.0', ''),
                    "Naziv proizvoda": row[config["columns"]["naziv"]],
                    "Cijena (€)": row["CIJENA"],
                    "Jedinica mjere": jedinica,
                    "Kategorija": row[config["columns"]["kategorija"]]
                })
        
        return rezultati
        
    except Exception as e:
        st.warning(f"⚠️ {ducan_naziv}: {str(e)}")
        return rezultati

def create_excel_download(df):
    """Kreira Excel file za download"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Rezultati')
        workbook = writer.book
        worksheet = writer.sheets['Rezultati']
        
        # Formatiranje
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#667eea',
            'font_color': 'white',
            'border': 1
        })
        
        # Primijeni header format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Auto-width za kolone
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_len)
    
    return output.getvalue()

# ----------------- MAIN APP -----------------

def main():
    # Header
    st.markdown("""
    <div class="header-container">
        <h1 class="main-title">🛒 Pretraga Cijena</h1>
        <p class="subtitle">Pronađi najbolje cijene u trgovačkim lancima u Zaprešiću</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Info box
    st.markdown("""
    <div class="info-box">
        <p style="font-size: 0.9rem;"><strong>💡 Pretraga proizvoda:</strong></p>
        <p style="margin-top: 0.5rem; font-size: 0.85rem;">
        Unesite pojmove koje pretražujete u predviđena polja (max 6)<br>
        Sustav traži pojam od početka naziva proizvoda.<br>
        • Npr. ako unesete pojam <code>mlijeko</code> pronaći će "mlijeko dukat" ali ne i "dukat mlijeko"
        </p>
        <p style="margin-top: 0.5rem; font-size: 0.85rem;">
        <strong>Wildcard znakovi:</strong><br>
        • <code>*</code> zamjenjuje bilo koji broj znakova<br>
        • <code>?</code> zamjenjuje točno jedan znak
        </p>
        <p style="margin-top: 0.5rem; font-size: 0.85rem;">
        <strong>Primjeri:</strong><br>
        • <code>*mlijeko*</code> → pronalazi sve što bilo gdje u nazivu ima "mlijeko"<br>
        • <code>sir ?0%</code> → "sir 20%", "sir 30%"
        </p>
        <p style="margin-top: 0.5rem; font-size: 0.85rem;">
        <strong>💡 Savjet:</strong> Ako niste sigurni, uvijek koristite <code>*</code> prije i poslije pojma pretrage (npr. <code>*mlijeko*</code>)
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Input sekcija
    st.markdown("### 🔍 Unesite pojmove za pretragu")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pojam1 = st.text_input("Pojam 1", placeholder="npr. *mlijeko*", key="pojam1")
        pojam2 = st.text_input("Pojam 2", placeholder="npr. jogurt", key="pojam2")
        pojam3 = st.text_input("Pojam 3", placeholder="npr. sir ?0%", key="pojam3")
    
    with col2:
        pojam4 = st.text_input("Pojam 4", placeholder="", key="pojam4")
        pojam5 = st.text_input("Pojam 5", placeholder="", key="pojam5")
        pojam6 = st.text_input("Pojam 6", placeholder="", key="pojam6")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Gumb za pretragu
    if st.button("🔎 Pretraži cijene", use_container_width=True):
        pojmovi = [p.strip() for p in [pojam1, pojam2, pojam3, pojam4, pojam5, pojam6] if p and p.strip()]
        
        if not pojmovi:
            st.error("❌ Molimo unesite barem jedan pojam za pretragu!")
            return
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Provjeri je li Dropbox konfiguriran
        use_dropbox = "DROPBOX_ACCESS_TOKEN" in st.secrets
        
        if not use_dropbox:
            st.warning("⚠️ Dropbox nije konfiguriran. Koristim lokalne CSV datoteke za testiranje.")
        
        svi_rezultati = []
        total_ducani = len(DUCANI_CONFIG)
        
        # Pretraga
        for idx, (ducan_naziv, config) in enumerate(DUCANI_CONFIG.items()):
            status_text.text(f"Pretražujem {ducan_naziv}...")
            rezultati = pretrazi_ducan(ducan_naziv, config, pojmovi, use_dropbox)
            svi_rezultati.extend(rezultati)
            progress_bar.progress((idx + 1) / total_ducani)
        
        progress_bar.empty()
        status_text.empty()
        
        if not svi_rezultati:
            st.warning("😕 Nažalost, nisu pronađeni rezultati za unesene pojmove.")
            return
        
        # Kreiraj DataFrame
        df_rezultati = pd.DataFrame(svi_rezultati)
        
        # Deduplikacija
        df_rezultati = (
            df_rezultati
            .sort_values("Cijena (€)")
            .drop_duplicates(subset=["Trgovački lanac", "Šifra"], keep="first")
            .reset_index(drop=True)
        )
        
        # Sortiraj po cijeni (od najjeftinije)
        df_rezultati = df_rezultati.sort_values("Cijena (€)").reset_index(drop=True)
        
        # Statistike
        st.markdown('<h2 class="results-header">📊 Rezultati pretrage</h2>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-value">{len(df_rezultati)}</p>
                <p class="stat-label">Pronađenih artikala</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            min_cijena = df_rezultati["Cijena (€)"].min()
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-value">€{min_cijena:.2f}</p>
                <p class="stat-label">Najniža cijena</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            broj_ducana = df_rezultati["Trgovački lanac"].nunique()
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-value">{broj_ducana}</p>
                <p class="stat-label">Trgovačkih lanaca</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Tablica rezultata
        st.markdown("### 🏆 Najbolje ponude (sortirano po cijeni)")
        
        # Formatiranje cijena u tablici
        df_display = df_rezultati.copy()
        df_display["Cijena (€)"] = df_display["Cijena (€)"].apply(lambda x: f"€{x:.2f}" if pd.notna(x) else "")
        
        st.dataframe(
            df_display,
            use_container_width=True,
            height=500,
            hide_index=True
        )
        
        # Download gumb
        st.markdown("### 💾 Preuzmi rezultate")
        excel_data = create_excel_download(df_rezultati)
        
        st.download_button(
            label="📥 Preuzmi Excel tablicu",
            data=excel_data,
            file_name="rezultati_pretrage_cijena.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>Izrađeno uz pomoć AI | Cijene se ažuriraju pon-sub u 8:20</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
