# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import calendar
from datetime import date, timedelta

# -------------------------------
# Ruta y validación del archivo
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "ffmm_merged.parquet")

if not os.path.exists(file_path):
    st.error("❌ No se encontró el archivo 'ffmm_merged.parquet'. Verificá que esté subido al repositorio.")
    st.stop()

# -------------------------------
# Función cacheada para cargar datos
# -------------------------------
@st.cache_data
def cargar_datos_parquet(path):
    columnas_necesarias = [
        "FECHA_INF", "RUN_FM", "Nombre_Corto", "NOM_ADM", "SERIE",
        "PATRIMONIO_NETO_MM", "VENTA_NETA_MM", "TIPO_FM", "Categoría"
    ]
    return pd.read_parquet(path, columns=columnas_necesarias, engine="pyarrow")

@st.cache_data
def obtener_rango_fechas(df):
    años = sorted(df["FECHA_INF_DATE"].dt.year.unique())
    meses = list(calendar.month_name)[1:]
    return años, meses

try:
    df = cargar_datos_parquet(file_path)
except Exception as e:
    st.error(f"❌ Error al leer el archivo Parquet: {e}")
    st.stop()

# -------------------------------
# Preprocesamiento
# -------------------------------
df["FECHA_INF_DATE"] = pd.to_datetime(df["FECHA_INF"], format="%Y%m%d", errors="coerce")
df["RUN_FM_NOMBRECORTO"] = df["RUN_FM"].astype(str) + " - " + df["Nombre_Corto"].astype(str)

# -------------------------------
# Título con logo
# -------------------------------
st.markdown("""
<div style='display: flex; align-items: center; gap: 15px; padding-top: 10px;'>
    <img src='https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Owl_in_the_Moonlight.jpg/640px-Owl_in_the_Moonlight.jpg'
         width='60' style='border-radius: 50%; box-shadow: 0 2px 6px rgba(0,0,0,0.2);'/>
    <h1 style='margin: 0; font-size: 2.2em;'>Dashboard Fondos Mutuos</h1>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# Filtro de fechas con Mes/Año
# -------------------------------
st.markdown("### Rango de Fechas")
fechas_disponibles = df["FECHA_INF_DATE"].dropna()

if not fechas_disponibles.empty:
    años_disponibles, meses_disponibles = obtener_rango_fechas(df)

    fecha_min_real = fechas_disponibles.min().date()
    fecha_max_real = fechas_disponibles.max().date()

    año_inicio_default = fecha_min_real.year
    mes_inicio_default = fecha_min_real.month - 1

    año_fin_default = fecha_max_real.year
    mes_fin_default = fecha_max_real.month - 1

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    año_inicio = col1.selectbox("Año inicio", años_disponibles,
                                index=años_disponibles.index(año_inicio_default))
    mes_inicio = col2.selectbox("Mes inicio", meses_disponibles,
                                index=mes_inicio_default)

    año_fin = col3.selectbox("Año fin", años_disponibles,
                             index=años_disponibles.index(año_fin_default))
    mes_fin = col4.selectbox("Mes fin", meses_disponibles,
                             index=mes_fin_default)

    # Calcular fechas exactas y limitar al máximo real
    fecha_inicio = date(año_inicio, meses_disponibles.index(mes_inicio)+1, 1)
    ultimo_dia_mes = calendar.monthrange(año_fin, meses_disponibles.index(mes_fin)+1)[1]
    fecha_fin_teorica = date(año_fin, meses_disponibles.index(mes_fin)+1, ultimo_dia_mes)
    fecha_fin = min(fecha_fin_teorica, fecha_max_real)

    rango_fechas = (fecha_inicio, fecha_fin)
else:
    st.warning("No hay fechas disponibles para este filtro.")
    st.stop()

# Filtrar DF por rango de fechas primero
df = df[(df["FECHA_INF_DATE"].dt.date >= rango_fechas[0]) &
        (df["FECHA_INF_DATE"].dt.date <= rango_fechas[1])]

if df.empty:
    st.warning("No hay datos disponibles en el rango seleccionado.")
    st.stop()

# -------------------------------
# Inicializar session_state para slider/botones
# -------------------------------
if "rango_fechas" not in st.session_state:
    st.session_state["rango_fechas"] = (rango_fechas[0], rango_fechas[1])

# -------------------------------
# Multiselect con "Seleccionar todo"
# -------------------------------
def multiselect_con_todo(label, opciones):
    opciones_mostradas = ["(Seleccionar todo)"] + list(opciones)
    seleccion = st.multiselect(label, opciones_mostradas, default=["(Seleccionar todo)"])
    if "(Seleccionar todo)" in seleccion or not seleccion:
        return list(opciones)
    else:
        return seleccion

# -------------------------------
# Filtros adaptativos
# -------------------------------
def filtro_dinamico(label, opciones):
    if len(opciones) < 5:
        seleccion = st.selectbox(label, opciones)
        return [seleccion]
    else:
        return multiselect_con_todo(label, opciones)

# -------------------------------
# Filtros principales
# -------------------------------
categoria_opciones = sorted(df["Categoría"].dropna().unique())
categoria_seleccionadas = filtro_dinamico("Categoría", categoria_opciones)

adm_opciones = sorted(df[df["Categoría"].isin(categoria_seleccionadas)]["NOM_ADM"].dropna().unique())
adm_seleccionadas = filtro_dinamico("Administradora(s)", adm_opciones)

fondo_opciones = sorted(df[df["NOM_ADM"].isin(adm_seleccionadas)]["RUN_FM_NOMBRECORTO"].dropna().unique())
fondo_seleccionados = filtro_dinamico("Fondo(s)", fondo_opciones)

with st.expander("🔧 Filtros adicionales"):
    tipo_opciones = sorted(df["TIPO_FM"].dropna().unique())
    tipo_seleccionados = filtro_dinamico("Tipo de Fondo", tipo_opciones)

    serie_opciones = sorted(df[df["RUN_FM_NOMBRECORTO"].isin(fondo_seleccionados)]["SERIE"].dropna().unique())
    serie_seleccionadas = filtro_dinamico("Serie(s)", serie_opciones)

    # -------------------------------
    # Ajuste fino de fechas con slider + botones rápidos
    # -------------------------------
    st.markdown("#### Ajuste fino de fechas")

    fechas_unicas = sorted(df["FECHA_INF_DATE"].dt.date.unique())
    fecha_min_real = fechas_unicas[0]
    fecha_max_real = fechas_unicas[-1]
    hoy = fecha_max_real

    # Slider dinámico conectado a session_state
    st.session_state["rango_fechas"] = st.slider(
        "Rango exacto",
        min_value=fecha_min_real,
        max_value=fecha_max_real,
        value=st.session_state["rango_fechas"],
        format="DD-MM-YYYY"
    )

    # Botones rápidos que actualizan slider
    col_a, col_b, col_c, col_d, col_e = st.columns(5)

    if col_a.button("1M"):
        st.session_state["rango_fechas"] = (max(hoy - timedelta(days=30), fecha_min_real), hoy)
    if col_b.button("3M"):
        st.session_state["rango_fechas"] = (max(hoy - timedelta(days=90), fecha_min_real), hoy)
    if col_c.button("6M"):
        st.session_state["rango_fechas"] = (max(hoy - timedelta(days=180), fecha_min_real), hoy)
    if col_d.button("MTD"):
        st.session_state["rango_fechas"] = (date(hoy.year, hoy.month, 1), hoy)
    if col_e.button("YTD"):
        st.session_state["rango_fechas"] = (date(hoy.year, 1, 1), hoy)

# -------------------------------
# Aplicar filtros juntos
# -------------------------------
rango_fechas = st.session_state["rango_fechas"]

df_filtrado = df[df["TIPO_FM"].isin(tipo_seleccionados)]
df_filtrado = df_filtrado[df_filtrado["Categoría"].isin(categoria_seleccionadas)]
df_filtrado = df_filtrado[df_filtrado["NOM_ADM"].isin(adm_seleccionadas)]
df_filtrado = df_filtrado[df_filtrado["RUN_FM_NOMBRECORTO"].isin(fondo_seleccionados)]
df_filtrado = df_filtrado[df_filtrado["SERIE"].isin(serie_seleccionadas)]
df_filtrado = df_filtrado[(df_filtrado["FECHA_INF_DATE"].dt.date >= rango_fechas[0]) &
                          (df_filtrado["FECHA_INF_DATE"].dt.date <= rango_fechas[1])]

if df_filtrado.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
    st.stop()

# -------------------------------
# Tabs
# -------------------------------
tab1, tab2, tab3 = st.tabs([
    "Patrimonio Neto Total (MM CLP)",
    "Venta Neta Acumulada (MM CLP)",
    "Listado de Fondos Mutuos"
])

with tab1:
    st.subheader("Evolución del Patrimonio Neto Total (en millones de CLP)")
    patrimonio_total = (
        df_filtrado.groupby(df_filtrado["FECHA_INF_DATE"].dt.date)["PATRIMONIO_NETO_MM"]
        .sum()
        .sort_index()
    )
    patrimonio_total.index = pd.to_datetime(patrimonio_total.index)
    st.bar_chart(patrimonio_total, height=300, use_container_width=True)

with tab2:
    st.subheader("Evolución acumulada de la Venta Neta (en millones de CLP)")
    venta_neta_acumulada = (
        df_filtrado.groupby(df_filtrado["FECHA_INF_DATE"].dt.date)["VENTA_NETA_MM"]
        .sum()
        .cumsum()
        .sort_index()
    )
    venta_neta_acumulada.index = pd.to_datetime(venta_neta_acumulada.index)
    st.bar_chart(venta_neta_acumulada, height=300, use_container_width=True)

with tab3:
    ranking_ventas = (
        df_filtrado
        .groupby(["RUN_FM", "Nombre_Corto", "NOM_ADM"], as_index=False)["VENTA_NETA_MM"]
        .sum()
        .sort_values(by="VENTA_NETA_MM", ascending=False)
        .head(20)
        .copy()
    )

    total_fondos = df_filtrado[["RUN_FM", "Nombre_Corto", "NOM_ADM"]].drop_duplicates().shape[0]
    cantidad_ranking = ranking_ventas.shape[0]

    if total_fondos <= 20:
        titulo = f"Listado de Fondos Mutuos (total: {total_fondos})"
    else:
        titulo = f"Listado de Fondos Mutuos (top {cantidad_ranking} por Venta Neta de {total_fondos})"

    st.subheader(titulo)

    def generar_url_cmf(rut):
        return f"https://www.cmfchile.cl/institucional/mercados/entidad.php?auth=&send=&mercado=V&rut={rut}&tipoentidad=RGFMU&vig=VI&row=AAAw+cAAhAABP4UAAB&control=svs&pestania=1"

    ranking_ventas["URL CMF"] = ranking_ventas["RUN_FM"].astype(str).apply(generar_url_cmf)

    ranking_ventas = ranking_ventas.rename(columns={
        "RUN_FM": "RUT",
        "Nombre_Corto": "Nombre del Fondo",
        "NOM_ADM": "Administradora",
        "VENTA_NETA_MM": "Venta Neta Acumulada (MM CLP)"
    })

    ranking_ventas["Venta Neta Acumulada (MM CLP)"] = ranking_ventas["Venta Neta Acumulada (MM CLP)"].apply(
        lambda x: f"{x:,.0f}".replace(",", ".")
    )

    ranking_ventas["URL CMF"] = ranking_ventas["URL CMF"].apply(lambda x: f'<a href="{x}" target="_blank">Ver en CMF</a>')

    st.markdown(ranking_ventas.to_html(index=False, escape=False), unsafe_allow_html=True)

# -------------------------------
# Descargar CSV
# -------------------------------
st.markdown("### Descargar datos filtrados")

MAX_FILAS = 100_000
st.caption(f"🔢 Total de filas: {df_filtrado.shape[0]:,}")

if df_filtrado.shape[0] > MAX_FILAS:
    st.warning(f"⚠️ La descarga del Excel está limitada a {MAX_FILAS:,} filas. Aplicá más filtros para reducir el tamaño (actual: {df_filtrado.shape[0]:,} filas).")
else:
    @st.cache_data
    def generar_csv(df):
        return df.to_csv(index=False).encode("utf-8-sig")

    csv_data = generar_csv(df_filtrado)

    st.download_button(
        label="⬇️ Descargar CSV",
        data=csv_data,
        file_name="ffmm_filtrado.csv",
        mime="text/csv"
    )

# -------------------------------
# Footer
# -------------------------------
st.markdown("<br><br><br><br>", unsafe_allow_html=True)

footer = """
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #f0f2f6;
    color: #333;
    text-align: center;
    font-size: 12px;
    padding: 10px;
    border-top: 1px solid #ccc;
    z-index: 999;
}
</style>

<div class="footer">
    Autor: Nicolás Fernández Ponce, CFA | Este dashboard muestra la evolución del patrimonio y las ventas netas de fondos mutuos en Chile.  
    Datos provistos por la <a href="https://www.cmfchile.cl" target="_blank">CMF</a>
</div>
"""
st.markdown(footer, unsafe_allow_html=True)
