# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os

# -------------------------------
# Cargar datos optimizado desde Parquet (misma carpeta)
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "ffmm_merged.parquet")

columnas_necesarias = [
    "FECHA_INF", "RUN_FM", "Nombre_Corto", "NOM_ADM", "SERIE",
    "PATRIMONIO_NETO_MM", "VENTA_NETA_MM"
]

df = pd.read_parquet(
    file_path,
    columns=columnas_necesarias,
    engine="pyarrow"
)

df["FECHA_INF_DATE"] = pd.to_datetime(df["FECHA_INF"], format="%Y%m%d", errors="coerce")
df["RUN_FM_NOMBRECORTO"] = df["RUN_FM"].astype(str) + " - " + df["Nombre_Corto"].astype(str)

# -------------------------------
# Título
# -------------------------------
st.title("Dashboard Fondos Mutuos")

# -------------------------------
# Función multiselect con opción "Seleccionar todo"
# -------------------------------
def multiselect_con_todo(label, opciones):
    opciones_mostradas = ["(Seleccionar todo)"] + list(opciones)
    seleccion = st.multiselect(label, opciones_mostradas, default=["(Seleccionar todo)"])
    if "(Seleccionar todo)" in seleccion or not seleccion:
        return list(opciones)
    else:
        return seleccion

# -------------------------------
# Filtros
# -------------------------------
adm_opciones = sorted(df["NOM_ADM"].dropna().unique())
adm_seleccionadas = multiselect_con_todo("Administradora(s)", adm_opciones)
df_filtrado = df[df["NOM_ADM"].isin(adm_seleccionadas)]

run_nombre_opciones = sorted(df_filtrado["RUN_FM_NOMBRECORTO"].dropna().unique())
run_nombre_seleccionados = multiselect_con_todo("Fondo(s)", run_nombre_opciones)
df_filtrado = df_filtrado[df_filtrado["RUN_FM_NOMBRECORTO"].isin(run_nombre_seleccionados)]

serie_opciones = sorted(df_filtrado["SERIE"].dropna().unique())
serie_seleccionadas = multiselect_con_todo("Serie(s)", serie_opciones)
df_filtrado = df_filtrado[df_filtrado["SERIE"].isin(serie_seleccionadas)]

# -------------------------------
# Filtro de fechas
# -------------------------------
st.markdown("### Rango de Fechas")
fechas_disponibles = df_filtrado["FECHA_INF_DATE"].dropna()

if not fechas_disponibles.empty:
    fecha_min = fechas_disponibles.min().date()
    fecha_max = fechas_disponibles.max().date()
    rango_fechas = st.slider(
        "Selecciona un rango de fechas",
        min_value=fecha_min,
        max_value=fecha_max,
        value=(fecha_min, fecha_max)
    )
    df_filtrado = df_filtrado[
        (df_filtrado["FECHA_INF_DATE"].dt.date >= rango_fechas[0]) &
        (df_filtrado["FECHA_INF_DATE"].dt.date <= rango_fechas[1])
    ]
else:
    st.warning("No hay fechas disponibles para este filtro.")

# -------------------------------
# Validar que haya datos después de todos los filtros
# -------------------------------
if df_filtrado.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
    st.stop()

# -------------------------------
# Tabs
# -------------------------------
tab1, tab2 = st.tabs(["Patrimonio Neto Total (MM CLP)", "Venta Neta Total (MM CLP)"])

# --- Tab 1: PATRIMONIO_NETO_MM total por día ---
with tab1:
    st.subheader("Evolución del Patrimonio Neto Total (en millones de CLP)")
    patrimonio_total = (
        df_filtrado.groupby("FECHA_INF_DATE")["PATRIMONIO_NETO_MM"]
        .sum()
        .sort_index()
    )
    st.bar_chart(patrimonio_total, height=300, use_container_width=True)

# --- Tab 2: VENTA_NETA_MM por día ---
with tab2:
    st.subheader("Evolución de la Venta Neta Total (en millones de CLP)")
    venta_neta_por_dia = (
        df_filtrado.groupby("FECHA_INF_DATE")["VENTA_NETA_MM"]
        .sum()
        .sort_index()
    )
    st.bar_chart(venta_neta_por_dia, height=300, use_container_width=True)

# -------------------------------
# Botón para descargar CSV (abajo de los gráficos)
# -------------------------------
st.markdown("### Descargar datos filtrados")
st.download_button(
    label="📥 Descargar CSV",
    data=df_filtrado.to_csv(index=False).encode("utf-8-sig"),
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
    Datos provistos por la <a href=\"https://www.cmfchile.cl\" target=\"_blank\">CMF</a>
</div>
"""
st.markdown(footer, unsafe_allow_html=True)
