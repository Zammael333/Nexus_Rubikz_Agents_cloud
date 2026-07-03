# WORKLIST — COLA DE EJECUCIÓN ÁGIL

> **Sprint activo:** Bloque I — Orquestación y Digital Twin (Pasos 41-50)
> **Error Budget:** 0.0027% (10× estricto, 100% disponible)
> **SLO actual:** 99.9973% (10× más estricto que nominal)
> **Veredicto Auditoría Externa:** HARDENED
> **Fortress-to-Asset Ratio:** > 1.0 (nominal)

---

## Tareas Activas

### T-001: AsyncEventBus — Cola Asíncrona Nativa (Pasos 11-18)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `AsyncEventBus` con spans OTEL en `emit()`, `_flush_batch()`, `_deliver_remote()`, `_send_to_dlq()`, `_consumer_loop()`. 35 tests unitarios pasan (9 bus + 6 OTEL + 9 Phoenix + 11 Sat). |
| **Módulos** | `app/bus/` (async_event_bus.py, \_\_init\_\_.py) |
| **Próximo** | Budget Watchdog (Paso 23), reconciliación contable (Paso 24) |

### T-002: Phoenix Protocol — Auto-Recuperación (Paso 22)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `PhoenixProtocol` implementado en `app/phoenix/protocol.py` con health check loop (1s), RTO < 2.5s, auto-recovery con nuevo UUID, quarantine tras 3 fallos en 30s, force_recovery manual. |
| **Módulos** | `app/phoenix/` (protocol.py, \_\_init\_\_.py) |

### T-003: SAT Shield — Validador Fiscal Edge (Paso 21)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `SatShieldResult` + `calculate_da()` + `verify_ledger_consistency()` implementados en `app/sat_shield/validator.py`. Función pura, sin estado, ejecutable en edge. Movido de Bloque IV a Bloque I. |
| **Módulos** | `app/sat_shield/` (validator.py, \_\_init\_\_.py) |

### T-004: Anomalía de Directorio (Nested Structure)

| Campo | Valor |
|-------|-------|
| **Estado** | 🔴 ANOMALÍA DETECTADA |
| **Descripción** | Estructura anidada: `Z973/PROYECTO/nexus-rubykz/`. Código fuente en tercer nivel. |
| **Ruta real del proyecto** | `Z973/PROYECTO/nexus-rubykz/` |
| **Ruta deseada** | `Z973/` (raíz unificada) |
| **Acción requerida** | Evaluar consolidación moviendo `app/`, `pyproject.toml`, `uv.lock` a `Z973/`. |
| **Riesgo** | Ruptura de imports Python si se mueve sin actualizar `sys.path`. |
| **Recomendación** | ~NO MOVER~ hasta plan de migración controlada. |

### T-005: Scorpion Scan — Vulnerabilidades Identificadas por Auditoría

| ID | Vector | Severidad | Estado | Módulo |
|----|--------|-----------|--------|--------|
| SC-01 | Race Condition en Inventory: doble asignación de SKU bajo concurrencia | CRITICAL | ✅ IMPLEMENTADO (AsyncEventBus + recovery UUID + ScorpionScanner) | `app/bus/`, `app/scorpion/` |
| SC-02 | Accounting Drift: discrepancia fiscal no detectada en tiempo real | HIGH | ✅ IMPLEMENTADO (Sat Shield edge + ReconciliationWorker periódico) | `app/sat_shield/`, `app/reconciliation/` |
| SC-03 | Watchdog Fatigue: neutralización del watchdog por workers maliciosos | CRITICAL | ✅ MITIGADO (WatchdogGuardian — Paso 33) | `app/watchdog/` |
| SC-04 | Dead-Letter Orphan: eventos fallidos sin recuperación | MEDIUM | ✅ IMPLEMENTADO (DLQ + recover_dlq + NotificationDispatcher) | `app/bus/`, `app/notifications/` |
| SC-05 | Budget Exhaustion: congelamiento no notificado | MEDIUM | ✅ IMPLEMENTADO (BudgetWatchdog — Paso 23) | `app/budget_watchdog/` |

### T-006: Estado de la Telemetría OpenTelemetry

| Campo | Valor |
|-------|-------|
| **Estado** | 🟢 COMPLETO |
| **Descripción** | `AsyncEventBus` ahora emite spans OTEL para `emit()`, `flush()`, `consume.poll`, `deliver_remote`, `dlq`. `setup_telemetry()` sigue exportando GenAI a GCS. |
| **Nota** | OTEL tracer configurable vía parámetro `tracer`; fallback a `trace.get_tracer("nexus.bus")` si SDK disponible. |

### T-007: Veredicto de Auditoría Externa — Items Post-Auditoría

| ID | Hallazgo | Estado |
|----|----------|--------|
| AU-01 | Ecuación Da — MATEMÁTICAMENTE COMPLIANT | ✅ CERRADO |
| AU-02 | Error Budget 0.027% — ESTRUCTURALMENTE COMPLIANT | ✅ CERRADO |
| AU-03 | Idempotencia UUID — ARQUITECTÓNICAMENTE COMPLIANT | ✅ CERRADO |
| AU-04 | Fortress-to-Asset Ratio — VERIFICADO | ✅ CERRADO |
| AU-05 | Estado Compartido entre Workers — REQUIERE MITIGACIÓN | 🟡 PARCIAL (AsyncEventBus MVP implementado) |
| AU-06 | Escalabilidad Horizontal — REQUIERE VALIDACIÓN | 🟡 PENDIENTE (post-Paso 110) |

### T-008: Pendientes de Bloque 0 (Post-Mortem)

| ID | Item | Estado |
|----|------|--------|
| PM-01 | Cobertura de tests unitarios (`tests/unit/`) — 74 tests, 9 módulos | 🟢 74/74 PASAN |
| PM-02 | `deployment_metadata.json` con valores reales | ✅ ACTUALIZADO |
| PM-03 | Confirmar que `agents-cli eval` tenga al menos 1 dataset en `tests/eval/datasets/` | 🟠 SIN VERIFICAR |
| PM-04 | Validar que el manifest `agents-cli-manifest.yaml` refleje la región correcta (`us-east1`) | 🟢 OK |

### T-009: Budget Watchdog — Error Budget Monitoreo en Tiempo Real (Paso 23)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `BudgetWatchdog` monitorea error budget, alerta al 50%, congela al 100%. Ejecuta como worker periódico en `app/budget_watchdog/watchdog.py`. |
| **Módulos** | `app/budget_watchdog/` |

### T-010: ReconciliationWorker — Ecuación Da Periódica (Paso 24)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `ReconciliationWorker` ejecuta ecuación Da cada N eventos. Detecta discrepancias fiscales en tiempo real. |
| **Módulos** | `app/reconciliation/` |

### T-011: Inventory SKU Lock Hardening (Paso 25)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | Integración de `inventory_sku_lock` con AsyncEventBus. Propagación de UUID como `recovery_epoch`. |
| **Módulos** | `app/inventory/` |

### T-012: Scorpion Scanner — Vulnerabilidades de Inventario (Paso 26)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `ScorpionScanner` escanea race condition, doble asignación, dead stock. Workers de inventario con detección proactiva. |
| **Módulos** | `app/scorpion/` |

### T-013: Edge Glow — Indicador Visual de Salud (Paso 27)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | Indicador visual de salud del worker en tiempo real (verde/ámbar/rojo). Útil para monitoreo edge. |
| **Módulos** | `app/edge_glow/` |

### T-014: NotificationDispatcher — Alertas CRITICAL (Paso 28)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | Worker de notificaciones: alertas CRITICAL → SMS/email/webhook. Integrado con AsyncEventBus DLQ. |
| **Módulos** | `app/notifications/` |

### T-015: Semantic Watchdog Hardening (Paso 29)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | Hardening de `semantic_watchdog_scan`: expandir patrones adversariales, integrar detector de neutralización. Mitigación parcial de SC-03. |
| **Módulos** | `app/watchdog/` |

### T-016: Chaos Engineering Suite (Paso 30)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | Suite de tests de caos para workers atómicos: backpressure, inyección de fallos, recuperación. 74 tests pasan. |
| **Módulos** | `tests/unit/test_chaos_workers.py` |

### T-017: Persistencia ACID — Migraciones + Repositorio (Paso 31)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `app/db/` implementado con `migrations.py` (schema SQL) + `repository.py` (CRUD para worker_state, event_log, budget_snapshot, scorpion_finding). SQLite vía aiosqlite, swappable a Cloud SQL. Pool de conexiones con `ensure_schema()`. 10 tests unitarios. |
| **Módulos** | `app/db/` (migrations.py, repository.py, __init__.py) |

### T-018: PhoenixProtocol DB Persistence (Paso 32)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `PhoenixProtocol` ahora persiste estado de workers vía `WorkerStateRepo` inyectable (opcional). `_persist()` es async y se llama desde `_check_worker()`; `_schedule_persist()` para fire-and-forget desde `force_recovery()`. Backward compatible: sin repo, todo funciona en memoria como antes. |
| **Módulos** | `app/phoenix/protocol.py`, `tests/unit/test_phoenix_db.py` |
| **Próximo** | — |

### T-019: Watchdog Inneutralizable (Paso 33)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `WatchdogGuardian` en `app/watchdog/guardian.py`: `detect_neutralization()` con 8 regex (en/es), severidad SUSPICIOUS/EXPLICIT/CRITICAL, auto-integridad vía SHA-256, heartbeat loop, Phoenix registration. Integrado en `semantic_watchdog_scan()` vía `agent.py`. |
| **Módulos** | `app/watchdog/guardian.py`, `tests/unit/test_watchdog_guardian.py` (18 tests) |

### T-020: Sanitize Context Payload Expandido (Paso 34)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `sanitize_context_payload()` en `guardian.py` con 11 patrones: Google API key, OpenAI key, email, JWT, GitHub token, Slack token, AWS key, private key (DOTALL), secret key, PAN, token genérico. Reemplaza la versión legacy de 3 patrones en `agent.py`. |
| **Módulos** | `app/watchdog/guardian.py` |

### T-021: SPIRE/SPIFFE — Identidades de Workers (Paso 35)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `SpiffeManager` en `app/spiffe/manager.py`: registro de workers con SPIFFE IDs (`spiffe://nexus.local/worker/<id>`), `get()`/`get_all()`, `build_entries()`, generación de archivo de configuración SPIRE Agent, modo DEV sin dependencia externa. Integrado en `agent.py` como `get_spiffe_identity()` tool. |
| **Módulos** | `app/spiffe/manager.py`, `tests/unit/test_spiffe.py` (16 tests) |

### T-022: Vibe Diff Dashboard (Paso 36)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `VibeDiffDashboard` en `app/vibe_diff/dashboard.py`: ciclo de vida de revisión (submit → pending → approve/reject/escalate), expiración automática tras 24h, callback on_review, máximo de pendientes configurable (default 100). Integrado en `agent.py` como `submit_vibe_diff_decision()` tool. |
| **Módulos** | `app/vibe_diff/dashboard.py`, `tests/unit/test_vibe_diff.py` (17 tests) |

### T-023: gVisor Sandbox Runtime (Paso 37)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `SandboxRuntime` en `app/sandbox/runtime.py`: 6 perfiles de worker con niveles NONE/NET_ONLY/FULL/CUSTOM, validación de acceso a archivos/comandos/red, simulación de verificación gVisor, default levels por worker. Integrado en `agent.py` como `get_worker_sandbox()` tool. |
| **Módulos** | `app/sandbox/runtime.py`, `tests/unit/test_sandbox.py` (16 tests) |

### T-024: Vector Memory / Pinecone (Paso 38)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `VectorMemoryStore` en `app/vector_memory/store.py`: store/get/search con cosine similarity, eviction LRU (max 1000 vectores), `local_fallback` para modo dev sin Pinecone, filtro por event_type, embedder custom plugeable. Integrado en `agent.py` como `search_vector_memory()` tool. |
| **Módulos** | `app/vector_memory/store.py`, `tests/unit/test_vector_memory.py` (20 tests) |

### T-025: Trust Score System (Paso 39)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `TrustScorer` en `app/trust_score/scorer.py`: compute() con 10 ScoreFactors (FAILURES, NEUTRALIZATION, BUDGET, UPTIME, QUARANTINE, SCORPION + 4 reservados), interpretación en 5 niveles (PERFECT/HIGH/MEDIUM/LOW/CRITICAL), historial capped 100 entradas, pesos configurables, clamp a [0, 2.0]. Integrado en `agent.py`: tool `get_trust_score()`, tracking en `inventory_sku_lock` y `semantic_watchdog_scan` failure paths. |
| **Módulos** | `app/trust_score/scorer.py`, `tests/unit/test_trust_score.py` (18 tests) |

### T-026: Red Team Automatizado (Paso 40)

| Campo | Valor |
|-------|-------|
| **Estado** | ✅ COMPLETADO |
| **Descripción** | `RedTeamSimulator` en `app/red_team/simulator.py`: 9 AttackVectors (prompt_injection, code_injection, reverse_engineering, data_leakage, privilege_escalation, resource_exhaustion, neutralization, social_engineering, supply_chain), payloads predefinidos por vector, callback on_result. Integrado en `agent.py`: tool `run_red_team_audit()`, ejecución automática al inicio. |
| **Módulos** | `app/red_team/simulator.py`, `tests/unit/test_red_team.py` (19 tests) |

---

## KPIs del Sprint

| Métrica | Actual | Meta |
|---------|--------|------|
| Workers atómicos operativos | 16/16 | 16/16 |
| Pasos completados | 40/120 | 50/120 |
| Bloques completados | Bloque 0 + Bloque I (Ciberdefensa + Persistencia) | Bloque I |
| Eventos en bus de telemetría | ~1 (local) | ≥ 1000 (asíncrono) al cierre del Bloque I |
| Anomalías de directorio | 1 | 0 |
| Vulnerabilidades Scorpion sin mitigar | 0/5 (SC-03 mitigado) | 0 |
| Cobertura de tests (units) | 222 tests, 25 módulos | ≥ 70% |
| SLO real | 99.9973% (10× estricto) | 99.9973% |
| Error Budget consumido | 0% | < 0.0027% |
| Phoenix Protocol RTO | < 2.5s (implementado) | < 2.5s |
| Fortress-to-Asset Ratio | > 1.0 | > 1.0 |

---

## Dependencias Críticas

```
T-001 (AsyncEventBus) → SC-01, SC-04 mitigados
T-002 (Phoenix Protocol) → recuperación automática operativa
T-003 (Sat Shield) → SC-02 mitigado
```

**Estado:** 5/5 Scorpion vectors mitigados.

**Próximo bloque:** Bloque I — Orquestación y Digital Twin (Pasos 41-50).
