# Makefile — run the federation end to end.

PYTHON ?= python3
ARTIFACTS := artifacts

.PHONY: help install test demo live clean

help:
	@echo "Federation targets:"
	@echo "  make install    — pip install dependencies"
	@echo "  make test       — run all tests"
	@echo "  make demo       — run federation demo (in-process, signed)"
	@echo "  make demo-unsigned — run demo without crypto"
	@echo "  make live       — run federation live (HTTP + conformance)"
	@echo "  make clean      — remove artifacts and __pycache__"
	@echo ""
	@echo "Artifacts (JSON + text) are saved to $(ARTIFACTS)/<timestamp>/."

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m pytest -v --tb=short \
		multiverse_c*_test.py wcp_conformance*_test.py federation_test.py

demo:
	$(PYTHON) federation.py --mode demo

demo-unsigned:
	$(PYTHON) federation.py --mode demo --no-signed

live:
	$(PYTHON) federation.py --mode live

clean:
	rm -rf $(ARTIFACTS) __pycache__ */__pycache__
	@echo "Cleaned."
