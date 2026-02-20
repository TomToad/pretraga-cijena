import streamlit as st
import pandas as pd
import re
from io import BytesIO, StringIO
import dropbox
from dropbox.exceptions import AuthError

# ──────────────────────────────────────────────────────────────────────
# KONFIGURACIJA
# ──────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Pretraga Cijena | Price Finder",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        color: #e0e0e0;
    }
    
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 600;
    }
    
    .info-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .info-box h3 {
        color: white !important;
        margin-top: 0;
    }
    
    .info-box ul {
        color: #f0f0f0;
        line-height: 1.8;
    }
    
    .info-box code {
        background: rgba(255, 255, 255, 0.2);
        padding: 2px 6px;
        border-radius: 4px;
        color: #fff;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #43cea2 0%, #185a9d 100%);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .stat-number {
        font-size: 2.5em;
        font-weight: bold;
        color: white;
        margin: 10px 0;
    }
    
    .stat-label {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1em;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
    }
    
    .scanner-btn {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
    }
    
    .stTextInput > div > div > input {
        background-color: #2d2d44;
        color: #e0e0e0;
        border: 2px solid #3d3d54;
        border-radius: 8px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
    }
    
    .footer {
        text-align: center;
        padding: 20px;
        color: #999;
        margin-top: 40px;
        border-top: 1px solid #3d3d54;
    }
    
    .header-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .header-title {
        font-size: 2.5em;
        font-weight: bold;
        color: white;
        margin: 0;
    }
    
    .header-subtitle {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1em;
        margin-top: 10px;
    }
    
    .barcode-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────
# KONFIGURACIJA DUĆANA
# ──────────────────────────────────────────────────────────────────────

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

# ──────────────────────────────────────────────────────────────────────
# HELPER FUNKCIJE
# ──────────────────────────────────────────────────────────────────────

def wildcard_to_regex(pattern):
    """Pretvara wildcard pattern (* i ?) u regex"""
    pattern = re.escape(pattern.lower())
    pattern = pattern.replace(r'\*', '.*').replace(r'\?', '.')
    return '^' + pattern

def convert_price(val):
    """Konvertira string cijene u float"""
    if pd.isna(val) or val == '':
        return None
    try:
        cleaned = str(val).replace(',', '.').replace(' ', '').strip()
        if cleaned == '':
            return None
        return float(cleaned)
    except:
        return None

@st.cache_data(ttl=3600)
def load_csv_from_dropbox(filename):
    """Učitava CSV datoteku s Dropboxa"""
    try:
        dbx = dropbox.Dropbox(
            app_key=st.secrets["DROPBOX_APP_KEY"],
            app_secret=st.secrets["DROPBOX_APP_SECRET"],
            oauth2_refresh_token=st.secrets["DROPBOX_REFRESH_TOKEN"]
        )
        _, response = dbx.files_download(f"/{filename}")
        return response.content
    except AuthError as e:
        st.error(f"Dropbox autentikacija nije uspjela: {e}")
        return None
    except Exception as e:
        st.error(f"Greška pri učitavanju {filename} s Dropboxa: {e}")
        return None

def determine_final_price(row, config, debug_mode=False):
    """Određuje finalnu cijenu proizvoda"""
    maloprodajna_col = config["columns"]["maloprodajna"]
    akcijska_col = config["columns"]["akcijska"]
    
    maloprodajna = row.get(maloprodajna_col)
    akcijska = row.get(akcijska_col) if akcijska_col else None
    
    if pd.notna(akcijska) and akcijska > 0:
        return akcijska
    return maloprodajna

def pretrazi_ducan(ducan_naziv, config, pojmovi=None, barkod=None, debug_mode=False):
    """Pretražuje jedan dućan"""
    rezultati = []
    
    try:
        content = load_csv_from_dropbox(config["filename"])
        if content is None:
            return rezultati
        
        df = pd.read_csv(
            StringIO(content.decode(config["encoding"])),
            sep=config["separator"],
            on_bad_lines='skip'
        )
        
        df.columns = df.columns.str.strip()
        
        if config["columns"]["maloprodajna"] is None:
            cijene = [c for c in df.columns if "maloprod" in c.lower()]
            if cijene:
                config["columns"]["maloprodajna"] = cijene[0]
            else:
                return rezultati
        
        df[config["columns"]["maloprodajna"]] = df[config["columns"]["maloprodajna"]].apply(convert_price)
        
        if config["columns"]["akcijska"]:
            df[config["columns"]["akcijska"]] = df[config["columns"]["akcijska"]].apply(convert_price)
        
        df["CIJENA"] = df.apply(
            lambda row: determine_final_price(row, config, debug_mode),
            axis=1
        )
        
        if barkod:
            barkod_clean = barkod.strip()
            df[config["columns"]["barkod"]] = df[config["columns"]["barkod"]].astype(str).str.replace('.0', '', regex=False)
            mask = df[config["columns"]["barkod"]] == barkod_clean
            
            for _, row in df[mask].iterrows():
                rezultati.append({
                    "Trgovački lanac": ducan_naziv,
                    "Traženi pojam": f"🔢 {barkod_clean}",
                    "Šifra": row.get(config["columns"]["sifra"], ""),
                    "Barkod": str(row.get(config["columns"]["barkod"], "")).replace('.0', ''),
                    "Naziv proizvoda": row[config["columns"]["naziv"]],
                    "Cijena (€)": row["CIJENA"],
                    "Jedinica mjere": row.get(config["columns"]["jedinica"], ""),
                    "Kategorija": row.get(config["columns"]["kategorija"], "")
                })
        
        if pojmovi:
            for pojam in pojmovi:
                if not pojam.strip():
                    continue
                
                regex = wildcard_to_regex(pojam)
                mask = df[config["columns"]["naziv"]].astype(str).str.lower().str.contains(
                    regex, na=False, regex=True
                )
                
                for _, row in df[mask].iterrows():
                    rezultati.append({
                        "Trgovački lanac": ducan_naziv,
                        "Traženi pojam": pojam,
                        "Šifra": row.get(config["columns"]["sifra"], ""),
                        "Barkod": str(row.get(config["columns"]["barkod"], "")).replace('.0', ''),
                        "Naziv proizvoda": row[config["columns"]["naziv"]],
                        "Cijena (€)": row["CIJENA"],
                        "Jedinica mjere": row.get(config["columns"]["jedinica"], ""),
                        "Kategorija": row.get(config["columns"]["kategorija"], "")
                    })
        
        return rezultati
        
    except Exception as e:
        st.error(f"{ducan_naziv}: {str(e)}")
        return rezultati

def create_excel_download(df):
    """Kreira Excel datoteku"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Rezultati')
        ws = writer.sheets['Rezultati']
        
        header_fmt = writer.book.add_format({
            'bold': True,
            'bg_color': '#667eea',
            'font_color': 'white',
            'border': 1
        })
        
        for col_num, value in enumerate(df.columns):
            ws.write(0, col_num, value, header_fmt)
        
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            ws.set_column(i, i, max_len)
    
    return output.getvalue()

# ──────────────────────────────────────────────────────────────────────
# GLAVNI DIO APLIKACIJE
# ──────────────────────────────────────────────────────────────────────

def main():
    # Initialize session state
    if 'barkod_value' not in st.session_state:
        st.session_state.barkod_value = ''
    
    # Check for barcode in URL parameters
    query_params = st.query_params
    if 'barcode' in query_params:
        st.session_state.barkod_value = query_params['barcode']
        # Clear the parameter
        st.query_params.clear()
    
    st.markdown("""
<div class="header-banner">
    <div class="header-title">🛒 Pretraga Cijena</div>
    <div class="header-subtitle">
        Najbolje cijene u trgovačkim lancima – Zaprešić<br>
        (samo kategorije: hrana, piće, kozmetika, sredstva za čišćenje, toaletne potrepštine i proizvodi za kućanstvo)
    </div>
</div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        debug_mode = st.checkbox("🐛 Debug mode", value=False)
    
    st.markdown(r"""
<div class="info-box">
    <h3>🔍 Kako pretraživati</h3>
    <ul>
        <li><strong>Do 6 pojmova</strong> ili <strong>1 barkod</strong></li>
        <li><strong>Bez *</strong> → traži na početku naziva</li>
        <li><strong>Bilo gdje u nazivu</strong> → koristi *</li>
    </ul>
    <p><strong>💡 Brzi trikovi:</strong> <code>*kava*</code>, <code>*mlijeko 3.5*</code></p>
</div>
    """, unsafe_allow_html=True)
    
    # Barkod pretraga
    st.markdown('<div class="barcode-box">', unsafe_allow_html=True)
    st.markdown("### 🔢 Pretraga po barkodu")
    
    barkod_input = st.text_input(
        "Unesite ili skenirajte barkod proizvoda",
        value=st.session_state.barkod_value,
        placeholder="npr. 3017620422003",
        key="barkod"
    )
    
    # Scanner button - opens external scanner page
    # Get current URL for return
    scanner_url = "barcode_scanner.html"  # You'll need to host this somewhere
    current_url = "your-streamlit-app-url"  # Replace with actual Streamlit app URL
    
    st.markdown(f"""
    <a href="{scanner_url}?return={current_url}" target="_blank" style="text-decoration: none;">
        <button style="
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            font-size: 1em;
            width: 100%;
            cursor: pointer;
            transition: all 0.3s;
        ">
            📷 Skeniraj Barkod Kamerom (mobitel)
        </button>
    </a>
    <p style="text-align: center; margin-top: 10px; opacity: 0.8; font-size: 0.9em;">
        Gumb otvara scanner u novom tabu
    </p>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### 🔍 Pretraga po nazivu proizvoda")
    
    col1, col2 = st.columns(2)
    
    with col1:
        p1 = st.text_input("Pojam 1", placeholder="npr. mlijeko ili *mlijeko*", key="p1")
        p2 = st.text_input("Pojam 2", placeholder="npr. nutella ili *nutella*", key="p2")
        p3 = st.text_input("Pojam 3", placeholder="npr. jogurt ili sir ?0%", key="p3")
    
    with col2:
        p4 = st.text_input("Pojam 4", placeholder="npr. kava ili *kava*", key="p4")
        p5 = st.text_input("Pojam 5", key="p5")
        p6 = st.text_input("Pojam 6", key="p6")
    
    if st.button("🔎 Pretraži cijene", use_container_width=True):
        pojmovi = [p.strip() for p in [p1, p2, p3, p4, p5, p6] if p and p.strip()]
        barkod = barkod_input.strip() if barkod_input else None
        
        if not pojmovi and not barkod:
            st.error("Unesite barem jedan pojam ili barkod za pretragu.")
            return
        
        if pojmovi and barkod:
            st.warning("⚠️ Koristim samo barkod pretragu.")
            pojmovi = []
        
        progress = st.progress(0)
        status = st.empty()
        svi_rez = []
        
        total = len(DUCANI_CONFIG)
        
        for i, (ime, cfg) in enumerate(DUCANI_CONFIG.items()):
            status.text(f"Pretražujem {ime}...")
            rez = pretrazi_ducan(ime, cfg, pojmovi=pojmovi if not barkod else None, 
                                barkod=barkod, debug_mode=debug_mode)
            svi_rez.extend(rez)
            progress.progress((i + 1) / total)
        
        progress.empty()
        status.empty()
        
        if not svi_rez:
            st.warning("Nisu pronađeni rezultati.")
            return
        
        df = pd.DataFrame(svi_rez)
        df = df.sort_values("Cijena (€)")
        df = df.drop_duplicates(["Trgovački lanac", "Šifra"]).reset_index(drop=True)
        
        zeljeni_redoslijed = [
            "Traženi pojam",
            "Naziv proizvoda",
            "Jedinica mjere",
            "Cijena (€)",
            "Trgovački lanac",
            "Šifra",
            "Barkod",
            "Kategorija"
        ]
        
        df = df[zeljeni_redoslijed]
        
        st.markdown('### 📊 Rezultati')
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown(f"""
<div class="stat-card">
    <div class="stat-number">{len(df)}</div>
    <div class="stat-label">Artikala</div>
</div>
            """, unsafe_allow_html=True)
        
        with c2:
            st.markdown(f"""
<div class="stat-card">
    <div class="stat-number">€{df["Cijena (€)"].min():.2f}</div>
    <div class="stat-label">Najjeftinije</div>
</div>
            """, unsafe_allow_html=True)
        
        with c3:
            st.markdown(f"""
<div class="stat-card">
    <div class="stat-number">{df["Trgovački lanac"].nunique()}</div>
    <div class="stat-label">Lanaca</div>
</div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 🏆 Najbolje ponude")
        
        df_show = df.copy()
        df_show["Cijena (€)"] = df_show["Cijena (€)"].apply(
            lambda x: f"€{x:.2f}" if pd.notna(x) else ""
        )
        df_show["Šifra"] = df_show["Šifra"].astype(str).str.replace(r'\.0$', '', regex=True)
        
        st.dataframe(
            df_show,
            use_container_width=True,
            height=520,
            hide_index=True
        )
        
        excel = create_excel_download(df)
        
        st.download_button(
            "📥 Preuzmi Excel",
            excel,
            "rezultati_cijene.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    st.markdown("""
<div class="footer">
    Izrađeno uz pomoć AI  |  Cijene ažurirane pon–sub ~8:20
</div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
