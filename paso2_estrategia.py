# =============================================================
# PASO 2 - Probar una estrategia simple: cruce de medias móviles
#
# La idea:
#   - Media corta (20 días) = hacia dónde va el precio AHORA
#   - Media larga (50 días) = hacia dónde va a LARGO plazo
#   - Si la corta está POR ENCIMA de la larga -> tenemos Bitcoin
#   - Si está POR DEBAJO -> vendemos y nos quedamos en dólares
#
# Pregunta: ¿esto gana más que comprar y no tocar nada?
#
# Ejecutar en Mac:
#     python3 paso2_estrategia.py
# =============================================================

import requests
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. CONFIGURACIÓN: juega con estos números ---
MONEDA = "BTCUSDT"
INTERVALO = "1d"
CANTIDAD = 1000        # unos 3 años de días
MEDIA_CORTA = 20
MEDIA_LARGA = 50
DINERO_INICIAL = 1000  # dólares imaginarios
COMISION = 0.001       # 0,1 % por operación (lo que cobra Binance)

# --- 2. DESCARGAR DATOS (igual que en el paso 1) ---
url = "https://api.binance.com/api/v3/klines"
parametros = {"symbol": MONEDA, "interval": INTERVALO, "limit": CANTIDAD}
respuesta = requests.get(url, params=parametros, timeout=10)
respuesta.raise_for_status()

df = pd.DataFrame(respuesta.json()).iloc[:, [0, 4]]  # solo fecha y cierre
df.columns = ["fecha", "cierre"]
df["fecha"] = pd.to_datetime(df["fecha"], unit="ms")
df["cierre"] = df["cierre"].astype(float)

# --- 3. CALCULAR LAS MEDIAS MÓVILES ---
# rolling(20).mean() = media de los últimos 20 cierres, día a día
df["media_corta"] = df["cierre"].rolling(MEDIA_CORTA).mean()
df["media_larga"] = df["cierre"].rolling(MEDIA_LARGA).mean()
df = df.dropna().reset_index(drop=True)  # quitamos los primeros días sin media

# --- 4. LA SEÑAL: ¿tenemos Bitcoin o no? ---
# 1 = dentro (tenemos BTC), 0 = fuera (tenemos dólares)
df["senal"] = (df["media_corta"] > df["media_larga"]).astype(int)

# MUY IMPORTANTE: la señal de HOY solo la podemos usar MAÑANA.
# Si no hacemos este shift(1) estaríamos "viendo el futuro" (trampa).
df["posicion"] = df["senal"].shift(1).fillna(0)

# --- 5. CALCULAR GANANCIAS ---
df["cambio_dia"] = df["cierre"].pct_change().fillna(0)  # % que se movió el precio

# Cada vez que la posición cambia (entramos o salimos) pagamos comisión
df["operacion"] = df["posicion"].diff().abs().fillna(0)

# Lo que gana la estrategia cada día
df["ganancia_estrategia"] = df["posicion"] * df["cambio_dia"] - df["operacion"] * COMISION

# Evolución del dinero
df["dinero_estrategia"] = DINERO_INICIAL * (1 + df["ganancia_estrategia"]).cumprod()
df["dinero_comprar_y_mantener"] = DINERO_INICIAL * (1 + df["cambio_dia"]).cumprod()

# --- 6. RESULTADOS ---
final_estrategia = df["dinero_estrategia"].iloc[-1]
final_mantener = df["dinero_comprar_y_mantener"].iloc[-1]
num_operaciones = int(df["operacion"].sum())
dias_dentro = df["posicion"].mean() * 100

# Peor caída desde un máximo (cuánto llegaste a perder en el peor momento)
def peor_caida(serie):
    return ((serie / serie.cummax()) - 1).min() * 100

print(f"\n===== RESULTADOS {MONEDA} =====")
print(f"Periodo: {df['fecha'].iloc[0].date()} -> {df['fecha'].iloc[-1].date()}")
print(f"Empezaste con: {DINERO_INICIAL:,.0f} $\n")
print(f"{'':28}{'ESTRATEGIA':>14}{'COMPRAR Y':>14}")
print(f"{'':28}{'':>14}{'MANTENER':>14}")
print(f"{'Dinero final':28}{final_estrategia:>12,.0f} ${final_mantener:>12,.0f} $")
print(f"{'Ganancia':28}{(final_estrategia/DINERO_INICIAL-1)*100:>12.1f} %{(final_mantener/DINERO_INICIAL-1)*100:>12.1f} %")
print(f"{'Peor caída':28}{peor_caida(df['dinero_estrategia']):>12.1f} %{peor_caida(df['dinero_comprar_y_mantener']):>12.1f} %")
print(f"\nOperaciones hechas: {num_operaciones}")
print(f"Tiempo dentro del mercado: {dias_dentro:.0f} %")

if final_estrategia > final_mantener:
    print("\n-> La estrategia GANÓ a no hacer nada.")
else:
    print("\n-> La estrategia PERDIÓ contra no hacer nada.")

# --- 7. GRÁFICOS ---
fig, (arriba, abajo) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# Arriba: precio y medias
arriba.plot(df["fecha"], df["cierre"], label="Precio", color="gray", alpha=0.6)
arriba.plot(df["fecha"], df["media_corta"], label=f"Media {MEDIA_CORTA} días", color="tab:blue")
arriba.plot(df["fecha"], df["media_larga"], label=f"Media {MEDIA_LARGA} días", color="tab:orange")
# Sombreado verde = días en los que tenemos Bitcoin
arriba.fill_between(df["fecha"], df["cierre"].min(), df["cierre"].max(),
                    where=df["posicion"] == 1, color="green", alpha=0.08,
                    label="Dentro del mercado")
arriba.set_title(f"{MONEDA} - cruce de medias {MEDIA_CORTA}/{MEDIA_LARGA}")
arriba.set_ylabel("Precio (USDT)")
arriba.legend(loc="upper left")
arriba.grid(alpha=0.3)

# Abajo: evolución del dinero
abajo.plot(df["fecha"], df["dinero_estrategia"], label="Estrategia", color="tab:green")
abajo.plot(df["fecha"], df["dinero_comprar_y_mantener"], label="Comprar y mantener", color="gray")
abajo.axhline(DINERO_INICIAL, color="black", linestyle="--", linewidth=0.8)
abajo.set_title("¿Cuánto dinero tendrías?")
abajo.set_ylabel("Dólares")
abajo.legend(loc="upper left")
abajo.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(f"paso2_{MONEDA}.png")
plt.show()
