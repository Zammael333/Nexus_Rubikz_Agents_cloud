# PLAN MAESTRO — NEXUS-RUBYKZ / KOYOTTE NEXUS

## Roadmap de 120 Pasos — Despliegue por Bloques

### Notación de Bloques (desde Manuales Canónicos PDF)

- **Bloque 0 (Pasos 1-10):** Inicialización y Fundación (COMPLETADO)
- **Bloque I (Pasos 11-50):** Creación de Backend (4 sub-bloques × 10)
- **Bloque IV (Pasos 51-110):** Frontend + SAT Shield (6 sub-bloques × 10)
- **Bloque V (Pasos 111-120):** Configuración de Repositorio y Test Élite (COMPLETADO)

**SLO VINCULANTE:** 99.9973% (10× más estricto que nominal 99.973%) | **Error Budget:** 0.0027% (10× más estricto) | **Veredicto Auditoría:** HARDENED

---

## BLOQUE 0 — INICIALIZACIÓN Y FUNDACIÓN (Pasos 1-10)

| Paso | Descripción | Estado |
|------|-------------|--------|
| 1 | Inicialización del proyecto con `agents-cli scaffold` | ✅ COMPLETADO |
| 2 | Configuración de dependencias en `pyproject.toml` (google-adk, OTEL, GCP) | ✅ COMPLETADO |
| 3 | Definición del Conmutador Híbrido Vertex AI ↔ Google AI Studio | ✅ COMPLETADO |
| 4 | Implementación de `sanitize_context_payload()` — middleware PII/Key masking | ✅ COMPLETADO |
| 5 | Implementación de `semantic_watchdog_scan()` — filtro adversarial multilingüe | ✅ COMPLETADO |
| 6 | Implementación de `inventory_sku_lock()` — lock ACID con idempotencia UUID | ✅ COMPLETADO |
| 7 | Implementación de `calculate_sat_discrepancy()` — ecuación Da de auditoría SAT | ✅ COMPLETADO |
| 8 | Configuración del `LocalEventBus` con persistencia a `nexus_telemetry.log` | ✅ COMPLETADO |
| 9 | Configuración del `Agent` raíz y `AgentEngineApp` + telemetría OpenTelemetry | ✅ COMPLETADO |
| 10 | Suite de pruebas unitarias básicas y linting (ruff + ty + codespell) | ✅ COMPLETADO |

---

## BLOQUE I — BACKEND: BUS ASÍNCRONO Y SAT SHIELD (Pasos 11-20)

| Paso | Descripción | Estado |
|------|-------------|--------|
| **11** | **Migrar `LocalEventBus` a `AsyncEventBus` con asyncio.Queue, prioridad CRITICAL, Dead-Letter Queue** | **✅ COMPLETADO** |
| 12 | Implementar consumer worker dedicado con batch writer (N eventos / T segundos) y persistencia dual | ✅ COMPLETADO |
| 13 | Buffer de eventos con backpressure configurable y timeout 1s → Dead-Letter | ✅ COMPLETADO |
| 14 | Remote delivery hook para integración futura con Google PubSub / Kafka | ✅ COMPLETADO |
| 15 | Formato estructurado BusEvent con UUID, timestamp, recovery_epoch, prioridad | ✅ COMPLETADO |
| 16 | Canal de alertas tempranas (severidad CRITICAL → cola prioritaria) | ✅ COMPLETADO |
| 17 | Sistema de retry con backoff en remote hook (3 intentos → Dead-Letter) | ✅ COMPLETADO |
| 18 | Hook de integración con OpenTelemetry para exportar trazas del bus como spans | ✅ COMPLETADO |
| 19 | Test de integración para el bus bajo carga simulada (1000 eventos/segundo) | ⬜ PENDIENTE |
| 20 | Documentación del contrato del bus de eventos + diagrama de arquitectura | ⬜ PENDIENTE |

---

## BLOQUE I — BACKEND: SAT SHIELD Y PHOENIX PROTOCOL (Pasos 21-30)

| Paso | Descripción | Estado |
|------|-------------|--------|
| 21 | **SAT Shield Edge: módulo `app/sat_shield/validator.py` con `calculate_da()` y `verify_ledger_consistency()`** | **✅ COMPLETADO (movido de Bloque IV)** |
| 22 | **Phoenix Protocol: módulo `app/phoenix/protocol.py` con health check loop, RTO < 2.5s, recovery UUID** | **✅ COMPLETADO** |
| 23 | Budget Watchdog: monitoreo de error budget en tiempo real, alerta al 50%, congelamiento al 100% | ✅ COMPLETADO |
| 24 | Worker de reconciliación contable periódica con ecuación Da | ✅ COMPLETADO |
| 25 | Hardening de `inventory_sku_lock`: integración con AsyncEventBus, UUID propagation como recovery_epoch | ✅ COMPLETADO |
| 26 | Worker de inventario con escaneo Scorpion (race condition, doble asignación, dead stock) | ✅ COMPLETADO |
| 27 | Edge Glow: indicador visual de salud del worker en tiempo real | ✅ COMPLETADO |
| 28 | Worker de notificaciones: alertas CRITICAL → SMS/email/webhook | ✅ COMPLETADO |
| 29 | Hardening de `semantic_watchdog_scan`: expandir patrones adversariales, integrar detector de neutralización | ✅ COMPLETADO |
| 30 | Suite de tests para workers atómicos bajo condiciones de caos (Chaos Engineering) | ✅ COMPLETADO |

---

## BLOQUE I — BACKEND: PERSISTENCIA Y CIBERDEFENSA (Pasos 31-40)

| Paso | Descripción | Estado |
|------|-------------|--------|
| 31 | Configurar Cloud SQL (PostgreSQL) como base de datos transaccional primaria | ✅ COMPLETADO (SQLite vía aiosqlite — swappable a Cloud SQL) |
| 32 | Migrar estado de workers desde memoria volátil a Cloud SQL con conexión SPIFFE | ✅ COMPLETADO (worker_state vía WorkerStateRepo + SQLite — swappable a Cloud SQL) |
| 33 | Watchdog Inneutralizable: detector de intentos de neutralización + alarma CRITICAL inmediata | ✅ COMPLETADO |
| 34 | Ampliar `sanitize_context_payload()` con masking de tokens JWT, secretos, y custom patterns | ✅ COMPLETADO |
| 35 | Configurar SPIRE para emisión automática de identidades SPIFFE a todos los workers | ✅ COMPLETADO |
| 36 | Vibe Diff Dashboard: interfaz para aprobar/rechazar decisiones del agente con confianza baja | ✅ COMPLETADO |
| 37 | gVisor sandbox para workers de alto riesgo (ejecución remota, acceso a archivos) | ✅ COMPLETADO |
| 38 | Integración con Pinecone para memoria vectorial de eventos pasados | ✅ COMPLETADO |
| 39 | Sistema de Trust Score: puntuación de confianza por worker basada en histórico de fallos | ✅ COMPLETADO |
| 40 | Red-Team automatizado: simulaciones periódicas de ataque contra el watchdog | ✅ COMPLETADO |

---

## BLOQUE I — BACKEND: ORQUESTACIÓN Y DIGITAL TWIN (Pasos 41-50)

| Paso | Descripción | Estado |
|------|-------------|--------|
| 41 | Protocolo A2A entre workers: comunicación estructurada con identidad SPIFFE + mTLS | ⬜ PENDIENTE |
| 42 | Orquestador DAG: grafo acíclico de dependencias entre workers | ⬜ PENDIENTE |
| 43 | Inyección automática de telemetría en todos los workers vía decorador OTEL | ⬜ PENDIENTE |
| 44 | Emisor de Digital Twin: segundo container que refleja el estado del kernel P2P en tiempo real | ⬜ PENDIENTE |
| 45 | Progressive Disclosure: niveles de logging incrementales (ERROR → WARN → INFO → DEBUG) controlados por Trust Score | ⬜ PENDIENTE |
| 46 | Recursion Kill-Switch: detector de bucles infinitos entre workers + corte automático | ⬜ PENDIENTE |
| 47 | Post-mortem Memory: almacenamiento persistente de incidentes pasados para evitar recurrencia | ⬜ PENDIENTE |
| 48 | Edge Glow: calibración dinámica del indicador visual basada en SLO real vs. nominal | ⬜ PENDIENTE |
| 49 | Sandboxing en runtime: workers se auto-aislan si detectan comportamiento anómalo | ⬜ PENDIENTE |
| 50 | Validación de fidelidad del Digital Twin: discrepancia < 0.1% entre kernel y twin | ⬜ PENDIENTE |

---

## BLOQUE IV — FRONTEND: INTERFAZ POLIMÓRFICA Y GRAFO (Pasos 51-60)

| Paso | Descripción | Estado |
|------|-------------|--------|
| 51 | Scaffolding del frontend: Next.js + Tailwind + TypeScript | ✅ COMPLETADO |
| 52 | Vista de Grafo: visualización interactiva de workers atómicos y sus conexiones con React Flow | ✅ COMPLETADO |
| 53 | Panel de control del Digital Twin: estado del kernel en tiempo real | ✅ COMPLETADO |
| 54 | Vista de Eventos: timeline del bus PubSub con filtros por severidad, worker, rango de tiempo | ✅ COMPLETADO |
| 55 | Modal de inventario: CRUD de SKUs con visualización de locks activos | ✅ COMPLETADO |
| 56 | Modal de transacciones: historial con UUID, estado ACID, re-intentos | ✅ COMPLETADO |
| 57 | Vista de Health: dashboard de health checks por worker con indicador Edge Glow | ✅ COMPLETADO |
| 58 | Componente de búsqueda y filtrado global sobre eventos | ✅ COMPLETADO |
| 59 | Responsive design: desktop + tablet + móvil (sidebar fijo + overlay móvil) | ✅ COMPLETADO |
| 60 | Tests E2E del grafo y componentes principales con Playwright | ✅ COMPLETADO |

---

## BLOQUE IV — FRONTEND: MODALES FORENSES Y CONTROL CRÍTICO (Pasos 61-70)

| Paso | Descripción | Estado |
|------|-------------|--------|
| 61 | Modal de Detalle de Evento: payload completo, metadatos, trace OTEL | ✅ COMPLETADO |
| 62 | Modal de Alerta CRITICAL: overlay con acción requerida (ACK, ESCALATE, DISMISS) | ✅ COMPLETADO |
| 63 | Modal de Worker Detail: estado, health, config, últimas N ejecuciones | ✅ COMPLETADO |
| 64 | Control de Phoenix Protocol: toggle manual de reinicio por worker | ✅ COMPLETADO |
| 65 | Control de Budget Watchdog: override manual de congelamiento / descongelamiento | ✅ COMPLETADO |
| 66 | Vista de Dead-Letter Queue: eventos fallidos con opción de re-encolar | ✅ COMPLETADO |
| 67 | Control de Sandbox: indicador visual de workers en sandbox vs. nativos | ✅ COMPLETADO |
| 68 | Modal de Vibe Diff: aprobar/rechazar decisiones pendientes con firma de operador | ✅ COMPLETADO |
| 69 | Vista de SPIFFE identities: mapa de identidades workers + estado mTLS | ✅ COMPLETADO |
| 70 | Tests de integración frontend-backend para modales | ✅ COMPLETADO |

---

## BLOQUE IV — FRONTEND: OBSERVABILIDAD Y DIGITAL TWIN (Pasos 71-80)

| Paso | Descripción | Estado |
|------|-------------|--------|
| 71 | Dashboard SLO: medidor en tiempo real de SLO 99.9973%, error budget restante, 44 failures/mes (calculado sobre 99.9973%) | ⬜ PENDIENTE |
| 72 | Timeline del Digital Twin: diff visual entre kernel state y twin state | ⬜ PENDIENTE |
| 73 | Gráfico de Einstein-Williams: trazas OTEL visualizadas como cascada de spans | ⬜ PENDIENTE |
| 74 | Heatmap de workers: uso de CPU, memoria, latencia, tasa de error por worker | ⬜ PENDIENTE |
| 75 | Línea de tiempo de Scorpion Scans: resultados históricos de escaneos de vulnerabilidad | ⬜ PENDIENTE |
| 76 | Dashboard de Trust Scores: evolución de puntuación por worker | ⬜ PENDIENTE |
| 77 | Vista de Error Budget: gráfico de consumo histórico con proyección | ⬜ PENDIENTE |
| 78 | Exportador de reportes: PDF con estado del sistema para auditoría | ⬜ PENDIENTE |
| 79 | Componente de Phoenix Protocol: historial de recuperaciones con RTO medido | ⬜ PENDIENTE |
| 80 | Integración con Cloud Monitoring: enlace directo a alerts y dashboards GCP | ⬜ PENDIENTE |

---

## BLOQUE IV — FRONTEND: SAT SHIELD UI Y RECONCILIACIÓN (Pasos 81-90)

| Paso | Descripción | Estado |
|------|-------------|--------|
| 81 | SAT Shield UI: componente frontend que invoca `calculate_da()` del backend | ⬜ PENDIENTE |
| 82 | Modal de Discrepancia: muestra desglose `platform_val`, `ledger_val`, `tax_factor`, Da, bloquea submit si ≥ 0.01 | ⬜ PENDIENTE |
| 83 | Ledger Display: tabla interactiva de partidas contables con filtro por período | ⬜ PENDIENTE |
| 84 | Vista de Reconciliación: diff visual entre platform ledger y SAT ledger | ⬜ PENDIENTE |
| 85 | Alerta SAT: notificación push cuando Da ≥ 0.01 con enlace al modal de discrepancia | ⬜ PENDIENTE |
| 86 | Historial de Reconciliación: auditoría completa de todas las ejecuciones de Da | ⬜ PENDIENTE |
| 87 | Exportador CSV de ledger para descarga fiscal | ⬜ PENDIENTE |
| 88 | Vista comparativa multi-período: evolución de Da semanal/mensual/trimestral | ⬜ PENDIENTE |
| 89 | Test de integración SAT Shield + backend Da | ⬜ PENDIENTE |
| 90 | Documentación de usuario del módulo SAT Shield | ⬜ PENDIENTE |

---

## BLOQUE IV — FRONTEND: PULIDO PREMIUM Y SELLO PRODUCCIÓN (Pasos 91-100)

| Paso | Descripción | Estado |
|------|-------------|--------|
| 91 | Tema visual consistente: dark mode, glassmorphism, animaciones sutiles | ⬜ PENDIENTE |
| 92 | Modo presentación: vista de grafo a pantalla completa para demos | ⬜ PENDIENTE |
| 93 | Atajos de teclado para todas las vistas y modales críticos | ⬜ PENDIENTE |
| 94 | Estado vacío y error states en todos los componentes | ⬜ PENDIENTE |
| 95 | Optimización de rendimiento: lazy loading, virtual scrolling para timelines grandes | ⬜ PENDIENTE |
| 96 | Modo offline: funcionalidad limitada sin backend (último snapshot del Digital Twin) | ⬜ PENDIENTE |
| 97 | i18n: Español + Inglés + labels técnicos sin traducir | ⬜ PENDIENTE |
| 98 | WCAG 2.2 AA: accesibilidad completa (contraste, ARIA, navegación por teclado) | ⬜ PENDIENTE |
| 99 | PWA: service worker, instalable, notificaciones push | ⬜ PENDIENTE |
| 100 | Sello de Producción: auditoría final de frontend + firma crítica | ⬜ PENDIENTE |

---

## BLOQUE IV — FRONTEND: PERSISTENCIA ACID Y PRODUCCIÓN (Pasos 101-110)

| Paso | Descripción | Estado |
|------|-------------|--------|
| 101 | Configurar Cloud SQL para persistencia ACID del frontend (PostgreSQL) | ⬜ PENDIENTE |
| 102 | Inyección automática de UUID en todas las transacciones de base de datos | ⬜ PENDIENTE |
| 103 | ETL de purga: política de retención de datos + archive a BigQuery | ⬜ PENDIENTE |
| 104 | Configuración de Agent Runtime (google-adk deploy) con target `agent_runtime` | ⬜ PENDIENTE |
| 105 | SBOM automatizado: generación de Software Bill of Materials en cada build | ⬜ PENDIENTE |
| 106 | Aprovisionamiento SPIFFE en producción: SPIRE Server + SPIRE Agent | ⬜ PENDIENTE |
| 107 | Red-Team como suite CI/CD: prueba de penetración automatizada pre-deploy | ⬜ PENDIENTE |
| 108 | Dry-run completo del sistema en entorno staging | ⬜ PENDIENTE |
| 109 | Deploy a producción con feature flags y progressive rollout | ⬜ PENDIENTE |
| 110 | Sello de Observabilidad: dashboard Einstein-Williams + alertas Cloud Monitoring + BigQuery | ⬜ PENDIENTE |

---

## BLOQUE V — CONFIGURACIÓN DE REPOSITORIO Y TEST DE EJECUCIÓN ÉLITE (Pasos 111-120)

| Paso | Descripción | Estado |
|------|-------------|--------|
| 111 | CI/CD completo: GitHub Actions con lint, test, build, deploy secuencial (.github/workflows/ci.yml + security.yml) | ✅ COMPLETADO |
| 112 | Pre-commit hooks: ruff, ty, codespell, seguridad básica (.pre-commit-config.yaml) | ✅ COMPLETADO |
| 113 | Configuración de entornos: dev, staging, production con variables separadas (.env.dev, .env.staging, .env.production) | ✅ COMPLETADO |
| 114 | Secretos en GitHub Secrets / Secret Manager: rotación automática (scripts/rotate_secrets.sh) | ✅ COMPLETADO |
| 115 | Documentación de API: OpenAPI/Swagger para todos los endpoints de workers (docs/api.md) | ✅ COMPLETADO |
| 116 | Test de Ejecución Élite: simulación completa del sistema con carga máxima (scripts/stress_test.py — 1000 ev/s, 60s) | ✅ COMPLETADO |
| 117 | Verificación de SLO 99.9973% bajo carga: medición continua (scripts/verify_slo.py — 100K requests) | ✅ COMPLETADO |
| 118 | Fire Drill: simulación de caída de Vertex AI + failover a Google AI Studio (scripts/fire_drill.py — 3 fases, RTO < 2.5s) | ✅ COMPLETADO |
| 119 | Post-mortem del Fire Drill: documentar lecciones, ajustar SLO si es necesario (scripts/post_mortem.py) | ✅ COMPLETADO |
| 120 | Sello de Producción: verificación final completa (scripts/production_seal.py + Makefile) | ✅ COMPLETADO |

---

## Leyenda

| Símbolo | Significado |
|---------|-------------|
| ✅ COMPLETADO | Paso verificado y operativo |
| ⬜ PENDIENTE | No iniciado, con diseño conceptual trazado |
