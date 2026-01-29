# Lokalno testiranje BEZ Dropboxa

Ako želiš prvo testirati aplikaciju lokalno bez Dropbox integracije:

## 1. Kreiraj `data/` folder

```bash
mkdir data
```

## 2. Kopiraj CSV cjenike u `data/`

Kopiraj sve CSV datoteke iz `D:\Py_skripte\Cjenici_jucer\` u `data/` folder:

```
pretraga-cijena/
├── app.py
├── data/
│   ├── plodine_jucer.csv
│   ├── eurospin_jucer.csv
│   ├── kaufland_jucer.csv
│   ├── konzum_jucer.csv
│   ├── lidl_jucer.csv
│   └── spar_jucer.csv
```

## 3. Pokreni aplikaciju

```bash
streamlit run app.py
```

Aplikacija će automatski detektirati da Dropbox nije konfiguriran i koristit će lokalne CSV datoteke iz `data/` foldera.

## 4. Testiraj pretragu

- Unesi pojmove (npr. "mlijeko*", "jogurt", "sir")
- Klikni "Pretraži cijene"
- Provjeri rezultate
- Testiraj download u Excel

## 5. Kada si spreman za Dropbox

1. Dodaj Dropbox token u `.streamlit/secrets.toml`
2. Uploada CSV-ove na Dropbox (koristi `upload_to_dropbox.py`)
3. Ponovno pokreni aplikaciju - sada će koristiti Dropbox

---

## Razlika između lokalnog i Dropbox moda

| Feature | Lokalni mod | Dropbox mod |
|---------|-------------|-------------|
| CSV lokacija | `data/` folder | Dropbox `/Cjenici_jucer/` |
| Automatsko ažuriranje | Ne | Da (kad uploadaš nove CSV-ove) |
| Cache | 1 sat | 1 sat |
| Deployment | Ne može na Cloud | Može na Streamlit Cloud |

**Preporuka:** Testiraj lokalno, zatim pređi na Dropbox za production.
