# Trabajo individual — Spotify Dataset Analysis: The Smiths

Este proyecto resuelve el trabajo individual basado en el fichero de ejemplo `Spotify_simple_Colab`.

El objetivo es analizar canciones sobre la banda musical The Smiths del dataset de Spotify, filtrar los álbumes de estudio de un artista, incorporar gráficos relacionados con letras de canciones y construir una pequeña web app interactiva

## 1. Estructura del proyecto

```text
.
├── analysis_cursor.py
├── verify_dataset.py
├── requirements.txt
├── README_ENTREGA.md
├── app
│   └── streamlit_app.py
├── notebook
│   └── Spotify_TheSmiths_Analysis.ipynb
├── data
│   ├── raw
│   └── processed
└── outputs
    └── plots
```

## 2. Dataset utilizado

El dataset utilizado es `tracks_features.csv`, indicado en el notebook de ejemplo como procedente de Kaggle:

**Spotify 1.2M+ Songs**  
`https://www.kaggle.com/datasets/rodolfofigueroa/spotify-12m-songs`

El script intenta descargar automáticamente el fichero mediante `gdown`, usando el ID de Google Drive que aparecía en el notebook base. Si la descarga falla, se debe colocar manualmente el fichero en:

```text
data/raw/tracks_features.csv
```

## 3. Cómo ejecutar el proyecto en Cursor / local

### 3.1 Crear entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3.2 Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3.3 Ejecutar el análisis principal

```bash
python analysis_cursor.py
```

Este script genera:

```text
data/processed/the_smiths_studio_tracks.csv
data/processed/conteo_albumes_estudio_the_smiths.csv
data/processed/lyrics_summary.csv
data/processed/lyrics_word_frequency.csv
outputs/plots/01_energy_por_cancion.png
outputs/plots/02_valence_por_cancion.png
outputs/plots/03_energy_vs_valence_por_cancion.png
outputs/plots/04_palabras_frecuentes_letras.png
outputs/plots/05_nube_palabras_letras.png
```

### 3.4 Ejecutar la verificación del dataset

```bash
python verify_dataset.py
```

Este script permite comprobar que:

- `str.contains("The Smiths")` genera falsos positivos.
- La coincidencia exacta de artista es más fiable.
- El dataset no contiene todos los álbumes de estudio originales de The Smiths.
- Solo aparece `Strangeways, Here We Come` como álbum de estudio original de The Smiths dentro del dataset.

## 4. Cómo ejecutar la web app

Después de ejecutar `analysis_cursor.py`, lanzar Streamlit:

```bash
streamlit run app/streamlit_app.py
```

La app se abrirá normalmente en:

```text
http://localhost:8501
```

La web app incluye:

- tabla de filtrado de álbumes de estudio;
- exploración de canciones disponibles;
- gráfico por variable musical;
- gráfico `energy` vs `valence`;
- análisis de letras con frecuencia de palabras;
- nube de palabras;
- componente de consulta manual a `lyrics.ovh`.

## 5. Apartados del enunciado cubiertos

### Apartado 1 — Filtrar álbumes de estudio

Se definieron los cuatro álbumes de estudio oficiales de The Smiths:

- `The Smiths`
- `Meat Is Murder`
- `The Queen Is Dead`
- `Strangeways, Here We Come`

Se aplicó el filtro sobre el dataset para conservar únicamente canciones pertenecientes a estos álbumes. Tras la verificación, el dataset solo contiene canciones originales de The Smiths del álbum:

```text
Strangeways, Here We Come
```

Por tanto, el filtro se aplica correctamente, pero el análisis queda limitado por la cobertura del dataset.

### Apartado 2 — Gráficos sobre letras

Se intentó recuperar letras de canciones de The Smiths usando `lyrics.ovh`. Como no se obtuvieron resultados, se utilizó un conjunto alternativo de canciones de varios artistas, tal como permite el enunciado.

Con las letras recuperadas se generaron:

- gráfico de palabras más frecuentes;
- nube de palabras.

### Apartado 3 — Web app

Se creó una aplicación con Streamlit en:

```text
app/streamlit_app.py
```

La app permite explorar los resultados de forma interactiva.

## 6. Comentario

En una primera aproximación se utilizó una búsqueda textual con `str.contains("The Smiths")`, pero esta técnica generaba falsos positivos, ya que también coincidía con artistas como `The Smithsonian Chamber Players`. Por este motivo, se mejoró el filtrado transformando la columna `artists` en una lista y comprobando que el artista coincidiera exactamente con `The Smiths`.

Después de aplicar esta comprobación, el dataset contenía 11 canciones asociadas exactamente a The Smiths: 10 canciones del álbum `Strangeways, Here We Come` y 1 canción incluida en la banda sonora `The Wedding Singer`. Como el objetivo era conservar únicamente álbumes de estudio, se eliminó la banda sonora y se conservaron solo las canciones del álbum de estudio disponible.

Aunque la discografía oficial de The Smiths incluye cuatro álbumes de estudio, en el dataset utilizado no aparecen registros originales de `The Smiths`, `Meat Is Murder` ni `The Queen Is Dead`. Por tanto, el filtrado se ha aplicado correctamente, pero el análisis queda limitado a las canciones disponibles en el dataset.

Como tres álbumes quedan sin canciones, los gráficos principales se realizaron por canción y no por álbum. Esto permite aportar más valor analítico, comparando variables como `energy` y `valence` entre las canciones disponibles.
