"""Tests de clima.py. No usan internet: la respuesta de la API se simula."""

import csv
from unittest.mock import Mock, patch

import pytest
import requests

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


def respuesta_ok():
    respuesta = Mock()
    respuesta.json.return_value = RESPUESTA_FALSA
    return respuesta


def test_obtener_clima_reintenta_y_se_recupera():
    with patch("clima.time.sleep"), patch(
        "clima.requests.get",
        side_effect=[requests.Timeout("lento"), respuesta_ok()],
    ) as get_falso:
        fila = clima.obtener_clima()

    assert fila["temperatura_c"] == 24.5
    assert get_falso.call_count == 2


def test_obtener_clima_lanza_error_si_siempre_falla():
    with patch("clima.time.sleep"), patch(
        "clima.requests.get", side_effect=requests.ConnectionError("sin red")
    ) as get_falso:
        with pytest.raises(clima.ErrorClima):
            clima.obtener_clima()

    assert get_falso.call_count == clima.INTENTOS


def test_obtener_clima_error_http():
    respuesta = Mock()
    respuesta.raise_for_status.side_effect = requests.HTTPError("500")

    with patch("clima.time.sleep"), patch("clima.requests.get", return_value=respuesta):
        with pytest.raises(clima.ErrorClima):
            clima.obtener_clima()


def test_obtener_clima_respuesta_sin_clave_current():
    respuesta = Mock()
    respuesta.json.return_value = {"error": True}

    with patch("clima.time.sleep"), patch("clima.requests.get", return_value=respuesta):
        with pytest.raises(clima.ErrorClima):
            clima.obtener_clima()


def test_guardar_fila_en_archivo_existente_vacio_escribe_encabezado(tmp_path):
    archivo = tmp_path / "clima.csv"
    archivo.write_text("", encoding="utf-8")
    fila = {"fecha": "2026-11-13T15:00", "temperatura_c": 24.5, "viento_kmh": 12.3}

    assert clima.guardar_fila(fila, archivo) is True

    lineas = archivo.read_text(encoding="utf-8").splitlines()
    assert lineas == ["fecha,temperatura_c,viento_kmh", "2026-11-13T15:00,24.5,12.3"]


def test_guardar_fila_sin_salto_de_linea_final_no_pega_filas(tmp_path):
    archivo = tmp_path / "clima.csv"
    archivo.write_text(
        "fecha,temperatura_c,viento_kmh\n2026-11-13T15:00,24.5,12.3",
        encoding="utf-8",
    )
    fila = {"fecha": "2026-11-13T16:00", "temperatura_c": 25.1, "viento_kmh": 9.8}

    clima.guardar_fila(fila, archivo)

    lineas = archivo.read_text(encoding="utf-8").splitlines()
    assert lineas[-1] == "2026-11-13T16:00,25.1,9.8"
    assert len(lineas) == 3


def test_guardar_fila_omite_fecha_repetida(tmp_path):
    archivo = tmp_path / "clima.csv"
    fila = {"fecha": "2026-11-13T15:00", "temperatura_c": 24.5, "viento_kmh": 12.3}

    assert clima.guardar_fila(fila, archivo) is True
    assert clima.guardar_fila(fila, archivo) is False

    assert len(archivo.read_text(encoding="utf-8").splitlines()) == 2


def test_main_guarda_y_devuelve_cero(capsys):
    with patch("clima.truststore.inject_into_ssl"), patch(
        "clima.requests.get", return_value=respuesta_ok()
    ), patch("clima.guardar_fila", return_value=True) as guardar:
        assert clima.main() == 0

    guardar.assert_called_once()
    assert "24.5 C" in capsys.readouterr().out


def test_main_devuelve_uno_si_falla_la_api(capsys):
    with patch("clima.truststore.inject_into_ssl"), patch(
        "clima.obtener_clima", side_effect=clima.ErrorClima("caída")
    ):
        assert clima.main() == 1

    assert "caída" in capsys.readouterr().err
