# ROADMAP — NEXUS-RUBYKZ / KOYOTTE NEXUS

**SLO Vincular:** 99.9973% · **Error Budget:** 0.0027% · **RTO Phoenix:** < 2.5s

---

## Fase 0 — Fundación (Pasos 1-10) ✅ COMPLETADO

- Scaffold proyecto + dependencias google-adk, OTEL, GCP
- Conmutador híbrido Vertex AI ↔ AI Studio
- Middleware PII/Key masking, watchdog adversarial multilingüe
- Lock ACID inventario, ecuación Da SAT
- Bus de eventos local, agente raíz con telemetría OTEL
- Lint + tests unitarios básicos

## Fase I — Backend: Bus, SAT Shield, Phoenix (Pasos 11-30) ✅ COMPLETADO

- AsyncEventBus con DLQ, backpressure, prioridad CRITICAL, OTel spans
- SAT Shield: `calculate_da()`, `verify_ledger_consistency()`
- Phoenix Protocol: health check loop, RTO < 2.5s, quarantine, recovery UUID
- Budget Watchdog: error budget sliding window, freeze al 100%
- Edge Glow: health aggregator GREEN/YELLOW/ORANGE/RED
- Scorpion Scanner: race condition, dead stock, double allocation
- Notification dispatcher: local_log + webhook
- Tests de caos para workers atómicos

## Fase II — Backend: Persistencia y Ciberdefensa (Pasos 31-40) ✅ COMPLETADO

- Cloud SQL (SQLite swappable → asyncpg)
- SPIRE + SPIFFE identity management
- gVisor sandbox para workers de alto riesgo
- Pinecone vector memory + Trust Score (9 factores)
- Red-Team automatizado (9 vectores de ataque)
- Watchdog inneutralizable + vibe diff dashboard

## Fase III — Backend: Orquestación y Digital Twin (Pasos 41-50)

| Paso | Descripción | Estado |
|------|-------------|--------|
| 41 | Protocolo A2A entre workers: identidad SPIFFE + mTLS | ⬜ PENDIENTE |
| 42 | Orquestador DAG: grafo acíclico de dependencias entre workers | ⬜ PENDIENTE |
| 43 | Inyección automática de telemetría vía decorador OTEL | ⬜ PENDIENTE |
| 44 | Digital Twin: segundo container que refleja estado del kernel | ⬜ PENDIENTE |
| 45 | Progressive Disclosure: logging por Trust Score | ⬜ PENDIENTE |
| 46 | Recursion Kill-Switch: detector de bucles + corte | ⬜ PENDIENTE |
| 47 | Post-mortem Memory: almacenamiento persistente de incidentes | ⬜ PENDIENTE |
| 48 | Edge Glow: calibración dinámica basada en SLO real | ⬜ PENDIENTE |
| 49 | Sandboxing runtime: auto-aislamiento por anomalía | ⬜ PENDIENTE |
| 50 | Validación de fidelidad Digital Twin: discrepancia < 0.1% | ⬜ PENDIENTE |

## Fase IV — Frontend (Pasos 51-110)

| Subfase | Pasos | Descripción | Estado |
|---------|-------|-------------|--------|
| Interfaz polimórfica y grafo | 51-60 | Next.js, React Flow, Edge Glow, timeline eventos | ✅ COMPLETADO |
| Modales forenses y control crítico | 61-70 | DLQ, Phoenix toggle, Budget override, SPIFFE map | ✅ COMPLETADO |
| Observabilidad y Digital Twin | 71-80 | SLO dashboard, twin diff, Einstein-Williams, heatmap | ⬜ PENDIENTE |
| SAT Shield UI y reconciliación | 81-90 | Da calculator UI, ledger, reconciliation history | ⬜ PENDIENTE |
| Pulido premium y sello producción | 91-100 | Tema, a11y, i18n, PWA, sello frontend | ⬜ PENDIENTE |
| Persistencia ACID y producción | 101-110 | Cloud SQL frontend, purge ETL, SBOM, deploy prod | ⬜ PENDIENTE |

## Fase V — Configuración y Test Élite (Pasos 111-120) ✅ COMPLETADO

- CI/CD (GitHub Actions lint+test+build+deploy + security SAST)
- Pre-commit hooks (ruff, ty, codespell)
- Entornos dev/staging/production con variables separadas
- Secretos en Secret Manager con rotación
- Documentación API (OpenAPI/Swagger)
- Stress test (1000 ev/s, 60s) → 397 ev/s sostenidos
- SLO verification (100K requests) → 100% success rate
- Fire drill (Vertex AI failover, RTO < 2.5s) → fases < 0.03s
- Post-mortem fire drill
- Sello de producción (15/15 checks passed)

---

## GAPS CRÍTICOS IDENTIFICADOS — PRIORIDAD MÁXIMA

1. **Container faltante:** Digital Twin (Container 2 según SPEC.md)
2. **Failover dinámico:** Vertex AI ↔ AI Studio solo en startup, no por request
3. **Cloud SQL asyncpg:** Solo SQLite implementado
4. **SPIFFE → mTLS gRPC:** Identidades configuradas pero no usadas en canales reales
5. **A2A wire transport:** Mensajes definidos, sin transporte gRPC/HTTP
6. **K8s ConfigMap + Secret:** Manifiestos faltantes para env vars separadas
7. **Budget Watchdog → freeze:** `freeze()`/`unfreeze()` no llamados desde agent.py
8. **Tests faltantes:** notifications.py, edge_glow.py, disclosure/, otel/, killswitch/
9. **Pasos PENDIENTES:** 41-50 (Backend orquestación), 71-110 (Frontend + Cloud SQL)

---

*Generado desde PLAN.md — 120 pasos, bloques 0-V*
