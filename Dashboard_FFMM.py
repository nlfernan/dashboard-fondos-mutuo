# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os

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
# Filtros dinámicos con cache
# -------------------------------
@st.cache_data
def aplicar_filtros(df, tipo, categoria, adm, fondo, serie, fechas):
    df_filtrado = df[df["TIPO_FM"].isin(tipo)]
    df_filtrado = df_filtrado[df_filtrado["Categoría"].isin(categoria)]
    df_filtrado = df_filtrado[df_filtrado["NOM_ADM"].isin(adm)]
    df_filtrado = df_filtrado[df_filtrado["RUN_FM_NOMBRECORTO"].isin(fondo)]
    df_filtrado = df_filtrado[df_filtrado["SERIE"].isin(serie)]
    df_filtrado = df_filtrado[
        (df_filtrado["FECHA_INF_DATE"].dt.date >= fechas[0]) &
        (df_filtrado["FECHA_INF_DATE"].dt.date <= fechas[1])
    ]
    return df_filtrado

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
# Aplicar filtros
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
# Filtro de fechas
# -------------------------------
st.markdown("### Rango de Fechas")
fechas_disponibles = df["FECHA_INF_DATE"].dropna()

if not fechas_disponibles.empty:
    fecha_min = fechas_disponibles.min().date()
    fecha_max = fechas_disponibles.max().date()
    rango_fechas = st.slider(
        "Selecciona un rango de fechas",
        min_value=fecha_min,
        max_value=fecha_max,
        value=(fecha_min, fecha_max)
    )
else:
    st.warning("No hay fechas disponibles para este filtro.")
    st.stop()

# -------------------------------
# Aplicar todos los filtros juntos
# -------------------------------
df_filtrado = aplicar_filtros(
    df, tipo_seleccionados, categoria_seleccionadas,
    adm_seleccionadas, fondo_seleccionados, serie_seleccionadas, rango_fechas
)

if df_filtrado.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
    st.stop()

# -------------------------------
# Tabs
# -------------------------------
tab1, tab2 = st.tabs(["Patrimonio Neto Total (MM CLP)", "Venta Neta Acumulada (MM CLP)"])

with tab1:
    st.subheader("Evolución del Patrimonio Neto Total (en millones de CLP)")
    patrimonio_total = (
        df_filtrado.groupby("FECHA_INF_DATE")["PATRIMONIO_NETO_MM"]
        .sum()
        .sort_index()
    )
    st.bar_chart(patrimonio_total, height=300, use_container_width=True)

with tab2:
    st.subheader("Evolución acumulada de la Venta Neta (en millones de CLP)")
    venta_neta_acumulada = (
        df_filtrado.groupby("FECHA_INF_DATE")["VENTA_NETA_MM"]
        .sum()
        .cumsum()
        .sort_index()
    )
    st.bar_chart(venta_neta_acumulada, height=300, use_container_width=True)

# -------------------------------
# Descargar CSV (limitado a 100.000 filas)
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
