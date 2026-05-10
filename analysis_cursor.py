# ============================================================
# Trabajo individual Spotify — The Smiths
# Análisis principal en Cursor / Python script
# ============================================================

import ast
import os
import re
import json
import time
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt
import requests

try:
    import gdown
except ImportError:
    gdown = None

try:
    from wordcloud import WordCloud
except ImportError:
    WordCloud = None


# ============================================================
# 1. Configuración general
# ============================================================

TARGET_ARTIST_NAME = "The Smiths"

DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
PLOTS_DIR = os.path.join("outputs", "plots")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

DATA_FILE = os.path.join(RAW_DIR, "tracks_features.csv")

# ID usado en el notebook base para descargar tracks_features.csv.
# Fuente indicada en el notebook de ejemplo: Kaggle Spotify 1.2M+ Songs.
GDRIVE_FILE_ID = "1jsXTNtGhOrsCApQctYx-hRxAQASAcPlI"


# ============================================================
# 2. Funciones auxiliares
# ============================================================

def parse_possible_list(value):
    """
    Convierte valores tipo "['The Smiths']" en una lista real.
    Si no se puede convertir, devuelve el texto como una lista.
    """
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


def artist_exact_match(artists_value, target_artist):
    """
    Comprueba si el artista aparece exactamente en la lista de artistas.
    Evita falsos positivos como 'The Smithsonian Chamber Players'.
    """
    artists = parse_possible_list(artists_value)
    return any(a.lower().strip() == target_artist.lower() for a in artists)


def normalize_album_name(album):
    """
    Limpia nombres de álbumes para compararlos con la discografía oficial.
    Ejemplos:
    - 'The Queen Is Dead (Deluxe Edition)' -> 'The Queen Is Dead'
    - 'The Smiths - 2011 Remaster' -> 'The Smiths'
    """
    album = str(album)

    # Quitar contenido entre paréntesis y corchetes
    album = re.sub(r"\(.*?\)", "", album)
    album = re.sub(r"\[.*?\]", "", album)

    # Quitar sufijos después de guion
    album = re.sub(r"\s*-\s*.*Remaster.*$", "", album, flags=re.IGNORECASE)
    album = re.sub(r"\s*-\s*.*Deluxe.*$", "", album, flags=re.IGNORECASE)
    album = re.sub(r"\s*-\s*.*Edition.*$", "", album, flags=re.IGNORECASE)
    album = re.sub(r"\s*-\s*.*Expanded.*$", "", album, flags=re.IGNORECASE)
    album = re.sub(r"\s*-\s*.*Collector.*$", "", album, flags=re.IGNORECASE)

    # Limpiar espacios
    album = re.sub(r"\s+", " ", album).strip()
    return album


def clean_track_title(title):
    """
    Limpia títulos para mostrar en gráficos.
    """
    title = str(title)
    title = re.sub(r"\s*-\s*\d{4}\s*Remaster.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*-\s*Remaster.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*-\s*Digital Remaster.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def download_dataset_if_needed():
    """
    Descarga el dataset si no existe en data/raw.
    Si falla la descarga, se debe colocar manualmente tracks_features.csv
    dentro de data/raw.
    """
    if os.path.exists(DATA_FILE):
        print(f"Dataset encontrado: {DATA_FILE}")
        return

    print("No se encontró tracks_features.csv en data/raw.")

    if gdown is None:
        print("No está instalado gdown.")
        print("Instala dependencias con: pip install -r requirements.txt")
        return

    print("Intentando descargar dataset con gdown...")
    url = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"

    try:
        gdown.download(url, DATA_FILE, quiet=False)
    except Exception as e:
        print("No se pudo descargar automáticamente el dataset.")
        print("Error:", e)
        print("Coloca manualmente tracks_features.csv en data/raw.")


# ============================================================
# 3. Carga del dataset
# ============================================================

download_dataset_if_needed()

if not os.path.exists(DATA_FILE):
    raise FileNotFoundError(
        "No se encontró tracks_features.csv. "
        "Colócalo en data/raw/tracks_features.csv y vuelve a ejecutar."
    )

df = pd.read_csv(DATA_FILE)

print("\n============================================================")
print("Dataset cargado")
print("============================================================")
print("Shape:", df.shape)
print("Columnas:")
print(df.columns.tolist())


# ============================================================
# 4. Filtrado exacto del artista
# ============================================================

if "artists" not in df.columns:
    raise KeyError("El dataset no contiene la columna 'artists'.")

# No usamos str.contains porque introduce falsos positivos como
# 'The Smithsonian Chamber Players'.
smiths_df = df[
    df["artists"].apply(lambda x: artist_exact_match(x, TARGET_ARTIST_NAME))
].copy()

print("\n============================================================")
print(f"Filtrado exacto del artista: {TARGET_ARTIST_NAME}")
print("============================================================")
print(f"Total de canciones encontradas antes del filtro de álbumes: {len(smiths_df)}")

if len(smiths_df) == 0:
    raise ValueError(
        "No se encontraron canciones de The Smiths en el dataset. "
        "Revisa si el nombre del artista aparece de otra forma en la columna artists."
    )

print("\nPrimeras canciones encontradas:")
print(
    smiths_df[["name", "album", "artists", "year"]]
    .sort_values(["year", "album", "name"])
    .head(30)
    .to_string(index=False)
)


# ============================================================
# 5. Diagnóstico de álbumes antes del filtrado
# ============================================================

albums_raw = (
    smiths_df
    .groupby("album")
    .agg(
        canciones=("name", "count"),
        year=("year", "min")
    )
    .sort_values(["year", "album"])
)

albums_raw.to_csv(
    os.path.join(PROCESSED_DIR, "albumes_encontrados_antes_del_filtrado.csv")
)

print("\n============================================================")
print("Álbumes encontrados antes de filtrar")
print("============================================================")
print(albums_raw.to_string())

smiths_df["short_album_name"] = smiths_df["album"].apply(normalize_album_name)

albums_normalized = (
    smiths_df
    .groupby("short_album_name")
    .agg(
        canciones=("name", "count"),
        year=("year", "min")
    )
    .sort_values(["year", "short_album_name"])
)

albums_normalized.to_csv(
    os.path.join(PROCESSED_DIR, "albumes_normalizados.csv")
)

print("\n============================================================")
print("Álbumes normalizados encontrados")
print("============================================================")
print(albums_normalized.to_string())


# ============================================================
# 6. Filtrar álbumes de estudio de The Smiths
# ============================================================

# Según la discografía oficial, The Smiths tiene 4 álbumes de estudio.
STUDIO_ALBUMS = [
    "The Smiths",
    "Meat Is Murder",
    "The Queen Is Dead",
    "Strangeways, Here We Come"
]

studio_df = smiths_df[
    smiths_df["short_album_name"].isin(STUDIO_ALBUMS)
].copy()

studio_df = (
    studio_df
    .sort_values(["year", "short_album_name", "track_number", "name"])
    .drop_duplicates(subset=["short_album_name", "name"], keep="first")
    .reset_index(drop=True)
)

studio_df["clean_name"] = studio_df["name"].apply(clean_track_title)

studio_df.to_csv(
    os.path.join(PROCESSED_DIR, "the_smiths_studio_tracks.csv"),
    index=False
)

print("\n============================================================")
print("Resultado del filtrado de álbumes de estudio")
print("============================================================")
print(f"Total de canciones después de filtrar álbumes de estudio: {len(studio_df)}")

album_counts = []

print("\nÁlbumes de estudio incluidos:")
for album in STUDIO_ALBUMS:
    count = int((studio_df["short_album_name"] == album).sum())
    album_counts.append({"album": album, "canciones": count})
    print(f"- {album}: {count} canciones")

album_counts_df = pd.DataFrame(album_counts)
album_counts_df.to_csv(
    os.path.join(PROCESSED_DIR, "conteo_albumes_estudio_the_smiths.csv"),
    index=False
)

print("\nCanciones filtradas:")
if len(studio_df) > 0:
    print(
        studio_df[["clean_name", "short_album_name", "album", "year", "track_number"]]
        .sort_values(["year", "short_album_name", "track_number", "clean_name"])
        .to_string(index=False)
    )
else:
    print("No quedaron canciones después del filtrado.")


# ============================================================
# 7. Gráficos principales por canción
# ============================================================

if len(studio_df) > 0:
    if "track_number" in studio_df.columns:
        studio_df_plot = studio_df.sort_values(["short_album_name", "track_number"]).copy()
    else:
        studio_df_plot = studio_df.sort_values(["short_album_name", "clean_name"]).copy()

    # --------------------------------------------------------
    # 7.1 Energy por canción
    # --------------------------------------------------------
    plt.figure(figsize=(11, 6))
    plt.barh(studio_df_plot["clean_name"], studio_df_plot["energy"])
    plt.xlabel("Energy")
    plt.ylabel("Canción")
    plt.title("Energy por canción — The Smiths")
    plt.gca().invert_yaxis()
    plt.tight_layout()

    plot_path = os.path.join(PLOTS_DIR, "01_energy_por_cancion.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"\nGráfico guardado: {plot_path}")

    # --------------------------------------------------------
    # 7.2 Valence por canción
    # --------------------------------------------------------
    plt.figure(figsize=(11, 6))
    plt.barh(studio_df_plot["clean_name"], studio_df_plot["valence"])
    plt.xlabel("Valence / positividad musical")
    plt.ylabel("Canción")
    plt.title("Valence por canción — The Smiths")
    plt.gca().invert_yaxis()
    plt.tight_layout()

    plot_path = os.path.join(PLOTS_DIR, "02_valence_por_cancion.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Gráfico guardado: {plot_path}")

    # --------------------------------------------------------
    # 7.3 Energy vs Valence por canción
    # --------------------------------------------------------
    plt.figure(figsize=(9, 6))
    plt.scatter(studio_df_plot["valence"], studio_df_plot["energy"], alpha=0.8)

    for _, row in studio_df_plot.iterrows():
        plt.text(
            row["valence"],
            row["energy"],
            row["clean_name"][:22],
            fontsize=8,
            alpha=0.8
        )

    plt.xlabel("Valence / positividad musical")
    plt.ylabel("Energy / energía")
    plt.title("Energy vs Valence por canción — The Smiths")
    plt.tight_layout()

    plot_path = os.path.join(PLOTS_DIR, "03_energy_vs_valence_por_cancion.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Gráfico guardado: {plot_path}")
else:
    print("No se generaron gráficos por canción porque no hay canciones filtradas.")


# ============================================================
# 8. Letras con lyrics.ovh
# ============================================================

LYRICS_CACHE_FILE = os.path.join(PROCESSED_DIR, "lyrics_cache.json")


def load_lyrics_cache(path=LYRICS_CACHE_FILE):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_lyrics_cache(cache, path=LYRICS_CACHE_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def clean_track_title_for_lyrics(title):
    """
    Limpia títulos para mejorar la búsqueda en lyrics.ovh.
    """
    title = str(title)
    title = re.sub(r"\s*-\s*\d{4}\s*Remaster.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*-\s*Remaster.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*-\s*Digital Remaster.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*-\s*Live.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*-\s*Demo.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\(.*?\)", "", title)
    title = re.sub(r"\s*\[.*?\]", "", title)
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def get_lyrics_lyricsovh(artist, title, cache):
    """
    Consulta lyrics.ovh.
    Devuelve None si no encuentra letra.
    """
    clean_title = clean_track_title_for_lyrics(title)
    key = f"{artist}|||{clean_title}"

    if key in cache:
        return cache[key]

    url = (
        "https://api.lyrics.ovh/v1/"
        f"{requests.utils.quote(artist)}/"
        f"{requests.utils.quote(clean_title)}"
    )

    try:
        response = requests.get(url, timeout=12)

        if response.status_code == 200:
            data = response.json()
            lyrics = data.get("lyrics")

            if lyrics and len(lyrics.strip()) > 0:
                cache[key] = lyrics
            else:
                cache[key] = None
        else:
            cache[key] = None

    except Exception:
        cache[key] = None

    time.sleep(0.3)
    return cache[key]


lyrics_cache = load_lyrics_cache()

MAX_SONGS_FOR_LYRICS = 25
lyrics_rows = []

songs_to_query = (
    studio_df[["name", "short_album_name"]]
    .drop_duplicates()
    .head(MAX_SONGS_FOR_LYRICS)
)

for _, row in songs_to_query.iterrows():
    title = row["name"]
    album = row["short_album_name"]

    lyrics = get_lyrics_lyricsovh(TARGET_ARTIST_NAME, title, lyrics_cache)

    if lyrics:
        lyrics_rows.append({
            "artist": TARGET_ARTIST_NAME,
            "song": clean_track_title(title),
            "album": album,
            "source": "The Smiths",
            "lyrics": lyrics,
            "lyrics_length": len(lyrics.split())
        })

save_lyrics_cache(lyrics_cache)

lyrics_df = pd.DataFrame(
    lyrics_rows,
    columns=["artist", "song", "album", "source", "lyrics", "lyrics_length"]
)

print("\n============================================================")
print("Letras recuperadas de The Smiths")
print("============================================================")
print(f"Letras encontradas: {len(lyrics_df)} de {len(songs_to_query)} canciones consultadas")

if len(lyrics_df) > 0:
    print(lyrics_df[["artist", "song", "album", "lyrics_length"]].to_string(index=False))
else:
    print("No se encontraron letras de The Smiths con lyrics.ovh.")


# ============================================================
# 9. Alternativa para análisis de letras
# ============================================================

if len(lyrics_df) == 0:
    print("\nSe usará un conjunto de canciones de varios artistas para crear los gráficos de letras.")

    lyrics_candidates = [
        {"artist": "Coldplay", "song": "Yellow"},
        {"artist": "Coldplay", "song": "The Scientist"},
        {"artist": "Radiohead", "song": "Creep"},
        {"artist": "Oasis", "song": "Wonderwall"},
        {"artist": "Queen", "song": "Bohemian Rhapsody"},
        {"artist": "Nirvana", "song": "Smells Like Teen Spirit"},
        {"artist": "Adele", "song": "Hello"},
        {"artist": "The Beatles", "song": "Hey Jude"},
        {"artist": "R.E.M.", "song": "Losing My Religion"},
        {"artist": "David Bowie", "song": "Heroes"},
    ]

    alt_rows = []

    for item in lyrics_candidates:
        artist = item["artist"]
        song = item["song"]
        lyrics = get_lyrics_lyricsovh(artist, song, lyrics_cache)

        if lyrics:
            alt_rows.append({
                "artist": artist,
                "song": song,
                "album": "",
                "source": "Conjunto de artistas",
                "lyrics": lyrics,
                "lyrics_length": len(lyrics.split())
            })

    save_lyrics_cache(lyrics_cache)

    lyrics_df = pd.DataFrame(
        alt_rows,
        columns=["artist", "song", "album", "source", "lyrics", "lyrics_length"]
    )

    print(f"Letras encontradas en conjunto alternativo: {len(lyrics_df)} de {len(lyrics_candidates)} canciones consultadas")

    if len(lyrics_df) > 0:
        print(lyrics_df[["artist", "song", "lyrics_length"]].to_string(index=False))
    else:
        print("No se encontraron letras tampoco en el conjunto alternativo.")

lyrics_df.to_csv(
    os.path.join(PROCESSED_DIR, "lyrics_summary.csv"),
    index=False
)


# ============================================================
# 10. Análisis de palabras frecuentes
# ============================================================

STOPWORDS = {
    "the", "and", "you", "your", "that", "this", "with", "for", "are",
    "was", "were", "but", "not", "have", "has", "had", "they", "them",
    "his", "her", "she", "him", "our", "out", "all", "can", "will",
    "just", "from", "there", "what", "when", "where", "who", "why",
    "how", "into", "about", "over", "under", "then", "than", "too",
    "i", "me", "my", "we", "us", "a", "an", "of", "to", "in", "on",
    "it", "is", "be", "am", "do", "so", "no", "yes", "oh", "la",
    "na", "yeah", "hey", "got", "get", "let"
}


def tokenize_lyrics(text):
    text = str(text).lower()
    words = re.findall(r"[a-zA-Z']+", text)
    words = [w for w in words if w not in STOPWORDS and len(w) > 2]
    return words


if len(lyrics_df) > 0:
    all_words = []

    for lyrics in lyrics_df["lyrics"]:
        all_words.extend(tokenize_lyrics(lyrics))

    word_counts = Counter(all_words)
    common_words = word_counts.most_common(20)

    words_df = pd.DataFrame(common_words, columns=["word", "frequency"])

    words_df.to_csv(
        os.path.join(PROCESSED_DIR, "lyrics_word_frequency.csv"),
        index=False
    )

    print("\n============================================================")
    print("Palabras más frecuentes en las letras")
    print("============================================================")
    print(words_df.to_string(index=False))

    plt.figure(figsize=(10, 6))
    plt.barh(words_df["word"], words_df["frequency"])
    plt.xlabel("Frecuencia")
    plt.ylabel("Palabra")
    plt.title("Palabras más frecuentes en las letras analizadas")
    plt.gca().invert_yaxis()
    plt.tight_layout()

    plot_path = os.path.join(PLOTS_DIR, "04_palabras_frecuentes_letras.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Gráfico guardado: {plot_path}")

    if WordCloud is not None:
        text_for_wordcloud = " ".join(lyrics_df["lyrics"].astype(str))

        wordcloud = WordCloud(
            width=1000,
            height=500,
            background_color="white",
            stopwords=STOPWORDS,
            max_words=100
        ).generate(text_for_wordcloud)

        plt.figure(figsize=(12, 6))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.title("Nube de palabras de las letras analizadas")
        plt.tight_layout()

        plot_path = os.path.join(PLOTS_DIR, "05_nube_palabras_letras.png")
        plt.savefig(plot_path, dpi=150)
        plt.close()
        print(f"Gráfico guardado: {plot_path}")
    else:
        print("No se generó nube de palabras porque falta la librería wordcloud.")
else:
    print("\nNo se puede generar análisis de palabras porque no se recuperaron letras.")


# ============================================================
# 11. Resumen para la memoria
# ============================================================

summary_text = """
1. Se cargó el dataset de Spotify tracks_features.csv.
2. Se filtraron las canciones del artista The Smiths usando coincidencia exacta en la columna artists.
3. Se evitó usar str.contains porque generaba falsos positivos como The Smithsonian Chamber Players.
4. Se compararon los álbumes encontrados en el dataset con la discografía oficial del artista.
5. Se definieron como álbumes de estudio oficiales:
   The Smiths, Meat Is Murder, The Queen Is Dead y Strangeways, Here We Come.
6. Tras aplicar el filtro, el dataset solo conservó canciones del álbum:
   Strangeways, Here We Come.
   Esto indica que el dataset utilizado no contiene canciones originales de los otros
   álbumes de estudio de The Smiths.
7. Como tres álbumes quedan sin canciones, los gráficos principales se realizaron por canción,
   no por álbum, para aportar más valor analítico.
8. Se generaron gráficos de energy, valence y energy vs valence por canción.
9. Se intentó obtener letras de The Smiths usando lyrics.ovh, pero la API no devolvió resultados.
10. Para cumplir el apartado de análisis de letras, se utilizó un conjunto alternativo de canciones
    de varios artistas, tal como permite el enunciado.
11. Se generaron gráficos de frecuencia de palabras y una nube de palabras a partir de las letras recuperadas.
"""

with open(os.path.join(PROCESSED_DIR, "resumen_memoria.txt"), "w", encoding="utf-8") as f:
    f.write(summary_text)

print("\n============================================================")
print("RESUMEN PARA LA MEMORIA")
print("============================================================")
print(summary_text)
print(f"Resumen guardado: {os.path.join(PROCESSED_DIR, 'resumen_memoria.txt')}")
