# ============================================================
# AGROCOL – Motor de datos (AgroEngine)
# ============================================================
import numpy as np
import pandas as pd
from scipy import stats
from src.config import (
    DEPARTAMENTOS_OFICIALES, MES_NUM, DANE_DEPTO, ciudad_a_depto
)

class AgroEngine:
    def __init__(self):
        self.modo = 'DEMO'
        self.df_precios = None
        self.df_eva = None
        self.productos = ['Maíz', 'Arroz', 'Papa', 'Café', 'Plátano', 'Yuca', 'Tomate', 'Cebolla', 'Aguacate', 'Apio']
        self.version = '2.1-Optimizado-Completo'
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

    def cargar_precios(self, path_or_file):
        try:
            path = path_or_file.name if hasattr(path_or_file, 'name') else str(path_or_file)
            path_lower = path.lower()
            if path_lower.endswith('.csv'):
                df = pd.read_csv(path, low_memory=False, encoding='utf-8')
            elif path_lower.endswith(('.xlsx', '.xls')):
                xl = pd.ExcelFile(path, engine='openpyxl')
                sheet = 'Base consolidada' if 'Base consolidada' in xl.sheet_names else xl.sheet_names[0]
                df = pd.read_excel(path, sheet_name=sheet, engine='openpyxl')
            else:
                try:
                    df = pd.read_csv(path, low_memory=False, encoding='utf-8')
                except Exception:
                    df = pd.read_excel(path, engine='openpyxl')

            df.columns = [str(c).strip() for c in df.columns]
            df = df.loc[:, ~df.columns.str.match(r'^Unnamed', na=False)]
            df = df.loc[:, ~df.columns.duplicated()]
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
                return f'❌ Faltan columnas Producto/Precio. Vistas: {list(df.columns)[:12]}'

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

            if 'Año' in df.columns:
                df['Año'] = pd.to_numeric(df['Año'], errors='coerce')
            if 'Mes_numero' in df.columns:
                df['Mes_numero'] = pd.to_numeric(df['Mes_numero'], errors='coerce')
            df['Precio_por_kg_reportado'] = pd.to_numeric(df['Precio_por_kg_reportado'], errors='coerce')
            df['Producto'] = df['Producto'].astype(str).str.strip()
            df = df.dropna(subset=['Producto', 'Precio_por_kg_reportado'])
            df = df[df['Producto'].str.lower() != 'nan']

            if 'Departamento' in df.columns:
                df['Departamento'] = df['Departamento'].astype(str).str.strip()
                valid = df['Departamento'].replace({'nan': None, 'None': None, '': None})
                if valid.isna().mean() > 0.8 and 'Ciudad_mercado' in df.columns:
                    df['Departamento'] = df['Ciudad_mercado'].apply(ciudad_a_depto)
            elif 'Ciudad_mercado' in df.columns:
                df['Departamento'] = df['Ciudad_mercado'].apply(ciudad_a_depto)
            else:
                df['Departamento'] = None

            self.df_precios = df.reset_index(drop=True)
            prod_series = self.df_precios['Producto']
            if isinstance(prod_series, pd.DataFrame):
                prod_series = prod_series.iloc[:, 0]
            self.productos = sorted(prod_series.dropna().astype(str).unique().tolist())
            self.modo = 'REAL'
            amin = int(df['Año'].min()) if 'Año' in df.columns and df['Año'].notna().any() else '?'
            amax = int(df['Año'].max()) if 'Año' in df.columns and df['Año'].notna().any() else '?'
            nd = df['Departamento'].nunique() if 'Departamento' in df.columns else 0
            return f'✅ Precios: {len(df):,} filas · {len(self.productos)} productos · {nd} deptos · {amin}-{amax}'
        except Exception as e:
            import traceback
            return f'❌ Error precios: {e}\n{traceback.format_exc()[:350]}'

    def cargar_eva(self, path_or_file):
        try:
            path = path_or_file.name if hasattr(path_or_file, 'name') else str(path_or_file)
            df = pd.read_csv(path, low_memory=False)
            col_code = 'Código Dane departamento' if 'Código Dane departamento' in df.columns else df.columns[0]
            df['Departamento'] = pd.to_numeric(df[col_code], errors='coerce').map(DANE_DEPTO)
            df['Año'] = pd.to_numeric(df['Año'], errors='coerce')
            for c_src, c_dst in [
                ('Producción (t)', 'Produccion'),
                ('Área sembrada (ha)', 'Area_sembrada'),
                ('Área cosechada (ha)', 'Area_cosechada'),
                ('Rendimiento (t/ha)', 'Rendimiento'),
            ]:
                if c_src in df.columns:
                    df[c_dst] = pd.to_numeric(df[c_src], errors='coerce').fillna(0)
                else:
                    df[c_dst] = 0
            df = df.dropna(subset=['Departamento'])
            self.df_eva = df
            self.modo = 'REAL'
            return f'✅ EVA: {len(df):,} filas · {df["Departamento"].nunique()} deptos · {int(df["Año"].min())}-{int(df["Año"].max())}'
        except Exception as e:
            return f'❌ Error EVA: {e}'

    def cargar_archivos(self, f_precios, f_eva):
        msgs = []
        if f_precios is not None:
            msgs.append(self.cargar_precios(f_precios))
        if f_eva is not None:
            msgs.append(self.cargar_eva(f_eva))
        if not msgs:
            msgs.append('ℹ️ Sin archivos. Modo DEMO.')
        return '\n'.join(msgs)

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
            rows = [{'Departamento': d, 'Precio': self.precios_depto.get(d, 2200),
                     'Produccion': self.prod_depto.get(d, 100000)} for d in DEPARTAMENTOS_OFICIALES]
            return pd.DataFrame(rows)
        df = self.get_precios_filtrados(producto, anio, None, mes)
        if df is None or len(df) == 0:
            return pd.DataFrame({'Departamento': DEPARTAMENTOS_OFICIALES, 'Precio': np.nan, 'Produccion': 0})
        g = df.groupby('Departamento', as_index=False)['Precio_por_kg_reportado'].mean()
        g = g.rename(columns={'Precio_por_kg_reportado': 'Precio'})
        prod = self.get_prod_por_depto(anio)
        g = g.merge(prod, on='Departamento', how='left')
        g['Produccion'] = g['Produccion'].fillna(0)
        missing = set(DEPARTAMENTOS_OFICIALES) - set(g['Departamento'].dropna())
        if missing:
            g = pd.concat([g, pd.DataFrame({'Departamento': list(missing), 'Precio': np.nan, 'Produccion': 0})], ignore_index=True)
        return g

    def get_prod_por_depto(self, anio=None):
        if self.df_eva is None:
            return pd.DataFrame({'Departamento': list(self.prod_depto.keys()),
                                'Produccion': list(self.prod_depto.values())})
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
            return {'precio_prom': 2450, 'precio_min': 1800, 'precio_max': 3200,
                    'var': 6.8, 'prod_nacional': 12.5, 'n_obs': 0, 'demo': True}
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
                    if m in last.index:
                        prev_idx = [i for i in last.index if i < m]
                        if prev_idx:
                            var = (last.loc[m] - last.loc[prev_idx[-1]]) / last.loc[prev_idx[-1]] * 100
                elif len(last) >= 2:
                    var = (last.iloc[-1] - last.iloc[-2]) / last.iloc[-2] * 100
            except Exception:
                pass
        prod = self.get_prod_por_depto(anio)['Produccion'].sum() / 1e6
        return {
            'precio_prom': precio_prom, 'precio_min': precio_min, 'precio_max': precio_max,
            'var': var, 'prod_nacional': prod, 'n_obs': len(df), 'demo': False
        }

    # ---------- NUEVOS MÉTODOS PARA PESTAÑAS OPTIMIZADAS ----------

    def get_macro_kpis(self, anio=None):
        """KPIs macro nacionales para pestaña Inicio."""
        anio = anio or '2024'
        if self.df_precios is None:
            return {
                'precio_ponderado': 2450, 'prod_nacional_mt': 12.5,
                'var_intermensual': 2.1, 'n_mercados': 45, 'n_deptos': 28, 'demo': True
            }
        df = self.df_precios.copy()
        if str(anio) != 'Todos':
            df = df[df['Año'] == int(anio)]
        precio_pond = float(df['Precio_por_kg_reportado'].mean()) if len(df) else 0
        prod = self.get_prod_por_depto(anio)['Produccion'].sum() / 1e6
        var = None
        if 'Mes_numero' in df.columns and df['Mes_numero'].nunique() >= 2:
            last = df.groupby('Mes_numero')['Precio_por_kg_reportado'].mean().sort_index()
            if len(last) >= 2:
                var = (last.iloc[-1] - last.iloc[-2]) / last.iloc[-2] * 100
        n_mercados = df['Ciudad_mercado'].nunique() if 'Ciudad_mercado' in df.columns else 0
        n_deptos = df['Departamento'].nunique() if 'Departamento' in df.columns else 0
        return {
            'precio_ponderado': precio_pond, 'prod_nacional_mt': prod,
            'var_intermensual': var, 'n_mercados': n_mercados, 'n_deptos': n_deptos, 'demo': False
        }

    def get_top_alzas_bajas(self, anio=None, n=5):
        """Top 5 productos con mayor alza y baja intermensual."""
        if self.df_precios is None or 'Mes_numero' not in self.df_precios.columns:
            return pd.DataFrame({'Producto': [], 'Var_pct': [], 'Tipo': []})
        df = self.df_precios.copy()
        if anio and str(anio) != 'Todos':
            df = df[df['Año'] == int(anio)]
        g = df.groupby(['Producto', 'Mes_numero'])['Precio_por_kg_reportado'].mean().reset_index()
        rows = []
        for prod, sub in g.groupby('Producto'):
            sub = sub.sort_values('Mes_numero')
            if len(sub) < 2:
                continue
            var = (sub['Precio_por_kg_reportado'].iloc[-1] - sub['Precio_por_kg_reportado'].iloc[-2]) / sub['Precio_por_kg_reportado'].iloc[-2] * 100
            rows.append({'Producto': prod, 'Var_pct': var})
        if not rows:
            return pd.DataFrame({'Producto': [], 'Var_pct': [], 'Tipo': []})
        res = pd.DataFrame(rows).dropna()
        alzas = res.nlargest(n, 'Var_pct').assign(Tipo='Alza')
        bajas = res.nsmallest(n, 'Var_pct').assign(Tipo='Baja')
        return pd.concat([alzas, bajas], ignore_index=True)

    def get_df_mapa_produccion(self, anio=None):
        """Mapa coroplético de producción (toneladas) por departamento."""
        g = self.get_prod_por_depto(anio)
        missing = set(DEPARTAMENTOS_OFICIALES) - set(g['Departamento'].dropna())
        if missing:
            g = pd.concat([g, pd.DataFrame({'Departamento': list(missing), 'Produccion': 0})], ignore_index=True)
        total = g['Produccion'].sum()
        g['Participacion'] = (g['Produccion'] / total * 100).round(2) if total > 0 else 0
        return g

    def calcular_analisis_sensibilidad(self, depto, producto, shock_precio_pct=0, shock_rendimiento_pct=0):
        """Simulación de ingreso bruto y margen bajo choques de precio y rendimiento."""
        eva = self.get_eva_depto(depto, None)
        if eva is None:
            eva = {'Produccion': 100000, 'Area_cosechada': 5000, 'Rendimiento': 5.0, 'n': 0}
        kpis = self.get_kpis(producto, None, depto, None)
        precio_base = kpis.get('precio_prom', 2000)
        prod_base = eva['Produccion']
        rend_base = eva.get('Rendimiento', 5.0) or 5.0
        area = eva.get('Area_cosechada', 1) or 1

        prod_sim = prod_base * (1 + shock_rendimiento_pct / 100)
        precio_sim = precio_base * (1 + shock_precio_pct / 100)
        ingreso_base = prod_base * precio_base  # t * COP/kg ≈ COP (escala aproximada)
        ingreso_sim = prod_sim * precio_sim
        margen_ha_base = (prod_base / area) * precio_base if area > 0 else 0
        margen_ha_sim = (prod_sim / area) * precio_sim if area > 0 else 0

        # Matriz de elasticidad simple (exposición)
        escenarios = []
        for dp in [-30, -20, -10, 0, 10, 20]:
            for dr in [-30, -15, 0, 15]:
                p = prod_base * (1 + dr / 100) * precio_base * (1 + dp / 100)
                escenarios.append({'dP': dp, 'dR': dr, 'Ingreso': p})

        return {
            'precio_base': precio_base, 'prod_base': prod_base, 'rend_base': rend_base,
            'ingreso_base': ingreso_base, 'ingreso_sim': ingreso_sim,
            'margen_ha_base': margen_ha_base, 'margen_ha_sim': margen_ha_sim,
            'delta_ingreso_pct': ((ingreso_sim - ingreso_base) / ingreso_base * 100) if ingreso_base else 0,
            'escenarios': pd.DataFrame(escenarios),
            'n_obs': kpis.get('n_obs', 0)
        }

    def get_distribucion_precios(self, producto=None, anio=None, depto=None, mes=None):
        df = self.get_precios_filtrados(producto, anio, depto, mes)
        if df is None or len(df) == 0:
            return {'mean': 0, 'median': 0, 'std': 0, 'skew': 0, 'data': np.array([])}
        s = df['Precio_por_kg_reportado'].dropna()
        return {
            'mean': float(s.mean()), 'median': float(s.median()),
            'std': float(s.std()), 'skew': float(s.skew()) if len(s) > 2 else 0,
            'data': s.values
        }

    def get_distribucion_produccion(self, anio=None):
        g = self.get_prod_por_depto(anio)
        s = g['Produccion'].dropna()
        return {
            'mean': float(s.mean()) if len(s) else 0,
            'median': float(s.median()) if len(s) else 0,
            'std': float(s.std()) if len(s) else 0,
            'data': s.values, 'deptos': g
        }

    def get_serie_tendencia(self, producto=None, anio=None, depto=None):
        """Serie mensual + tendencia lineal + bandas de confianza aproximadas."""
        serie = self.get_serie_mensual(producto, anio, depto)
        if serie is None or len(serie) < 3:
            return serie, None
        y = serie['Precio'].values.astype(float)
        x = np.arange(len(y))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        trend = intercept + slope * x
        # IC 95% simple alrededor de la tendencia
        resid = y - trend
        se = np.std(resid, ddof=2) if len(resid) > 2 else 0
        ci = 1.96 * se
        serie = serie.copy()
        serie['Tendencia'] = trend
        serie['IC_inf'] = trend - ci
        serie['IC_sup'] = trend + ci
        # Proyección 3 meses
        fut_x = np.arange(len(y), len(y) + 3)
        fut_trend = intercept + slope * fut_x
        proy = pd.DataFrame({
            'Mes': [f'P+{i+1}' for i in range(3)],
            'Precio': fut_trend, 'Tendencia': fut_trend,
            'IC_inf': fut_trend - ci, 'IC_sup': fut_trend + ci
        })
        meta = {
            'slope': slope, 'r2': r_value**2, 'p_value': p_value,
            'cv': (np.std(y) / np.mean(y) * 100) if np.mean(y) else 0,
            'cambio_pct': ((y[-1] - y[0]) / y[0] * 100) if y[0] else 0
        }
        return pd.concat([serie, proy], ignore_index=True), meta

    def get_comparativo_cruzado(self, producto=None, anio=None, mes=None):
        """Cruza producción EVA + precio SIPSA por departamento."""
        prod = self.get_df_mapa_produccion(anio)
        prec = self.get_df_mapa_precios(producto, anio, mes)
        g = prod.merge(prec[['Departamento', 'Precio']], on='Departamento', how='outer')
        g['Produccion'] = g['Produccion'].fillna(0)
        g['Precio'] = g['Precio']
        g['Estado'] = np.where(
            (g['Produccion'] <= 0) & (g['Precio'].isna()),
            'No produce / Sin registro oficial',
            np.where(g['Produccion'] <= 0, 'Sin producción reportada', 'Activo')
        )
        total = g['Produccion'].sum()
        g['Participacion'] = (g['Produccion'] / total * 100).round(2) if total > 0 else 0
        return g

    def generar_reporte_departamental(self, depto, anio=None):
        """Top 5 cultivos por volumen en el departamento (agregado total EVA)."""
        if self.df_eva is None or not depto or depto == 'Todos':
            return pd.DataFrame()
        df = self.df_eva[self.df_eva['Departamento'] == depto].copy()
        if anio and str(anio) != 'Todos':
            df = df[df['Año'] == int(anio)]
        # Como EVA no trae nombres de cultivo legibles, usamos agregados por código
        # y devolvemos métricas totales + ranking de participación por año si es posible
        resumen = {
            'Produccion': float(df['Produccion'].sum()),
            'Area_sembrada': float(df['Area_sembrada'].sum()),
            'Area_cosechada': float(df['Area_cosechada'].sum()),
            'Rendimiento': float(df['Rendimiento'].mean()) if len(df) else 0,
            'n_registros': len(df)
        }
        # Ranking simplificado: top por producción agregada (sin nombre de cultivo legible)
        # En modo real se recomienda mapear códigos; aquí entregamos el total departamental
        return resumen, df.groupby('Año', as_index=False).agg(
            Produccion=('Produccion', 'sum'),
            Area_sembrada=('Area_sembrada', 'sum'),
            Area_cosechada=('Area_cosechada', 'sum'),
            Rendimiento=('Rendimiento', 'mean')
        ).sort_values('Produccion', ascending=False)


