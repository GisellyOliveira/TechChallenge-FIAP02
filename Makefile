.DEFAULT_GOAL := help
PY ?= python
IMAGE_TAG ?= latest

help: ## Lista os comandos
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

install: ## Instala o pacote com as ferramentas de desenvolvimento
	$(PY) -m pip install -e ".[dev]"

lint: ## Estilo e erros comuns
	ruff check . && ruff format --check .

type: ## Tipagem estrita
	mypy src

test: ## Testes unitários
	pytest

check: lint type test ## Tudo que a CI executa

deploy: ## Cria infraestrutura, constrói a imagem e cria os jobs
	./scripts/deploy.sh

evidence: ## Gera docs/execucao-cloud/evidencias.md a partir do BigQuery
	radar evidence

finops: ## Gera docs/finops.md e atualiza a tabela do README com valores medidos
	radar finops --readme README.md

.PHONY: help install lint type test check deploy evidence finops
