
import streamlit as st
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

st.set_page_config(
    page_title="Sistema de eficiencia operativa",
    page_icon="⛏️",
    layout="centered"
)

st.title("⛏️ Sistema de eficiencia operativa")

st.write("Este sistema clasifica una jornada de cantera como Roja, Amarilla o Verde según toneladas producidas, horas trabajadas y viajes totales.")

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

    df["puntaje_hora"] = df["ton_por_hora"].apply(lambda x: puntaje(x, p25_hora, p75_hora))
    df["puntaje_viaje"] = df["ton_por_viaje"].apply(lambda x: puntaje(x, p25_viaje, p75_viaje))
    df["puntaje_total"] = df["puntaje_hora"] + df["puntaje_viaje"]

    def semaforo(x):
        if x <= 1:
            return "Rojo"
        elif x <= 3:
            return "Amarillo"
        else:
            return "Verde"

    df["estado"] = df["puntaje_total"].apply(semaforo)

    return df

@st.cache_resource
def entrenar_modelo(df):
    X = df[["ton_total", "horas_trabajadas", "viajes_total"]]
    y = df["estado"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    modelo = RandomForestClassifier(
        n_estimators=300,
        random_state=42
    )

    modelo.fit(X_train, y_train)

    pred = modelo.predict(X_test)

    accuracy = accuracy_score(y_test, pred)
    matriz = confusion_matrix(y_test, pred, labels=modelo.classes_)
    reporte = classification_report(y_test, pred)

    return modelo, accuracy, matriz, reporte

df = cargar_datos()
modelo, accuracy, matriz, reporte = entrenar_modelo(df)

st.subheader("Ingresar datos de la jornada")

ton_total = st.number_input("Toneladas producidas", min_value=0.0, value=1600.0, step=50.0)
horas_trabajadas = st.number_input("Horas trabajadas", min_value=0.0, value=18.0, step=0.5)
viajes_total = st.number_input("Viajes totales", min_value=0.0, value=85.0, step=1.0)

if st.button("Evaluar eficiencia"):

    nuevo_dia = pd.DataFrame({
        "ton_total": [ton_total],
        "horas_trabajadas": [horas_trabajadas],
        "viajes_total": [viajes_total]
    })

    resultado = modelo.predict(nuevo_dia)[0]
    probabilidades = modelo.predict_proba(nuevo_dia)[0]

    st.markdown("---")
    st.subheader("Resultado del sistema")

    if resultado == "Verde":
        st.success("Resultado final: Verde")
    elif resultado == "Amarillo":
        st.warning("Resultado final: Amarillo")
    else:
        st.error("Resultado final: Rojo")

    prob_df = pd.DataFrame({
        "Estado": modelo.classes_,
        "Probabilidad": probabilidades
    })

    prob_df["Probabilidad"] = prob_df["Probabilidad"].apply(lambda x: f"{x:.2%}")

    st.write("Probabilidades estimadas:")
    st.table(prob_df)

    ton_por_hora = ton_total / horas_trabajadas if horas_trabajadas > 0 else 0
    ton_por_viaje = ton_total / viajes_total if viajes_total > 0 else 0

    st.write("Indicadores de la jornada:")
    st.write(f"Toneladas por hora: {ton_por_hora:.2f}")
    st.write(f"Toneladas por viaje: {ton_por_viaje:.2f}")

st.markdown("---")
st.subheader("Información del modelo")

st.write(f"Accuracy del modelo: {accuracy:.2%}")

with st.expander("Ver datos históricos procesados"):
    st.dataframe(df.head(30))

with st.expander("Ver matriz de confusión"):
    st.write(pd.DataFrame(matriz, index=modelo.classes_, columns=modelo.classes_))

with st.expander("Ver reporte de clasificación"):
    st.text(reporte)

st.caption("El sistema utiliza percentiles históricos para construir las clases de eficiencia y luego entrena un Random Forest para clasificar nuevas jornadas.")
