import streamlit as st
import pandas as pd
import os

# -------------------------------
# Cargar datos
# -------------------------------
file_path = "ffmm_merged.parquet"
columnas_necesarias = [
    "FECHA", "NOMBRE_FONDO", "SERIE", "CUOTAS_APORTADAS", "CUOTAS_RESCATADAS",
    "CUOTAS_EN_CIRCULACION", "PATRIMONIO_NETO", "PATRIMONIO_NETO_MM", "VENTA_NETA_MM"
]

try:
    df = pd.read_parquet(file_path, columns=columnas_necesarias, engine="pyarrow")
except FileNotFoundError:
    st.error(f"❌ No se encontró el archivo: {file_path}. Subilo o generalo antes de continuar.")
    st.stop()

# -------------------------------
# Filtrado por serie (corregido)
# -------------------------------
series_seleccionadas = st.multiselect("Seleccioná series", df["SERIE"].unique())
if series_seleccionadas:
    df_filtrado = df[df["SERIE"].isin(series_seleccionadas)]
else:
    df_filtrado = df

# -------------------------------
# Mostrar tabla
# -------------------------------
st.dataframe(df_filtrado.head())

# -------------------------------
# (opcional) Guardar una copia local (comentado)
# -------------------------------
# from datetime import datetime
# ruta_local = r"C:\Users\nlfer\Desktop\Proyectos\Fondos\Dashboard_FFMM"
# os.makedirs(ruta_local, exist_ok=True)
# fecha = datetime.today().strftime("%Y%m%d")
# df_filtrado.to_parquet(os.path.join(ruta_local, f"df_filtrado_{fecha}.parquet"), index=False)
