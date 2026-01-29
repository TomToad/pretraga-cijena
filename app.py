import streamlit as st
import pandas as pd
import re
from io import BytesIO, StringIO
import dropbox
from dropbox.exceptions import AuthError

# ────────────────────────────────────────────────
# KONFIGURACIJA
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="Pretraga Cijena | Price Finder",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - tamni elegantni dizajn
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Work+Sans:wght@400;500;600&display=swap');
    
    .main, .stApp { background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%); }
    
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(102,126,234,0.4);
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
        color: rgba(255,255,255,0.9);
        text-align: center;
        margin-top: 0.5rem;
    }
    
    h3 { font-family: 'Work Sans', sans-serif; color: #e2e8f0 !important; font-weight: 600; }
    
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
        box-shadow: 0 0 0 3px rgba(102,126,234,0.3);
        background-color: #252547;
    }
    
    .stTextInput > div > div > input::placeholder { color: #718096; }
    
    .stTextInput > label { color: #cbd5e0 !important; font-family: 'Work Sans', sans-serif; font-weight: 500; }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-family: 'Work Sans', sans-serif;
        font-weight: 600;
        font-size: 1.1rem;
        padding: 0.75rem 3rem;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 15px rgba(102,126,234,0.5);
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102,126,234,0.6);
    }
    
    .results-header { font-family: 'Playfair Display', serif; font-size: 2rem; color: #e2e8f0; margin: 2rem 0 1rem 0; font-weight: 700; }
    
    .stat-card {
        background: linear-gradient(135deg, #1e1e3f 0%, #252547 100%);
        padding: 1.5rem;
        border-radius: 15px;
        flex: 1;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border-left: 4px solid #667eea;
    }
    
    .stat-value { font-family: 'Playfair Display', serif; font-size: 2.5rem; font-weight: 700; color: #667eea; margin: 0; }
    .stat-label { font-family: 'Work Sans', sans-serif; font-size: 0.9rem; color: #a0aec0; margin-top: 0.25rem; }
    
    .info-box {
        background: linear-gradient(135deg, #1e1e3f 0%, #2d2d5f 100%);
        border-radius: 15px;
        border-left: 4px solid #667eea;
        margin-bottom: 1.5rem;
        color: #e2e8f0;
    }
    
    .info-box code {
        background: rgba(102,126,234,0.2);
        color: #a5b4fc;
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
    }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        font-weight: 600;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(72,187,120,0.4);
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(72,187,120,0.5);
    }
    
    .footer {
        text-align: center;
        padding: 2.5rem 1rem;
        color: #718096;
        font-size: 0.9rem;
        margin-top: 4rem;
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# KONFIGURACIJA DUĆANA
# ────────────────────────────────────────────────
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

# ────────────────────────────────────────────────
# HELPER FUNKCIJE
# ────────────────────────────────────────────────

def wildcard_to_regex(pattern):
    pattern = re.escape(pattern.lower())
    pattern = pattern.replace(r'\*', '.*').replace(r'\?', '.')
    return '^' + pattern

def convert_price(val):
    if pd.isna(val) or val == '': return None
    try:
        return float(str(val).replace(',', '.').replace(' ', ''))
    except:
        return None

@st.cache_data(ttl=3600)
def load_csv_from_dropbox(filename):
    try:
        dbx = dropbox.Dropbox(st.secrets["DROPBOX_ACCESS_TOKEN"])
        _, response = dbx.files_download(f"/{filename}")
        return response.content
    except AuthError as e:
        st.error(f"Dropbox autentikacija nije uspjela: {e}")
        return None
    except Exception as e:
        st.error(f"Greška pri učitavanju {filename} s Dropboxa: {e}")
        return None

def pretrazi_ducan(ducan_naziv, config, pojmovi):
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
                st.warning(f"{ducan_naziv}: nije pronađena kolona s maloprodajnom cijenom")
                return rezultati
        
        df[config["columns"]["maloprodajna"]] = df[config["columns"]["maloprodajna"]].apply(convert_price)
        if config["columns"]["akcijska"]:
            df[config["columns"]["akcijska"]] = df[config["columns"]["akcijska"]].apply(convert_price)
        
        if config["price_logic"] == "eurospin":
            df["CIJENA"] = df.apply(
                lambda x: x[config["columns"]["akcijska"]] if pd.notna(x[config["columns"]["akcijska"]]) and x[config["columns"]["akcijska"]] > 0
                else x[config["columns"]["maloprodajna"]], axis=1)
        elif config["price_logic"] == "spar":
            df["CIJENA"] = df.apply(
                lambda x: x[config["columns"]["akcijska"]] if pd.notna(x[config["columns"]["akcijska"]]) and x[config["columns"]["akcijska"]] > 0
                else x[config["columns"]["maloprodajna"]], axis=1)
        else:
            df["CIJENA"] = df[config["columns"]["maloprodajna"]].fillna(
                df[config["columns"]["akcijska"]] if config["columns"]["akcijska"] else pd.NA)
        
        for pojam in pojmovi:
            if not pojam.strip(): continue
            regex = wildcard_to_regex(pojam)
            mask = df[config["columns"]["naziv"]].astype(str).str.lower().str.contains(regex, na=False, regex=True)
            
            for _, row in df[mask].iterrows():
                rezultati.append({
                    "Trgovački lanac": ducan_naziv,
                    "Traženi pojam": pojam,
                    "Šifra": row.get(config["columns"]["sifra"], ""),
                    "Barkod": str(row.get(config["columns"]["barkod"], "")).replace('.0',''),
                    "Naziv proizvoda": row[config["columns"]["naziv"]],
                    "Cijena (€)": row["CIJENA"],
                    "Jedinica mjere": row.get(config["columns"]["jedinica"], ""),
                    "Kategorija": row.get(config["columns"]["kategorija"], "")
                })
        
        return rezultati
    
    except Exception as e:
        st.warning(f"{ducan_naziv}: {str(e)}")
        return rezultati

def create_excel_download(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Rezultati')
        ws = writer.sheets['Rezultati']
        header_fmt = writer.book.add_format({
            'bold': True, 'bg_color': '#667eea', 'font_color': 'white', 'border': 1
        })
        for col_num, value in enumerate(df.columns):
            ws.write(0, col_num, value, header_fmt)
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            ws.set_column(i, i, max_len)
    return output.getvalue()

# ────────────────────────────────────────────────
# GLAVNI DIO APLIKACIJE
# ────────────────────────────────────────────────

def main():
    st.markdown("""
    <div class="header-container">
        <h1 class="main-title">🛒 Pretraga Cijena</h1>
        <p class="subtitle">
            Najbolje cijene u trgovačkim lancima – Zaprešić<br>
            <span style="font-size: 0.9rem; opacity: 0.9;">
                (samo kategorije: hrana, piće, kozmetika, sredstva za čišćenje, toaletne potrepštine i proizvodi za kućanstvo)
            </span>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ── Ispravljeni info-box (raw string + čisti HTML) ────────────────────────────────
    st.markdown(r"""
<div class="info-box" style="padding:1.2rem;line-height:1.45;">
<p style="font-size:1rem;font-weight:600;margin-bottom:0.8rem;">🔍 Kako pretraživati</p>

<p style="font-size:0.9rem;margin:0.3rem 0;">Do 6 pojmova</p>

<p style="font-size:0.88rem;font-weight:500;margin:0.9rem 0 0.3rem 0;">Bez * → traži na početku naziva</p>
<ul style="margin:0.2rem 0 0.8rem 1.5rem;font-size:0.86rem;line-height:1.4;list-style-type:disc;padding-left:0;">
<li style="margin-bottom:0.2rem;"><strong>mlijeko</strong> → Mlijeko Dukat, Mlijeko fresh...</li>
<li style="margin-bottom:0.2rem;"><strong>nutella</strong> → Nutella, Nutella B-ready...</li>
<li><strong>jogurt</strong> → jogurti koji počinju tom riječi</li>
</ul>

<p style="font-size:0.88rem;font-weight:500;margin:1rem 0 0.3rem 0;">Bilo gdje u nazivu → koristi *</p>
<ul style="margin:0.2rem 0 0.8rem 1.5rem;font-size:0.86rem;line-height:1.4;list-style-type:disc;padding-left:0;">
<li style="margin-bottom:0.2rem;"><strong>*mlijeko*</strong> → sve što ima „mlijeko“</li>
<li style="margin-bottom:0.2rem;"><strong>*nutella*</strong> ili <strong>nutella*</strong> → svi Nutella proizvodi</li>
<li><strong>sir ?0%</strong> → sir 20%, 30%, 00%...</li>
</ul>

<p style="font-size:0.9rem;font-weight:500;color:#a5b4fc;margin:0.9rem 0 0.4rem 0;">💡 Brzi trikovi</p>
<ul style="margin:0.2rem 0 0.4rem 1.5rem;font-size:0.86rem;line-height:1.4;list-style-type:disc;padding-left:0;">
<li>*kava* ili *mlijeko 3.5*</li>
<li>dukat* ili *dukat*</li>
<li>nutella *200g* ili *sir *masni*</li>
</ul>

<p style="font-size:0.82rem;color:#94a3b8;margin-top:0.8rem;">Pretraga ne razlikuje velika/mala slova</p>
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
            rez = pretrazi_ducan(ime, cfg, pojmovi)
            svi_rez.extend(rez)
            progress.progress((i + 1) / total)
        
        progress.empty()
        status.empty()
        
        if not svi_rez:
            st.warning("Nisu pronađeni rezultati za unesene pojmove.")
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
        
        st.markdown('<h2 class="results-header">📊 Rezultati</h2>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="stat-card"><p class="stat-value">{len(df)}</p><p class="stat-label">Artikala</p></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card"><p class="stat-value">€{df["Cijena (€)"].min():.2f}</p><p class="stat-label">Najjeftinije</p></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card"><p class="stat-value">{df["Trgovački lanac"].nunique()}</p><p class="stat-label">Lanaca</p></div>', unsafe_allow_html=True)
        
        st.markdown("### 🏆 Najbolje ponude (sortirano po cijeni)")
        
        df_show = df.copy()
        df_show["Cijena (€)"] = df_show["Cijena (€)"].apply(lambda x: f"€{x:.2f}" if pd.notna(x) else "")
        
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
        
        st.markdown("### 💾 Preuzmi rezultate")
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
        <p>Izrađeno uz pomoć AI &nbsp;|&nbsp; Cijene ažurirane pon–sub ~8:20</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()