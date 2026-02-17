import streamlit as st
import pandas as pd
import re
from io import BytesIO, StringIO
import dropbox
from dropbox.exceptions import AuthError

st.set_page_config(
    page_title="Pretraga Cijena | Price Finder",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""<style></style>""", unsafe_allow_html=True)

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

# ── KLJUČNA FUNKCIJA: fuzzy pronalaženje kolone ──────────────────────
def find_column(df_columns, target, debug_name=""):
    """
    Pronalazi kolonu u DataFrameu:
    1. Egzaktno podudaranje (case-insensitive)
    2. Partial match — target sadržan u nazivu kolone
    3. Partial match — naziv kolone sadržan u targetu
    Vraća stvarni naziv kolone ili None.
    """
    if target is None:
        return None
    target_norm = target.lower().strip()
    cols_lower = {c.lower().strip(): c for c in df_columns}

    # 1. Egzaktno
    if target_norm in cols_lower:
        return cols_lower[target_norm]

    # 2. Target sadržan u nazivu kolone
    for col_lower, col_orig in cols_lower.items():
        if target_norm in col_lower:
            return col_orig

    # 3. Naziv kolone sadržan u targetu
    for col_lower, col_orig in cols_lower.items():
        if col_lower in target_norm and len(col_lower) > 4:
            return col_orig

    return None

def resolve_columns(config, df_columns, debug_mode=False, ducan_naziv=""):
    """
    Vraća dict s stvarnim nazivima kolona pronađenih u DataFrameu.
    Ispisuje debug info ako je debug_mode uključen.
    """
    resolved = {}
    for key, target in config["columns"].items():
        found = find_column(df_columns, target, debug_name=key)
        resolved[key] = found
        if debug_mode:
            status = "✅" if found else "❌"
            st.write(f"  {status} `{key}`: traženo=`{target}` → nađeno=`{found}`")
    return resolved

# ────────────────────────────────────────────────────────────────────────
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
    """
    Prioritet: akcijska (ako > 0) → maloprodajna (ako > 0) → None
    Koristi resolved_cols (stvarne nazive kolona u DataFrameu).
    """
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
            dtype=str  # sve učitaj kao string, konvertiramo ručno
        )

        # Očisti nazive kolona + ukloni BOM
        df.columns = df.columns.str.strip().str.replace('\ufeff', '', regex=False)

        if debug_mode:
            st.write(f"#### 🔍 {ducan_naziv} — kolone u CSV-u:")
            st.write(list(df.columns))

        # Rješavanje stvarnih naziva kolona (fuzzy matching)
        resolved = resolve_columns(config, df.columns, debug_mode=debug_mode, ducan_naziv=ducan_naziv)

        # Ako maloprodajna nije nađena, pokušaj auto-detect
        if resolved["maloprodajna"] is None:
            candidates = [c for c in df.columns if "maloprod" in c.lower()]
            if candidates:
                resolved["maloprodajna"] = candidates[0]
                if debug_mode:
                    st.write(f"  🔧 Auto-detect maloprodajna → `{resolved['maloprodajna']}`")
            else:
                st.warning(f"{ducan_naziv}: nije pronađena kolona s maloprodajnom cijenom")
                return rezultati

        # Konzum specifično: eksplicitno isključi "NAJNIŽA CIJENA" kolonu
        # (nikad ne smije biti akcijska ili maloprodajna)
        for key in ["maloprodajna", "akcijska"]:
            col = resolved.get(key)
            if col and "najni" in col.lower():
                st.warning(f"{ducan_naziv}: kolona '{col}' izgleda kao NAJNIŽA CIJENA — isključujem!")
                resolved[key] = None

        # Konvertiraj cijenske kolone u float
        if resolved["maloprodajna"]:
            df[resolved["maloprodajna"]] = df[resolved["maloprodajna"]].apply(convert_price)
        if resolved["akcijska"]:
            df[resolved["akcijska"]] = df[resolved["akcijska"]].apply(convert_price)

        if debug_mode:
            st.write(f"**Primjer prvih 3 retka (cijene):**")
            cols_to_show = [c for c in [resolved["naziv"], resolved["maloprodajna"], resolved["akcijska"]] if c]
            st.dataframe(df[cols_to_show].head(3))

        # Izračunaj finalnu cijenu
        df["CIJENA"] = df.apply(lambda row: determine_final_price(row, resolved), axis=1)

        naziv_col    = resolved["naziv"]
        sifra_col    = resolved["sifra"]
        barkod_col   = resolved["barkod"]
        kat_col      = resolved["kategorija"]
        jed_col      = resolved["jedinica"]
        mal_col      = resolved["maloprodajna"]
        akc_col      = resolved["akcijska"]

        # Pretraga po barkodu
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

        # Pretraga po pojmovima
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
        debug_mode = st.checkbox("🐛 Debug mode", value=False,
                                  help="Prikazuje nazive kolona i prvih par redaka za svaki dućan")

    st.markdown(r"""
<div style="background:#1e1e2e; border-radius:10px; padding:1rem 1.5rem; margin-bottom:1.5rem;">
<b>🔍 Kako pretraživati</b><br><br>
* Do 6 pojmova ili 1 barkod<br>
* Bez * → traži na početku naziva<br>
&nbsp;&nbsp;&nbsp;<code>mlijeko</code> → Mlijeko Dukat, Mlijeko fresh...<br>
* Bilo gdje u nazivu → koristi *<br>
&nbsp;&nbsp;&nbsp;<code>*mlijeko*</code> → sve što ima „mlijeko"<br>
&nbsp;&nbsp;&nbsp;<code>sir ?0%</code> → sir 20%, 30%, 00%...<br><br>
💡 Brzi trikovi: <code>*kava*</code>, <code>*mlijeko 3.5*</code>, <code>dukat*</code><br>
Pretraga ne razlikuje velika/mala slova
</div>
""", unsafe_allow_html=True)

    st.markdown("### 🔢 Pretraga po barkodu")
    barkod_input = st.text_input("Unesite barkod proizvoda",
                                  placeholder="npr. 3017620422003", key="barkod")

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
            # Deepcopy config da ne mutiramo global
            import copy
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
            st.metric("Artikala", len(df))
        with c2:
            min_c = df["Cijena (€)"].min()
            st.metric("Najjeftinije", f"€{min_c:.2f}" if pd.notna(min_c) else "N/A")
        with c3:
            st.metric("Lanaca", df["Trgovački lanac"].nunique())

        if barkod:
            st.markdown(f"### 🏆 Rezultati za barkod **{barkod}**")
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
<div style="text-align:center; color:#555; padding:2rem 0 1rem 0; font-size:0.85rem;">
    Izrađeno uz pomoć AI | Cijene ažurirane pon–sub ~8:20
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()