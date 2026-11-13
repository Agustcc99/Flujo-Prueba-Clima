"""Tests de clima.py. No usan internet: la respuesta de la API se simula."""

import csv
from unittest.mock import Mock, patch

import clima

RESPUESTA_FALSA = {
    "current": {
        "time": "2026-11-13T15:00",
        "temperature_2m": 24.5,
        "wind_speed_10m": 12.3,
    }
}


def test_obtener_clima_devuelve_fecha_temperatura_y_viento():
    respuesta = Mock()
    respuesta.json.return_value = RESPUESTA_FALSA

    with patch("clima.requests.get", return_value=respuesta) as get_falso:
        fila = clima.obtener_clima()

    assert fila == {
        "fecha": "2026-11-13T15:00",
        "temperatura_c": 24.5,
        "viento_kmh": 12.3,
    }
    respuesta.raise_for_status.assert_called_once()
    assert get_falso.call_args.kwargs["params"]["latitude"] == -34.6037


def test_guardar_fila_escribe_encabezado_una_sola_vez(tmp_path):
    archivo = tmp_path / "clima.csv"
    fila_1 = {"fecha": "2026-11-13T15:00", "temperatura_c": 24.5, "viento_kmh": 12.3}
    fila_2 = {"fecha": "2026-11-13T16:00", "temperatura_c": 25.1, "viento_kmh": 9.8}

    clima.guardar_fila(fila_1, archivo)
    clima.guardar_fila(fila_2, archivo)

    with archivo.open(newline="", encoding="utf-8") as f:
        filas = list(csv.reader(f))

    assert filas == [
        ["fecha", "temperatura_c", "viento_kmh"],
        ["2026-11-13T15:00", "24.5", "12.3"],
        ["2026-11-13T16:00", "25.1", "9.8"],
    ]
