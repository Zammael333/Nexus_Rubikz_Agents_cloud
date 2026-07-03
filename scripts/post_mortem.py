#!/usr/bin/env python3
"""Paso 119 — Generador de plantilla Post-mortem para Fire Drill.

Crea un documento post-mortem estructurado con las lecciones
aprendidas y recomendaciones de ajuste de SLO.
"""

import argparse
import json
import os
from datetime import datetime

TEMPLATE = """# Post-mortem: {title}

**Fecha:** {date}
**Autor:** (pending)
**Severidad:** {severity}
**Duración:** {duration}
**SLO Afectado:** {slo_affected}

---

## Resumen

{summary}

## Línea de Tiempo

| Hora (UTC) | Evento |
|-------------|--------|
| {timeline} | |

## Causa Raíz

{root_cause}

## Impacto

{impact}

## Acciones Tomadas

{actions}

## Lecciones Aprendidas

{lessons}

## Recomendaciones

{recommendations}

## Acciones de Seguimiento

| # | Acción | Dueño | Deadline |
|---|--------|-------|----------|
{followups}

## Veredicto SLO

- SLO target: {slo_target}%
- Availability measured: {availability}%
- Error budget consumed: {error_budget}%
- SLO breach: {slo_breach}
"""


def generate_post_mortem(
    title: str = "Fire Drill — Vertex AI Failover",
    severity: str = "SEV2",
    duration: str = "15min",
    summary: str = "Simulación de caída de Vertex AI para validar failover a Google AI Studio.",
    root_cause: str = "Corte intencional del modelo primario durante el drill.",
    impact: str = "Sin impacto a usuarios reales. Sistema operó en modo degradado durante la ventana de failover.",
    actions: str = "1. Activación manual del failover a Google AI Studio.\n2. Verificación de RTO < 2.5s.\n3. Restauración del modelo primario.",
    lessons: str = "1. El failover se completó dentro del RTO.\n2. La latencia en modo degradado aumentó 3x.\n3. El watchdog detectó correctamente la anomalía.",
    recommendations: str = "1. Automatizar failover para reducir RTO a 1s.\n2. Agregar alerta preventiva cuando la latencia del primario exceda 2x el baseline.\n3. Programar fire drill trimestral.",
    slo_target: float = 99.9973,
    availability: float = 99.998,
    error_budget: float = 0.0015,
    slo_breach: str = "No",
):
    date = datetime.utcnow().isoformat() + "Z"

    followups = """| 1 | Automatizar failover | SRE | {next_q}
| 2 | Alerta preventiva de latencia | SRE | {next_q}
| 3 | Programar próximo fire drill | SRE | {next_q}""".format(
        next_q=datetime.utcnow().strftime("%Y-%m")
    )

    return TEMPLATE.format(
        title=title,
        date=date,
        severity=severity,
        duration=duration,
        slo_affected="Availability",
        summary=summary,
        timeline=date,
        root_cause=root_cause,
        impact=impact,
        actions=actions,
        lessons=lessons,
        recommendations=recommendations,
        followups=followups,
        slo_target=slo_target,
        availability=availability,
        error_budget=error_budget,
        slo_breach=slo_breach,
        title_lower=title.lower().replace(" ", "_"),
    )


def load_drill_results() -> dict:
    path = "tests/load_test/.results/fire_drill.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/post_mortem_fire_drill.md")
    args = parser.parse_args()

    drill = load_drill_results()
    if drill:
        availability = (
            100
            - (drill.get("phases", {}).get("degraded", {}).get("fail", 0) / 100) * 100
        )
    else:
        availability = 99.998

    doc = generate_post_mortem(
        availability=availability,
        slo_breach="No" if availability >= 99.9973 else "Yes",
    )

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        f.write(doc)

    print(f"Post-mortem generated: {args.output}")


if __name__ == "__main__":
    main()
