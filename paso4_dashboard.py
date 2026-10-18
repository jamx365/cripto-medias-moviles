# =============================================================
# PASO 4 - Dashboard interactivo con Streamlit
#
# Lo mismo que el paso 2, pero en una página web local:
# eliges moneda y medias en el menú y todo se recalcula solo.
#
# Ejecutar en Mac:
#     pip3 install -r requirements.txt
#     python3 -m streamlit run paso4_dashboard.py
# Se abre solo en el navegador. Para pararlo: Control + C en la Terminal.
# =============================================================

import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(page_title="Cruce de medias", page_icon="📊", layout="wide")


# --- 1. DATOS ---
# @st.cache_data guarda la descarga 1 hora: si mueves un menú no vuelve a pedir a Binance
@st.cache_data(ttl=3600)
def descargar(moneda, intervalo, cantidad):
    url = "https://api.binance.com/api/v3/klines"
    parametros = {"symbol": moneda, "interval": intervalo, "limit": cantidad}
    respuesta = requests.get(url, params=parametros, timeout=10)
    respuesta.raise_for_status()
    df = pd.DataFrame(respuesta.json()).iloc[:, [0, 4]]
    df.columns = ["fecha", "cierre"]
    df["fecha"] = pd.to_datetime(df["fecha"], unit="ms")
    df["cierre"] = df["cierre"].astype(float)
    return df


# --- 2. ESTRATEGIA (la misma lógica del paso 2) ---
def calcular(df, corta, larga, comision, dinero_inicial):
    d = df.copy()
    d["media_corta"] = d["cierre"].rolling(corta).mean()
    d["media_larga"] = d["cierre"].rolling(larga).mean()
    d = d.dropna().reset_index(drop=True)
    # La señal de hoy se usa mañana: así no miramos el futuro
    d["posicion"] = (d["media_corta"] > d["media_larga"]).astype(int).shift(1).fillna(0)
    d["cambio"] = d["cierre"].pct_change().fillna(0)
    d["operacion"] = d["posicion"].diff().abs().fillna(0)
    d["ganancia"] = d["posicion"] * d["cambio"] - d["operacion"] * comision
    d["dinero_estrategia"] = dinero_inicial * (1 + d["ganancia"]).cumprod()
    d["dinero_mantener"] = dinero_inicial * (1 + d["cambio"]).cumprod()
    return d


def peor_caida(serie):
    return ((serie / serie.cummax()) - 1).min() * 100


def lista_operaciones(d):
    """Convierte las entradas y salidas en una tabla de operaciones."""
    filas, entrada = [], None
    for _, fila in d.iterrows():
        if fila["operacion"] == 1 and fila["posicion"] == 1:
            entrada = fila
        elif fila["operacion"] == 1 and fila["posicion"] == 0 and entrada is not None:
            filas.append({
                "entrada": str(entrada["fecha"].date()),
                "salida": str(fila["fecha"].date()),
                "precio_entrada": round(entrada["cierre"], 4),
                "precio_salida": round(fila["cierre"], 4),
                "resultado_%": round((fila["cierre"] / entrada["cierre"] - 1) * 100, 1),
            })
            entrada = None
    if entrada is not None:
        filas.append({
            "entrada": str(entrada["fecha"].date()),
            "salida": "abierta",
            "precio_entrada": round(entrada["cierre"], 4),
            "precio_salida": round(d["cierre"].iloc[-1], 4),
            "resultado_%": round((d["cierre"].iloc[-1] / entrada["cierre"] - 1) * 100, 1),
        })
    return pd.DataFrame(filas)


# --- 3. MENÚ LATERAL ---
st.sidebar.header("Configuración")
moneda = st.sidebar.selectbox("Moneda", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT"])
intervalo = st.sidebar.selectbox("Intervalo de vela", ["1d", "4h", "1h"])
cantidad = st.sidebar.slider("Número de velas", 200, 1000, 1000, step=100)
corta = st.sidebar.slider("Media corta", 3, 100, 20)
larga = st.sidebar.slider("Media larga", 10, 300, 50)
comision = st.sidebar.number_input("Comisión por operación (%)", 0.0, 2.0, 0.1, step=0.05) / 100
dinero_inicial = st.sidebar.number_input("Dinero inicial ($)", 100, 1_000_000, 1000, step=100)

st.title(f"📊 Cruce de medias {corta}/{larga} · {moneda}")
st.caption("Proyecto de aprendizaje en análisis de datos. No es asesoramiento financiero.")

if corta >= larga:
    st.error("La media corta tiene que ser menor que la larga.")
    st.stop()

try:
    df = descargar(moneda, intervalo, cantidad)
except requests.RequestException as error:
    st.error(f"No se pudieron descargar los datos de Binance: {error}")
    st.stop()

d = calcular(df, corta, larga, comision, dinero_inicial)
if d.empty:
    st.error("No hay suficientes velas para esas medias. Sube el número de velas o baja la media larga.")
    st.stop()

# --- 4. KPIs ---
final_e, final_m = d["dinero_estrategia"].iloc[-1], d["dinero_mantener"].iloc[-1]
gan_e, gan_m = (final_e / dinero_inicial - 1) * 100, (final_m / dinero_inicial - 1) * 100
caida_e, caida_m = peor_caida(d["dinero_estrategia"]), peor_caida(d["dinero_mantener"])

st.markdown(f"**Periodo:** {d['fecha'].iloc[0].date()} → {d['fecha'].iloc[-1].date()}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Dinero final (estrategia)", f"{final_e:,.0f} $", f"{gan_e:+.1f} %")
c2.metric("Dinero final (comprar y mantener)", f"{final_m:,.0f} $", f"{gan_m:+.1f} %")
c3.metric("Peor caída (estrategia)", f"{caida_e:.1f} %", f"{caida_e - caida_m:+.1f} pts vs mantener")
ops = lista_operaciones(d)
c4.metric("Operaciones", len(ops), f"{d['posicion'].mean() * 100:.0f} % del tiempo dentro",
          delta_color="off")

if final_e > final_m:
    st.success("La estrategia **ganó** a comprar y mantener en este periodo.")
else:
    st.warning("La estrategia **perdió** contra comprar y mantener en este periodo.")

# --- 5. GRÁFICOS ---
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                    subplot_titles=("Precio y medias móviles", "¿Cuánto dinero tendrías?"))
fig.add_trace(go.Scatter(x=d["fecha"], y=d["cierre"], name="Precio",
                         line=dict(color="gray", width=1)), row=1, col=1)
fig.add_trace(go.Scatter(x=d["fecha"], y=d["media_corta"], name=f"Media {corta}",
                         line=dict(color="#1f77b4")), row=1, col=1)
fig.add_trace(go.Scatter(x=d["fecha"], y=d["media_larga"], name=f"Media {larga}",
                         line=dict(color="#ff7f0e")), row=1, col=1)

entradas = d[(d["operacion"] == 1) & (d["posicion"] == 1)]
salidas = d[(d["operacion"] == 1) & (d["posicion"] == 0)]
fig.add_trace(go.Scatter(x=entradas["fecha"], y=entradas["cierre"], mode="markers", name="Compra",
                         marker=dict(symbol="triangle-up", size=10, color="green")), row=1, col=1)
fig.add_trace(go.Scatter(x=salidas["fecha"], y=salidas["cierre"], mode="markers", name="Venta",
                         marker=dict(symbol="triangle-down", size=10, color="red")), row=1, col=1)

fig.add_trace(go.Scatter(x=d["fecha"], y=d["dinero_estrategia"], name="Estrategia",
                         line=dict(color="green")), row=2, col=1)
fig.add_trace(go.Scatter(x=d["fecha"], y=d["dinero_mantener"], name="Comprar y mantener",
                         line=dict(color="gray")), row=2, col=1)
fig.add_hline(y=dinero_inicial, line_dash="dash", line_color="black", row=2, col=1)

fig.update_layout(height=750, hovermode="x unified", margin=dict(t=90),
                  legend=dict(orientation="h", y=1.12))
st.plotly_chart(fig, width="stretch")

# --- 6. REGISTRO DE OPERACIONES ---
st.subheader("Registro de operaciones")
if ops.empty:
    st.info("No hubo operaciones en este periodo.")
else:
    ganadoras = (ops["resultado_%"] > 0).mean() * 100
    st.markdown(f"**{len(ops)} operaciones** · {ganadoras:.0f} % ganadoras · "
                f"resultado medio {ops['resultado_%'].mean():+.1f} % (sin comisiones)")
    st.dataframe(ops, width="stretch", hide_index=True)
    st.download_button("Descargar CSV", ops.to_csv(index=False), f"operaciones_{moneda}.csv", "text/csv")
