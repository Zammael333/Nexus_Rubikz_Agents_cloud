# SPEC — NEXUS-RUBYKZ / KOYOTTE NEXUS

## 1. Conmutador Híbrido (Circuit Breaker Cloud)

### Lógica de Conmutación (`app/agent.py:16-32`)

```
TRY → google.auth.default() + Client.generate_content("ping")
  ├── ÉXITO → GOOGLE_GENAI_USE_VERTEXAI = "True"
  │            ACTIVE_MODEL = "gemini-3.1-flash-lite"
  │            PRINT: "[SRE KERNEL] Handshake con Vertex AI exitoso."
  │
  └── FALLO → GOOGLE_GENAI_USE_VERTEXAI = "False"
               ACTIVE_MODEL = "gemini-2.5-flash"
               PRINT: "[SRE KERNEL] Conmutador activado hacia Google AI Studio Local."
```

El conmutador no almacena estado persistente. Se evalúa en cada inicio del agente. El `HttpRetryOptions(attempts=3)` del modelo Gemini aplica backoff ante fallos transitorios.

## 2. Topología de Dos Contenedores

```
┌─────────────────────────────────────┐
│  CONTENEDOR 1 — KERNEL P2P          │
│  ┌───────────┐ ┌──────────────────┐ │
│  │ Switch    │ │ Workers Atómicos │ │
│  │ Cloud     │ │ - Inventory      │ │
│  │ (Vertex/  │ │ - Accounting     │ │
│  │  AI Std)  │ │ - Security       │ │
│  └───────────┘ └──────────────────┘ │
│  ┌───────────┐ ┌──────────────────┐ │
│  │ Watchdog  │ │ Phoenix Protocol │ │
│  │ Perimetral│ │ (RTO < 2.5s)    │ │
│  └───────────┘ └──────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │ SAT Shield (edge validator)    │ │
│  │ app/sat_shield/validator.py    │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
              │ mTLS + SPIFFE
              ▼
┌─────────────────────────────────────┐
│  CONTENEDOR 2 — DIGITAL TWIN        │
│  ┌───────────┐ ┌──────────────────┐ │
│  │ Async     │ │ Memoria          │ │
│  │ EventBus  │ │ Vectorial        │ │
│  │ (app/bus/)│ │ (Pinecone)       │ │
│  └───────────┘ └──────────────────┘ │
│  ┌───────────┐ ┌──────────────────┐ │
│  │ Dead-     │ │ Einstein-        │ │
│  │ Letter    │ │ Williams Trazas  │ │
│  │ Queue     │ │ (OTEL)           │ │
│  └───────────┘ └──────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │ Phoenix Protocol Controller   │ │
│  │ app/phoenix/protocol.py       │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## 3. Workers Atómicos (Implementados)

### 3.1 `semantic_watchdog_scan(user_query: str) -> str` — Worker de Seguridad

**Propósito:** Filtro de seguridad perimetral antífuga y anti-prompt-injection.

**Algoritmo:**
1. Aplica `sanitize_context_payload()` para enmascarar API keys y emails.
2. Escanea contra lista de patrones adversariales: `"ignore previous instructions"`, `"reprogram"`, `"sudo"`, `"drop table"`, `"flag_override"`.
3. Si hay match → emite `[EVENT_BUS] [SECURITY_ALERT]` y retorna denegación.
4. Si no hay match → retorna `"[WATCHDOG] PASSED"`.

**Uso obligatorio:** Inmediatamente después de recibir input del usuario, antes de cualquier otro tool call.

### 3.2 `inventory_sku_lock(sku: str, allocation_units: int, tx_token: str) -> str` — Worker de Inventario

**Propósito:** Aislamiento atómico de SKU de inventario con idempotencia UUID.

**Contrato ACID:**
- **Atomic:** La operación de lock se completa o no se aplica.
- **Consistent:** El token UUID (`tx_token`) garantiza idempotencia — misma transacción no puede ejecutarse dos veces.
- **Isolated:** Múltiples llamadas concurrentes al mismo SKU se serializan por token.
- **Durable:** Todo intento se persiste en `nexus_telemetry.log` como `[INVENTORY_LOCK_ATTEMPT]`.

**Retorno:** Cadena de confirmación con estado `ACID_COMPLIANT`.

### 3.3 `calculate_sat_discrepancy(platform_val: float, ledger_val: float, tax_factor: float) -> str` — Worker de Auditoría SAT

**Propósito:** Blindaje fiscal mediante la Ecuación de Discrepancia Absoluta (Da).

**Fórmula:**
```
Da = |platform_val - ledger_val| + tax_factor
```

**Evaluación:**
| Da | Estado |
|----|--------|
| < 0.01 | `VERIFIED_COMPLIANT` |
| ≥ 0.01 | `DISCREPANCY_DETECTED_ALERT_TRIGGERED` |

**Registro:** Emite `[EVENT_BUS] [FINANCIAL_AUDIT]` con `{"da": float, "status": str}`.

## 4. Bus de Eventos Asíncrono — AsyncEventBus

### Arquitectura (`app/bus/async_event_bus.py`)

```
Worker → asyncio.Queue + Priority Queue → Consumer (background)
                                              ├── Local log (nexus_telemetry.log)
                                              └── Remote hook (Google PubSub / Kafka)
                                              └── Dead-Letter Queue (3 retries → DLQ)
```

### Características

- **Backpressure configurable:** `max_queue_size` + timeout 1s → evento excede → Dead-Letter
- **Prioridad CRITICAL:** Cola separada para eventos CRITICAL, drenada antes que NORMAL
- **Batch writer:** N eventos o T segundos (lo que ocurra primero)
- **Dead-Letter Queue:** Almacenamiento en memoria de eventos fallidos con `recover_dlq()`
- **Recovery epoch:** UUID único por ciclo de vida del bus; tras Phoenix recovery se regenera
- **Remote delivery hook:** Callback opcional para envío a PubSub / Kafka externo
- **At-least-once:** Por defecto; retry individual por evento hasta `max_retries`

### 4.1 Tipos de Evento

| Tipo | Origen | Payload |
|------|--------|---------|
| `SECURITY_ALERT` | watchdog_scan | `{reason, query}` |
| `INVENTORY_LOCK_ATTEMPT` | inventory_sku_lock | `{sku, units, token}` |
| `FINANCIAL_AUDIT` | calculate_sat_discrepancy | `{da, status}` |
| `WORKER_RECOVERY` | Phoenix Protocol | `{worker, latency, rto_met}` |
| `WATCHDOG_NEUTRALIZATION_ATTEMPT` | Sistema | `{worker_id, method}` |
| `BUDGET_EXHAUSTED` | Budget Watchdog | `{current_budget, threshold}` |

### 4.2 AsyncEventBus API

| Método | Descripción |
|--------|-------------|
| `start()` | Inicia el consumer loop background |
| `emit(type, payload, source, priority)` | Encola evento; retorna False si backpressure |
| `stop()` | Detiene consumer, retorna DLQ |
| `recover_dlq()` | Re-intenta eventos en Dead-Letter Queue |
| `dlq_size` / `event_count` / `queue_size` | Propiedades de monitoreo |

### 4.3 Clases de Soporte

| Clase | Propósito |
|-------|-----------|
| `BusEvent` | Evento con UUID, timestamp, prioridad, recovery_epoch |
| `DeadLetterRecord` | Evento fallido + razón + timestamp de fallo |
| `EventPriority` | LOW, NORMAL, HIGH, CRITICAL |
| `DeliveryGuarantee` | AT_MOST_ONCE, AT_LEAST_ONCE |

## 5. Protocolo Phoenix — Auto-Recuperación

### Arquitectura (`app/phoenix/protocol.py`)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Health Check │────▶│ Worker       │────▶│ Reinicio     │
│ (Cada 1s)    │     │ Caído?       │     │ (RTO < 2.5s) │
└──────────────┘     └──────────────┘     └──────────────┘
       │                     │                     │
       ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 3 fallos en  │────▶│ Quarantine   │     │ Nuevo UUID   │
│ 30s?         │     │ (escala      │     │ recovery_    │
│              │     │  humano)     │     │ epoch        │
└──────────────┘     └──────────────┘     └──────────────┘
```

### API

| Método | Descripción |
|--------|-------------|
| `register(name, health_fn)` | Registra worker con función de health check |
| `unregister(name)` | Elimina worker del monitoreo |
| `start()` | Inicia loop de health checks cada 1s |
| `stop()` | Detiene el loop |
| `force_recovery(name)` | Forza reinicio manual de un worker |
| `get_report(name)` | Obtiene estado actual de un worker |
| `get_all_reports()` | Obtiene estado de todos los workers |

### Estados de Worker

| Estado | Significado |
|--------|-------------|
| `HEALTHY` | Health check OK |
| `DEGRADED` | Fallos consecutivos < umbral |
| `FAILED` | Excedió `max_failures` |
| `QUARANTINED` | 3 fallos en ventana de 30s |

### Recovery UUID

Tras cada reinicio automático (`_recover_worker`), PhoenixProtocol genera un nuevo `recovery_epoch` UUID. Esto invalida cualquier UUID pre-caída que pudiera estar en tránsito, previniendo procesamiento duplicado. El `recovery_epoch` se propaga a `BusEvent.recovery_epoch`.

## 6. SAT Shield — Validación Fiscal Edge

### Arquitectura (`app/sat_shield/validator.py`)

```
Frontend / API Layer
       │
       ▼
┌──────────────────────┐
│  calculate_da()      │
│  (función pura)      │
│  Da < 0.01 → ✅ OK   │
│  Da ≥ 0.01 → 🚫 ALERT│
└──────────────────────┘
       │
       ▼
┌──────────────────────┐
│  verify_ledger_      │
│  consistency()       │
│  (sum entries vs     │
│   expected total)    │
└──────────────────────┘
```

### API

| Función | Descripción |
|---------|-------------|
| `calculate_da(platform_val, ledger_val, tax_factor)` | Retorna `SatShieldResult` con Da, status, verified |
| `verify_ledger_consistency(entries, expected_total)` | Verifica suma de entradas contra total esperado |

### SatShieldResult

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `da` | float | Discrepancia absoluta |
| `status` | str | Estado de cumplimiento |
| `verified` | bool | True si Da < 0.01 |
| `timestamp` | str | ISO 8601 |
| `platform_val` | float | Valor de plataforma |
| `ledger_val` | float | Valor de ledger |
| `tax_factor` | float | Factor impositivo |

## 7. Middleware de Enmascaramiento

### `sanitize_context_payload(text: str) -> str`

| Patrón | Reemplazo |
|--------|-----------|
| `AIza[0-9A-Za-z-_]{35}` | `[[MASKED_GOOGLE_API_KEY]]` |
| `[\w\.-]+@[\w\.-]+\.\w+` | `[[MASKED_PII_EMAIL]]` |
| `sk-[a-zA-Z0-9]{32,}` | `[[MASKED_OPENAI_KEY]]` |

## 8. Protocolo SPIFFE (Identidad)

Todo worker DEBE presentar una identidad SPIFFE verificable en formato:
```
spiffe://nexus-rubykz.shadow-wrapper/worker/{worker_name}
```

La verificación mutua (mTLS) ocurre antes de cualquier intercambio de datos entre workers. Sin identidad válida → conexión rechazada.

## 9. Vibe Diff (Human-in-the-Loop)

Las decisiones del agente con confianza < 0.85 DEBEN pasar por Vibe Diff — un paso de verificación humana antes de ejecutarse. El Vibe Diff se registra en el bus como `HITL_VERIFICATION` con el resultado (APPROVED / REJECTED).

## 10. Scorpion Scan — Mitigaciones

La auditoría arquitectónica identificó los siguientes vectores de riesgo:

| Vector | Riesgo | Mitigación | Estado |
|--------|--------|------------|--------|
| Race Condition en Inventory | Doble asignación SKU | AsyncEventBus + UUID + recovery epoch | ✅ PARCIAL |
| Accounting Drift | Discrepancia fiscal no detectada | SAT Shield (calculate_da + verify_ledger_consistency) | ✅ IMPLEMENTADO |
| Watchdog Fatigue | Neutralización del watchdog | Watchdog inneutralizable + alarma CRITICAL | ⬜ PENDIENTE |
| Dead-Letter Orphan | Pérdida de eventos fallidos | Dead-Letter Queue con recover_dlq() | ✅ IMPLEMENTADO |
| Budget Exhaustion | Congelamiento no notificado | Budget Watchdog (Paso 23) | ⬜ PENDIENTE |

## 11. Stack Tecnológico

| Componente | Versión / Especificación |
|------------|--------------------------|
| Python | ≥ 3.11, < 3.14 |
| google-adk[gcp] | ≥ 2.0.0 |
| Vertex AI / Google AI Studio | Conmutación dinámica |
| OpenTelemetry GenAI | Instrumentación automática |
| Terraform (GCF) | Despliegue single-project / CI/CD |
| AsyncEventBus (MVP) | Cola asíncrona nativa + batch writer |
| Google PubSub / Kafka | Futuro reemplazo de AsyncEventBus MVP |
| Pinecone | Memoria vectorial |
| Cloud SQL (PostgreSQL) | Persistencia ACID |
| gVisor | Sandboxing de workers |
| SPIFFE / SPIRE | Identidad y mTLS |
| pytest | Suite unit + integration |
| ruff / ty / codespell | Linting estático |

## 12. Despliegue

- **Manifiesto:** `agents-cli-manifest.yaml` → target `agent_runtime`
- **Infraestructura:** Terraform en `deployment/terraform/single-project/`
- **Logs:** GCS bucket (`LOGS_BUCKET_NAME`) con schema `genai_logs_schema.json`
- **Región:** `us-east1`
- **Observabilidad:** Cloud Monitoring + BigQuery + Einstein-Williams dashboard

## 13. Estado de la Auditoría Externa

| Dimensión | Veredicto |
|-----------|-----------|
| Ecuación Da | ✅ COMPLIANT |
| Error Budget 0.027% | ✅ COMPLIANT |
| Idempotencia UUID | ✅ COMPLIANT |
| Architecture Fortress-to-Asset | ✅ COMPLIANT |
| Estado Compartido entre Workers | ⚠️ PARCIAL (AsyncEventBus MVP implementado, falta Kafka/PubSub nativo) |
| Escalabilidad Horizontal | ⚠️ REQUIERE VALIDACIÓN |
