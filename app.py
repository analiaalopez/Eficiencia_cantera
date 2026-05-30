import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Sistema de eficiencia operativa",
    page_icon="⛏️",
    layout="centered"
)
if "iniciar" not in st.session_state:
    st.session_state.iniciar = False

if not st.session_state.iniciar:
    st.markdown("""
    <div style="
        background-color:#f3f6f4;
        padding:35px;
        border-radius:18px;
        text-align:center;
        margin-top:25px;
        margin-bottom:25px;
    ">
        <h2>Panel de evaluación operativa</h2>
        <p style="font-size:18px;">
        Ingrese al sistema para analizar la eficiencia diaria de la cantera
        según el desempeño histórico.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Comenzar evaluación"):
        st.session_state.iniciar = True
        st.rerun()

    st.stop()
    st.write(
    "Herramienta de soporte a la decisión para evaluar la eficiencia diaria "
    "de operación en cantera mediante indicadores históricos de productividad."
)

st.title("⛏️ Sistema de eficiencia operativa")

st.write(
    "Este sistema clasifica una jornada de cantera como **Roja, Amarilla o Verde** "
    "según los resultados históricos de toneladas por hora y toneladas por viaje."
)

@st.cache_data
def cargar_datos():
    df = pd.read_csv("dataset_nivelia_2019_2022.csv")
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    df = df[
        (df["ton_total"] > 0) &
        (df["horas_trabajadas"] > 0) &
        (df["viajes_total"] > 0)
    ].copy()

    df["ton_por_hora"] = df["ton_total"] / df["horas_trabajadas"]
    df["ton_por_viaje"] = df["ton_total"] / df["viajes_total"]

    return df

df = cargar_datos()

p25_hora = df["ton_por_hora"].quantile(0.25)
p75_hora = df["ton_por_hora"].quantile(0.75)
p25_viaje = df["ton_por_viaje"].quantile(0.25)
p75_viaje = df["ton_por_viaje"].quantile(0.75)

def puntaje(valor, p25, p75):
    if valor < p25:
        return 0
    elif valor <= p75:
        return 1
    else:
        return 2

def clasificar_jornada(ton_total, horas_trabajadas, viajes_total):
    ton_por_hora = ton_total / horas_trabajadas if horas_trabajadas > 0 else 0
    ton_por_viaje = ton_total / viajes_total if viajes_total > 0 else 0

    puntaje_hora = puntaje(ton_por_hora, p25_hora, p75_hora)
    puntaje_viaje = puntaje(ton_por_viaje, p25_viaje, p75_viaje)

    puntaje_total = puntaje_hora + puntaje_viaje

    if puntaje_total <= 1:
        estado = "🔴 Rojo"
    elif puntaje_total <= 3:
        estado = "🟡 Amarillo"
    else:
        estado = "🟢 Verde"

    return estado, ton_por_hora, ton_por_viaje, puntaje_hora, puntaje_viaje, puntaje_total

st.subheader("Ingresar datos de la jornada")

ton_total = st.number_input("Toneladas producidas", min_value=0.0, value=3500.0, step=50.0)
horas_trabajadas = st.number_input("Horas trabajadas", min_value=0.1, value=24.0, step=0.5)
viajes_total = st.number_input("Viajes totales", min_value=0.1, value=80.0, step=1.0)

if st.button("Evaluar eficiencia"):
    estado, ton_por_hora, ton_por_viaje, puntaje_hora, puntaje_viaje, puntaje_total = clasificar_jornada(
        ton_total, horas_trabajadas, viajes_total
    )

    st.markdown("---")
    st.subheader("Resultado del sistema")

    if "Verde" in estado:
        st.success(f"Resultado final: {estado}")
    elif "Amarillo" in estado:
        st.warning(f"Resultado final: {estado}")
    else:
        st.error(f"Resultado final: {estado}")

    st.write("Indicadores de la jornada:")
    st.write(f"Toneladas por hora: **{ton_por_hora:.2f}**")
    st.write(f"Toneladas por viaje: **{ton_por_viaje:.2f}**")

def interpretar_puntaje(puntaje):
    if puntaje == 0:
        return "Inferior al 25% histórico"
    elif puntaje == 1:
        return "Entre el 25% y el 75% histórico"
    else:
        return "Superior al 75% histórico"

st.write("Comparación con el histórico:")
st.write(f"Productividad por hora: **{interpretar_puntaje(puntaje_hora)}**")
st.write(f"Productividad por viaje: **{interpretar_puntaje(puntaje_viaje)}**")
st.write(f"Clasificación global: **{estado}**")

st.markdown("---")
st.subheader("Criterios históricos utilizados")

st.write(f"Percentil 25 toneladas/hora: **{p25_hora:.2f}**")
st.write(f"Percentil 75 toneladas/hora: **{p75_hora:.2f}**")
st.write(f"Percentil 25 toneladas/viaje: **{p25_viaje:.2f}**")
st.write(f"Percentil 75 toneladas/viaje: **{p75_viaje:.2f}**")

st.markdown("""
### Interpretación

- 🔴 **Rojo:** desempeño bajo frente al histórico.
- 🟡 **Amarillo:** desempeño medio frente al histórico.
- 🟢 **Verde:** desempeño alto frente al histórico.

Para ser **Verde**, la jornada debe ubicarse por encima del percentil 75 histórico tanto en toneladas por hora como en toneladas por viaje.
""")

with st.expander("Ver datos históricos procesados"):
    st.dataframe(df.head(30))

st.caption(
    "El sistema usa percentiles históricos para clasificar la eficiencia operativa. "
    "No utiliza Random Forest, por lo que el resultado es más claro y explicable para la empresa."
)
