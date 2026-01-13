#!/usr/bin/env python3
"""
Script para adicionar clear cache step em todos os workflows de deploy das Cloud Functions.
Garante que sempre pegue a última versão do equidade-data-package.
"""

import os
from pathlib import Path

# Lista de repositórios das Cloud Functions (do trigger-deploys.yml)
REPOS = [
    "equidade-download-data-function",
    "iu-file-checker-function",
    "gf_treatment_data_function",
    "gf_raw_data_function",
    "iu-dataset-update-function",
    "consistency_checker_function",
    "pi_treatment_data_function",
    "pi_raw_data_function",
    "etl-surveycto-function",
    "dataset-update-function",
    "equidade-access-cloud-functions",
]

BASE_DIR = Path("/Users/spacejao")

# Step a ser adicionado antes do deploy
CACHE_CLEAR_STEP = """
    - name: Clear pip cache and update requirements
      run: |
        # Adiciona timestamp ao requirements.txt para forçar rebuild
        cd functions
        echo "# Last updated: $(date -u +\\"%Y-%m-%dT%H:%M:%SZ\\")" >> requirements.txt
        echo "Forcing rebuild to fetch latest equidade-data-package from main branch"
"""

def update_workflow(workflow_file: Path) -> bool:
    """Atualiza um arquivo de workflow adicionando o step de clear cache."""
    try:
        content = workflow_file.read_text()

        # Verificar se já tem o step
        if "Clear pip cache and update requirements" in content:
            return False

        # Encontrar a linha "- name: Deploy Cloud Function" e inserir antes
        lines = content.split('\n')
        new_lines = []

        for line in lines:
            if "- name: Deploy Cloud Function" in line:
                # Adicionar o novo step antes desta linha
                new_lines.append(CACHE_CLEAR_STEP.rstrip())
            new_lines.append(line)

        # Salvar o arquivo atualizado
        workflow_file.write_text('\n'.join(new_lines))
        return True

    except Exception as e:
        print(f"   ❌ Erro ao processar arquivo: {e}")
        return False


def main():
    print("🚀 Iniciando atualização dos workflows de deploy...")
    print()

    updated_count = 0
    skipped_count = 0

    for repo in REPOS:
        repo_dir = BASE_DIR / repo
        workflow_file = repo_dir / ".github" / "workflows" / "deploy.yaml"

        # Verificar se o repositório existe
        if not repo_dir.exists():
            print(f"⚠️  {repo} - não encontrado, pulando")
            skipped_count += 1
            continue

        # Verificar se o workflow existe
        if not workflow_file.exists():
            print(f"⚠️  {repo} - workflow não encontrado, pulando")
            skipped_count += 1
            continue

        # Criar backup
        backup_file = workflow_file.with_suffix('.yaml.backup')
        backup_file.write_text(workflow_file.read_text())

        # Atualizar o workflow
        if update_workflow(workflow_file):
            print(f"✅ {repo} - clear cache step adicionado")
            updated_count += 1
        else:
            print(f"ℹ️  {repo} - já tem clear cache step")
            skipped_count += 1

    print()
    print("🎉 Atualização concluída!")
    print(f"   - Arquivos atualizados: {updated_count}")
    print(f"   - Arquivos pulados: {skipped_count}")
    print()
    print("📝 Próximos passos:")
    print("1. Revise as mudanças com: git diff .github/workflows/deploy.yaml")
    print("2. Execute: python3 commit_all_workflow_changes.py")


if __name__ == "__main__":
    main()
