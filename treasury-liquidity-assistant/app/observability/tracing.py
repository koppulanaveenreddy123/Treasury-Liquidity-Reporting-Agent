from __future__ import annotations

from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter


_tracing_initialized = False


def setup_tracing(service_name: str, app=None) -> None:
    """Configure OpenTelemetry tracing with a Jaeger exporter endpoint."""
    global _tracing_initialized
    if _tracing_initialized:
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    if app is not None:
        FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    _tracing_initialized = True


@contextmanager
def tracer_span(name: str):
    tracer = trace.get_tracer("treasury-app")
    with tracer.start_as_current_span(name) as span:
        yield span


def get_tracer(name: str):
    """Return a configured tracer instance."""
    return trace.get_tracer(name)
