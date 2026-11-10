# ============================================================
# AGROCOL – Configuración, colores, departamentos, GeoJSON
# ============================================================
import pandas as pd
import requests

COLORES = {
    'sidebar': '#1B4332',
    'sidebar_hover': '#2D6A4F',
    'verde_kpi': '#40916C',
    'verde_claro': '#74C69D',
    'fondo': '#F5F7F6',
    'blanco': '#FFFFFF',
    'texto': '#1A202C',
    'texto_secundario': '#718096',
    'azul_linea': '#2B6CB0',
    'rojo': '#E53E3E',
    'amarillo': '#D69E2E',
    'gris_neutral': '#CBD5E0'
}

DEPARTAMENTOS_OFICIALES = [
    'Amazonas', 'Antioquia', 'Arauca', 'Atlántico', 'Bogotá D.C.', 'Bolívar', 'Boyacá',
    'Caldas', 'Caquetá', 'Casanare', 'Cauca', 'Cesar', 'Chocó', 'Córdoba', 'Cundinamarca',
    'Guainía', 'Guaviare', 'Huila', 'La Guajira', 'Magdalena', 'Meta', 'Nariño',
    'Norte de Santander', 'Putumayo', 'Quindío', 'Risaralda', 'San Andrés y Providencia',
    'Santander', 'Sucre', 'Tolima', 'Valle del Cauca', 'Vaupés', 'Vichada'
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
    91: 'Amazonas', 94: 'Guainía', 95: 'Guaviare', 97: 'Vaupés', 99: 'Vichada', 11: 'Bogotá D.C.'
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
    "https://raw.githubusercontent.com/santiblanko/colombia.geojson/master/depto.json",
    "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/COL/ADM1/geoBoundaries-COL-ADM1_simplified.geojson"
]


def cargar_geojson():
    for url in GEOJSON_URLS:
        try:
            r = requests.get(url, timeout=25)
            if r.status_code == 200:
                return r.json()
        except Exception:
            continue
    return None


def detectar_prop_nombre(geo):
    if geo is None:
        return None
    props = geo['features'][0]['properties']
    candidatos = ['DPTO_CNMBR', 'NOMBRE_DPT', 'name', 'NAME_1', 'shapeName', 'NOM_DEPART', 'departamento', 'DPTO']
    for c in candidatos:
        if c in props:
            return c
    return list(props.keys())[0]
