"""
AGROCOL – Dashboard Streamlit
Inteligencia de Mercados Agrícolas de Colombia
Fuentes: SIPSA (DANE) + EVA (UPRA)
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.config import (
    COLORES, DEPARTAMENTOS_OFICIALES, MES_LABELS, MES_NUM,
    icono_producto, cargar_geojson, detectar_prop_nombre,
)
from src.engine import AgroEngine
from src import viz

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AGROCOL | AgroData Colombia",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(f"""
<style>
    .stApp {{ background-color: {COLORES['fondo']}; }}
    [data-testid="stSidebar"] {{ background-color: {COLORES['sidebar']}; }}
    [data-testid="stSidebar"] * {{ color: #E8F5E9 !important; }}
    [data-testid="stSidebar"] .stRadio label {{ color: #E8F5E9 !important; }}
    div[data-testid="stMetricValue"] {{ font-size: 1.35rem; }}
    .block-container {{ padding-top: 1.2rem; }}
    h1, h2, h3 {{ color: {COLORES['texto']}; }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Paths & data loading helpers
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

# Rutas candidatas (prioridad: data/ del proyecto → rutas conocidas → cwd)
CANDIDATE_PRECIOS = [
    DATA_DIR / "Precios_agricolas_consolidados_2019_2024.csv",
    DATA_DIR / "Precios_agricolas_consolidados_2019_2024.xlsx",
    Path("/home/workdir/attachments/Precios_agricolas_consolidados_2019_2024.csv"),
    ROOT / "Precios_agricolas_consolidados_2019_2024.csv",
    Path("Precios_agricolas_consolidados_2019_2024.csv"),
]
CANDIDATE_EVA = [
    DATA_DIR / "EVA_COLOMBIA_AGRICOLA.csv",
    DATA_DIR / "EVA COLOMBIA AGRICOLA.csv",
    Path("/home/workdir/attachments/EVA COLOMBIA AGRICOLA.csv"),
    ROOT / "EVA COLOMBIA AGRICOLA.csv",
    Path("EVA COLOMBIA AGRICOLA.csv"),
]


@st.cache_resource
def get_engine() -> AgroEngine:
    """Crea el motor y carga automáticamente los CSV si existen."""
    engine = AgroEngine()
    _autoload_into(engine)
    return engine


@st.cache_data(show_spinner="Cargando GeoJSON de Colombia…")
def get_geojson():
    geo = cargar_geojson()
    prop = detectar_prop_nombre(geo)
    return geo, prop


def _autoload_into(engine: AgroEngine) -> list[str]:
    """Busca y carga precios + EVA sin intervención del usuario."""
    msgs = []
    loaded_p = loaded_e = False
    for p in CANDIDATE_PRECIOS:
        if p.exists():
            msgs.append(engine.cargar_precios(str(p)))
            loaded_p = True
            break
    for p in CANDIDATE_EVA:
        if p.exists():
            msgs.append(engine.cargar_eva(str(p)))
            loaded_e = True
            break
    if not loaded_p and not loaded_e:
        msgs.append(
            "ℹ️ No se encontraron CSV. Coloca los archivos en ./data/ "
            "o súbelos en Configuración."
        )
    return msgs


def try_autoload(engine: AgroEngine) -> str:
    return "\n".join(_autoload_into(engine))


# ---------------------------------------------------------------------------
# Session state — carga automática al arrancar
# ---------------------------------------------------------------------------
if "engine" not in st.session_state:
    st.session_state.engine = get_engine()
    st.session_state.load_msg = (
        f"Modo {st.session_state.engine.modo} · "
        f"{len(st.session_state.engine.productos)} productos · "
        f"precios: {len(st.session_state.engine.df_precios) if st.session_state.engine.df_precios is not None else 0:,} filas · "
        f"EVA: {len(st.session_state.engine.df_eva) if st.session_state.engine.df_eva is not None else 0:,} filas"
    )

engine: AgroEngine = st.session_state.engine
geojson, prop_nombre = get_geojson()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🌱 AgroData Colombia")
    st.caption("Inteligencia de Mercados · SIPSA + EVA")
    menu = st.radio(
        "Navegación",
        [
            "🏠 Inicio",
            "📊 Resumen",
            "💰 Precios Agrícolas",
            "🌾 Producción",
            "📍 Por Departamento",
            "🗺 Análisis Regional",
            "📈 Tendencias",
            "⚖️ Comparativo",
            "📋 Reportes",
            "📂 Fuentes y Auditoría",
            "⚙️ Configuración / Carga",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    if engine.modo == "REAL":
        st.success(f"✅ Modo **REAL** · v{engine.version}")
        n_p = len(engine.df_precios) if engine.df_precios is not None else 0
        n_e = len(engine.df_eva) if engine.df_eva is not None else 0
        st.caption(f"{len(engine.productos)} productos · {n_p:,} precios · {n_e:,} EVA")
    else:
        st.warning(f"⚠️ Modo **DEMO** · v{engine.version}")
        st.caption("Coloca los CSV en ./data/ para activar datos reales")
    st.caption("Fuentes: SIPSA · EVA · DIVIPOLA")

# ---------------------------------------------------------------------------
# Global filters
# ---------------------------------------------------------------------------
col_f1, col_f2, col_f3, col_f4 = st.columns([3, 1, 1, 2])
with col_f1:
    productos = engine.productos or ["Maíz"]
    producto = st.selectbox("Producto", productos, index=0)
with col_f2:
    anio = st.selectbox("Año", ["Todos"] + [str(y) for y in range(2019, 2025)], index=6)  # 2024
with col_f3:
    mes = st.selectbox("Mes", MES_LABELS, index=0)
with col_f4:
    depto = st.selectbox("Departamento", ["Todos"] + DEPARTAMENTOS_OFICIALES, index=0)

demo = engine.modo == "DEMO"
periodo = f"{mes} {anio}" if mes != "Todos" else str(anio)

# ---------------------------------------------------------------------------
# Helpers UI
# ---------------------------------------------------------------------------
def kpi_row(items: list[tuple]):
    cols = st.columns(len(items))
    for c, (label, value, delta) in zip(cols, items):
        c.metric(label, value, delta)


def badge_demo():
    if demo:
        st.warning("⚠️ **Modo DEMO** — Sube Precios + EVA en **⚙️ Configuración / Carga** para activar datos reales.")


# ===========================================================================
# PAGES
# ===========================================================================

# ---- INICIO ----
if "Inicio" in menu:
    st.title("🌱 AGROCOL – Inteligencia de Mercados Agrícolas")
    st.markdown(
        "Dashboard de **precios SIPSA (DANE)** y **producción EVA (UPRA)** para Colombia. "
        "Prioridad: exactitud estadística · trazabilidad · sin cifras inventadas."
    )
    badge_demo()
    macro = engine.get_macro_kpis(anio)
    top_ab = engine.get_top_alzas_bajas(anio, 5)
    ranking = engine.get_ranking(8, anio)

    kpi_row([
        ("Precio ponderado (COP/kg)", f"${macro['precio_ponderado']:,.0f}", None),
        ("Producción nacional (M t)", f"{macro['prod_nacional_mt']:.2f}", None),
        ("Var. intermensual", f"{macro['var_intermensual']:.1f}%" if macro.get('var_intermensual') is not None else "–", None),
        ("Mercados / Deptos", f"{macro.get('n_mercados',0)} / {macro.get('n_deptos',0)}", None),
    ])

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Top alzas / bajas (precio)")
        if top_ab is not None and len(top_ab):
            st.dataframe(top_ab, use_container_width=True, hide_index=True)
        else:
            st.info("Sin datos de variación para el filtro actual.")
    with c2:
        st.subheader("Ranking producción (EVA)")
        st.dataframe(ranking, use_container_width=True, hide_index=True)

# ---- RESUMEN / PRECIOS ----
elif any(x in menu for x in ("Resumen", "Precios")):
    st.title(f"{'📊 Resumen' if 'Resumen' in menu else '💰 Precios'} – {icono_producto(producto)} {producto}")
    badge_demo()
    kpis = engine.get_kpis(producto, anio, depto if depto != "Todos" else None, mes)
    ranking = engine.get_ranking(8, anio)
    df_mapa = engine.get_df_mapa_precios(producto, anio, mes)
    serie = engine.get_serie_mensual(producto, anio, depto if depto != "Todos" else None)

    kpi_row([
        ("Precio promedio", f"${kpis['precio_prom']:,.0f}", f"{kpis['var']:.1f}%" if kpis.get('var') is not None else None),
        ("Producción nacional (M t)", f"{kpis['prod_nacional']:.2f}", None),
        ("Precio mínimo", f"${kpis['precio_min']:,.0f}", None),
        ("Precio máximo", f"${kpis['precio_max']:,.0f}", None),
    ])

    c1, c2 = st.columns([1.2, 1])
    with c1:
        fig = viz.crear_mapa_coropletico(
            df_mapa, geojson, prop_nombre,
            f"Precio promedio – {producto} ({periodo})"
        )
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = viz.crear_grafico_combinado(serie, producto)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Ranking / detalle")
    if depto == "Todos":
        st.dataframe(ranking, use_container_width=True, hide_index=True)
    else:
        eva = engine.get_eva_depto(depto, anio)
        if eva:
            st.json(eva)

# ---- PRODUCCIÓN ----
elif "Producción" in menu:
    st.title("🌾 Producción agrícola por departamento")
    badge_demo()
    df_prod = engine.get_df_mapa_produccion(anio)
    total_prod = df_prod["Produccion"].sum()
    lider = df_prod.sort_values("Produccion", ascending=False).iloc[0] if len(df_prod) else None

    kpi_row([
        ("Producción nacional", f"{total_prod/1e6:.2f} M t", None),
        ("Departamento líder", lider["Departamento"] if lider is not None else "–", None),
        ("Volumen del líder", f"{lider['Produccion']:,.0f} t" if lider is not None else "–", None),
        ("Deptos con dato", f"{(df_prod['Produccion']>0).sum()}", None),
    ])

    fig = viz.crear_mapa_produccion(df_prod, geojson, prop_nombre, f"Producción (t) – {anio}")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(engine.get_ranking(15, anio), use_container_width=True, hide_index=True)

# ---- POR DEPARTAMENTO (Sensibilidad) ----
elif "Por Departamento" in menu:
    st.title("📍 Análisis de sensibilidad departamental")
    badge_demo()
    dsel = depto if depto != "Todos" else "Cundinamarca"
    sp = st.slider("Variación simulada de precio mayorista (%)", -50, 50, 0, 5)
    sr = st.slider("Choque de rendimiento / producción (%)", -50, 50, 0, 5)
    sens = engine.calcular_analisis_sensibilidad(dsel, producto, sp, sr)

    c1, c2, c3 = st.columns(3)
    c1.metric("Ingreso base (ref.)", f"{sens.get('ingreso_base', 0):,.0f}")
    c2.metric("Ingreso simulado", f"{sens.get('ingreso_sim', 0):,.0f}",
              f"{((sens.get('ingreso_sim',0)/max(sens.get('ingreso_base',1),1))-1)*100:.1f}%")
    c3.metric("Margen/ha simulado", f"{sens.get('margen_ha_sim', 0):,.0f}")

    heat = viz.crear_heatmap_sensibilidad(sens.get("escenarios"))
    torn = viz.crear_tornado_sensibilidad(sens)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(heat, use_container_width=True)
    with c2:
        st.plotly_chart(torn, use_container_width=True)

# ---- ANÁLISIS REGIONAL ----
elif "Regional" in menu or "Análisis Regional" in menu:
    st.title("🗺 Análisis distributivo regional")
    badge_demo()
    dist_p = engine.get_distribucion_precios(producto, anio, depto if depto != "Todos" else None, mes)
    dist_r = engine.get_distribucion_produccion(anio)
    st.caption(
        f"Precios: media {dist_p['mean']:,.0f} · mediana {dist_p['median']:,.0f} · "
        f"σ {dist_p['std']:,.0f} · sesgo {dist_p['skew']:.2f}"
    )
    hist = viz.crear_histogramas_regionales(dist_p, dist_r, producto)
    st.plotly_chart(hist, use_container_width=True)
    st.dataframe(engine.get_ranking(8, anio), use_container_width=True, hide_index=True)

# ---- TENDENCIAS ----
elif "Tendencias" in menu:
    st.title(f"📈 Tendencias e inferencia – {producto}")
    badge_demo()
    serie_ext, meta = engine.get_serie_tendencia(producto, anio, depto if depto != "Todos" else None)
    if meta:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pendiente (COP/mes)", f"{meta.get('slope', 0):.2f}")
        c2.metric("R²", f"{meta.get('r2', 0):.3f}")
        c3.metric("p-valor tendencia", f"{meta.get('pvalue', 1):.4f}")
        c4.metric("Proyección +3m", f"${meta.get('proyeccion', 0):,.0f}" if meta.get('proyeccion') else "–")
    graf = viz.crear_grafico_tendencias_proyectadas(serie_ext, meta, producto)
    st.plotly_chart(graf, use_container_width=True)

# ---- COMPARATIVO ----
elif "Comparativo" in menu:
    st.title("⚖️ Comparativo Producción (EVA) + Precio (SIPSA)")
    badge_demo()
    df_cruz = engine.get_comparativo_cruzado(producto, anio, mes)
    fig = viz.crear_mapa_comparativo(df_cruz, geojson, prop_nombre, producto, periodo)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        df_cruz.sort_values("Produccion", ascending=False).head(20),
        use_container_width=True, hide_index=True,
    )

# ---- REPORTES ----
elif "Reportes" in menu:
    st.title("📋 Reportes departamentales")
    badge_demo()
    dsel = depto if depto != "Todos" else "Cundinamarca"
    resumen, serie_anual = engine.generar_reporte_departamental(dsel, anio)
    st.subheader(f"Ficha – {dsel} · {anio}")
    if resumen:
        st.json(resumen)
    if serie_anual is not None and len(serie_anual):
        st.dataframe(serie_anual, use_container_width=True, hide_index=True)
        csv = serie_anual.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Descargar serie anual (CSV)",
            csv,
            file_name=f"reporte_{dsel.replace(' ', '_')}_{anio}.csv",
            mime="text/csv",
        )

# ---- FUENTES ----
elif "Fuentes" in menu or "Auditoría" in menu:
    st.title("📂 Fuentes y Auditoría")
    st.markdown("""
### Fuentes oficiales
| Fuente | Descripción | Institución |
|--------|-------------|-------------|
| **SIPSA** | Sistema de Información de Precios del Sector Agropecuario | DANE |
| **EVA** | Evaluaciones Agropecuarias Municipales | UPRA / MADR |
| **DIVIPOLA** | División Político-Administrativa | DANE |

### Limitaciones técnicas (auditoría)
1. **EVA no trae nombres de cultivo legibles** en este extracto (solo códigos). El ranking/producción por departamento es **total agrícola**.
2. El cruce **producto-específico** EVA ↔ SIPSA **no es directo**; los mapas de producción usan agregados departamentales.
3. Todo se etiqueta **DEMO** hasta cargar archivos reales.
4. GeoJSON se descarga de repositorios públicos; si falla, hay fallback a barras horizontales.
5. La serie de producción mensual en el gráfico combinado es una **aproximación** (producción anual / 12).

### Ficha técnica del motor
""")
    st.code(f"""
Modo actual     : {engine.modo}
Versión         : {engine.version}
Productos       : {len(engine.productos)}
Filas precios   : {len(engine.df_precios) if engine.df_precios is not None else 0}
Filas EVA       : {len(engine.df_eva) if engine.df_eva is not None else 0}
GeoJSON prop    : {prop_nombre}
""", language="text")

# ---- CONFIGURACIÓN ----
elif "Configuración" in menu or "Carga" in menu:
    st.title("⚙️ Configuración y Carga de datos")
    st.markdown("""
**Carga automática:** si los archivos están en la carpeta `data/` del proyecto,
la plataforma los detecta y carga **al iniciar** (modo REAL), sin subir nada a mano.

Archivos esperados:
- `data/Precios_agricolas_consolidados_2019_2024.csv` (o .xlsx)
- `data/EVA_COLOMBIA_AGRICOLA.csv`

Estado actual de la sesión:
""")
    st.info(st.session_state.get("load_msg", "Sin carga aún."))
    if engine.modo == "REAL":
        st.success("Los datos oficiales ya están cargados automáticamente.")
    else:
        st.warning("Modo DEMO activo. Coloca los CSV en `./data/` y reinicia la app, o súbelos abajo.")

    st.markdown("---")
    st.markdown("**Carga manual (opcional)** — útil si los archivos no están en disco:")
    f_prec = st.file_uploader("Precios consolidados (CSV / Excel)", type=["csv", "xlsx", "xls"])
    f_eva = st.file_uploader("EVA Colombia (CSV / Excel)", type=["csv", "xlsx", "xls"])
    if st.button("Cargar y activar modo REAL", type="primary"):
        msg = engine.cargar_archivos(f_prec, f_eva)
        # Invalidate cache so next get_engine sees REAL data if needed
        st.session_state.load_msg = msg
        st.session_state.engine = engine
        st.success(msg)
        st.rerun()

# Footer
st.markdown("---")
st.caption(
    "AGROCOL · AgroData Colombia · Fuentes: DANE (SIPSA) · UPRA (EVA) · "
    "**Prioridad:** Exactitud estadística · Trazabilidad · Sin cifras inventadas"
)
