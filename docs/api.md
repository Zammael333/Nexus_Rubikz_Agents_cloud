# API Documentation — NEXUS-RUBYKZ

## Worker Endpoints

### Event Bus

| Método | Ruta | Descripción |
|--------|------|-------------|
| `PUBLISH` | `AsyncEventBus.publish(event)` | Publica un evento en el bus asíncrono |
| `CONSUME` | `AsyncEventBus.consume()` | Consume el siguiente evento del bus |

**BusEvent Schema:**
```json
{
  "source": "string",
  "event_type": "string",
  "payload": "object",
  "priority": "CRITICAL | ERROR | WARN | INFO | DEBUG",
  "correlation_id": "uuid",
  "timestamp": "ISO8601"
}
```

### SAT Shield

| Método | Ruta | Descripción |
|--------|------|-------------|
| `calculate_da()` | `sat_shield/validator.py` | Calcula la ecuación Da de auditoría SAT |
| `verify_ledger_consistency()` | `sat_shield/validator.py` | Verifica consistencia del ledger |

**calculate_da(platform_val, ledger_val, tax_factor):**
- Input: `float, float, float`
- Output: `Da = abs(platform_val - ledger_val) / (max(abs(platform_val), abs(ledger_val)) + tax_factor)`
- Error if `tax_factor <= 0`

### Phoenix Protocol

| Método | Ruta | Descripción |
|--------|------|-------------|
| `health_check()` | `phoenix/protocol.py` | Health check loop con RTO < 2.5s |
| `recover(worker_id)` | `phoenix/protocol.py` | Recovery con UUID propagation |

### Budget Watchdog

| Método | Ruta | Descripción |
|--------|------|-------------|
| `check_budget()` | `budget` | Retorna estado del error budget |
| `freeze()` | `budget` | Congela operaciones si error budget agotado |
| `unfreeze()` | `budget` | Descongela tras reset de budget |

### SPIFFE Identity

| Método | Ruta | Descripción |
|--------|------|-------------|
| `get_spiffe_id(worker)` | `spiffe/` | Retorna identidad SPIFFE del worker |
| `verify_mtls(svid)` | `spiffe/` | Verifica conexión mTLS |

### Trust Score

| Método | Ruta | Descripción |
|--------|------|-------------|
| `get_score(worker_id)` | `trust_score/` | Retorna trust score (0.0 - 1.0) |
| `record_failure(worker_id)` | `trust_score/` | Registra fallo y recalcula score |

### Digital Twin

| Método | Ruta | Descripción |
|--------|------|-------------|
| `get_snapshot()` | `twin/` | Snapshot del estado actual del kernel |
| `compare()` | `twin/` | Diff entre kernel state y twin state |
| `verify_fidelity()` | `twin/` | Valida discrepancia < 0.1% |

### Vector Memory (Pinecone)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `store_event(event)` | `vector_memory/` | Almacena evento en memoria vectorial |
| `query_similar(vector, top_k)` | `vector_memory/` | Busca eventos similares |

---

## Frontend Routes

| Ruta | Descripción |
|------|-------------|
| `/` | Graph view — visualización interactiva de workers |
| `/events` | Timeline del bus PubSub |
| `/health` | Health checks con Edge Glow |
| `/inventory` | CRUD de SKUs |
| `/transactions` | Historial de transacciones ACID |
| `/slo` | Dashboard SLO 99.9973% |
| `/traces` | Einstein-Williams trace waterfall |
| `/heatmap` | Heatmap de workers |
| `/scans` | Scorpion scan timeline |
| `/trust` | Trust scores dashboard |
| `/budget` | Error budget history |
| `/twin-timeline` | Digital Twin diff timeline |
| `/phoenix-history` | Phoenix Protocol recovery history |
| `/cloud-monitoring` | GCP monitoring integration |
| `/compliance` | Compliance framework checks |
| `/incidents` | Incident history |
| `/audit-trail` | Audit log |
| `/cost` | Cost dashboard |
| `/secrets` | Secrets management |
| `/maintenance` | Maintenance windows |
| `/backups` | Backup status |
| `/runbooks` | Runbook library |

---

## SLO

| Métrica | Target |
|---------|--------|
| Availability | 99.9973% |
| Error Budget | 0.0027% |
| Phoenix RTO | < 2.5s |
| Twin Fidelity | < 0.1% discrepancy |
