#!/usr/bin/env python3
"""
Script para fazer commit e push das mudanças de workflow em todos os repositórios.
"""

import subprocess
from pathlib import Path

# Lista de repositórios das Cloud Functions
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

COMMIT_MSG = """chore: add cache clear step to always fetch latest equidade-data-package

Forces rebuild of dependencies to ensure latest version of equidade-data-package
is fetched from main branch during Cloud Function deployment.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"""


def run_git_command(repo_dir: Path, command: list) -> tuple[bool, str]:
    """Executa um comando git em um repositório."""
    try:
        result = subprocess.run(
            command,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def has_changes(repo_dir: Path) -> bool:
    """Verifica se há mudanças no workflow."""
    success, output = run_git_command(
        repo_dir,
        ["git", "diff", "--quiet", ".github/workflows/deploy.yaml"]
    )
    # git diff --quiet retorna 1 se há diferenças, 0 se não há
    return not success


def commit_and_push(repo_dir: Path, repo_name: str) -> bool:
    """Faz commit e push das mudanças."""
    # Add
    success, output = run_git_command(
        repo_dir,
        ["git", "add", ".github/workflows/deploy.yaml"]
    )
    if not success:
        print(f"   ❌ Erro ao fazer git add: {output}")
        return False

    # Commit
    success, output = run_git_command(
        repo_dir,
        ["git", "commit", "-m", COMMIT_MSG]
    )
    if not success:
        print(f"   ❌ Erro ao fazer commit: {output}")
        return False

    # Push
    success, output = run_git_command(
        repo_dir,
        ["git", "push", "origin", "main"]
    )
    if not success:
        print(f"   ❌ Erro ao fazer push: {output}")
        return False

    return True


def main():
    print("🚀 Iniciando commit e push das mudanças...")
    print()

    updated_count = 0
    skipped_count = 0
    error_count = 0

    for repo in REPOS:
        repo_dir = BASE_DIR / repo

        # Verificar se o repositório existe
        if not repo_dir.exists():
            print(f"⚠️  {repo} - não encontrado, pulando")
            skipped_count += 1
            continue

        # Verificar se há mudanças
        if not has_changes(repo_dir):
            print(f"ℹ️  {repo} - sem mudanças no workflow")
            skipped_count += 1
            continue

        # Fazer commit e push
        if commit_and_push(repo_dir, repo):
            print(f"✅ {repo} - committed and pushed")
            updated_count += 1
        else:
            print(f"❌ {repo} - erro ao fazer commit/push")
            error_count += 1

    print()
    print("🎉 Processo concluído!")
    print(f"   - Repositórios atualizados: {updated_count}")
    print(f"   - Repositórios pulados: {skipped_count}")
    print(f"   - Erros: {error_count}")
    print()
    print("📝 Os workflows agora forçarão rebuild das dependências para pegar sempre a última versão")


if __name__ == "__main__":
    main()
