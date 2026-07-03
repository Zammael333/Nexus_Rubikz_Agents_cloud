import logging
import os

logger = logging.getLogger(__name__)

_SERVICE_NAME = "nexus-rubykz"


def setup_telemetry(service_name: str = _SERVICE_NAME) -> None:
    exporter_type = os.getenv("OTEL_EXPORTER", "console")
    service = os.getenv("OTEL_SERVICE_NAME", service_name)

    resource = _build_resource(service)

    _setup_tracing(resource, exporter_type)
    _setup_metrics(resource, exporter_type)
    logger.info("[OTEL] Telemetry initialized — service=%s exporter=%s", service, exporter_type)


def get_tracer(module: str = _SERVICE_NAME):
    from opentelemetry import trace
    return trace.get_tracer(module)


def get_meter(module: str = _SERVICE_NAME):
    from opentelemetry import metrics
    return metrics.get_meter(module)


def _build_resource(service_name: str):
    from opentelemetry.sdk.resources import Resource
    return Resource.create({
        "service.name": service_name,
        "service.version": os.getenv("APP_VERSION", "0.1.0"),
        "deployment.environment": os.getenv("APP_ENV", "development"),
    })


def _setup_tracing(resource, exporter_type: str) -> None:
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor

    if exporter_type == "otlp":
        exporter = _build_otlp_trace_exporter()
    else:
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        exporter = ConsoleSpanExporter()

    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor if exporter_type == "otlp" else SimpleSpanProcessor
    provider.add_span_processor(processor(exporter))

    from opentelemetry import trace
    trace.set_tracer_provider(provider)


def _setup_metrics(resource, exporter_type: str) -> None:
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

    if exporter_type == "otlp":
        exporter = _build_otlp_metric_exporter()
    else:
        from opentelemetry.sdk.metrics.export import ConsoleMetricExporter
        exporter = ConsoleMetricExporter()

    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=30_000)
    provider = MeterProvider(resource=resource, metric_readers=[reader])

    from opentelemetry import metrics
    metrics.set_meter_provider(provider)


def _build_otlp_trace_exporter():
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    return OTLPSpanExporter()


def _build_otlp_metric_exporter():
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter,
    )
    return OTLPMetricExporter()
