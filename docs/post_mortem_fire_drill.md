# Post-mortem: Fire Drill — Vertex AI Failover

**Fecha:** 2026-07-02T05:09:26.060729Z
**Autor:** (pending)
**Severidad:** SEV2
**Duración:** 15min
**SLO Afectado:** Availability

---

## Resumen

Simulación de caída de Vertex AI para validar failover a Google AI Studio.

## Línea de Tiempo

| Hora (UTC) | Evento |
|-------------|--------|
| 2026-07-02T05:09:26.060729Z | |

## Causa Raíz

Corte intencional del modelo primario durante el drill.

## Impacto

Sin impacto a usuarios reales. Sistema operó en modo degradado durante la ventana de failover.

## Acciones Tomadas

1. Activación manual del failover a Google AI Studio.
2. Verificación de RTO < 2.5s.
3. Restauración del modelo primario.

## Lecciones Aprendidas

1. El failover se completó dentro del RTO.
2. La latencia en modo degradado aumentó 3x.
3. El watchdog detectó correctamente la anomalía.

## Recomendaciones

1. Automatizar failover para reducir RTO a 1s.
2. Agregar alerta preventiva cuando la latencia del primario exceda 2x el baseline.
3. Programar fire drill trimestral.

## Acciones de Seguimiento

| # | Acción | Dueño | Deadline |
|---|--------|-------|----------|
| 1 | Automatizar failover | SRE | 2026-07
| 2 | Alerta preventiva de latencia | SRE | 2026-07
| 3 | Programar próximo fire drill | SRE | 2026-07

## Veredicto SLO

- SLO target: 99.9973%
- Availability measured: 100.0%
- Error budget consumed: 0.0015%
- SLO breach: No
