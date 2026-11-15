.PHONY: verify-garden verify-garden-python verify-garden-both

verify-garden:
	@if [ -z "$(URL)" ]; then \
		echo "Usage: make verify-garden URL=<url>"; exit 1; \
	fi
	cargo run --manifest-path rust/ur-world/Cargo.toml \
		--example verify_garden -- $(URL)

verify-garden-python:
	@if [ -z "$(URL)" ]; then \
		echo "Usage: make verify-garden-python URL=<url>"; \
		exit 1; \
	fi
	$(PYTHON) rust/ur-world/examples/verify_garden.py $(URL)

verify-garden-both:
	@if [ -z "$(URL)" ]; then \
		echo "Usage: make verify-garden-both URL=<url>"; \
		exit 1; \
	fi
	@echo "=== Rust verifier ==="
	cargo run --manifest-path rust/ur-world/Cargo.toml \
		--example verify_garden -- $(URL)
	@echo ""
	@echo "=== Python verifier ==="
	$(PYTHON) rust/ur-world/examples/verify_garden.py $(URL)
