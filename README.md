# 🌱 AGROCOL – AgroData Colombia (Streamlit)

Dashboard de **inteligencia de mercados agrícolas** de Colombia.

**Fuentes oficiales**
- `Precios_agricolas_consolidados_2019_2024.csv` → precios SIPSA (DANE) por producto, ciudad, año-mes
- `EVA COLOMBIA AGRICOLA.csv` → producción, área y rendimiento por departamento (códigos DANE – UPRA)

**Prioridad:** Exactitud estadística · Trazabilidad · Sin cifras inventadas

---

## Estructura del repositorio

```
agrocol-streamlit/
├── app.py                 # Aplicación principal Streamlit
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/config.toml
├── data/                  # Colocar aquí los CSV oficiales (no se versionan)
│   └── .gitkeep
└── src/
    ├── __init__.py
    ├── config.py          # Colores, departamentos, GeoJSON, mapeos
    ├── engine.py          # AgroEngine (carga, filtros, KPIs, sensibilidad)
    └── viz.py             # Mapas y gráficos Plotly
```

---

## Cómo ejecutar en local

```bash
# 1. Clonar
git clone <tu-repo>
cd agrocol-streamlit

# 2. Entorno
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Datos oficiales → carga AUTOMÁTICA
#    Copia los dos archivos a ./data/ (solo una vez)
cp /ruta/Precios_agricolas_consolidados_2019_2024.csv data/
cp "/ruta/EVA COLOMBIA AGRICOLA.csv" data/EVA_COLOMBIA_AGRICOLA.csv

# 4. Lanzar — la app detecta los CSV y entra en modo REAL sola
streamlit run app.py
```

**Carga automática:** al arrancar, Streamlit busca los CSV en `./data/` (y rutas conocidas).
Si los encuentra, activa **modo REAL** sin subir nada manualmente.
Si no hay archivos, arranca en **modo DEMO**.

La pestaña **⚙️ Configuración** sigue disponible para carga manual opcional.

---

## Despliegue en Streamlit Community Cloud

1. Sube este repositorio a GitHub (**no subas los CSV grandes**; están en `.gitignore`).
2. En [share.streamlit.io](https://share.streamlit.io):
   - New app → selecciona el repo → Main file: `app.py`
3. Los datos oficiales:
   - Opción A: sube los CSV como *secrets* / *files* privados, o
   - Opción B: usa la pestaña de carga de la app en runtime, o
   - Opción C: Git LFS si el repo permite archivos grandes.

---

## Pestañas

| Pestaña | Contenido |
|---------|-----------|
| 🏠 Inicio | Macro KPIs, top alzas/bajas, ranking producción |
| 📊 Resumen / 💰 Precios | KPIs, mapa coroplético de precios, serie mensual |
| 🌾 Producción | Mapa de volumen (t) por departamento |
| 📍 Por Departamento | Análisis de sensibilidad (sliders precio/rendimiento) |
| 🗺 Análisis Regional | Histogramas de distribución precios y producción |
| 📈 Tendencias | Serie + tendencia lineal + IC 95% + proyección |
| ⚖️ Comparativo | Mapa dual producción + precio |
| 📋 Reportes | Ficha departamental + export CSV |
| 📂 Fuentes y Auditoría | Enlaces institucionales + ficha técnica |
| ⚙️ Configuración | Carga de archivos → modo REAL |

---

## Auditoría técnica (resumen)

### Hallazgos del código original (Gradio / notebook)

| # | Hallazgo | Severidad | Acción en esta versión |
|---|----------|-----------|------------------------|
| 1 | EVA no trae nombres de cultivo legibles (solo códigos). Ranking de producción = **total agrícola** por departamento. | Alta (semántica) | Documentado en UI y README. No se inventan nombres de cultivo. |
| 2 | Cruce producto-específico EVA ↔ SIPSA **no es directo**. | Alta | Mapas de producción usan agregados departamentales. Etiquetado claro. |
| 3 | Serie de “producción mensual” en gráfico combinado = producción anual / 12 (aproximación). | Media | Se mantiene como referencia; no se presenta como dato oficial mensual. |
| 4 | Dependencia de GeoJSON externo (3 mirrors). Si fallan → fallback a barras. | Baja | Misma lógica; carga cacheada con `@st.cache_data`. |
| 5 | Archivos de datos ~19 MB + ~25 MB. No deben ir al repo sin LFS. | Media | `.gitignore` excluye `data/*.csv`. |
| 6 | Gradio monolítico (HTML + callbacks). Difícil de versionar y desplegar. | – | Reescrito en Streamlit modular (`src/`). |
| 7 | `cargar_eva` mapea por `Código Dane departamento` → nombres oficiales. Correcto. | OK | Conservado. |
| 8 | Mapeo ciudad → departamento heurístico (substring). Cobertura parcial de mercados. | Media | Misma tabla; se puede ampliar en `config.py`. |
| 9 | Modo DEMO con cifras fijas hasta carga real. Buena práctica. | OK | Conservado + badge visible. |
| 10 | Sin tests automatizados ni validación de esquema de columnas. | Media | Carga tolerante a nombres de columnas; mensajes de error claros. |

### Principios aplicados

- **Sin cifras inventadas** en modo REAL: si no hay dato, se muestra vacío/NaN o se indica DEMO.
- **Trazabilidad**: pestaña Fuentes + ficha técnica del motor (modo, filas, versión).
- **Reproducibilidad**: requisitos fijados, estructura clara, carga por rutas estándar.

---

## Licencia de datos

Los datos SIPSA y EVA son de fuentes oficiales del Estado colombiano.  
Esta aplicación es una herramienta de visualización; no sustituye las publicaciones oficiales del DANE ni de la UPRA.

