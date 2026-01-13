#!/bin/bash

# Script para adicionar clear cache step em todos os workflows de deploy das Cloud Functions
# Garante que sempre pegue a última versão do equidade-data-package

set -e

# Lista de repositórios das Cloud Functions (do trigger-deploys.yml)
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

# Diretório base (assumindo que todos os repos estão no mesmo nível)
BASE_DIR="/Users/spacejao"

# Step a ser adicionado antes do deploy
CACHE_CLEAR_STEP='
    - name: Clear pip cache and update requirements
      run: |
        # Adiciona timestamp ao requirements.txt para forçar rebuild
        cd functions
        echo "# Last updated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> requirements.txt
        echo "Forcing rebuild to fetch latest equidade-data-package from main branch"
'

echo "🚀 Iniciando atualização dos workflows de deploy..."
echo ""

for REPO in "${REPOS[@]}"; do
    WORKFLOW_FILE="$BASE_DIR/$REPO/.github/workflows/deploy.yaml"

    # Verificar se o repositório existe localmente
    if [ ! -d "$BASE_DIR/$REPO" ]; then
        echo "⚠️  Repositório $REPO não encontrado em $BASE_DIR - pulando"
        continue
    fi

    # Verificar se o arquivo deploy.yaml existe
    if [ ! -f "$WORKFLOW_FILE" ]; then
        echo "⚠️  Workflow não encontrado: $WORKFLOW_FILE - pulando"
        continue
    fi

    # Verificar se já tem o step de clear cache
    if grep -q "Clear pip cache and update requirements" "$WORKFLOW_FILE"; then
        echo "✅ $REPO - já tem clear cache step"
        continue
    fi

    # Criar backup
    cp "$WORKFLOW_FILE" "$WORKFLOW_FILE.backup"

    # Adicionar o step antes do "Deploy Cloud Function"
    # Procura pela linha "- name: Deploy Cloud Function" e insere o novo step antes
    awk -v step="$CACHE_CLEAR_STEP" '
        /- name: Deploy Cloud Function/ {
            print step
        }
        { print }
    ' "$WORKFLOW_FILE.backup" > "$WORKFLOW_FILE"

    echo "✅ $REPO - clear cache step adicionado"

done

echo ""
echo "🎉 Atualização concluída!"
echo ""
echo "📝 Próximos passos:"
echo "1. Revise as mudanças nos repositórios"
echo "2. Faça commit e push das alterações em cada repositório"
echo "3. Ou use o script companion para fazer commit em todos de uma vez"
