# Tasks for RFM Architecture development.
# Run `just --list` to see all commands. Assumes an activated virtualenv
# (or use `poetry run just <task>` to pick up the Poetry env automatically).

default: test

# Install the project as editable + dev dependencies.
install:
    pip install -e .
    pip install -r requirements.txt
    pip install -r requirements_dev.txt

# Run the fast/default test subset — the same single-file set CI runs
# in the "Unit Tests" job of .github/workflows/resilience-tests.yml.
test:
    pytest tests/test_progress_reporting.py -v

# Run everything pytest can collect under tests/. Some modules require
# optional deps (dearpygui for UI integration tests); those will error
# out in headless envs. Use `just test` for the canonical fast path.
test-all:
    pytest tests/

# Reproduce the "Resilience Smoke" CI job locally. This is the custom
# harness — not pytest — and relies on self-signed certs (see `just ssl-certs`).
test-resilience:
    python tests/run_resilience_test.py --tests connection --start-server --duration 20 --restart-count 1 --restart-interval 2
    python tests/run_resilience_test.py --tests operation --start-server --duration 20 --operation-count 2

# Generate self-signed SSL certs required by the secure WebSocket server
# and the resilience smoke tests. CI runs the same script.
ssl-certs:
    chmod +x tools/ssl/generate_certs.sh
    tools/ssl/generate_certs.sh

# Housekeeping: delete __pycache__ dirs and compiled bytecode.
clean:
    find . -type d -name __pycache__ -not -path './.venv*' -not -path './node_modules/*' -exec rm -rf {} +
    find . -type f -name '*.pyc' -not -path './.venv*' -not -path './node_modules/*' -delete
