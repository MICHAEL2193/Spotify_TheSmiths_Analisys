# ============================================================
# Web app Streamlit — Trabajo Spotify / The Smiths
# ============================================================

import os
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PLOTS_DIR = BASE_DIR / "outputs" / "plots"

TRACKS_FILE = PROCESSED_DIR / "the_smiths_studio_tracks.csv"
ALBUM_COUNTS_FILE = PROCESSED_DIR / "conteo_albumes_estudio_the_smiths.csv"
LYRICS_SUMMARY_FILE = PROCESSED_DIR / "lyrics_summary.csv"
WORDS_FILE = PROCESSED_DIR / "lyrics_word_frequency.csv"
WORDCLOUD_FILE = PLOTS_DIR / "05_nube_palabras_letras.png"

st.set_page_config(
    page_title="Spotify + Letras — The Smiths",
    page_icon="🎧",
    layout="wide"
)

st.title("🎧 Spotify Dataset Analysis — The Smiths")
st.caption("Trabajo individual: filtrado de álbumes de estudio, análisis por canción y exploración de letras.")


@st.cache_data
def read_csv_if_exists(path):
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def clean_song_name(title):
    title = str(title)
    title = re.sub(r"\s*-\s*\d{4}\s*Remaster.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*-\s*Remaster.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def get_lyrics_ovh(artist, song):
    url = f"https://api.lyrics.ovh/v1/{requests.utils.quote(artist)}/{requests.utils.quote(song)}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get("lyrics")
    except Exception:
        return None
    return None


tracks_df = read_csv_if_exists(TRACKS_FILE)
album_counts_df = read_csv_if_exists(ALBUM_COUNTS_FILE)
lyrics_summary_df = read_csv_if_exists(LYRICS_SUMMARY_FILE)
words_df = read_csv_if_exists(WORDS_FILE)

if tracks_df.empty:
    st.warning(
        "No se encontraron los datos procesados. Ejecuta primero `python analysis_cursor.py` "
        "desde la raíz del proyecto para generar los CSV y gráficos."
    )
    st.stop()

if "clean_name" not in tracks_df.columns:
    tracks_df["clean_name"] = tracks_df["name"].apply(clean_song_name)

# ============================================================
# Sidebar
# ============================================================

st.sidebar.header("Filtros")

album_options = sorted(tracks_df["short_album_name"].dropna().unique().tolist())
selected_album = st.sidebar.selectbox("Álbum de estudio disponible", album_options)

filtered_df = tracks_df[tracks_df["short_album_name"] == selected_album].copy()

feature_options = [
    col for col in [
        "energy", "valence", "danceability", "acousticness", "instrumentalness",
        "liveness", "speechiness", "tempo", "loudness", "duration_ms"
    ]
    if col in filtered_df.columns
]

selected_feature = st.sidebar.selectbox("Variable musical para explorar", feature_options)

# ============================================================
# Tabs
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "1️⃣ Filtrado",
    "2️⃣ Canciones",
    "3️⃣ Audio features",
    "4️⃣ Letras"
])


with tab1:
    st.header("1️⃣ Filtrado de álbumes de estudio")

    st.markdown(
        """
        El enunciado pide filtrar los álbumes para conservar únicamente los álbumes de estudio.
        Para The Smiths se usó la lista oficial de cuatro álbumes de estudio:

        - The Smiths
        - Meat Is Murder
        - The Queen Is Dead
        - Strangeways, Here We Come

        Al comparar esta lista con el dataset, solo aparecen canciones originales de The Smiths
        en el álbum **Strangeways, Here We Come**. Por eso los gráficos principales se hacen
        por canción y no por álbum, ya que un gráfico con tres álbumes vacíos aportaría poco valor.
        """
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Conteo por álbum de estudio")
        if not album_counts_df.empty:
            st.dataframe(album_counts_df, use_container_width=True)
        else:
            st.info("No se encontró el CSV de conteo de álbumes.")

    with col2:
        st.subheader("Canciones conservadas tras el filtro")
        st.dataframe(
            filtered_df[["clean_name", "short_album_name", "year", "track_number"]],
            use_container_width=True,
            hide_index=True
        )


with tab2:
    st.header("2️⃣ Exploración por canción")

    st.markdown(
        "Como el dataset solo conserva un álbum de estudio de The Smiths, "
        "la visualización se centra en comparar canciones individuales."
    )

    fig = px.bar(
        filtered_df.sort_values("track_number"),
        x=selected_feature,
        y="clean_name",
        orientation="h",
        title=f"{selected_feature} por canción — {selected_album}",
        labels={"clean_name": "Canción", selected_feature: selected_feature},
    )
    fig.update_layout(yaxis={"categoryorder": "array", "categoryarray": filtered_df.sort_values("track_number")["clean_name"].tolist()[::-1]})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Datos de canciones")
    display_cols = ["clean_name", "energy", "valence", "danceability", "acousticness", "tempo", "duration_ms"]
    display_cols = [c for c in display_cols if c in filtered_df.columns]
    st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)


with tab3:
    st.header("3️⃣ Comparación Energy vs Valence")

    st.markdown(
        "Este gráfico permite ver si las canciones disponibles tienden a ser más energéticas, "
        "más positivas o más oscuras según las variables de Spotify."
    )

    fig = px.scatter(
        filtered_df,
        x="valence",
        y="energy",
        hover_name="clean_name",
        text="clean_name",
        title="Energy vs Valence por canción — The Smiths",
        labels={
            "valence": "Valence / positividad musical",
            "energy": "Energy / energía"
        }
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)


with tab4:
    st.header("4️⃣ Exploración de letras")

    st.markdown(
        """
        Primero se intentó obtener letras de The Smiths con `lyrics.ovh`, pero no se encontraron resultados.
        Para cumplir el apartado de letras, se utilizó un conjunto alternativo de canciones de varios artistas,
        tal como permite el enunciado.
        """
    )

    if not lyrics_summary_df.empty:
        st.subheader("Letras recuperadas")
        st.dataframe(
            lyrics_summary_df[["artist", "song", "source", "lyrics_length"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("No se encontró información de letras. Ejecuta `python analysis_cursor.py`.")

    if not words_df.empty:
        st.subheader("Palabras más frecuentes")
        fig = px.bar(
            words_df,
            x="frequency",
            y="word",
            orientation="h",
            title="Palabras más frecuentes en las letras analizadas",
            labels={"word": "Palabra", "frequency": "Frecuencia"}
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No se encontró el archivo de frecuencia de palabras.")

    if WORDCLOUD_FILE.exists():
        st.subheader("Nube de palabras")
        st.image(str(WORDCLOUD_FILE), use_container_width=True)

    st.divider()
    st.subheader("Consulta manual a lyrics.ovh")
    st.caption("Componente extra para probar una canción concreta desde la app.")

    col1, col2 = st.columns(2)
    with col1:
        custom_artist = st.text_input("Artista", value="Coldplay")
    with col2:
        custom_song = st.text_input("Canción", value="Yellow")

    if st.button("Buscar letra"):
        lyrics = get_lyrics_ovh(custom_artist, custom_song)
        if lyrics:
            st.text_area("Letra encontrada", lyrics, height=300)
        else:
            st.warning("No se encontró letra para esa búsqueda.")
