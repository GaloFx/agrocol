# ============================================================
# AGROCOL – Visualizaciones (Plotly)
# ============================================================
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def crear_mapa_coropletico(df_mapa, geojson, prop_nombre, titulo='Precio promedio por Departamento',
                           color_col='Precio', colorscale='Greens', units='COP/kg'):
    if geojson is None or df_mapa is None or len(df_mapa) == 0:
        fig = go.Figure(go.Bar(
            x=df_mapa[color_col] if df_mapa is not None and color_col in df_mapa.columns else [],
            y=df_mapa['Departamento'] if df_mapa is not None else [],
            orientation='h',
            marker=dict(color=df_mapa[color_col] if df_mapa is not None and color_col in df_mapa.columns else [],
                        colorscale=colorscale, showscale=True)
        ))
        fig.update_layout(title=titulo + ' (fallback)', height=420,
                          yaxis=dict(autorange='reversed'), margin=dict(l=10, r=10, t=40, b=10))
        return fig

    df = df_mapa.copy()
    vals = df[color_col].dropna()
    if len(vals) > 0:
        p5, p95 = np.nanpercentile(vals, [5, 95])
        if p5 == p95:
            p5, p95 = vals.min(), vals.max()
    else:
        p5, p95 = 0, 1

    hover = 'Departamento: %{location}<br>' + color_col + ': %{z:,.0f} ' + units + '<extra></extra>'
    if 'Participacion' in df.columns:
        hover = ('Departamento: %{location}<br>' + color_col + ': %{z:,.0f} ' + units +
                 '<br>Participación: %{customdata:.1f}%<extra></extra>')

    fig = px.choropleth(
        df, geojson=geojson, locations='Departamento',
        featureidkey=f'properties.{prop_nombre}',
        color=color_col, color_continuous_scale=colorscale,
        range_color=(p5, p95),
        custom_data=['Participacion'] if 'Participacion' in df.columns else None,
        title=titulo
    )
    fig.update_geos(fitbounds='locations', visible=False)
    fig.update_layout(
        height=480, margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(title=units, thickness=12),
        font=dict(family='Inter, sans-serif', size=12)
    )
    if 'Participacion' in df.columns:
        fig.update_traces(hovertemplate=hover)
    return fig


def crear_mapa_produccion(df_mapa, geojson, prop_nombre, titulo='Producción agrícola por Departamento'):
    return crear_mapa_coropletico(df_mapa, geojson, prop_nombre, titulo,
                                   color_col='Produccion', colorscale='Greens', units='t')


def crear_mapa_comparativo(df_mapa, geojson, prop_nombre, producto, periodo):
    """Mapa dual: color = producción; hover muestra precio + producción."""
    df = df_mapa.copy()
    df['Precio_disp'] = df['Precio'].fillna(-1)
    vals = df['Produccion'].dropna()
    p5, p95 = (np.nanpercentile(vals, [5, 95]) if len(vals) else (0, 1))
    if p5 == p95:
        p5, p95 = 0, max(vals.max() if len(vals) else 1, 1)

    fig = px.choropleth(
        df, geojson=geojson, locations='Departamento',
        featureidkey=f'properties.{prop_nombre}',
        color='Produccion', color_continuous_scale='Greens',
        range_color=(p5, p95),
        custom_data=['Precio', 'Participacion', 'Estado'],
        title=f'Comparativo Producción + Precio – {producto} ({periodo})'
    )
    fig.update_traces(
        hovertemplate=(
            '<b>%{location}</b><br>'
            'Producción: %{z:,.0f} t<br>'
            'Participación: %{customdata[1]:.1f}%<br>'
            'Precio prom.: %{customdata[0]:,.0f} COP/kg<br>'
            'Estado: %{customdata[2]}<extra></extra>'
        )
    )
    fig.update_geos(fitbounds='locations', visible=False)
    fig.update_layout(height=480, margin=dict(l=0, r=0, t=40, b=0),
                      coloraxis_colorbar=dict(title='t', thickness=12),
                      font=dict(family='Inter, sans-serif', size=12))
    return fig


def crear_grafico_combinado(serie, producto):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=serie['Mes'], y=serie['Produccion'], name='Producción (M t)',
                         marker_color='#74C69D', opacity=0.7), secondary_y=False)
    fig.add_trace(go.Scatter(x=serie['Mes'], y=serie['Precio'], name='Precio (COP/kg)',
                             mode='lines+markers', line=dict(color='#2B6CB0', width=2.5),
                             marker=dict(size=7)), secondary_y=True)
    fig.update_layout(
        title=f'Serie mensual – {producto}', height=380,
        legend=dict(orientation='h', y=1.08),
        margin=dict(l=10, r=10, t=50, b=10),
        font=dict(family='Inter, sans-serif', size=12),
        plot_bgcolor='white'
    )
    fig.update_yaxes(title_text='Producción (Millones t)', secondary_y=False, gridcolor='#EDF2F7')
    fig.update_yaxes(title_text='Precio (COP/kg)', secondary_y=True, gridcolor='#EDF2F7')
    fig.update_xaxes(gridcolor='#EDF2F7')
    return fig


def crear_histogramas_regionales(dist_precio, dist_prod, producto):
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=(f'Distribución de Precios – {producto}',
                                        'Distribución de Producción por Depto'))
    if len(dist_precio.get('data', [])) > 0:
        fig.add_trace(go.Histogram(x=dist_precio['data'], nbinsx=30, name='Precios',
                                   marker_color='#40916C', opacity=0.85),
                      row=1, col=1)
        fig.add_vline(x=dist_precio['mean'], line_dash='dash', line_color='#E53E3E',
                      annotation_text=f"Media {dist_precio['mean']:,.0f}", row=1, col=1)
    if len(dist_prod.get('data', [])) > 0:
        fig.add_trace(go.Histogram(x=dist_prod['data'], nbinsx=20, name='Producción',
                                   marker_color='#2B6CB0', opacity=0.85),
                      row=1, col=2)
    fig.update_layout(height=380, showlegend=False, margin=dict(l=10, r=10, t=50, b=10),
                      font=dict(family='Inter, sans-serif', size=12))
    fig.update_xaxes(title_text='COP/kg', row=1, col=1)
    fig.update_xaxes(title_text='Toneladas', row=1, col=2)
    return fig


def crear_grafico_tendencias_proyectadas(serie_ext, meta, producto):
    if serie_ext is None or len(serie_ext) == 0:
        return go.Figure()
    hist = serie_ext[~serie_ext['Mes'].astype(str).str.startswith('P+')]
    proy = serie_ext[serie_ext['Mes'].astype(str).str.startswith('P+')]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist['Mes'], y=hist['Precio'], mode='lines+markers',
                             name='Precio histórico', line=dict(color='#2B6CB0', width=2.5)))
    if 'Tendencia' in hist.columns:
        fig.add_trace(go.Scatter(x=hist['Mes'], y=hist['Tendencia'], mode='lines',
                                 name='Tendencia', line=dict(color='#40916C', width=2, dash='dash')))
        fig.add_trace(go.Scatter(x=hist['Mes'], y=hist['IC_sup'], mode='lines',
                                 line=dict(width=0), showlegend=False))
        fig.add_trace(go.Scatter(x=hist['Mes'], y=hist['IC_inf'], mode='lines',
                                 fill='tonexty', fillcolor='rgba(64,145,108,0.15)',
                                 line=dict(width=0), name='IC 95%'))
    if len(proy) > 0:
        fig.add_trace(go.Scatter(x=proy['Mes'], y=proy['Tendencia'], mode='lines+markers',
                                 name='Proyección', line=dict(color='#D69E2E', width=2, dash='dot')))
    fig.update_layout(title=f'Tendencia y proyección – {producto}', height=400,
                      legend=dict(orientation='h', y=1.08),
                      margin=dict(l=10, r=10, t=50, b=10),
                      font=dict(family='Inter, sans-serif', size=12),
                      plot_bgcolor='white')
    fig.update_yaxes(title_text='COP/kg', gridcolor='#EDF2F7')
    return fig


def crear_heatmap_sensibilidad(escenarios):
    if escenarios is None or len(escenarios) == 0:
        return go.Figure()
    pivot = escenarios.pivot(index='dR', columns='dP', values='Ingreso')
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        colorscale='RdYlGn', colorbar=dict(title='Ingreso')
    ))
    fig.update_layout(title='Matriz de sensibilidad (Δ Precio % vs Δ Rendimiento %)',
                      xaxis_title='Choque de precio (%)', yaxis_title='Choque de rendimiento (%)',
                      height=360, margin=dict(l=10, r=10, t=40, b=10),
                      font=dict(family='Inter, sans-serif', size=12))
    return fig


def crear_tornado_sensibilidad(sens):
    base = sens['ingreso_base'] or 1
    # Impacto aislado de precio ±20% y rendimiento ±20%
    impacto_p = abs(sens['precio_base'] * 0.2 * sens['prod_base'])
    impacto_r = abs(sens['prod_base'] * 0.2 * sens['precio_base'])
    fig = go.Figure()
    fig.add_trace(go.Bar(y=['Precio (±20%)', 'Rendimiento (±20%)'],
                         x=[impacto_p, impacto_r], orientation='h',
                         marker_color=['#2B6CB0', '#40916C'],
                         text=[f'{impacto_p:,.0f}', f'{impacto_r:,.0f}'], textposition='auto'))
    fig.update_layout(title='Descomposición de sensibilidad (impacto absoluto)',
                      height=280, margin=dict(l=10, r=10, t=40, b=10),
                      font=dict(family='Inter, sans-serif', size=12),
                      xaxis_title='Impacto en ingreso estimado')
    return fig

