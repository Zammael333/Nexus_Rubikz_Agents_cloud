# NEXUS-RUBYKZ Makefile — Bloque V: Test Élite y Sello Producción
# Compatible con uv (Python) + npm (frontend)
.PHONY: help install lint test test-unit test-integration stress-test slo-verify \
        fire-drill post-mortem production-seal pre-commit clean sbom env-check \
        check-all

help:
	@echo "NEXUS-RUBYKZ — Comandos disponibles"
	@echo ""
	@echo "Desarrollo"
	@echo "  make install         Instalar dependencias (Python + Node)"
	@echo "  make lint            Ruff + codespell + ty"
	@echo "  make test            Unit + Integration tests"
	@echo ""
	@echo "Bloque V — Test Élite"
	@echo "  make stress-test     Test de carga (1000 ev/s, 60s)"
	@echo "  make slo-verify      Verificación SLO 99.9973%"
	@echo "  make fire-drill      Simulación de caída Vertex AI + failover"
	@echo "  make post-mortem     Generar post-mortem del Fire Drill"
	@echo "  make production-seal Verificación final pre-producción"
	@echo ""
	@echo "Mantenimiento"
	@echo "  make pre-commit      Ejecutar pre-commit hooks"
	@echo "  make sbom            Generar SBOM"
	@echo "  make check-all       Ejecutar toda la suite de verificación"
	@echo "  make clean           Limpiar caches y artefactos"

install:
	uv sync --group dev --group lint
	cd frontend && npm ci

lint:
	uv run ruff check app/ tests/ scripts/
	uv run codespell app/ tests/ scripts/ --skip="./frontend,*.log" --ignore-words-list=Comandos,Autor,inaccesible,ignora,Caracteres,secur
	uv run ty check app/ tests/ --exclude .venv

test: test-unit test-integration

test-unit:
	uv run python -m pytest tests/unit/ -v --tb=short

test-integration:
	uv run python -m pytest tests/integration/ -v --tb=short

stress-test:
	uv run python scripts/stress_test.py

slo-verify:
	uv run python scripts/verify_slo.py

fire-drill:
	uv run python scripts/fire_drill.py

post-mortem:
	uv run python scripts/post_mortem.py

production-seal:
	uv run python scripts/production_seal.py

pre-commit:
	uv run ruff check app/ tests/ scripts/
	uv run codespell app/ tests/ scripts/ --skip="./frontend,*.log" --ignore-words-list=Comandos,Autor,inaccesible,ignora,Caracteres,secur
	uv run ty check app/ tests/ --exclude .venv
	@echo "Pre-commit checks passed."

sbom:
	uv export --format requirements-txt --no-hashes > /tmp/requirements-sbom.txt
	uv pip install cyclonedx-py 2>/dev/null || true
	uv run cyclonedx-py /tmp/requirements-sbom.txt --output-format json -o sbom.json
	@echo "SBOM generated: sbom.json"

env-check:
	@echo "Checking environment files..."
	@for f in .env.dev .env.staging .env.production .pre-commit-config.yaml; do \
		test -f $$f && echo "  ✓ $$f" || echo "  ✗ $$f (missing)"; \
	done

check-all: lint test-unit test-integration env-check
	@echo ""
	@echo "=== ALL CHECKS PASSED ==="

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf tests/load_test/.results/ 2>/dev/null || true
	rm -f sbom.json requirements.txt 2>/dev/null || true
	@echo "Done."
