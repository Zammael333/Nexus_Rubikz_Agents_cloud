# NEXUS-RUBYKZ

**Multi-Agent SRE Symbiote Core** — blindaje de la capa de ejecución contra intrusiones semánticas, fiscales y de infraestructura.
Desplegado en GKE con conmutador híbrido Vertex AI ↔ AI Studio, identidad SPIFFE/SPIRE, auto-healing vía Phoenix Protocol (RTO < 2.5s),
y monitorización de error budget al SLO 99.9973%.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                      Container 1: Kernel P2P                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Vertex AI   │  │    Hybrid    │  │    16 Atomic     │  │
│  │  / AI Studio │◄─┤  Circuit     │◄─┤    Workers       │  │
│  │  Circuit     │  │  Breaker     │  │  (SPIFFE mTLS)   │  │
│  └──────────────┘  └──────┬───────┘  └──────────────────┘  │
│                           │                                 │
│              ┌────────────┼────────────┐                    │
│              ▼            ▼            ▼                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Phoenix    │ │  Stability   │ │    Budget    │        │
│  │   Cycle      │ │   Tensor     │ │   Watchdog   │        │
│  │  RTO < 2.5s │ │  Converge    │ │SLO 99.9973%  │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                      Container 2: Digital Twin               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Telemetry   │  │   Vector     │  │   Progressive    │  │
│  │  Emitter     │──┤   Memory     │──┤   Disclosure     │  │
│  │  (Pinecone)  │  │  Semantic    │  │   Logging        │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │        AsyncEventBus         │
              │   + DLQ + Backpressure       │
              │   + OTEL Spans               │
              └─────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
  ┌────────────────────┐    ┌────────────────────┐
  │  DAG Orchestrator  │    │   Post-Mortem /     │
  │  Multi-worker      │    │   Vibe Diff (HITL)  │
  └────────────────────┘    └────────────────────┘
```

## Core Components

### DAG Graph

Directed acyclic graph engine for multi-worker dependency resolution. Ingests 16 worker nodes with 24 dependency edges, computes a topological execution plan via Kahn's algorithm O(V+E), and parallelizes fan-out across independent branches. Cycle detection enforced at deploy time — any cycle rejects the plan before execution. Critical-path analysis drives RTO guarantees: the scheduler tracks the longest dependency chain and alerts when it exceeds 50ms.

**SLO**: Critical path ≤ 50ms · Zero deadlock invariant · Topological levels recomputed on topology change.

### Budget Watchdog

Error budget enforcement at 10× industry standard. Sliding window of 720 hours with a max error rate of 0.0027% (SLO 99.9973%). The watchdog computes `budget_remaining = (1 − errors_total / (requests_total × (1 − SLO_target))) × 100` on every event. At 50% consumption, an alert threshold fires. At 100%, non-critical workers are automatically frozen — only the circuit breaker and phoenix cycle remain operational to recover the system. Auto-thaw occurs when the budget recovers below the freeze line.

**SLO**: 99.9973% · Alert: 50% consumed · Freeze: 100% consumed · Window: 720h.

### SPIFFE Identity (SPIRE)

Cryptographic identity layer for all inter-worker communication. Every worker node holds a SPIFFE Verifiable Identity Document (SVID) bound to a configurable trust domain. Before any A2A gRPC call, mutual TLS requires valid SVID presentation from both parties — unsigned frames are rejected at the transport level. SPIRE agent manages automatic rotation: SVIDs expire every 24 hours, triggering a Certificate Signing Request to the SPIRE server for re-enrollment. The trust bundle is distributed at node bootstrap.

**SLO**: SVID rotation: 24h · mTLS handshake: < 50ms · Zero unsigned frames.

### DualStabilityMonitor

8-dimensional stability tensor reduced via PCA to a scalar stability rank in [0, 1]. Dimensions: latency, throughput, error_rate, memory_util, cpu_load, connection_pool, queue_depth, circuit_state. Eigen-decomposition identifies the dominant instability vector (the axis contributing most to variance). The Frobenius norm of the delta-tensor across a 60-second sliding window drives a four-state classifier:

| State | Norm Range | Action |
|---|---|---|
| **CONVERGENT** | ΔF < 0.03 | No action |
| **STABLE** | ΔF 0.03–0.08 | Log observation |
| **OSCILLATING** | ΔF 0.08–0.15 | Alert + increase health-check frequency |
| **DIVERGENT** | ΔF > 0.15 | Freeze non-critical + page SRE |

**SLO**: Eigen-stability ≥ 0.97 for CONVERGENT · PCA components: 3 · Norm threshold: 0.03.

### Phoenix Cycle

Auto-healing protocol that guarantees RTO < 2.5s. A health check runs every 1 second against each registered worker. After 3 consecutive failures, the worker enters quarantine — it is removed from the DAG routing table, a recovery epoch UUID is generated, and the resurrection sequence initiates. The cycle tracks: `total_recoveries`, `mean_time_to_recover` (MTTR), `epoch_count`, and `current_quarantine_depth`. Successful recovery re-registers the worker with a new epoch. If 3 recovery attempts fail, the worker is permanently retired and an incident is triggered.

**SLO**: RTO target: 2.5s · MTTR target < 1.8s · Heartbeat: 1s · Quarantine threshold: 3 failures.

### Component Summary

| Component | Description | SLO |
|---|---|---|
| **Kernel P2P** | Hybrid circuit breaker Vertex AI ↔ AI Studio, 16 SPIFFE-mTLS workers | RTO failover < 0.03s |
| **Phoenix Cycle** | Health checks, quarantine after 3 fails, epoch-based recovery | RTO < 2.5s, MTTR < 1.8s |
| **SAT Shield** | SAT fiscal validation via absolute discrepancy equation Da | Da < 0.01 |
| **Budget Watchdog** | Sliding-window error budget, auto-freeze at 100% consumption | 99.9973% (10× industry) |
| **DualStabilityMonitor** | 8-dim PCA stability tensor, eigen-decomposition, 4-state classifier | Eigen-stability ≥ 0.97 |
| **AsyncEventBus** | Priority queue, DLQ, backpressure, OTEL spans per event | 397 ev/s sustained |
| **Digital Twin** | Shadow container, vector memory (Pinecone), fidelity validation | Fidelity > 99.97% |
| **DAG Orchestrator** | Directed acyclic graph, topological sort, parallel fan-out | Critical path < 50ms |
| **SPIFFE Identity** | SPIRE-issued SVIDs, mTLS handshake, 24h rotation | Handshake < 50ms |
| **Scorpion Scanner** | Forensic inventory (race conditions, double allocation, dead stock) | 5 vectors mitigated |
| **Watchdog Guardian** | Adversarial pattern detector (50+ detection signatures) | Zero false positives |

---

## Integration Guide

### 1. Environment Setup

```bash
git clone <repo-url> nexus-rubykz && cd nexus-rubykz

uv venv
source .venv/bin/activate

uv sync --group dev --group lint

uv run python -c "from app.config import Settings; print('OK')"
```

### 2. Environment Configuration

```bash
cp .env.example .env.dev
```

Edit `.env.dev` and replace placeholders:

| Variable | Placeholder | Description |
|---|---|---|
| `PROJECT_ID` | `your-gcp-project-id-anon` | GCP project identifier |
| `LOCATION` | `us-central1` | GCP region |
| `VERTEX_API_KEY` | `your-vertex-api-key-here` | Vertex AI API key |
| `SPIFFE_TRUST_DOMAIN` | `your-trust-domain.example` | SPIFFE trust domain |
| `DATABASE_URL` | `sqlite:///nexus_vault.db` | Connection string (use PostgreSQL in production) |

All values in `.env.example` are anonymized placeholders. Never commit real credentials. Use Google Secret Manager in production.

### 3. Lint (Ruff)

```bash
uv run ruff check app/ tests/ scripts/

make lint
```

Rules: E, F, W, I (isort), C (comprehensions), B (bugbear), UP (pyupgrade), RUF. Line length: 88.

### 4. Test (Pytest)

```bash
uv run python -m pytest tests/unit/ -v --tb=short

uv run python -m pytest tests/integration/ -v --tb=short

make test
```

**508 tests** across 30 unit and 2 integration files, covering: A2A gRPC protocol, DAG orchestration, Phoenix recovery, SAT shield, SPIFFE mTLS, budget watchdog, digital twin, red team, scorpion scanner, and more.

### 5. Deploy (Cloud Build)

```bash
gcloud builds submit --config=cloudbuild.yaml
```

Pipeline stages:
1. **lint** — Ruff + ty over `app/` `tests/` `scripts/`
2. **test** — pytest (unit + integration)
3. **docker-build** — Multi-stage with uv → slim runtime
4. **docker-push** — Artifact Registry (`:$SHORT_SHA` + `:latest`)
5. **deploy-gke** — `kubectl apply` with image substitution

GKE deployment: 3 replicas, rolling update (maxSurge 1, maxUnavailable 0), LoadBalancer service, HPA at 70% CPU, PDB with minAvailable 2, liveness + readiness + startup probes on port 9464.

---

## Quick Verification

```bash
make check-all    # lint + test-unit + test-integration + env-check
```

Open `simulator.html` in a browser for a real-time 8-panel dashboard of the entire system.

---

## Project Structure

```
nexus-rubykz/
├── app/                          # Kernel P2P + Digital Twin (58 modules)
│   ├── agent.py                  # Root ADK agent + 16 workers
│   ├── config.py                 # Centralized Settings from .env
│   ├── budget_watchdog.py        # Error budget SLO 99.9973%
│   ├── dual_stability.py         # 8-dim PCA stability tensor
│   ├── edge_glow.py              # Pulse health aggregator
│   ├── scorpion_scanner.py       # Forensic inventory scanner
│   ├── a2a/                      # Agent-to-agent protocol
│   ├── bus/                      # Async event bus + sync bridge
│   ├── dag/                      # DAG orchestrator multi-worker
│   ├── db/                       # NexusVault (SQLite/Cloud SQL)
│   ├── phoenix/                  # Phoenix Protocol (RTO < 2.5s)
│   ├── sat_shield/               # SAT fiscal validator
│   ├── spiffe/                   # SPIFFE/SPIRE identity mTLS
│   ├── twin/                     # Digital Twin telemetry
│   └── watchdog/                 # Guardian adversarial
├── tests/                        # 508 tests (30 unit + 2 integration)
├── frontend/                     # Next.js + Tailwind + TypeScript
├── scripts/                      # stress_test, verify_slo, fire_drill
├── deployment.yaml               # GKE manifests
├── cloudbuild.yaml               # CI/CD pipeline
├── .env.example                  # Anonymized environment template
├── simulator.html                # Runtime simulator with 8 panels
├── Makefile                      # Dev commands (lint, test, deploy)
└── README.md                     # This file
```

---

## Resources

- `docs/api.md` — API endpoint documentation
- `CONSTITUTION.md` — Multi-agent system rules
- `SPEC.md` — Detailed technical specification
- `PLAN.md` / `WORKLIST.md` — Roadmap and tracking
- `simulator.html` — 8-panel simulated runtime with live SLO 99.9973% metrics
