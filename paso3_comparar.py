# =============================================================
# PASO 3 - Probar MUCHAS combinaciones automáticamente
#
# En vez de cambiar números a mano, el programa prueba:
#   5 monedas x varias medias = decenas de estrategias
# y te da una tabla para comparar.
#
# Al final hace la PRUEBA DE LA VERDAD:
#   - Elige la mejor combinación usando solo el PASADO
#   - Mira qué tal le fue después, en el FUTURO
# Así descubrimos si la estrategia funciona o si fue suerte.
#
# Ejecutar en Mac:
#     cd ~/Desktop/datos
#     python3 paso3_comparar.py
# =============================================================

import requests
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. CONFIGURACIÓN ---
MONEDAS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT"]
MEDIAS_CORTAS = [5, 10, 20, 30]
MEDIAS_LARGAS = [30, 50, 100, 200]
CANTIDAD = 1000        # días de datos (unos 3 años)
COMISION = 0.001       # 0,1 % por operación


# --- 2. FUNCIONES (bloques de código que reutilizamos) ---

def descargar(moneda):
    """Descarga los cierres diarios de una moneda."""
    url = "https://api.binance.com/api/v3/klines"
    parametros = {"symbol": moneda, "interval": "1d", "limit": CANTIDAD}
    respuesta = requests.get(url, params=parametros, timeout=10)
    respuesta.raise_for_status()
    df = pd.DataFrame(respuesta.json()).iloc[:, [0, 4]]
    df.columns = ["fecha", "cierre"]
    df["fecha"] = pd.to_datetime(df["fecha"], unit="ms")
    df["cierre"] = df["cierre"].astype(float)
    return df


def probar(df, corta, larga):
    """Prueba una estrategia y devuelve sus resultados (lo mismo que el paso 2)."""
    d = df.copy()
    d["media_corta"] = d["cierre"].rolling(corta).mean()
    d["media_larga"] = d["cierre"].rolling(larga).mean()
    d = d.dropna()
    d["posicion"] = (d["media_corta"] > d["media_larga"]).astype(int).shift(1).fillna(0)
    d["cambio_dia"] = d["cierre"].pct_change().fillna(0)
    d["operacion"] = d["posicion"].diff().abs().fillna(0)
    d["ganancia"] = d["posicion"] * d["cambio_dia"] - d["operacion"] * COMISION

    dinero = (1 + d["ganancia"]).cumprod()
    mantener = (1 + d["cambio_dia"]).cumprod()
    return {
        "ganancia_%": round((dinero.iloc[-1] - 1) * 100, 1),
        "mantener_%": round((mantener.iloc[-1] - 1) * 100, 1),
        "peor_caida_%": round(((dinero / dinero.cummax()) - 1).min() * 100, 1),
        "operaciones": int(d["operacion"].sum()),
    }


# --- 3. DESCARGAR TODAS LAS MONEDAS ---
datos = {}
for moneda in MONEDAS:
    print(f"Descargando {moneda}...")
    datos[moneda] = descargar(moneda)

# --- 4. PROBAR TODAS LAS COMBINACIONES ---
filas = []
for moneda in MONEDAS:
    for corta in MEDIAS_CORTAS:
        for larga in MEDIAS_LARGAS:
            if corta >= larga:
                continue  # la corta tiene que ser más corta que la larga
            resultado = probar(datos[moneda], corta, larga)
            filas.append({"moneda": moneda, "corta": corta, "larga": larga, **resultado})

tabla = pd.DataFrame(filas)
tabla["gana_a_mantener"] = tabla["ganancia_%"] > tabla["mantener_%"]
tabla.to_csv("paso3_resultados.csv", index=False)

print(f"\nProbadas {len(tabla)} estrategias. Tabla completa en paso3_resultados.csv\n")

print("===== TOP 10 MEJORES =====")
print(tabla.sort_values("ganancia_%", ascending=False).head(10).to_string(index=False))

print("\n===== TOP 5 PEORES =====")
print(tabla.sort_values("ganancia_%").head(5).to_string(index=False))

# Resumen por moneda (como una tabla dinámica de Excel)
resumen = tabla.groupby("moneda").agg(
    estrategias=("ganancia_%", "count"),
    ganan_a_mantener=("gana_a_mantener", "sum"),
    ganancia_media_pct=("ganancia_%", "mean"),
    mantener_pct=("mantener_%", "first"),
).round(1)
print("\n===== RESUMEN POR MONEDA =====")
print(resumen.to_string())

# --- 5. LA PRUEBA DE LA VERDAD: pasado vs futuro ---
# Partimos los datos en dos mitades.
# Elegimos la mejor combinación mirando SOLO la primera mitad
# y comprobamos qué hubiera pasado en la segunda.
print("\n===== PRUEBA DE LA VERDAD: ¿la mejor del pasado sirve en el futuro? =====")
prueba = []
for moneda in MONEDAS:
    df = datos[moneda]
    mitad = len(df) // 2
    pasado, futuro = df.iloc[:mitad], df.iloc[mitad:]

    mejor, mejor_ganancia = None, -999
    for corta in MEDIAS_CORTAS:
        for larga in MEDIAS_LARGAS:
            if corta >= larga:
                continue
            g = probar(pasado, corta, larga)["ganancia_%"]
            if g > mejor_ganancia:
                mejor, mejor_ganancia = (corta, larga), g

    en_futuro = probar(futuro, *mejor)
    prueba.append({
        "moneda": moneda,
        "mejor_combo": f"{mejor[0]}/{mejor[1]}",
        "en_pasado_%": mejor_ganancia,
        "en_futuro_%": en_futuro["ganancia_%"],
        "mantener_futuro_%": en_futuro["mantener_%"],
    })

prueba = pd.DataFrame(prueba)
print(prueba.to_string(index=False))

# --- 6. GRÁFICO DE LA PRUEBA DE LA VERDAD ---
x = range(len(prueba))
ancho = 0.27
fig, ax = plt.subplots(figsize=(11, 5))
ax.bar([i - ancho for i in x], prueba["en_pasado_%"], ancho, label="Mejor combo en el PASADO", color="tab:blue")
ax.bar(list(x), prueba["en_futuro_%"], ancho, label="Esa misma combo en el FUTURO", color="tab:orange")
ax.bar([i + ancho for i in x], prueba["mantener_futuro_%"], ancho, label="Comprar y mantener en el FUTURO", color="gray")
ax.axhline(0, color="black", linewidth=0.8)
ax.set_xticks(list(x))
ax.set_xticklabels([f"{m}\n({c})" for m, c in zip(prueba["moneda"], prueba["mejor_combo"])])
ax.set_ylabel("Ganancia (%)")
ax.set_title("¿Lo que funcionó en el pasado sigue funcionando después?")
ax.legend()
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("paso3_prueba_verdad.png")
plt.show()
