# CONSTITUCIÓN — NEXUS-RUBYKZ / KOYOTTE NEXUS

## Preámbulo

NEXUS-RUBYKZ opera como un **Shadow Wrapper** de ciber-soberanía. Su propósito no es servir contenido — es **blindar la capa de ejecución** contra intrusiones semánticas, fiscales y de infraestructura. El simbionte SRE no negocia con el caos: lo intercepta, lo mide y lo neutraliza antes de que toque tierra firme.

La arquitectura descansa sobre una **Topología de Dos Contenedores**:
- **Contenedor 1 — Kernel P2P:** ejecución transaccional, workers atómicos, switch cloud, watchdog perimetral.
- **Contenedor 2 — Digital Twin / Observabilidad:** telemetría, trazas, Einstein-Williams, bus de eventos asíncrono, memoria vectorial.

El sistema fue sometido a una **Auditoría Arquitectónica Externa** que emitió un veredicto **COMPLIANT** sobre la ecuación Da, el error budget, el protocolo de idempotencia y la arquitectura de fortaleza. Sin embargo, la auditoría identificó vulnerabilidades en la gestión de estado compartido entre workers, que requieren mitigación vía bus PubSub asíncrono.

## Métricas Vinculantes (SRE Covenant)

| Métrica | Objetivo | Tolerancia | Ciclo |
|---------|----------|------------|-------|
| **SLO Transaccional Estricto** | 99.973% | 0.027% error budget | Por ciclo de despliegue |
| **Error Budget** | ≤ 0.027% | Agotamiento → congelamiento inmediato de deploys | Reinicio en siguiente ciclo |
| **Ventana de Error Budget** | 30 días | 280 fallos/mes teóricos | 0.027% × 1,036,800 requests/mes ≈ 280 |
| **Latencia de Conmutación (Failover)** | < 500ms | Vertex AI → Google AI Studio | Por solicitud |
| **Phoenix Protocol RTO** | < 2.5s | Recuperación automática post-caída, nuevo UUID por recovery | Por incidencia |
| **Fortress-to-Asset Ratio** | > 1.0 | La capa SRE DEBE pesar más que la capa de negocio | Por release |

## Ecuaciones Vinculantes

### Ecuación de Discrepancia Absoluta (Da)
```
Da = |platform_val - ledger_val| + tax_factor
```
- Da < 0.01 → `VERIFIED_COMPLIANT`
- Da ≥ 0.01 → `DISCREPANCY_DETECTED_ALERT_TRIGGERED`

### Capacidad de Fallo Teórica
```
280 fallos/mes = (0.00027) × (1,036,800 requests/mes)
```

## Políticas de Ejecución Zero-Trust

### Artículo I — Validación de Idempotencia
Toda operación de inventario DEBE portar un token UUID único (`tx_token`). El sistema rechazará dobles asignaciones aunque el payload sea idéntico. Este UUID se propaga a través del bus de eventos como clave de partición para garantizar orden global. Tras una recuperación Phoenix, se genera un nuevo recovery UUID para invalidar UUIDs pre-caída.

### Artículo II — Middleware de Enmascaramiento
Ninguna credencial, API key (patrón `AIza...`) o dirección de correo electrónico puede abandonar el perímetro sin ser transformada por `sanitize_context_payload()`. La máscara sustituye el valor original por `[[MASKED_*]]`.

### Artículo III — Watchdog Perimetral
El worker `semantic_watchdog_scan()` DEBE ejecutarse como primer filtro en toda interacción con el agente. Si detecta un patrón adversarial, la ejecución se aborta de inmediato y se emite un evento de alarma al bus de telemetría. El watchdog no puede ser neutralizado por ningún worker — cualquier intento de neutralización constituye una violación de grado CRITICAL.

### Artículo IV — Auditoría Inmutable (Bus de Eventos)
Todo evento de negocio (lock de inventario, auditoría SAT, alerta de seguridad) DEBE registrarse en un bus de eventos asíncrono con persistencia dual:
1. Archivo local (`nexus_telemetry.log`) con batch writer (N eventos o T segundos)
2. Dead-Letter Queue con backpressure configurable y 3 reintentos máximos

No existe operación sin huella. Eventos huérfanos constituyen `DATA_LOSS`.

### Artículo V — Discrepancia Cero (SAT Shield)
La Ecuación de Discrepancia Absoluta es la ley de cierre fiscal. Cualquier resultado ≥ 0.01 activa una alerta inmediata de `DISCREPANCY_DETECTED_ALERT_TRIGGERED`. La reconciliación DEBE ejecutarse en el edge desde el día 1 de operación — no en lote nocturno. El módulo `app/sat_shield/` implementa `calculate_da()` como función pura.

### Artículo VI — Phoenix Protocol
Todo worker DEBE tener un mecanismo de auto-recuperación con RTO < 2.5s. Si un worker no responde a su health check en ese intervalo, el Phoenix Protocol lo reinicia automáticamente, genera un nuevo recovery UUID, y emite un evento de `WORKER_RECOVERY` al bus de telemetría. Tras 3 fallos consecutivos en 30s, el worker entra en cuarentena. El módulo `app/phoenix/` implementa `PhoenixProtocol`.

### Artículo VII — SPIFFE Identity
Toda comunicación entre workers DEBE autenticarse mediante identidad SPIFFE con mTLS. No se permite tráfico intra-workers sin verificación de identidad.

### Artículo VIII — Sandboxing
Workers de alto riesgo (ejecución de código, acceso a sistema de archivos) DEBEN ejecutarse en sandbox aislado (gVisor o contenedor efímero). La fuga de un worker no puede comprometer el Kernel P2P.

---

*Esta constitución es vinculante. Cualquier desviación de estos umbrales constituye una violación del pacto SRE y requiere un informe de incidencia en menos de 1 ciclo de error budget.*
