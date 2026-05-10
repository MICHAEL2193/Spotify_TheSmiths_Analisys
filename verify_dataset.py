# ============================================================
# Verificación del dataset para The Smiths
# ============================================================

import ast
import os
import re
from collections import Counter

import pandas as pd

DATA_FILE = "data/raw/tracks_features.csv"
TARGET_ARTIST_NAME = "The Smiths"

STUDIO_ALBUMS = [
    "The Smiths",
    "Meat Is Murder",
    "The Queen Is Dead",
    "Strangeways, Here We Come",
]

KNOWN_TRACKS = [
    # The Smiths
    "Reel Around the Fountain",
    "This Charming Man",
    "Still Ill",
    "Hand in Glove",

    # Meat Is Murder
    "The Headmaster Ritual",
    "Rusholme Ruffians",
    "That Joke Isn't Funny Anymore",
    "How Soon Is Now?",

    # The Queen Is Dead
    "The Queen Is Dead",
    "Bigmouth Strikes Again",
    "The Boy with the Thorn in His Side",
    "There Is a Light That Never Goes Out",

    # Strangeways, Here We Come
    "A Rush and a Push and the Land Is Ours",
    "Girlfriend in a Coma",
    "Stop Me If You Think You've Heard This One Before",
    "Last Night I Dreamt That Somebody Loved Me",
]


def parse_possible_list(value):
    if pd.isna(value):
        return []

    text = str(value)

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed]
        return [str(parsed).strip()]
    except Exception:
        return [text.strip()]


def normalize_text(text):
    text = str(text).lower()
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\s*-\s*\d{4}\s*remaster.*$", "", text)
    text = re.sub(r"\s*-\s*remaster.*$", "", text)
    text = re.sub(r"\s*-\s*digital remaster.*$", "", text)
    text = re.sub(r"\s*-\s*live.*$", "", text)
    text = re.sub(r"\s*-\s*demo.*$", "", text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def artist_exact_match(artists_value, target_artist):
    artists = parse_possible_list(artists_value)
    return any(a.lower().strip() == target_artist.lower() for a in artists)


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


if not os.path.exists(DATA_FILE):
    raise FileNotFoundError(
        f"No se encontró {DATA_FILE}. Ejecuta primero analysis_cursor.py "
        "o coloca tracks_features.csv en data/raw."
    )

df = pd.read_csv(DATA_FILE)

print_section("1. Información general del dataset")
print("Shape:", df.shape)
print("Columnas:", df.columns.tolist())


# ------------------------------------------------------------
# 2. Búsqueda por contains vs artista exacto
# ------------------------------------------------------------

print_section("2. Comparación: búsqueda por texto vs artista exacto")

contains_mask = df["artists"].astype(str).str.contains(
    TARGET_ARTIST_NAME, case=False, na=False
)

exact_mask = df["artists"].apply(
    lambda x: artist_exact_match(x, TARGET_ARTIST_NAME)
)

contains_df = df[contains_mask].copy()
exact_df = df[exact_mask].copy()

print(f"Filas encontradas con str.contains('{TARGET_ARTIST_NAME}'): {len(contains_df)}")
print(f"Filas encontradas con artista exacto '{TARGET_ARTIST_NAME}': {len(exact_df)}")

false_positives = contains_df[~contains_df.index.isin(exact_df.index)]
print(f"Posibles falsos positivos del filtro contains: {len(false_positives)}")

if len(false_positives) > 0:
    print("\nEjemplos de posibles falsos positivos:")
    print(
        false_positives[["name", "album", "artists", "year"]]
        .head(20)
        .to_string(index=False)
    )


# ------------------------------------------------------------
# 3. Álbumes del artista exacto
# ------------------------------------------------------------

print_section("3. Álbumes encontrados para The Smiths como artista exacto")

if len(exact_df) > 0:
    albums_exact = (
        exact_df
        .groupby("album")
        .agg(
            canciones=("name", "count"),
            year=("year", "min")
        )
        .sort_values(["year", "album"])
    )
    print(albums_exact.to_string())
else:
    print("No se encontraron filas con The Smiths como artista exacto.")


# ------------------------------------------------------------
# 4. Búsqueda global por nombres de álbumes de estudio
# ------------------------------------------------------------

print_section("4. Búsqueda directa de los 4 álbumes de estudio en todo el dataset")

df["album_norm"] = df["album"].apply(normalize_text)

for album in STUDIO_ALBUMS:
    album_norm = normalize_text(album)
    rows = df[df["album_norm"] == album_norm].copy()

    print(f"\nÁlbum buscado: {album}")
    print(f"Filas encontradas en todo el dataset: {len(rows)}")

    if len(rows) > 0:
        print(
            rows[["name", "album", "artists", "year"]]
            .head(15)
            .to_string(index=False)
        )
    else:
        print("No aparece ningún registro con ese álbum.")


# ------------------------------------------------------------
# 5. Búsqueda de canciones conocidas
# ------------------------------------------------------------

print_section("5. Búsqueda directa de canciones conocidas de The Smiths")

df["name_norm"] = df["name"].apply(normalize_text)

for track in KNOWN_TRACKS:
    track_norm = normalize_text(track)
    rows = df[df["name_norm"] == track_norm].copy()

    print(f"\nCanción buscada: {track}")
    print(f"Filas encontradas: {len(rows)}")

    if len(rows) > 0:
        print(
            rows[["name", "album", "artists", "year"]]
            .head(10)
            .to_string(index=False)
        )


# ------------------------------------------------------------
# 6. Comprobación con artist_ids
# ------------------------------------------------------------

print_section("6. Comprobación con artist_ids")

if "artist_ids" not in df.columns:
    print("El dataset no contiene la columna artist_ids.")
else:
    confirmed_studio = exact_df.copy()
    confirmed_studio["album_norm"] = confirmed_studio["album"].apply(normalize_text)

    confirmed_studio = confirmed_studio[
        confirmed_studio["album_norm"].isin([normalize_text(a) for a in STUDIO_ALBUMS])
    ]

    all_ids = []
    for value in confirmed_studio["artist_ids"]:
        all_ids.extend(parse_possible_list(value))

    id_counts = Counter(all_ids)
    print("IDs de artista encontrados en filas confirmadas de The Smiths:")
    print(id_counts)

    if len(id_counts) > 0:
        likely_smiths_id = id_counts.most_common(1)[0][0]
        print(f"\nID candidato para The Smiths: {likely_smiths_id}")

        id_mask = df["artist_ids"].astype(str).str.contains(
            likely_smiths_id, regex=False, na=False
        )
        id_df = df[id_mask].copy()

        print(f"Filas encontradas usando artist_id candidato: {len(id_df)}")

        albums_by_id = (
            id_df
            .groupby("album")
            .agg(
                canciones=("name", "count"),
                year=("year", "min")
            )
            .sort_values(["year", "album"])
        )

        print("\nÁlbumes encontrados usando artist_id:")
        print(albums_by_id.to_string())
    else:
        print("No hay IDs confirmados porque no se encontraron filas de álbumes de estudio.")


# ------------------------------------------------------------
# 7. Conclusión orientativa
# ------------------------------------------------------------

print_section("7. Conclusión orientativa")

print("""
Revisa especialmente estas secciones:

- Sección 3:
  muestra qué álbumes aparecen cuando el artista es exactamente The Smiths.

- Sección 4:
  busca directamente los nombres de los cuatro álbumes de estudio en todo el dataset.

- Sección 5:
  busca canciones conocidas de los álbumes que aparecen con 0 canciones.

- Sección 6:
  comprueba usando artist_ids, que suele ser más fiable que buscar texto en artists.

Si los álbumes The Smiths, Meat Is Murder y The Queen Is Dead no aparecen en las secciones 3, 4 ni 6,
entonces podemos afirmar que el dataset usado no contiene esos álbumes originales para The Smiths.
""")
