# ¿Funciona el cruce de medias móviles en criptomonedas?

Análisis en Python de una estrategia de trading clásica (cruce de medias móviles) sobre 5 criptomonedas, con datos reales de Binance. El objetivo no es encontrar una máquina de hacer dinero, sino **comprobar con datos si una estrategia popular funciona o solo lo parece**.

> Proyecto de aprendizaje en análisis de datos. No es asesoramiento financiero.

## Conclusión

> El cruce de medias **no gana dinero de forma fiable**. Funciona como un **seguro**: reduce las pérdidas en mercados bajistas a cambio de perder parte de las subidas. Y las combinaciones que parecen espectaculares en el pasado **no repiten** después (sobreajuste).

## Preguntas y resultados

Datos diarios de ~1.000 días (2024 – octubre 2026), comisión del 0,1 % por operación.

### 1. ¿Gana a "comprar y mantener"? Depende del mercado

75 estrategias probadas (5 monedas × 15 combinaciones de medias):

| Moneda | Comprar y mantener | Estrategias que ganan |
|---|---|---|
| XRP | +136 % | 3 de 15 |
| BNB | +91 % | 3 de 15 |
| BTC | +58 % | 4 de 15 |
| SOL | -1 % | 6 de 15 |
| ETH | -19 % | **13 de 15** |

**Patrón:** gana cuando el mercado cae y pierde cuando sube.

### 2. ¿Reduce el riesgo? Sí

Ejemplo con ETH (medias 10/30):

| | Estrategia | Comprar y mantener |
|---|---|---|
| Ganancia | **+40,7 %** | -18,5 % |
| Peor caída | **-44,5 %** | -67,6 % |

### 3. ¿Lo que funcionó en el pasado sigue funcionando? No

Elijo la mejor combinación usando solo la primera mitad de los datos y la pruebo en la segunda:

| Moneda | Mejor combo | En el pasado | En el futuro | Mantener (futuro) |
|---|---|---|---|---|
| XRP | 20/200 | +198 % | -4 % | -32 % |
| SOL | 5/30 | +100 % | -8 % | -30 % |
| BTC | 5/100 | +58 % | -7 % | -29 % |
| ETH | 20/30 | +44 % | +56 % | -4 % |
| BNB | 20/30 | +22 % | +52 % | +10 % |

Los resultados espectaculares se desploman fuera de la muestra, aunque la estrategia perdió menos que no hacer nada en las 5 monedas (en un periodo mayormente bajista).

## Metodología

- **Señal:** dentro del mercado si la media corta está por encima de la larga; fuera si está por debajo.
- **Sin mirar el futuro:** la señal de un día se aplica al día siguiente (`shift(1)`).
- **Costes:** 0,1 % por cada entrada o salida.
- **Métricas:** ganancia total, peor caída desde máximos (drawdown) y número de operaciones.
- **Validación:** división pasado / futuro (out-of-sample) para detectar sobreajuste.

**Limitaciones:** un único periodo histórico, monedas muy correlacionadas entre sí, sin deslizamiento de precio ni impuestos.

## Estructura

| Archivo | Qué hace |
|---|---|
| `paso1_btc.py` | Descarga velas de Binance, limpia los datos, resumen y gráfico de precio |
| `paso2_estrategia.py` | Backtest de una estrategia frente a comprar y mantener, con gráficos |
| `paso3_comparar.py` | Prueba 75 combinaciones, resumen por moneda y prueba pasado/futuro |
| `paso4_dashboard.py` | Dashboard interactivo: eliges moneda y medias y se recalcula todo (KPIs, gráficos, registro de operaciones) |

## Cómo ejecutarlo

Necesitas Python 3.

```bash
git clone https://github.com/jamx365/cripto-medias-moviles.git
cd cripto-medias-moviles
pip3 install -r requirements.txt

python3 paso1_btc.py
python3 paso2_estrategia.py
python3 paso3_comparar.py

# Dashboard interactivo (se abre en el navegador)
python3 -m streamlit run paso4_dashboard.py
```

Cada script tiene la configuración (moneda, medias, comisión) al principio para cambiarla fácilmente. Cierra la ventana del gráfico para que el script termine.

## Herramientas

Python · pandas · matplotlib · Plotly · Streamlit · requests · API pública de Binance

## Autor

**Johan Mentado** — 10 años en hostelería (gerencia de beach club de eventos y jefe de sector en hotel de 2.200 huéspedes), en transición hacia el análisis de datos.
