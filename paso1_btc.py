# =============================================================
# PASO 1 - Descargar precios de Bitcoin y dibujar el gráfico
# Requisitos (una sola vez, en la terminal):
#     pip install pandas matplotlib requests
# Ejecutar:
#     python paso1_btc.py
# =============================================================

import requests                  # para pedir datos a internet
import pandas as pd              # para trabajar con tablas (como Excel)
import matplotlib.pyplot as plt  # para dibujar gráficos

# --- 1. CONFIGURACIÓN: cambia esto para probar otras cosas ---
MONEDA = "BTCUSDT"   # prueba "ETHUSDT" o "SOLUSDT"
INTERVALO = "1d"     # "1d" = 1 vela por día, "4h", "1h", "15m"...
CANTIDAD = 365       # cuántas velas quieres (máximo 1000)

# --- 2. PEDIR LOS DATOS A BINANCE (gratis, sin cuenta) ---
url = "https://api.binance.com/api/v3/klines"
parametros = {"symbol": MONEDA, "interval": INTERVALO, "limit": CANTIDAD}
respuesta = requests.get(url, params=parametros, timeout=10)
respuesta.raise_for_status()     # si algo falla, para aquí y avisa
datos = respuesta.json()         # lista de listas con números

# --- 3. CONVERTIR A TABLA ---
# Binance devuelve 12 columnas; solo nos quedamos con las 6 útiles.
columnas = ["fecha", "apertura", "maximo", "minimo", "cierre", "volumen",
            "c7", "c8", "c9", "c10", "c11", "c12"]
df = pd.DataFrame(datos, columns=columnas)
df = df[["fecha", "apertura", "maximo", "minimo", "cierre", "volumen"]]

# La fecha viene en milisegundos -> la pasamos a fecha normal
df["fecha"] = pd.to_datetime(df["fecha"], unit="ms")
# Los precios vienen como texto -> los pasamos a número
for col in ["apertura", "maximo", "minimo", "cierre", "volumen"]:
    df[col] = df[col].astype(float)

# --- 4. MIRAR LOS DATOS (igual que mirar un Excel) ---
print("\nPrimeras 5 filas:")
print(df.head())
print("\nResumen rápido:")
print(f"  Precio más alto:  {df['maximo'].max():,.2f} $")
print(f"  Precio más bajo:  {df['minimo'].min():,.2f} $")
print(f"  Precio de hoy:    {df['cierre'].iloc[-1]:,.2f} $")
cambio = (df["cierre"].iloc[-1] / df["cierre"].iloc[0] - 1) * 100
print(f"  Cambio en el periodo: {cambio:+.2f} %")

# Guardar en CSV para abrirlo en Excel si quieres
df.to_csv(f"{MONEDA}_{INTERVALO}.csv", index=False)
print(f"\nGuardado: {MONEDA}_{INTERVALO}.csv")

# --- 5. DIBUJAR EL GRÁFICO ---
plt.figure(figsize=(12, 5))
plt.plot(df["fecha"], df["cierre"], label="Precio de cierre")
plt.title(f"{MONEDA} - últimas {CANTIDAD} velas ({INTERVALO})")
plt.xlabel("Fecha")
plt.ylabel("Precio (USDT)")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(f"{MONEDA}_{INTERVALO}.png")   # guarda la imagen
plt.show()                                  # abre la ventana
