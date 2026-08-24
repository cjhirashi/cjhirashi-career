# `tests/fixtures/`

Paquete reservado para factories/datos de prueba reutilizables.

## Arquitectura

```mermaid
flowchart LR
    Conf[conftest.py] --> Tests[unit / integration]
    Fix[fixtures/] -.->|futuro| Conf
    Fix --> Init[__init__.py]
```

Hoy las fixtures viven en [`../conftest.py`](../conftest.py) (`test_db`, usuario, cliente HTTP). `__init__.py` solo marca el directorio como paquete.

Si se extraen builders (p. ej. `make_vacancy()`, JSON de Adzuna), van aquí y se importan desde conftest o tests.
