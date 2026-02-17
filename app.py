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
        "encoding": "utf-8-sig",
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
    """
    Određuje finalnu cijenu proizvoda prema logici dućana.
    Prioritet: akcijska cijena (ako postoji i > 0) -> maloprodajna cijena
    """
    maloprodajna_col = config["columns"]["maloprodajna"]
    akcijska_col = config["columns"]["akcijska"]

    maloprodajna = row.get(maloprodajna_col) if (maloprodajna_col and maloprodajna_col in row.index) else None
    akcijska = row.get(akcijska_col) if (akcijska_col and akcijska_col in row.index) else None

    if debug_mode:
        st.write(f"Debug - {row.get(config['columns']['naziv'], 'N/A')}")
        st.write(f"  Maloprodajna: {maloprodajna}")
        st.write(f"  Akcijska: {akcijska}")

    if pd.notna(akcijska) and akcijska > 0:
        if debug_mode:
            st.write(f"  ✓ Koristi akcijsku: {akcijska}")
        return akcijska

    if pd.notna(maloprodajna) and maloprodajna > 0:
        if debug_mode:
            st.write(f"  → Koristi maloprodajnu: {maloprodajna}")
        return maloprodajna

    return None

def pretrazi_ducan(ducan_naziv, config, pojmovi=None, barkod=None, debug_mode=False):
    """Pretražuje jedan dućan za zadane pojmove ili barkod"""
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

        # Očisti nazive kolona + ukloni BOM ako postoji
        df.columns = df.columns.str.strip().str.replace('\ufeff', '', regex=False)

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
            akcijske_count = df[config["columns"]["akcijska"]].notna().sum()
            st.write(f"\nProizvoda s akcijskom cijenom: {akcijske_count} / {len(df)}")

        # Uvijek koristi prioritet akcijska -> maloprodajna
        df["CIJENA"] = df.apply(
            lambda row: determine_final_price(row, config, debug_mode and ducan_naziv == "Spar"),
            axis=1
        )

        # Pretraži po barkodu (točno podudaranje)
        if barkod:
            barkod_clean = barkod.strip()
            df[config["columns"]["barkod"]] = df[config["columns"]["barkod"]].astype(str).str.replace('.0', '', regex=False)
            mask = df[config["columns"]["barkod"]] == barkod_clean
            matched_count = mask.sum()
            if debug_mode and matched_count > 0:
                st.write(f"\n**Barkod '{barkod_clean}' - pronađeno: {matched_count} proizvoda**")
            for _, row in df[mask].iterrows():
                rezultati.append({
                    "Trgovački lanac": ducan_naziv,
                    "Traženi pojam": f"🔢 {barkod_clean}",
                    "Šifra": row.get(config["columns"]["sifra"], ""),
                    "Barkod": str(row.get(config["columns"]["barkod"], "")).replace('.0', ''),
                    "Naziv proizvoda": row[config["columns"]["naziv"]],
                    "Cijena (€)": row["CIJENA"],
                    "Maloprodajna (€)": row[config["columns"]["maloprodajna"]],
                    "Akcijska (€)": row.get(config["columns"]["akcijska"]) if config["columns"]["akcijska"] else None,
                    "Jedinica mjere": row.get(config["columns"]["jedinica"], ""),
                    "Kategorija": row.get(config["columns"]["kategorija"], "")
                })

        # Pretraži po pojmovima (wildcard)
        if pojmovi:
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
                        "Maloprodajna (€)": row[config["columns"]["maloprodajna"]],
                        "Akcijska (€)": row.get(config["columns"]["akcijska"]) if config["columns"]["akcijska"] else None,
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
    st.markdown("""
<div style="text-align:center; padding: 2rem 0 1rem 0;">
    <h1>🛒 Pretraga Cijena</h1>
    <p style="color: #888;">Najbolje cijene u trgovačkim lancima – Zaprešić
    (samo kategorije: hrana, piće, kozmetika, sredstva za čišćenje, toaletne potrepštine i proizvodi za kućanstvo)</p>
</div>
""", unsafe_allow_html=True)

    with st.sidebar:
        debug_mode = st.checkbox("🐛 Debug mode", value=False, help="Prikazuje dodatne informacije o obradi cijena")

    st.markdown(r"""
<div style="background:#1e1e2e; border-radius:10px; padding:1rem 1.5rem; margin-bottom:1.5rem;">
<b>🔍 Kako pretraživati</b><br><br>
* Do 6 pojmova ili 1 barkod<br>
* Bez * → traži na početku naziva<br>
&nbsp;&nbsp;&nbsp;<code>mlijeko</code> → Mlijeko Dukat, Mlijeko fresh...<br>
&nbsp;&nbsp;&nbsp;<code>nutella</code> → Nutella, Nutella B-ready...<br>
* Bilo gdje u nazivu → koristi *<br>
&nbsp;&nbsp;&nbsp;<code>*mlijeko*</code> → sve što ima „mlijeko"<br>
&nbsp;&nbsp;&nbsp;<code>*nutella*</code> ili <code>nutella*</code> → svi Nutella proizvodi<br>
&nbsp;&nbsp;&nbsp;<code>sir ?0%</code> → sir 20%, 30%, 00%...<br><br>
💡 Brzi trikovi: <code>*kava*</code>, <code>*mlijeko 3.5*</code>, <code>dukat*</code>, <code>*dukat*</code><br>
Pretraga ne razlikuje velika/mala slova
</div>
""", unsafe_allow_html=True)

    st.markdown("### 🔢 Pretraga po barkodu")
    barkod_input = st.text_input(
        "Unesite barkod proizvoda",
        placeholder="npr. 3017620422003",
        help="Točna pretraga po barkodu - pronalazi samo taj proizvod",
        key="barkod"
    )

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
            if barkod:
                status.text(f"Pretražujem {ime} po barkodu {barkod}...")
            else:
                status.text(f"Pretražujem {ime}...")
            rez = pretrazi_ducan(
                ime, cfg,
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

        if not debug_mode:
            df = df.drop(columns=["Maloprodajna (€)", "Akcijska (€)"], errors='ignore')

        df = df[zeljeni_redoslijed]

        st.markdown("### 📊 Rezultati")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Artikala", len(df))
        with c2:
            min_cijena = df["Cijena (€)"].min()
            st.metric("Najjeftinije", f"€{min_cijena:.2f}" if pd.notna(min_cijena) else "N/A")
        with c3:
            st.metric("Lanaca", df["Trgovački lanac"].nunique())

        if barkod:
            st.markdown(f"### 🏆 Rezultati za barkod **{barkod}** (sortirano po cijeni)")
        else:
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

    st.markdown("""
<div style="text-align:center; color:#555; padding:2rem 0 1rem 0; font-size:0.85rem;">
    Izrađeno uz pomoć AI | Cijene ažurirane pon–sub ~8:20
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()