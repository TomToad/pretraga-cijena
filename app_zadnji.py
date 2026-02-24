import streamlit as st
import pandas as pd
import re
from io import BytesIO, StringIO
import dropbox
from dropbox.exceptions import AuthError
import copy

st.set_page_config(
    page_title="Pretraga Cijena | Price Finder",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
    
    .barcode-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .scanner-btn {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        font-size: 1.1em !important;
        cursor: pointer !important;
        transition: all 0.3s !important;
        margin-top: 8px !important;
    }
    
    .scanner-btn:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(240, 147, 251, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

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
        }
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
        }
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
        }
    },
    "Konzum": {
        "filename": "konzum_jucer.csv",
        "separator": ",",
        "encoding": "utf-8-sig",
        "columns": {
            "naziv": "NAZIV PROIZVODA",
            "sifra": "ŠIFRA PROIZVODA",
            "barkod": "BARKOD",
            "kategorija": "KATEGORIJA PROIZVODA",
            "maloprodajna": "MALOPRODAJNA CIJENA",
            "akcijska": "MPC ZA VRIJEME POSEBNOG OBLIKA PRODAJE",
            "jedinica": "JEDINICA MJERE"
        }
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
        }
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
        }
    }
}

def find_column(df_columns, target, debug_name=""):
    if target is None:
        return None
    target_norm = target.lower().strip()
    cols_lower = {c.lower().strip(): c for c in df_columns}

    if target_norm in cols_lower:
        return cols_lower[target_norm]

    for col_lower, col_orig in cols_lower.items():
        if target_norm in col_lower:
            return col_orig

    for col_lower, col_orig in cols_lower.items():
        if col_lower in target_norm and len(col_lower) > 4:
            return col_orig

    return None

def resolve_columns(config, df_columns, debug_mode=False, ducan_naziv=""):
    resolved = {}
    for key, target in config["columns"].items():
        found = find_column(df_columns, target, debug_name=key)
        resolved[key] = found
        if debug_mode:
            status = "✅" if found else "❌"
            st.write(f"  {status} `{key}`: traženo=`{target}` → nađeno=`{found}`")
    return resolved

def wildcard_to_regex(pattern):
    pattern = re.escape(pattern.lower())
    pattern = pattern.replace(r'\*', '.*').replace(r'\?', '.')
    return '^' + pattern

def convert_price(val):
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

def determine_final_price(row, resolved_cols):
    mal_col = resolved_cols.get("maloprodajna")
    akc_col = resolved_cols.get("akcijska")

    maloprodajna = row[mal_col] if (mal_col and mal_col in row.index) else None
    akcijska     = row[akc_col] if (akc_col and akc_col in row.index) else None

    if pd.notna(akcijska) and akcijska > 0:
        return akcijska
    if pd.notna(maloprodajna) and maloprodajna > 0:
        return maloprodajna
    return None

def pretrazi_ducan(ducan_naziv, config, pojmovi=None, barkod=None, debug_mode=False):
    rezultati = []
    try:
        content = load_csv_from_dropbox(config["filename"])
        if content is None:
            return rezultati

        df = pd.read_csv(
            StringIO(content.decode(config["encoding"])),
            sep=config["separator"],
            on_bad_lines='skip',
            dtype=str
        )

        df.columns = df.columns.str.strip().str.replace('\ufeff', '', regex=False)

        if debug_mode:
            st.write(f"#### 🔍 {ducan_naziv} — kolone u CSV-u:")
            st.write(list(df.columns))

        resolved = resolve_columns(config, df.columns, debug_mode=debug_mode, ducan_naziv=ducan_naziv)

        if resolved["maloprodajna"] is None:
            candidates = [c for c in df.columns if "maloprod" in c.lower()]
            if candidates:
                resolved["maloprodajna"] = candidates[0]
                if debug_mode:
                    st.write(f"  🔧 Auto-detect maloprodajna → `{resolved['maloprodajna']}`")
            else:
                st.warning(f"{ducan_naziv}: nije pronađena kolona s maloprodajnom cijenom")
                return rezultati

        for key in ["maloprodajna", "akcijska"]:
            col = resolved.get(key)
            if col and "najni" in col.lower():
                st.warning(f"{ducan_naziv}: kolona '{col}' izgleda kao NAJNIŽA CIJENA — isključujem!")
                resolved[key] = None

        if resolved["maloprodajna"]:
            df[resolved["maloprodajna"]] = df[resolved["maloprodajna"]].apply(convert_price)
        if resolved["akcijska"]:
            df[resolved["akcijska"]] = df[resolved["akcijska"]].apply(convert_price)

        if debug_mode:
            st.write(f"**Primjer prvih 3 retka (cijene):**")
            cols_to_show = [c for c in [resolved["naziv"], resolved["maloprodajna"], resolved["akcijska"]] if c]
            st.dataframe(df[cols_to_show].head(3))

        df["CIJENA"] = df.apply(lambda row: determine_final_price(row, resolved), axis=1)

        naziv_col  = resolved["naziv"]
        sifra_col  = resolved["sifra"]
        barkod_col = resolved["barkod"]
        kat_col    = resolved["kategorija"]
        jed_col    = resolved["jedinica"]
        mal_col    = resolved["maloprodajna"]
        akc_col    = resolved["akcijska"]

        if barkod and barkod_col:
            barkod_clean = barkod.strip()
            df[barkod_col] = df[barkod_col].astype(str).str.replace('.0', '', regex=False).str.strip()
            mask = df[barkod_col] == barkod_clean
            for _, row in df[mask].iterrows():
                rezultati.append({
                    "Trgovački lanac": ducan_naziv,
                    "Traženi pojam": f"🔢 {barkod_clean}",
                    "Šifra": row.get(sifra_col, "") if sifra_col else "",
                    "Barkod": row.get(barkod_col, ""),
                    "Naziv proizvoda": row.get(naziv_col, ""),
                    "Cijena (€)": row["CIJENA"],
                    "Maloprodajna (€)": row.get(mal_col) if mal_col else None,
                    "Akcijska (€)": row.get(akc_col) if akc_col else None,
                    "Jedinica mjere": row.get(jed_col, "") if jed_col else "",
                    "Kategorija": row.get(kat_col, "") if kat_col else ""
                })

        if pojmovi and naziv_col:
            for pojam in pojmovi:
                if not pojam.strip():
                    continue
                regex = wildcard_to_regex(pojam)
                mask = df[naziv_col].astype(str).str.lower().str.contains(regex, na=False, regex=True)
                for _, row in df[mask].iterrows():
                    rezultati.append({
                        "Trgovački lanac": ducan_naziv,
                        "Traženi pojam": pojam,
                        "Šifra": row.get(sifra_col, "") if sifra_col else "",
                        "Barkod": str(row.get(barkod_col, "")).replace('.0', '') if barkod_col else "",
                        "Naziv proizvoda": row.get(naziv_col, ""),
                        "Cijena (€)": row["CIJENA"],
                        "Maloprodajna (€)": row.get(mal_col) if mal_col else None,
                        "Akcijska (€)": row.get(akc_col) if akc_col else None,
                        "Jedinica mjere": row.get(jed_col, "") if jed_col else "",
                        "Kategorija": row.get(kat_col, "") if kat_col else ""
                    })

        return rezultati

    except Exception as e:
        st.error(f"{ducan_naziv}: {str(e)}")
        if debug_mode:
            import traceback
            st.code(traceback.format_exc())
        return rezultati

def create_excel_download(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Rezultati')
        ws = writer.sheets['Rezultati']
        header_fmt = writer.book.add_format({
            'bold': True, 'bg_color': '#667eea',
            'font_color': 'white', 'border': 1
        })
        for col_num, value in enumerate(df.columns):
            ws.write(0, col_num, value, header_fmt)
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            ws.set_column(i, i, max_len)
    return output.getvalue()

def main():
    st.markdown("""
<div class="header-banner">
    <div class="header-title">🛒 Pretraga Cijena</div>
    <div class="header-subtitle">Najbolje cijene u trgovačkim lancima – Zaprešić
    (samo kategorije: hrana, piće, kozmetika, sredstva za čišćenje, toaletne potrepštine i proizvodi za kućanstvo)</div>
</div>
""", unsafe_allow_html=True)

    with st.sidebar:
        debug_mode = st.checkbox("🐛 Debug mode", value=False,
                                  help="Prikazuje nazive kolona i prvih par redaka za svaki dućan")

    st.markdown(r"""
<div class="info-box">
<h3>🔍 Kako pretraživati</h3>
<ul>
<li>Do 6 pojmova ili 1 barkod</li>
<li>Bez * → traži na početku naziva<br>
&nbsp;&nbsp;<code>mlijeko</code> → Mlijeko Dukat, Mlijeko fresh...<br>
&nbsp;&nbsp;<code>nutella</code> → Nutella, Nutella B-ready...</li>
<li>Bilo gdje u nazivu → koristi *<br>
&nbsp;&nbsp;<code>*mlijeko*</code> → sve što ima „mlijeko"<br>
&nbsp;&nbsp;<code>*nutella*</code> ili <code>nutella*</code> → svi Nutella proizvodi<br>
&nbsp;&nbsp;<code>sir ?0%</code> → sir 20%, 30%, 00%...</li>
</ul>
💡 Brzi trikovi: <code>*kava*</code>, <code>*mlijeko 3.5*</code>, <code>dukat*</code>, <code>*dukat*</code><br>
Pretraga ne razlikuje velika/mala slova
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="barcode-box">', unsafe_allow_html=True)
    st.markdown("### 🔢 Pretraga po barkodu")
    barkod_input = st.text_input("Unesite barkod proizvoda",
                                  placeholder="npr. 3017620422003",
                                  help="Točna pretraga po barkodu - pronalazi samo taj proizvod",
                                  key="barkod")
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
            st.warning("⚠️ Možete pretraživati po pojmovima ILI po barkodu, ne oboje istovremeno. Koristim samo barkod pretragu.")
            pojmovi = []

        progress = st.progress(0)
        status = st.empty()
        svi_rez = []
        total = len(DUCANI_CONFIG)

        for i, (ime, cfg) in enumerate(DUCANI_CONFIG.items()):
            status.text(f"Pretražujem {ime}...")
            cfg_copy = copy.deepcopy(cfg)
            rez = pretrazi_ducan(
                ime, cfg_copy,
                pojmovi=pojmovi if not barkod else None,
                barkod=barkod,
                debug_mode=debug_mode
            )
            svi_rez.extend(rez)
            progress.progress((i + 1) / total)

        progress.empty()
        status.empty()

        if not svi_rez:
            if barkod:
                st.warning(f"Barkod **{barkod}** nije pronađen ni u jednom trgovačkom lancu.")
            else:
                st.warning("Nisu pronađeni rezultati za unesene pojmove.")
            return

        df = pd.DataFrame(svi_rez)
        df = df.sort_values("Cijena (€)")
        df = df.drop_duplicates(["Trgovački lanac", "Šifra"]).reset_index(drop=True)

        if debug_mode:
            zeljeni_redoslijed = [
                "Traženi pojam", "Naziv proizvoda", "Jedinica mjere",
                "Cijena (€)", "Maloprodajna (€)", "Akcijska (€)",
                "Trgovački lanac", "Šifra", "Barkod", "Kategorija"
            ]
        else:
            zeljeni_redoslijed = [
                "Traženi pojam", "Naziv proizvoda", "Jedinica mjere",
                "Cijena (€)", "Trgovački lanac", "Šifra", "Barkod", "Kategorija"
            ]
            df = df.drop(columns=["Maloprodajna (€)", "Akcijska (€)"], errors='ignore')

        df = df[[c for c in zeljeni_redoslijed if c in df.columns]]

        st.markdown("### 📊 Rezultati")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
<div class="stat-card">
    <div class="stat-number">{len(df)}</div>
    <div class="stat-label">Artikala</div>
</div>""", unsafe_allow_html=True)
        with c2:
            min_c = df["Cijena (€)"].min()
            min_str = f"€{min_c:.2f}" if pd.notna(min_c) else "N/A"
            st.markdown(f"""
<div class="stat-card">
    <div class="stat-number">{min_str}</div>
    <div class="stat-label">Najjeftinije</div>
</div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
<div class="stat-card">
    <div class="stat-number">{df["Trgovački lanac"].nunique()}</div>
    <div class="stat-label">Lanaca</div>
</div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if barkod:
            st.markdown(f"### 🏆 Rezultati za barkod **{barkod}** (sortirano po cijeni)")
        else:
            st.markdown("### 🏆 Najbolje ponude (sortirano po cijeni)")

        df_show = df.copy()
        df_show["Cijena (€)"] = df_show["Cijena (€)"].apply(
            lambda x: f"€{x:.2f}" if pd.notna(x) else "")
        if debug_mode:
            for col in ["Maloprodajna (€)", "Akcijska (€)"]:
                if col in df_show.columns:
                    df_show[col] = df_show[col].apply(
                        lambda x: f"€{x:.2f}" if pd.notna(x) else "")
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

        st.markdown("### 💾 Preuzmi rezultate")
        df_excel = df.drop(columns=["Maloprodajna (€)", "Akcijska (€)"], errors='ignore')
        excel = create_excel_download(df_excel)
        st.download_button(
            "📥 Preuzmi Excel", excel,
            "rezultati_cijene.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.markdown("""
<div class="footer">
    Izrađeno uz pomoć AI | Cijene ažurirane pon–sub ~8:20
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()