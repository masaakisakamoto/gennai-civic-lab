.PHONY: install test eval eval-easy-ja eval-faq-rag red-team run-easy-ja run-faq-rag run-local-runner validate-manifests zip

install:
	python -m pip install --upgrade pip
	pip install -e packages/gennai_app_kit
	pip install -e packages/gennai_evals
	pip install -e packages/gennai_cli
	pip install -e packages/gennai_local_runner
	pip install -e packages/gennai_red_team_lite
	pip install fastapi uvicorn pytest pyyaml jsonschema

test:
	pytest -q

eval: eval-easy-ja eval-faq-rag

eval-easy-ja:
	python packages/gennai_evals/src/gennai_evals/runner.py evals/easy_japanese.yaml

eval-faq-rag:
	python packages/gennai_evals/src/gennai_evals/runner.py evals/citizen_faq.yaml

red-team:
	python packages/gennai_red_team_lite/src/gennai_red_team_lite/runner.py evals/red_team.yaml

run-easy-ja:
	uvicorn apps.easy_japanese_rewriter.app:app --reload --port 8000

run-faq-rag:
	uvicorn apps.citizen_faq_rag.app:app --reload --port 8001

run-local-runner:
	uvicorn gennai_local_runner.app:app --reload --port 8010

validate-manifests:
	python scripts/validate_manifests.py

zip:
	cd .. && zip -r gennai-civic-lab.zip gennai-civic-lab -x 'gennai-civic-lab/.git/*' 'gennai-civic-lab/.venv/*' 'gennai-civic-lab/.pytest_cache/*' 'gennai-civic-lab/**/__pycache__/*'
