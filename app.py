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

# Custom CSS - tamni elegantni dizajn
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
    
    .debug-box {
        background: #2d2d44;
        border: 2px solid #667eea;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        font-family: monospace;
        font-size: 0.9em;
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
        # Ukloni sve razmake i zamijeni zarez s točkom
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
    """
    Određuje finalnu cijenu proizvoda prema logici dućana.
    Prioritet: akcijska cijena (ako postoji i > 0) -> maloprodajna cijena
    """
    maloprodajna_col = config["columns"]["maloprodajna"]
    akcijska_col = config["columns"]["akcijska"]
    
    maloprodajna = row.get(maloprodajna_col)
    akcijska = row.get(akcijska_col) if akcijska_col else None
    
    # Debug info
    if debug_mode:
        st.write(f"Debug - {row.get(config['columns']['naziv'], 'N/A')[:50]}...")
        st.write(f"  Maloprodajna: {maloprodajna} (type: {type(maloprodajna)})")
        st.write(f"  Akcijska: {akcijska} (type: {type(akcijska)})")
    
    # Provjeri da li postoji akcijska cijena i da li je validna (> 0)
    if pd.notna(akcijska) and akcijska > 0:
        if debug_mode:
            st.write(f"  ✓ Koristi akcijsku: {akcijska}")
        return akcijska
    
    # Inače koristi maloprodajnu
    if debug_mode:
        st.write(f"  → Koristi maloprodajnu: {maloprodajna}")
    return maloprodajna

def pretrazi_ducan(ducan_naziv, config, pojmovi, debug_mode=False):
    """Pretražuje jedan dućan za zadane pojmove"""
    rezultati = []
    
    try:
        content = load_csv_from_dropbox(config["filename"])
        if content is None:
            return rezultati
        
        # Učitaj CSV
        df = pd.read_csv(
            StringIO(content.decode(config["encoding"])),
            sep=config["separator"],
            on_bad_lines='skip'
        )
        
        # Očisti nazive kolona
        df.columns = df.columns.str.strip()
        
        if debug_mode and ducan_naziv == "Spar":
            st.write(f"### 🔍 Debug info za {ducan_naziv}")
            st.write(f"Učitano redaka: {len(df)}")
            st.write(f"Kolone u CSV-u: {list(df.columns)}")
        
        # Pronađi kolonu za maloprodajnu cijenu ako nije definirana
        if config["columns"]["maloprodajna"] is None:
            cijene = [c for c in df.columns if "maloprod" in c.lower()]
            if cijene:
                config["columns"]["maloprodajna"] = cijene[0]
            else:
                st.warning(f"{ducan_naziv}: nije pronađena kolona s maloprodajnom cijenom")
                return rezultati
        
        # Konvertiraj cijene u numeričke vrijednosti
        df[config["columns"]["maloprodajna"]] = df[config["columns"]["maloprodajna"]].apply(convert_price)
        
        if config["columns"]["akcijska"]:
            df[config["columns"]["akcijska"]] = df[config["columns"]["akcijska"]].apply(convert_price)
            
            if debug_mode and ducan_naziv == "Spar":
                st.write(f"\n**Primjer prvih 5 redaka s cijenama:**")
                sample_df = df[[
                    config["columns"]["naziv"],
                    config["columns"]["maloprodajna"],
                    config["columns"]["akcijska"]
                ]].head()
                st.dataframe(sample_df)
                
                # Provjeri ima li akcijskih cijena
                akcijske_count = df[config["columns"]["akcijska"]].notna().sum()
                st.write(f"\nProizvoda s akcijskom cijenom: {akcijske_count} / {len(df)}")
        
        # KLJUČNA IZMJENA: Uvijek koristi prioritet akcijska -> maloprodajna
        # bez obzira na price_logic postavku
        df["CIJENA"] = df.apply(
            lambda row: determine_final_price(row, config, debug_mode and ducan_naziv == "Spar"),
            axis=1
        )
        
        # Pretraži po pojmovima
        for pojam in pojmovi:
            if not pojam.strip():
                continue
            
            regex = wildcard_to_regex(pojam)
            mask = df[config["columns"]["naziv"]].astype(str).str.lower().str.contains(
                regex, na=False, regex=True
            )
            
            matched_count = mask.sum()
            if debug_mode and ducan_naziv == "Spar" and matched_count > 0:
                st.write(f"\n**Pojam '{pojam}' - pronađeno: {matched_count} proizvoda**")
            
            for _, row in df[mask].iterrows():
                rezultati.append({
                    "Trgovački lanac": ducan_naziv,
                    "Traženi pojam": pojam,
                    "Šifra": row.get(config["columns"]["sifra"], ""),
                    "Barkod": str(row.get(config["columns"]["barkod"], "")).replace('.0', ''),
                    "Naziv proizvoda": row[config["columns"]["naziv"]],
                    "Cijena (€)": row["CIJENA"],
                    "Maloprodajna (€)": row[config["columns"]["maloprodajna"]],  # DODANO za debug
                    "Akcijska (€)": row.get(config["columns"]["akcijska"]) if config["columns"]["akcijska"] else None,  # DODANO za debug
                    "Jedinica mjere": row.get(config["columns"]["jedinica"], ""),
                    "Kategorija": row.get(config["columns"]["kategorija"], "")
                })
        
        return rezultati
        
    except Exception as e:
        st.error(f"{ducan_naziv}: {str(e)}")
        if debug_mode:
            import traceback
            st.code(traceback.format_exc())
        return rezultati

def create_excel_download(df):
    """Kreira Excel datoteku za preuzimanje"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Rezultati')
        ws = writer.sheets['Rezultati']
        
        # Formatiraj header
        header_fmt = writer.book.add_format({
            'bold': True,
            'bg_color': '#667eea',
            'font_color': 'white',
            'border': 1
        })
        
        for col_num, value in enumerate(df.columns):
            ws.write(0, col_num, value, header_fmt)
        
        # Prilagodi širinu kolona
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            ws.set_column(i, i, max_len)
    
    return output.getvalue()

# ──────────────────────────────────────────────────────────────────────
# GLAVNI DIO APLIKACIJE
# ──────────────────────────────────────────────────────────────────────

def main():
    st.markdown("""
<div class="header-banner">
    <div class="header-title">🛒 Pretraga Cijena</div>
    <div class="header-subtitle">
        Najbolje cijene u trgovačkim lancima – Zaprešić<br>
        (samo kategorije: hrana, piće, kozmetika, sredstva za čišćenje, toaletne potrepštine i proizvodi za kućanstvo)
    </div>
</div>
    """, unsafe_allow_html=True)
    
    # Debug mode toggle (skriveno u sidebar)
    with st.sidebar:
        debug_mode = st.checkbox("🐛 Debug mode", value=False, 
                                 help="Prikazuje dodatne informacije o obradi cijena")
    
    # Info box s uputama
    st.markdown(r"""
<div class="info-box">
    <h3>🔍 Kako pretraživati</h3>
    <ul>
        <li><strong>Do 6 pojmova</strong></li>
        <li><strong>Bez *</strong> → traži na početku naziva
            <ul>
                <li><code>mlijeko</code> → Mlijeko Dukat, Mlijeko fresh...</li>
                <li><code>nutella</code> → Nutella, Nutella B-ready...</li>
            </ul>
        </li>
        <li><strong>Bilo gdje u nazivu</strong> → koristi *
            <ul>
                <li><code>*mlijeko*</code> → sve što ima „mlijeko"</li>
                <li><code>*nutella*</code> ili <code>nutella*</code> → svi Nutella proizvodi</li>
                <li><code>sir ?0%</code> → sir 20%, 30%, 00%...</li>
            </ul>
        </li>
    </ul>
    <p><strong>💡 Brzi trikovi:</strong> <code>*kava*</code>, <code>*mlijeko 3.5*</code>, <code>dukat*</code>, <code>*dukat*</code></p>
    <p style="margin-top:10px; opacity:0.8;">Pretraga ne razlikuje velika/mala slova</p>
</div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔍 Unesite pojmove za pretragu")
    
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
        
        if not pojmovi:
            st.error("Unesite barem jedan pojam za pretragu.")
            return
        
        progress = st.progress(0)
        status = st.empty()
        svi_rez = []
        
        total = len(DUCANI_CONFIG)
        
        for i, (ime, cfg) in enumerate(DUCANI_CONFIG.items()):
            status.text(f"Pretražujem {ime}...")
            rez = pretrazi_ducan(ime, cfg, pojmovi, debug_mode=debug_mode)
            svi_rez.extend(rez)
            progress.progress((i + 1) / total)
        
        progress.empty()
        status.empty()
        
        if not svi_rez:
            st.warning("Nisu pronađeni rezultati za unesene pojmove.")
            return
        
        # Kreiraj DataFrame
        df = pd.DataFrame(svi_rez)
        
        # Sortiraj po cijeni
        df = df.sort_values("Cijena (€)")
        
        # Ukloni duplikate (isti proizvod iz istog dućana)
        df = df.drop_duplicates(["Trgovački lanac", "Šifra"]).reset_index(drop=True)
        
        # Pripremi kolone za prikaz
        if debug_mode:
            zeljeni_redoslijed = [
                "Traženi pojam",
                "Naziv proizvoda",
                "Jedinica mjere",
                "Cijena (€)",
                "Maloprodajna (€)",
                "Akcijska (€)",
                "Trgovački lanac",
                "Šifra",
                "Barkod",
                "Kategorija"
            ]
        else:
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
            # Ukloni debug kolone
            df = df.drop(columns=["Maloprodajna (€)", "Akcijska (€)"], errors='ignore')
        
        df = df[zeljeni_redoslijed]
        
        # Prikaži statistiku
        st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
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
        
        # Prikaži tablicu
        st.markdown("### 🏆 Najbolje ponude (sortirano po cijeni)")
        
        df_show = df.copy()
        df_show["Cijena (€)"] = df_show["Cijena (€)"].apply(
            lambda x: f"€{x:.2f}" if pd.notna(x) else ""
        )
        
        if debug_mode:
            df_show["Maloprodajna (€)"] = df_show["Maloprodajna (€)"].apply(
                lambda x: f"€{x:.2f}" if pd.notna(x) else ""
            )
            df_show["Akcijska (€)"] = df_show["Akcijska (€)"].apply(
                lambda x: f"€{x:.2f}" if pd.notna(x) else ""
            )
        
        # Popravi šifru
        df_show["Šifra"] = df_show["Šifra"].astype(str).str.replace(r'\.0$', '', regex=True)
        
        st.dataframe(
            df_show,
            use_container_width=True,
            height=520,
            hide_index=True,
            column_config={
                "Naziv proizvoda": st.column_config.TextColumn("Naziv", width="medium"),
                "Cijena (€)": st.column_config.TextColumn("Cijena", width="small"),
                "Trgovački lanac": st.column_config.TextColumn("Lanac", width="small"),
                "Jedinica mjere": st.column_config.TextColumn("Jedinica", width="small"),
                "Traženi pojam": st.column_config.TextColumn("Pojam", width="small"),
            }
        )
        
        # Preuzimanje Excel datoteke
        st.markdown("### 💾 Preuzmi rezultate")
        
        # Pripremi DataFrame za Excel (bez debug kolona)
        df_excel = df.copy()
        if "Maloprodajna (€)" in df_excel.columns:
            df_excel = df_excel.drop(columns=["Maloprodajna (€)", "Akcijska (€)"], errors='ignore')
        
        excel = create_excel_download(df_excel)
        
        st.download_button(
            "📥 Preuzmi Excel",
            excel,
            "rezultati_cijene.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # Footer
    st.markdown("""
<div class="footer">
    Izrađeno uz pomoć AI  |  Cijene ažurirane pon–sub ~8:20
</div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()