.PHONY: install test eval eval-easy-ja eval-faq-rag run-easy-ja run-faq-rag validate-manifests zip

install:
	python -m pip install --upgrade pip
	pip install -e packages/gennai_app_kit
	pip install -e packages/gennai_evals
	pip install fastapi uvicorn pytest pyyaml jsonschema

test:
	pytest -q

eval: eval-easy-ja eval-faq-rag

eval-easy-ja:
	python packages/gennai_evals/src/gennai_evals/runner.py evals/easy_japanese.yaml

eval-faq-rag:
	python packages/gennai_evals/src/gennai_evals/runner.py evals/citizen_faq.yaml

run-easy-ja:
	uvicorn apps.easy_japanese_rewriter.app:app --reload --port 8000

run-faq-rag:
	uvicorn apps.citizen_faq_rag.app:app --reload --port 8001

validate-manifests:
	python scripts/validate_manifests.py

zip:
	cd .. && zip -r gennai-civic-lab.zip gennai-civic-lab -x 'gennai-civic-lab/.git/*' 'gennai-civic-lab/.venv/*' 'gennai-civic-lab/**/__pycache__/*'
