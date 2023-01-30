# Vedro Telemetry

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
import vedro_telemetry

class Config(vedro.Config):

    class Plugins(vedro.Config.Plugins):

        class VedroTelemetry(vedro_telemetry.VedroTelemetry):
            enabled = True

            api_url: str = "http://localhost:8080"
            timeout: float = 5.0
```
