#!/bin/bash

# Script para fazer commit e push das mudanças de workflow em todos os repositórios

set -e

# Lista de repositórios das Cloud Functions
REPOS=(
    "equidade-download-data-function"
    "iu-file-checker-function"
    "gf_treatment_data_function"
    "gf_raw_data_function"
    "iu-dataset-update-function"
    "consistency_checker_function"
    "pi_treatment_data_function"
    "pi_raw_data_function"
    "etl-surveycto-function"
    "dataset-update-function"
    "equidade-access-cloud-functions"
)

BASE_DIR="/Users/spacejao"
COMMIT_MSG="chore: add cache clear step to always fetch latest equidade-data-package

Forces rebuild of dependencies to ensure latest version of equidade-data-package
is fetched from main branch during Cloud Function deployment.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

echo "🚀 Iniciando commit e push das mudanças..."
echo ""

UPDATED_COUNT=0
SKIPPED_COUNT=0

for REPO in "${REPOS[@]}"; do
    REPO_DIR="$BASE_DIR/$REPO"
    WORKFLOW_FILE="$REPO_DIR/.github/workflows/deploy.yaml"

    # Verificar se o repositório existe
    if [ ! -d "$REPO_DIR" ]; then
        echo "⚠️  $REPO - não encontrado, pulando"
        ((SKIPPED_COUNT++))
        continue
    fi

    # Verificar se há mudanças no workflow
    cd "$REPO_DIR"

    if ! git diff --quiet .github/workflows/deploy.yaml 2>/dev/null; then
        # Há mudanças - fazer commit
        git add .github/workflows/deploy.yaml
        git commit -m "$COMMIT_MSG"
        git push origin main

        echo "✅ $REPO - committed and pushed"
        ((UPDATED_COUNT++))
    else
        echo "ℹ️  $REPO - sem mudanças no workflow"
        ((SKIPPED_COUNT++))
    fi

done

echo ""
echo "🎉 Processo concluído!"
echo "   - Repositórios atualizados: $UPDATED_COUNT"
echo "   - Repositórios pulados: $SKIPPED_COUNT"
echo ""
echo "📝 Os workflows agora forçarão rebuild das dependências para pegar sempre a última versão"
