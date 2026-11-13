"""Descarga el clima actual de Buenos Aires desde Open-Meteo y lo agrega a clima.csv."""

import csv
from pathlib import Path

import requests
import truststore

# Usa los certificados del sistema operativo en lugar de la lista propia de
# requests. Necesario cuando un antivirus (ej. Avast) inspecciona el HTTPS.
truststore.inject_into_ssl()

URL = "https://api.open-meteo.com/v1/forecast"
PARAMETROS = {
    "latitude": -34.6037,
    "longitude": -58.3816,
    "current": "temperature_2m,wind_speed_10m",
    "timezone": "America/Argentina/Buenos_Aires",
}
ARCHIVO_CSV = Path(__file__).with_name("clima.csv")
COLUMNAS = ["fecha", "temperatura_c", "viento_kmh"]


def obtener_clima():
    """Consulta la API y devuelve un dict con fecha, temperatura y viento."""
    respuesta = requests.get(URL, params=PARAMETROS, timeout=10)
    respuesta.raise_for_status()
    actual = respuesta.json()["current"]
    return {
        "fecha": actual["time"],
        "temperatura_c": actual["temperature_2m"],
        "viento_kmh": actual["wind_speed_10m"],
    }


def guardar_fila(fila, archivo=ARCHIVO_CSV):
    """Agrega una fila al CSV; escribe el encabezado si el archivo es nuevo."""
    archivo = Path(archivo)
    es_nuevo = not archivo.exists() or archivo.stat().st_size == 0
    with archivo.open("a", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        if es_nuevo:
            escritor.writeheader()
        escritor.writerow(fila)


def main():
    fila = obtener_clima()
    guardar_fila(fila)
    print(
        f"{fila['fecha']}: {fila['temperatura_c']} °C, "
        f"viento {fila['viento_kmh']} km/h -> {ARCHIVO_CSV.name}"
    )


if __name__ == "__main__":
    main()
