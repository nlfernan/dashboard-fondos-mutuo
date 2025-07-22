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
df_filtrado = df_filtrado[df_filtrado["SERIE"].isin(se