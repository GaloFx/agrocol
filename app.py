import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime
import warnings
from scipy import stats

warnings.filterwarnings('ignore')

# Configuración inicial de la página en Streamlit
st.set_page_config(
    page_title="AGROCOL – AgroData Colombia",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para mantener la identidad visual institucional
st.markdown("""
    <style>
    .main { background-color: #F5F7F6; }
    .stSidebar { background-color: #1B4332 !important; }
    h1, h2, h3 { color: #1B4332; }
    .metric-card { background: white; border-radius: 12px; padding: 16px; box-shadow: 0 1px 8px rgba(0,0,0,0.06); border: 1px solid #E2E8F0; }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================
COLORES = {
    'sidebar': '#1B4332',
    'verde_kpi': '#40916C',
    'verde_claro': '#74C69D',
    'azul_linea': '#2B6CB0',
    'rojo': '#E53E3E',
    'amarillo': '#D69E2E'
}

DEPARTAMENTOS_OFICIALES = [
    'Amazonas','Antioquia','Arauca','Atlántico','Bogotá D.C.','Bolívar','Boyacá',
    'Caldas','Caquetá','Casanare','Cauca','Cesar','Chocó','Córdoba','Cundinamarca',
    'Guainía','Guaviare','Huila','La Guajira','Magdalena','Meta','Nariño',
    'Norte de Santander','Putumayo','Quindío','Risaralda','San Andrés y Providencia',
    'Santander','Sucre','Tolima','Valle del Cauca','Vaupés','Vichada'
]

MESES = [
    ('Todos', None),
    ('Enero', 1), ('Febrero', 2), ('Marzo', 3), ('Abril', 4),
    ('Mayo', 5), ('Junio', 6), ('Julio', 7), ('Agosto', 8),
    ('Septiembre', 9), ('Octubre', 10), ('Noviembre', 11), ('Diciembre', 12)
]
MES_LABELS = [m[0] for m in MESES]
MES_NUM = {m[0]: m[1] for m in MESES}

ICONOS_PRODUCTO = [
    ('acelga', '🥬'), ('ahuyama', '🎃'), ('ajo', '🧄'), ('apio', '🥬'),
    ('arveja', '🟢'), ('berenjena', '🍆'), ('brócoli', '🥦'), ('brocoli', '🥦'),
    ('calabacín', '🥒'), ('calabaza', '🎃'), ('cebolla', '🧅'), ('cilantro', '🌿'),
    ('coliflor', '🥦'), ('espinaca', '🥬'), ('fríjol', '🫘'), ('frijol', '🫘'),
    ('haba', '🟢'), ('habichuela', '🫛'), ('lechuga', '🥬'), ('pepino', '🥒'),
    ('perejil', '🌿'), ('pimentón', '🫑'), ('remolacha', '🟣'), ('repollo', '🥬'),
    ('rábano', '🔴'), ('tomate', '🍅'), ('zanahoria', '🥕'),
    ('aguacate', '🥑'), ('banano', '🍌'), ('lulo', '🟠'), ('mango', '🥭'),
    ('manzana', '🍎'), ('maracuyá', '🟡'), ('melón', '🍈'), ('mora', '🫐'),
    ('naranja', '🍊'), ('papaya', '🧡'), ('patilla', '🍉'), ('pera', '🍐'),
    ('piña', '🍍'), ('uva', '🍇'), ('papa', '🥔'), ('plátano', '🍌'),
    ('platano', '🍌'), ('yuca', '🤍'), ('maíz', '🌽'), ('maiz', '🌽'),
    ('arroz', '🍚'), ('café', '☕'), ('cafe', '☕'), ('chócolo', '🌽'),
]

def icono_producto(nombre):
    if not nombre:
        return '🌽'
    n = str(nombre).lower()
    for key, icon in ICONOS_PRODUCTO:
        if key in n:
            return icon
    return '🌱'

DANE_DEPTO = {
    5: 'Antioquia', 8: 'Atlántico', 13: 'Bolívar', 15: 'Boyacá', 17: 'Caldas',
    18: 'Caquetá', 19: 'Cauca', 20: 'Cesar', 23: 'Córdoba', 25: 'Cundinamarca',
    27: 'Chocó', 41: 'Huila', 44: 'La Guajira', 47: 'Magdalena', 50: 'Meta',
    52: 'Nariño', 54: 'Norte de Santander', 63: 'Quindío', 66: 'Risaralda',
    68: 'Santander', 70: 'Sucre', 73: 'Tolima', 76: 'Valle del Cauca',
    81: 'Arauca', 85: 'Casanare', 86: 'Putumayo', 88: 'San Andrés y Providencia',
    91: 'Amazonas', 94: 'Guainía', 95: 'Guaviare', 97: 'Vaupés', 99: 'Vichada'
}

CIUDAD_A_DEPTO = {
    'Bogotá': 'Bogotá D.C.', 'Corabastos': 'Bogotá D.C.', 'Medellín': 'Antioquia',
    'Cali': 'Valle del Cauca', 'Cavasa': 'Valle del Cauca', 'Santa Helena': 'Valle del Cauca',
    'Santa Elena': 'Valle del Cauca', 'Barranquilla': 'Atlántico', 'Cartagena': 'Bolívar',
    'Bucaramanga': 'Santander', 'Cúcuta': 'Norte de Santander', 'Pereira': 'Risaralda',
    'Manizales': 'Caldas', 'Armenia': 'Quindío', 'Ibagué': 'Tolima', 'Neiva': 'Huila',
    'Pasto': 'Nariño', 'Ipiales': 'Nariño', 'Túquerres': 'Nariño', 'Villavicencio': 'Meta',
    'Montería': 'Córdoba', 'Sincelejo': 'Sucre', 'Valledupar': 'Cesar',
    'Santa Marta': 'Magdalena', 'Florencia': 'Caquetá', 'Yopal': 'Casanare',
    'Arauca': 'Arauca', 'Tunja': 'Boyacá', 'Duitama': 'Boyacá', 'Sogamoso': 'Boyacá',
    'Chiquinquirá': 'Boyacá', 'Pamplona': 'Norte de Santander', 'San Gil': 'Santander',
    'Socorro': 'Santander', 'Rionegro': 'Antioquia', 'Marinilla': 'Antioquia',
    'La Ceja': 'Antioquia', 'El Carmen de Viboral': 'Antioquia',
    'El Santuario': 'Antioquia', 'Sonsón': 'Antioquia', 'San Vicente': 'Antioquia',
    'Palmira': 'Valle del Cauca', 'Tuluá': 'Valle del Cauca', 'Cartago': 'Valle del Cauca',
    'Buenaventura': 'Valle del Cauca', 'Popayán': 'Cauca', 'Ubaté': 'Cundinamarca',
    'La Unión': 'Nariño', 'Tibasosa': 'Boyacá', 'Peñol': 'Antioquia',
    'Santa Bárbara': 'Antioquia', 'Retiro': 'Quindío'
}

def ciudad_a_depto(ciudad):
    if pd.isna(ciudad):
        return None
    c = str(ciudad)
    for key, depto in CIUDAD_A_DEPTO.items():
        if key.lower() in c.lower():
            return depto
    return None

GEOJSON_URLS = [
    "https://raw.githubusercontent.com/caticoa3/colombia_mapa/master/co_2018_MGN_DPTO_POLITICO.geojson",
    "https://raw.githubusercontent.com/santiblanko/colombia.geojson/master/depto.json"
]

@st.cache_data
def cargar_geojson():
    for url in GEOJSON_URLS:
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception:
            continue
    return None

geojson_colombia = cargar_geojson()

def detectar_prop_nombre(geo):
    if geo is None:
        return None
    props = geo['features'][0]['properties']
    candidatos = ['DPTO_CNMBR', 'NOMBRE_DPT', 'name', 'NAME_1', 'shapeName', 'NOM_DEPART', 'departamento', 'DPTO']
    for c in candidatos:
        if c in props:
            return c
    return list(props.keys())[0]

PROP_NOMBRE = detectar_prop_nombre(geojson_colombia)


# ============================================================
# MOTOR DE DATOS (AgroEngine)
# ============================================================
class AgroEngine:
    def __init__(self):
        self.modo = 'DEMO'
        self.df_precios = None
        self.df_eva = None
        self.productos = ['Maíz', 'Arroz', 'Papa', 'Café', 'Plátano', 'Yuca', 'Tomate', 'Cebolla', 'Aguacate', 'Apio']
        self.version = '2.1-Streamlit-Optimizado'
        self._init_demo()

    def _init_demo(self):
        np.random.seed(42)
        self.precios_depto = {d: 2000 + np.random.randint(0, 800) for d in DEPARTAMENTOS_OFICIALES}
        self.prod_depto = {
            'Cundinamarca': 1842000, 'Meta': 1703000, 'Antioquia': 1592000,
            'Tolima': 1421000, 'Valle del Cauca': 1223000, 'Huila': 980000,
            'Nariño': 850000, 'Boyacá': 720000, 'Santander': 690000, 'Córdoba': 610000,
            'Cauca': 580000, 'Cesar': 420000, 'Magdalena': 390000, 'Bolívar': 350000,
            'Atlántico': 280000, 'Sucre': 250000, 'La Guajira': 180000,
            'Norte de Santander': 410000, 'Caldas': 320000, 'Risaralda': 290000,
            'Quindío': 210000, 'Chocó': 150000, 'Caquetá': 190000, 'Putumayo': 160000,
            'Arauca': 220000, 'Casanare': 480000, 'Vichada': 90000, 'Guainía': 40000,
            'Guaviare': 70000, 'Vaupés': 25000, 'Amazonas': 35000,
            'San Andrés y Providencia': 15000, 'Bogotá D.C.': 120000
        }
        self.serie = pd.DataFrame({
            'Mes': ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'],
            'Precio': [2350,2450,2420,2380,2410,2480,2520,2550,2580,2600,2620,2590],
            'Produccion': [6.2,6.5,6.8,6.9,7.0,7.1,7.3,7.2,7.0,7.1,7.2,7.3]
        })

    def cargar_precios(self, uploaded_file):
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, low_memory=False, encoding='utf-8')
            else:
                df = pd.read_excel(uploaded_file, engine='openpyxl')

            df.columns = [str(c).strip() for c in df.columns]
            df = df.loc[:, ~df.columns.str.match(r'^Unnamed', na=False)]
            cols_lower = {c.lower(): c for c in df.columns}

            def find_col(exact_list, contains_list=None):
                for e in exact_list:
                    if e in cols_lower:
                        return cols_lower[e]
                if contains_list:
                    for cand in contains_list:
                        for k, orig in cols_lower.items():
                            if cand in k:
                                return orig
                return None

            col_anio = find_col(['año', 'anio', 'year'], ['año', 'anio'])
            col_mes = find_col(['mes_numero', 'mes_num'], ['mes_numero'])
            col_prod = find_col(['producto'], ['producto'])
            col_precio = find_col(['precio_por_kg_reportado', 'precio_por_kg', 'precio'], ['precio_por_kg', 'precio'])
            col_ciudad = find_col(['ciudad_mercado', 'ciudad'], ['ciudad', 'mercado'])
            col_depto = find_col(['departamento', 'depto'], ['departamento'])

            if col_prod is None or col_precio is None:
                return '❌ Faltan columnas obligatorias (Producto / Precio).'

            keep = {}
            if col_anio: keep[col_anio] = 'Año'
            if col_mes: keep[col_mes] = 'Mes_numero'
            keep[col_prod] = 'Producto'
            keep[col_precio] = 'Precio_por_kg_reportado'
            if col_ciudad: keep[col_ciudad] = 'Ciudad_mercado'
            if col_depto: keep[col_depto] = 'Departamento'

            used, final_keep = set(), {}
            for o, t in keep.items():
                if t not in used:
                    final_keep[o] = t
                    used.add(t)
            df = df[list(final_keep.keys())].rename(columns=final_keep)

            if 'Año' in df.columns: df['Año'] = pd.to_numeric(df['Año'], errors='coerce')
            if 'Mes_numero' in df.columns: df['Mes_numero'] = pd.to_numeric(df['Mes_numero'], errors='coerce')
            df['Precio_por_kg_reportado'] = pd.to_numeric(df['Precio_por_kg_reportado'], errors='coerce')
            df['Producto'] = df['Producto'].astype(str).str.strip()
            df = df.dropna(subset=['Producto', 'Precio_por_kg_reportado'])

            if 'Departamento' in df.columns:
                df['Departamento'] = df['Departamento'].astype(str).str.strip()
                valid = df['Departamento'].replace({'nan': None, '': None})
                if valid.isna().mean() > 0.8 and 'Ciudad_mercado' in df.columns:
                    df['Departamento'] = df['Ciudad_mercado'].apply(ciudad_a_depto)
            elif 'Ciudad_mercado' in df.columns:
                df['Departamento'] = df['Ciudad_mercado'].apply(ciudad_a_depto)
            else:
                df['Departamento'] = None

            self.df_precios = df.reset_index(drop=True)
            self.productos = sorted(self.df_precios['Producto'].dropna().astype(str).unique().tolist())
            self.modo = 'REAL'
            return f"✅ Precios cargados con éxito: {len(df):,} registros, {len(self.productos)} productos."
        except Exception as e:
            return f"❌ Error al procesar precios: {e}"

    def cargar_eva(self, uploaded_file):
        try:
            df = pd.read_csv(uploaded_file, low_memory=False)
            col_code = 'Código Dane departamento' if 'Código Dane departamento' in df.columns else df.columns[0]
            df['Departamento'] = pd.to_numeric(df[col_code], errors='coerce').map(DANE_DEPTO)
            df['Año'] = pd.to_numeric(df['Año'], errors='coerce')
            for c_src, c_dst in [
                ('Producción (t)', 'Produccion'),
                ('Área sembrada (ha)', 'Area_sembrada'),
                ('Área cosechada (ha)', 'Area_cosechada'),
                ('Rendimiento (t/ha)', 'Rendimiento'),
            ]:
                df[c_dst] = pd.to_numeric(df[c_src], errors='coerce').fillna(0) if c_src in df.columns else 0
            df = df.dropna(subset=['Departamento'])
            self.df_eva = df
            self.modo = 'REAL'
            return f"✅ EVA cargado con éxito: {len(df):,} registros agrícolas."
        except Exception as e:
            return f"❌ Error al procesar EVA: {e}"

    def cargar_archivos(self, f_prec, f_eva):
        msgs = []
        if f_prec: msgs.append(self.cargar_precios(f_prec))
        if f_eva: msgs.append(self.cargar_eva(f_eva))
        return "\n".join(msgs) if msgs else "ℹ️ No se cargaron archivos."

    def get_precios_filtrados(self, producto=None, anio=None, depto=None, mes=None):
        if self.df_precios is None:
            return None
        df = self.df_precios.copy()
        if producto and producto != 'Todos':
            df = df[df['Producto'] == producto]
        if anio and str(anio) != 'Todos':
            df = df[df['Año'] == int(anio)]
        if depto and depto != 'Todos':
            df = df[df['Departamento'] == depto]
        if mes and mes != 'Todos' and MES_NUM.get(mes) is not None and 'Mes_numero' in df.columns:
            df = df[df['Mes_numero'] == MES_NUM[mes]]
        return df

    def get_df_mapa_precios(self, producto=None, anio=None, mes=None):
        if self.df_precios is None:
            return pd.DataFrame([{'Departamento': d, 'Precio': self.precios_depto.get(d, 2200), 'Produccion': self.prod_depto.get(d, 100000)} for d in DEPARTAMENTOS_OFICIALES])
        df = self.get_precios_filtrados(producto, anio, None, mes)
        if df is None or len(df) == 0:
            return pd.DataFrame({'Departamento': DEPARTAMENTOS_OFICIALES, 'Precio': np.nan, 'Produccion': 0})
        g = df.groupby('Departamento', as_index=False)['Precio_por_kg_reportado'].mean().rename(columns={'Precio_por_kg_reportado': 'Precio'})
        prod = self.get_prod_por_depto(anio)
        g = g.merge(prod, on='Departamento', how='left').fillna({'Produccion': 0})
        missing = set(DEPARTAMENTOS_OFICIALES) - set(g['Departamento'].dropna())
        if missing:
            g = pd.concat([g, pd.DataFrame({'Departamento': list(missing), 'Precio': np.nan, 'Produccion': 0})], ignore_index=True)
        return g

    def get_prod_por_depto(self, anio=None):
        if self.df_eva is None:
            return pd.DataFrame({'Departamento': list(self.prod_depto.keys()), 'Produccion': list(self.prod_depto.values())})
        df = self.df_eva.copy()
        if anio and str(anio) != 'Todos':
            df = df[df['Año'] == int(anio)]
        return df.groupby('Departamento', as_index=False)['Produccion'].sum()

    def get_eva_depto(self, depto, anio=None):
        if self.df_eva is None or not depto or depto == 'Todos':
            return None
        df = self.df_eva[self.df_eva['Departamento'] == depto].copy()
        if anio and str(anio) != 'Todos':
            df = df[df['Año'] == int(anio)]
        if len(df) == 0:
            return {'Area_sembrada': 0, 'Area_cosechada': 0, 'Produccion': 0, 'Rendimiento': 0, 'n': 0}
        return {
            'Area_sembrada': float(df['Area_sembrada'].sum()),
            'Area_cosechada': float(df['Area_cosechada'].sum()),
            'Produccion': float(df['Produccion'].sum()),
            'Rendimiento': float(df['Rendimiento'].mean()) if 'Rendimiento' in df.columns else 0.0,
            'n': int(len(df))
        }

    def get_ranking(self, n=8, anio=None):
        df = self.get_prod_por_depto(anio).sort_values('Produccion', ascending=False).head(n)
        total = df['Produccion'].sum()
        df['Participacion'] = (df['Produccion'] / total * 100).round(1) if total > 0 else 0
        return df

    def get_serie_mensual(self, producto=None, anio=None, depto=None):
        if self.df_precios is None:
            return self.serie.copy()
        df = self.get_precios_filtrados(producto, anio, depto, None)
        if df is None or len(df) == 0 or 'Mes_numero' not in df.columns:
            return self.serie.copy()
        g = df.groupby('Mes_numero', as_index=False).agg(Precio=('Precio_por_kg_reportado', 'mean'))
        meses = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}
        g['Mes'] = g['Mes_numero'].map(meses)
        g = g.sort_values('Mes_numero')
        prod_anual = self.get_prod_por_depto(anio)['Produccion'].sum()
        g['Produccion'] = round(prod_anual / 12 / 1e6, 2)
        return g[['Mes', 'Precio', 'Produccion']]

    def get_kpis(self, producto=None, anio=None, depto=None, mes=None):
        df = self.get_precios_filtrados(producto, anio, depto, mes)
        if df is None or len(df) == 0:
            return {'precio_prom': 2450, 'precio_min': 1800, 'precio_max': 3200, 'var': 6.8, 'prod_nacional': 12.5, 'n_obs': 0, 'demo': True}
        precio_prom = float(df['Precio_por_kg_reportado'].mean())
        precio_min = float(df['Precio_por_kg_reportado'].min())
        precio_max = float(df['Precio_por_kg_reportado'].max())
        var = None
        if 'Mes_numero' in df.columns:
            try:
                base = self.get_precios_filtrados(producto, anio, depto, None)
                last = base.groupby('Mes_numero')['Precio_por_kg_reportado'].mean().sort_index()
                if mes and mes != 'Todos' and MES_NUM.get(mes):
                    m = MES_NUM[mes]
                    prev_idx = [i for i in last.index if i < m]
                    if prev_idx:
                        var = (last.loc[m] - last.loc[prev_idx[-1]]) / last.loc[prev_idx[-1]] * 100
                elif len(last) >= 2:
                    var = (last.iloc[-1] - last.iloc[-2]) / last.iloc[-2] * 100
            except Exception:
                pass
        prod = self.get_prod_por_depto(anio)['Produccion'].sum() / 1e6
        return {'precio_prom': precio_prom, 'precio_min': precio_min, 'precio_max': precio_max, 'var': var, 'prod_nacional': prod, 'n_obs': len(df), 'demo': False}

    def get_macro_kpis(self, anio=None):
        anio = anio or '2024'
        if self.df_precios is None:
            return {'precio_ponderado': 2450, 'prod_nacional_mt': 12.5, 'var_intermensual': 2.1, 'n_mercados': 45, 'n_deptos': 28, 'demo': True}
        df = self.df_precios.copy()
        if str(anio) != 'Todos': df = df[df['Año'] == int(anio)]
        precio_pond = float(df['Precio_por_kg_reportado'].mean()) if len(df) else 0
        prod = self.get_prod_por_depto(anio)['Produccion'].sum() / 1e6
        var = None
        if 'Mes_numero' in df.columns and df['Mes_numero'].nunique() >= 2:
            last = df.groupby('Mes_numero')['Precio_por_kg_reportado'].mean().sort_index()
            if len(last) >= 2: var = (last.iloc[-1] - last.iloc[-2]) / last.iloc[-2] * 100
        return {
            'precio_ponderado': precio_pond, 'prod_nacional_mt': prod,
            'var_intermensual': var, 'n_mercados': df['Ciudad_mercado'].nunique() if 'Ciudad_mercado' in df.columns else 0,
            'n_deptos': df['Departamento'].nunique() if 'Departamento' in df.columns else 0, 'demo': False
        }

    def get_top_alzas_bajas(self, anio=None, n=5):
        if self.df_precios is None or 'Mes_numero' not in self.df_precios.columns:
            return pd.DataFrame({'Producto': [], 'Var_pct': [], 'Tipo': []})
        df = self.df_precios.copy()
        if anio and str(anio) != 'Todos': df = df[df['Año'] == int(anio)]
        g = df.groupby(['Producto', 'Mes_numero'])['Precio_por_kg_reportado'].mean().reset_index()
        rows = []
        for prod, sub in g.groupby('Producto'):
            sub = sub.sort_values('Mes_numero')
            if len(sub) < 2: continue
            var = (sub['Precio_por_kg_reportado'].iloc[-1] - sub['Precio_por_kg_reportado'].iloc[-2]) / sub['Precio_por_kg_reportado'].iloc[-2] * 100
            rows.append({'Producto': prod, 'Var_pct': var})
        if not rows: return pd.DataFrame({'Producto': [], 'Var_pct': [], 'Tipo': []})
        res = pd.DataFrame(rows).dropna()
        alzas = res.nlargest(n, 'Var_pct').assign(Tipo='Alza')
        bajas = res.nsmallest(n, 'Var_pct').assign(Tipo='Baja')
        return pd.concat([alzas, bajas], ignore_index=True)

    def calcular_analisis_sensibilidad(self, depto, producto, shock_p=0, shock_r=0):
        eva = self.get_eva_depto(depto, None) or {'Produccion': 100000, 'Area_cosechada': 5000, 'Rendimiento': 5.0}
        kpis = self.get_kpis(producto, None, depto, None)
        precio_base = kpis.get('precio_prom', 2000)
        prod_base = eva['Produccion']
        area = eva.get('Area_cosechada', 1) or 1
        prod_sim = prod_base * (1 + shock_r / 100)
        precio_sim = precio_base * (1 + shock_p / 100)
        ingreso_base = prod_base * precio_base
        ingreso_sim = prod_sim * precio_sim
        return {
            'precio_base': precio_base, 'prod_base': prod_base,
            'ingreso_base': ingreso_base, 'ingreso_sim': ingreso_sim,
            'margen_ha_base': (prod_base / area) * precio_base,
            'margen_ha_sim': (prod_sim / area) * precio_sim,
            'delta_ingreso_pct': ((ingreso_sim - ingreso_base) / ingreso_base * 100) if ingreso_base else 0,
            'n_obs': kpis.get('n_obs', 0)
        }

# Inicializar motor en la sesión de Streamlit
if 'engine' not in st.session_state:
    st.session_state.engine = AgroEngine()

engine = st.session_state.engine

# ============================================================
# INTERFAZ DE USUARIO – STREAMLIT
# ============================================================
st.sidebar.markdown("## 🌱 AGROCOL")
st.sidebar.markdown("### Inteligencia de Mercados Agrícolas")

menu = st.sidebar.radio(
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
        "⚙️ Configuración / Carga"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("Datos oficiales:\n- DANE SIPSA\n- UPRA EVA")

# Filtros globales superiores
col_f1, col_f2, col_f3, col_f4 = st.columns(4)
with col_f1:
    producto = st.selectbox("Producto", engine.productos)
with col_f2:
    anio = st.selectbox("Año", ["Todos"] + [str(y) for y in range(2019, 2025)], index=5)
with col_f3:
    mes = st.selectbox("Mes", MES_LABELS)
with col_f4:
    depto = st.selectbox("Departamento", ["Todos"] + DEPARTAMENTOS_OFICIALES)

st.markdown("---")

# ============================================================
# LÓGICA DE VISTAS
# ============================================================

if "Inicio" in menu:
    st.markdown("# 🌱 Bienvenido a AgroData Colombia")
    st.markdown("Sistema de inteligencia de mercados agrícolas anclado a fuentes oficiales **DANE-SIPSA** (precios mayoristas) y **UPRA-EVA** (producción y área).")
    
    macro = engine.get_macro_kpis(anio)
    top_ab = engine.get_top_alzas_bajas(anio, 5)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Índice Precios Ponderado", f"${macro['precio_ponderado']:,.0f} COP/kg")
    with col2: st.metric("Producción Nacional EVA", f"{macro['prod_nacional_mt']:.2f} M t")
    with col3: st.metric("Var. Intermensual", f"{macro['var_intermensual']:+.1f}%" if macro['var_intermensual'] else "N/D")
    with col4: st.metric("Mercados / Deptos", f"{macro['n_mercados']} / {macro['n_deptos']}")

    st.markdown("### 📊 Top Alzas y Bajas Intermensuales")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.subheader("🔴 Principales Alzas")
        alzas = top_ab[top_ab['Tipo'] == 'Alza']
        st.dataframe(alzas[['Producto', 'Var_pct']], use_container_width=True)
    with col_a2:
        st.subheader("🟢 Principales Bajas")
        bajas = top_ab[top_ab['Tipo'] == 'Baja']
        st.dataframe(bajas[['Producto', 'Var_pct']], use_container_width=True)

elif "Resumen" in menu or "Precios" in menu:
    kpis = engine.get_kpis(producto, anio, depto, mes)
    st.markdown(f"## 💰 Análisis de Precios – {producto}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precio Promedio", f"${kpis['precio_prom']:,.0f} COP/kg", f"{kpis.get('var', 0):+.1f}%" if kpis.get('var') else None)
    c2.metric("Producción Nacional", f"{kpis['prod_nacional']:.2f} M t")
    c3.metric("Precio Mínimo", f"${kpis['precio_min']:,.0f} COP/kg")
    c4.metric("Precio Máximo", f"${kpis['precio_max']:,.0f} COP/kg")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.subheader("🗺️ Mapa de Precios por Departamento")
        df_mapa = engine.get_df_mapa_precios(producto, anio, mes)
        if geojson_colombia:
            fig_map = px.choropleth(df_mapa, geojson=geojson_colombia, locations='Departamento',
                                    featureidkey=f'properties.{PROP_NOMBRE}', color='Precio',
                                    color_continuous_scale='Greens', title=f"Precio Promedio – {producto}")
            fig_map.update_geos(fitbounds="locations", visible=False)
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.bar_chart(df_mapa.set_index('Departamento')['Precio'])

    with col_m2:
        st.subheader("📈 Serie Mensual y Producción")
        serie = engine.get_serie_mensual(producto, anio, depto if depto != 'Todos' else None)
        fig_serie = make_subplots(specs=[[{"secondary_y": True}]])
        fig_serie.add_trace(go.Bar(x=serie['Mes'], y=serie['Produccion'], name='Producción (Mt)', marker_color='#74C69D', opacity=0.7), secondary_y=False)
        fig_serie.add_trace(go.Scatter(x=serie['Mes'], y=serie['Precio'], name='Precio (COP/kg)', mode='lines+markers', line=dict(color='#2B6CB0', width=2.5)), secondary_y=True)
        st.plotly_chart(fig_serie, use_container_width=True)

elif "Producción" in menu:
    st.markdown("## 🌾 Producción Agrícola (EVA-UPRA)")
    df_prod = engine.get_df_mapa_produccion(anio)
    total_prod = df_prod['Produccion'].sum()
    st.metric("Volumen Total Nacional", f"{total_prod:,.0f} Toneladas")
    
    if geojson_colombia:
        fig_prod = px.choropleth(df_prod, geojson=geojson_colombia, locations='Departamento',
                                 featureidkey=f'properties.{PROP_NOMBRE}', color='Produccion',
                                 color_continuous_scale='Greens', title=f"Producción Agrícola por Departamento ({anio})")
        fig_prod.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig_prod, use_container_width=True)
    
    st.subheader("🏆 Ranking Departamental")
    st.dataframe(engine.get_ranking(15, anio), use_container_width=True)

elif "Por Departamento" in menu:
    st.markdown("## 📍 Análisis de Sensibilidad y Vulnerabilidad")
    dsel = depto if depto != 'Todos' else 'Cundinamarca'
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        sp = st.slider("Variación simulada de precio mayorista (%)", -50, 50, 0, 5)
    with col_s2:
        sr = st.slider("Choque de rendimiento / producción (%)", -50, 50, 0, 5)
        
    sens = engine.calcular_analisis_sensibilidad(dsel, producto, sp, sr)
    
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("Ingreso Base Estimado", f"{sens['ingreso_base']:,.0f}")
    col_r2.metric("Ingreso Simulado", f"{sens['ingreso_sim']:,.0f}", f"{sens['delta_ingreso_pct']:+.1f}%")
    col_r3.metric("Margen por Hectárea", f"{sens['margen_ha_sim']:,.0f}")

elif "Tendencias" in menu:
    st.markdown("## 📈 Tendencias e Inferencia Estadística")
    serie_ext, meta = engine.get_serie_tendencia(producto, anio, depto if depto != 'Todos' else None)
    if meta:
        st.info(f"**Dirección de tendencia:** {'Alcista' if meta['slope'] > 0 else 'Bajista'} | R² = {meta['r2']:.3f} | Coeficiente de variación: {meta['cv']:.1f}%")
    st.line_chart(serie_ext.set_index('Mes')[['Precio', 'Tendencia']])

elif "Comparativo" in menu:
    st.markdown("## ⚖️ Comparativo Dual: Producción (EVA) + Precio (SIPSA)")
    df_cruz = engine.get_comparativo_cruzado(producto, anio, mes)
    st.dataframe(df_cruz, use_container_width=True)

elif "Reportes" in menu:
    st.markdown("## 📋 Reportes Departamentales y Diagnóstico Causal")
    dsel = depto if depto != 'Todos' else 'Cundinamarca'
    resumen, serie_anual = engine.generar_reporte_departamental(dsel, anio)
    if resumen:
        st.json(resumen)
        st.dataframe(serie_anual, use_container_width=True)
        
        # Botón de exportación CSV
        csv_data = pd.DataFrame([resumen]).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte CSV", data=csv_data, file_name=f"reporte_{dsel}_{anio}.csv", mime="text/csv")
    else:
        st.warning("Selecciona un departamento válido.")

elif "Fuentes y Auditoría" in menu:
    st.markdown("## 📂 Fuentes y Auditoría Institucional")
    st.markdown("""
    - **DANE SIPSA**: Precios mayoristas y abastecimiento.
    - **UPRA / EVA**: Área, producción y aptitud de suelos.
    - **IDEAM**: Alertas climáticas e hidrometeorológicas.
    - **ICA**: Sanidad, plagas y cuarentenas.
    """)
    st.success(f"Motor activo: `{engine.version}` | Modo: **{engine.modo}**")

elif "Configuración / Carga" in menu:
    st.markdown("## ⚙️ Configuración y Carga de Archivos Oficiales")
    st.markdown("Sube tus archivos oficiales (`Precios_agricolas_consolidados_2019_2024.csv` y `EVA COLOMBIA AGRICOLA.csv`) para activar el **Modo Real**.")
    
    f_prec = st.file_uploader("Precios consolidados (Excel o CSV)", type=[".xlsx", ".xls", ".csv"])
    f_eva = st.file_uploader("EVA Colombia (CSV)", type=[".csv"])
    
    if st.button("Cargar bases de datos", type="primary"):
        msg = engine.cargar_archivos(f_prec, f_eva)
        st.success(msg)
