# Vedro Telemetry

[![Codecov](https://img.shields.io/codecov/c/github/tsv1/vedro-telemetry/main.svg?style=flat-square)](https://codecov.io/gh/tsv1/vedro-telemetry)
[![PyPI](https://img.shields.io/pypi/v/vedro-telemetry.svg?style=flat-square)](https://pypi.python.org/pypi/vedro-telemetry/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/vedro-telemetry?style=flat-square)](https://pypi.python.org/pypi/vedro-telemetry/)
[![Python Version](https://img.shields.io/pypi/pyversions/vedro-telemetry.svg?style=flat-square)](https://pypi.python.org/pypi/vedro-telemetry/)

Vedro plugin for self-hosted telemetry

## Installation

### 1. Install package

```shell
$ pip3 install vedro-telemetry
```

### 2. Enable plugin

```python
# ./vedro.cfg.py
import vedro
import vedro_telemetry as t

class Config(vedro.Config):

    class Plugins(vedro.Config.Plugins):

        class VedroTelemetry(t.VedroTelemetry):
            enabled = True

            # Vedro Telemetry API URL
            api_url: str = "http://localhost:8080"

```
