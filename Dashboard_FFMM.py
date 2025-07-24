
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
        "PATRIMONIO_NETO_MM", "VENTA_NETA_MM", "TIPO_FM"
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
st.markdown('''
<div style='display: flex; align-items: center; gap: 15px; padding-top: 10px;'>
    <img src='https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Owl_in_the_Moonlight.jpg/640px-Owl_in_the_Moonlight.jpg'
         width='60' style='border-radius: 50%; box-shadow: 0 2px 6px rgba(0,0,0,0.2);'/>
    <h1 style='margin: 0; font-size: 2.2em;'>Dashboard Fondos Mutuos</h1>
</div>
''', unsafe_allow_html=True)

# -------------------------------
# Filtros dinámicos estilo QlikView
# -------------------------------
def multiselect_con_todos(label, opciones, key):
    seleccionados = st.multiselect(label, opciones, default=opciones, key=key)
    if set(seleccionados) == set(opciones):
        seleccionados = opciones
    return seleccionados

tipo_opciones = sorted(df["TIPO_FM"].dropna().unique())
tipo_seleccionados = multiselect_con_todos("Tipo de Fondo", tipo_opciones, key="tipo")

df_tmp = df[df["TIPO_FM"].isin(tipo_seleccionados)]

adm_opciones = sorted(df_tmp["NOM_ADM"].dropna().unique())
adm_seleccionadas = multiselect_con_todos("Administradora(s)", adm_opciones, key="adm")

df_tmp = df_tmp[df_tmp["NOM_ADM"].isin(adm_seleccionadas)]

fondo_opciones = sorted(df_tmp["RUN_FM_NOMBRECORTO"].dropna().unique())
fondo_seleccionados = multiselect_con_todos("Fondo(s)", fondo_opciones, key="fondo")

df_tmp = df_tmp[df_tmp["RUN_FM_NOMBRECORTO"].isin(fondo_seleccionados)]

serie_opciones = sorted(df_tmp["SERIE"].dropna().unique())
serie_seleccionadas = multiselect_con_todos("Serie(s)", serie_opciones, key="serie")

# -------------------------------
# Filtro de fechas
# -------------------------------
st.markdown("### Rango de Fechas")
fechas_disponibles = df_tmp["FECHA_INF_DATE"].dropna()
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
# Aplicar todos los filtros
# -------------------------------
df_filtrado = df[
    df["TIPO_FM"].isin(tipo_seleccionados) &
    df["NOM_ADM"].isin(adm_seleccionadas) &
    df["RUN_FM_NOMBRECORTO"].isin(fondo_seleccionados) &
    df["SERIE"].isin(serie_seleccionadas) &
    (df["FECHA_INF_DATE"].dt.date >= rango_fechas[0]) &
    (df["FECHA_INF_DATE"].dt.date <= rango_fechas[1])
]

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
# Descargar CSV optimizado con cache
# -------------------------------
@st.cache_data
def generar_csv(df_filtrado):
    return df_filtrado.to_csv(index=False).encode("utf-8-sig")

csv_data = generar_csv(df_filtrado)

st.markdown("### Descargar datos filtrados")
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

st.markdown('''
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
''', unsafe_allow_html=True)
