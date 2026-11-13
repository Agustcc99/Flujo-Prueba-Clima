# Clima de Buenos Aires

Script en Python que consulta el clima actual de Buenos Aires en la API gratuita
[Open-Meteo](https://open-meteo.com/) (no requiere clave) y agrega una fila a
`clima.csv`. Un workflow de GitHub Actions lo ejecuta todos los días y sube el
CSV actualizado al repositorio.

## Instalación

```bash
pip install -r requirements.txt        # solo para ejecutar
pip install -r requirements-dev.txt    # incluye pytest
```

## Uso

```bash
python clima.py
```

Ejemplo de salida: `2026-11-13T15:00: 24.5 C, viento 12.3 km/h -> clima.csv`

- Si la API falla, reintenta 3 veces; si sigue fallando, imprime el error y
  termina con código 1.
- Si la última fila del CSV ya tiene la misma fecha, no se agrega otra.

## Formato de `clima.csv`

| Columna | Descripción |
|---|---|
| `fecha` | Momento de la medición, hora local de Buenos Aires (sin offset) |
| `temperatura_c` | Temperatura a 2 m, en °C |
| `viento_kmh` | Velocidad del viento a 10 m, en km/h |

## Tests

```bash
python -m pytest
```

Los tests no usan internet: la API se simula.

## GitHub Actions (`.github/workflows/clima.yml`)

- **Tests:** corren en cada push a `main` y en cada pull request.
- **Clima:** todos los días a las 9:00 de Buenos Aires (12:00 UTC, Argentina es
  UTC-3 todo el año) y también a mano desde la pestaña *Actions*
  (`workflow_dispatch`). Ejecuta `clima.py` y commitea `clima.csv` solo si hubo
  cambios.
- GitHub puede demorar los cron unos minutos, y desactiva los workflows
  programados si el repositorio pasa 60 días sin actividad.

## Por qué `truststore`

Algunos antivirus (por ejemplo Avast) inspeccionan el tráfico HTTPS con su propio
certificado. `truststore` hace que `requests` use los certificados del sistema
operativo y evita errores de verificación SSL.
