"""Descarga el clima actual de Buenos Aires desde Open-Meteo y lo agrega a clima.csv.

La columna ``fecha`` está en hora local de Buenos Aires (sin offset), porque la
API se consulta con ``timezone=America/Argentina/Buenos_Aires``.
"""

import csv
import sys
import time
from pathlib import Path

import requests
import truststore

URL = "https://api.open-meteo.com/v1/forecast"
PARAMETROS = {
    "latitude": -34.6037,
    "longitude": -58.3816,
    "current": "temperature_2m,wind_speed_10m",
    "timezone": "America/Argentina/Buenos_Aires",
}
ARCHIVO_CSV = Path(__file__).with_name("clima.csv")
COLUMNAS = ["fecha", "temperatura_c", "viento_kmh"]
INTENTOS = 3
ESPERA_ENTRE_INTENTOS = 2  # segundos


class ErrorClima(Exception):
    """No se pudo obtener o interpretar la respuesta de la API."""


def obtener_clima():
    """Consulta la API y devuelve un dict con fecha, temperatura y viento.

    Reintenta ante errores de red o de la API. Si todos los intentos fallan,
    o la respuesta no tiene el formato esperado, lanza ErrorClima.
    """
    ultimo_error = None
    for intento in range(1, INTENTOS + 1):
        try:
            respuesta = requests.get(URL, params=PARAMETROS, timeout=10)
            respuesta.raise_for_status()
            actual = respuesta.json()["current"]
            return {
                "fecha": actual["time"],
                "temperatura_c": actual["temperature_2m"],
                "viento_kmh": actual["wind_speed_10m"],
            }
        except (requests.RequestException, ValueError, KeyError, TypeError) as error:
            ultimo_error = error
            if intento < INTENTOS:
                time.sleep(ESPERA_ENTRE_INTENTOS)
    raise ErrorClima(
        f"No se pudo obtener el clima tras {INTENTOS} intentos: "
        f"{type(ultimo_error).__name__}: {ultimo_error}"
    )


def ultima_fecha(archivo):
    """Devuelve la fecha de la última fila del CSV, o None si no hay datos."""
    archivo = Path(archivo)
    if not archivo.exists():
        return None
    with archivo.open(newline="", encoding="utf-8") as f:
        filas = [fila for fila in csv.reader(f) if fila]
    if len(filas) < 2:  # vacío o solo encabezado
        return None
    return filas[-1][0]


def guardar_fila(fila, archivo=ARCHIVO_CSV):
    """Agrega una fila al CSV; escribe el encabezado si el archivo es nuevo.

    Devuelve True si guardó la fila, o False si se omitió porque ya existe
    una fila con la misma fecha al final del archivo.
    """
    archivo = Path(archivo)
    if ultima_fecha(archivo) == fila["fecha"]:
        return False
    es_nuevo = not archivo.exists() or archivo.stat().st_size == 0
    # Si el archivo no termina en salto de línea, se agrega uno para no pegar filas.
    falta_salto = False
    if not es_nuevo:
        with archivo.open("rb") as f:
            f.seek(-1, 2)
            falta_salto = f.read(1) not in (b"\n", b"\r")
    with archivo.open("a", newline="", encoding="utf-8") as f:
        if falta_salto:
            f.write("\r\n")
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        if es_nuevo:
            escritor.writeheader()
        escritor.writerow(fila)
    return True


def main():
    """Obtiene el clima y lo guarda. Devuelve el código de salida del proceso."""
    # Usa los certificados del sistema operativo en lugar de la lista propia de
    # requests. Necesario cuando un antivirus (ej. Avast) inspecciona el HTTPS.
    truststore.inject_into_ssl()
    try:
        fila = obtener_clima()
    except ErrorClima as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    guardada = guardar_fila(fila)
    detalle = f"{fila['temperatura_c']} C, viento {fila['viento_kmh']} km/h"
    if guardada:
        print(f"{fila['fecha']}: {detalle} -> {ARCHIVO_CSV.name}")
    else:
        print(f"{fila['fecha']}: ya estaba registrada, no se agrega ({detalle})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
