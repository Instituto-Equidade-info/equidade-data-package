# 🚀 Automação de Deploys

Este documento descreve como configurar a automação de deploys para atualizar automaticamente todas as Cloud Functions quando o pacote `equidade-data-package` for atualizado.

## 📋 Visão Geral

Quando você publica uma nova versão do pacote, um GitHub Action automaticamente:
1. Detecta o novo release/tag
2. Dispara workflows em todos os repositórios configurados
3. Cada repositório atualiza o pacote e faz redeploy da Cloud Function

## 🔧 Setup Inicial

### 1. Criar Personal Access Token (PAT)

Você precisa de um PAT com permissões para disparar workflows em outros repositórios.

1. Acesse: https://github.com/settings/tokens
2. Clique em **Generate new token** → **Generate new token (classic)**
3. Configure:
   - **Note**: `Deploy Trigger Token`
   - **Expiration**: Escolha uma duração apropriada
   - **Scopes**:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `workflow` (Update GitHub Action workflows)

4. Clique em **Generate token**
5. **COPIE O TOKEN** (você não verá novamente!)

### 2. Adicionar Secret neste Repositório

1. No repositório `equidade-data-package`, vá em **Settings** → **Secrets and variables** → **Actions**
2. Clique em **New repository secret**
3. Configure:
   - **Name**: `DEPLOY_TRIGGER_TOKEN`
   - **Secret**: Cole o PAT que você copiou
4. Clique em **Add secret**

### 3. Configurar Organização e Repositórios

Edite o arquivo [`.github/workflows/trigger-deploys.yml`](.github/workflows/trigger-deploys.yml):

**A) Defina o nome da sua organização:**

```yaml
env:
  GITHUB_ORG: 'sua-org'  # ⚠️ MUDAR para o nome da sua org
```

**B) Adicione os nomes dos repositórios (sem o prefixo da org):**

```yaml
strategy:
  matrix:
    repo:
      - 'cloud-function-1'
      - 'cloud-function-2'
      - 'cloud-function-3'
      # Adicione mais repositórios aqui
```

**💡 Dica**: Use o script auxiliar para gerenciar repositórios facilmente:

```bash
./scripts/manage-repos.sh
```

## 🔨 Configurar Repositórios de Cloud Functions

Para cada repositório que usa o pacote:

### 1. Copiar Workflow de Exemplo

Copie o arquivo [`.github/workflows/example-cloud-function-workflow.yml.example`](.github/workflows/example-cloud-function-workflow.yml.example) para cada repositório:

```bash
# No repositório da Cloud Function
mkdir -p .github/workflows
cp /path/to/equidade-data-package/.github/workflows/example-cloud-function-workflow.yml.example \
   .github/workflows/deploy.yml
```

### 2. Personalizar o Workflow

Edite `.github/workflows/deploy.yml` em cada repositório:

```yaml
env:
  FUNCTION_NAME: sua-cloud-function-name  # ⚠️ MUDAR
  REGION: us-central1                     # Ajuste se necessário
  RUNTIME: python311
```

**Ajustes adicionais** (se necessário):

- **Trigger**: Modifique triggers HTTP, Pub/Sub, etc.
- **Memory/Timeout**: Ajuste limites de recursos
- **Environment variables**: Adicione variáveis de ambiente

### 3. Adicionar Secret do GCP

Cada repositório precisa de credenciais do GCP:

1. Vá em **Settings** → **Secrets and variables** → **Actions**
2. Adicione:
   - **Name**: `GCP_SA_KEY`
   - **Secret**: JSON da service account com permissões de deploy

### 4. Garantir requirements.txt Correto

Certifique-se que `requirements.txt` inclui:

```txt
equidade-data-package==0.2.2
# ou sem versão fixa:
equidade-data-package
```

O workflow vai atualizar automaticamente para a nova versão.

## 🎯 Como Usar

### Opção 1: Script Automatizado (Mais Fácil!)

Use o script auxiliar que faz tudo automaticamente:

```bash
./scripts/release.sh
```

O script vai:
- ✅ Perguntar a nova versão
- ✅ Atualizar pyproject.toml
- ✅ Rodar testes
- ✅ Fazer build
- ✅ Criar commit e tag
- ✅ Fazer push
- ✅ Criar release no GitHub
- ✅ Disparar deploys automaticamente

**Requisitos**: Instale o GitHub CLI:
```bash
brew install gh
gh auth login
```

### Opção 2: Release Manual no GitHub (Recomendado)

```bash
# 1. Atualizar versão no pyproject.toml
# version = "0.2.3"

# 2. Commit e push
git add pyproject.toml
git commit -m "chore: bump version to 0.2.3"
git push

# 3. Criar tag
git tag v0.2.3
git push --tags

# 4. Criar release no GitHub
gh release create v0.2.3 --generate-notes
```

Isso automaticamente vai:
- ✅ Disparar workflow em todos os repos configurados
- ✅ Atualizar o pacote em cada um
- ✅ Fazer redeploy de todas as Cloud Functions

### Opção 2: Push de Tag Manual

```bash
git tag v0.2.3
git push --tags
```

### Opção 3: Push de Tag Manual

```bash
git tag v0.2.3
git push --tags
```

### Opção 4: Trigger Manual

No GitHub:
1. Vá em **Actions** → **Trigger Deploys on Package Update**
2. Clique em **Run workflow**
3. (Opcional) Especifique uma versão
4. Clique em **Run workflow**

## 🛠️ Scripts Auxiliares

### `scripts/release.sh` - Release Automatizado

Cria um novo release automaticamente:

```bash
./scripts/release.sh
```

**Features**:
- ✅ Validação de versão (semantic versioning)
- ✅ Roda testes antes de release
- ✅ Build do pacote
- ✅ Criação de commit e tag
- ✅ Push automático
- ✅ Criação de release no GitHub
- ✅ Notas de release geradas automaticamente

### `scripts/manage-repos.sh` - Gerenciar Repositórios

Gerencia a lista de repositórios que recebem deploy automático:

```bash
./scripts/manage-repos.sh
```

**Features**:
- 📋 Listar repositórios configurados
- ➕ Adicionar novo repositório
- ➖ Remover repositório
- 🔄 Mudar organização
- 🧪 Testar acesso aos repositórios

**Exemplo de uso:**

```bash
$ ./scripts/manage-repos.sh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Manage Deployment Repositories
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ Current organization: equidade-info

Current repositories:
  - cloud-function-1
  - cloud-function-2

What would you like to do?
  1) List current repositories
  2) Add a repository
  3) Remove a repository
  4) Change organization name
  5) Test repository access
  6) Exit

Enter choice [1-6]: 2
Enter repository name (without org prefix): cloud-function-3
✓ Added repository: equidade-info/cloud-function-3
```

## 📊 Monitoramento

### Ver Status dos Deploys

1. No repositório `equidade-data-package`:
   - **Actions** → **Trigger Deploys on Package Update**
   - Veja quais repos foram disparados

2. Em cada repositório de Cloud Function:
   - **Actions** → **Deploy Cloud Function on Package Update**
   - Veja o status do deploy

### Logs

```bash
# Ver logs da Cloud Function
gcloud functions logs read FUNCTION_NAME \
  --region=REGION \
  --limit=50
```

## 🔍 Troubleshooting

### ❌ Erro: "Resource not accessible by integration"

**Causa**: PAT não tem permissões suficientes

**Solução**:
1. Verifique se o PAT tem scopes `repo` e `workflow`
2. Verifique se o secret `DEPLOY_TRIGGER_TOKEN` está configurado
3. Regenere o PAT se necessário

### ❌ Erro: "Not found or repository_dispatch not enabled"

**Causa**: Repositório não existe ou workflow não configurado

**Solução**:
1. Verifique o nome do repositório em `trigger-deploys.yml`
2. Certifique-se que o workflow existe no repositório de destino
3. Verifique permissões de acesso ao repositório

### ❌ Deploy Falha em Alguns Repositórios

**Causa**: Cada repositório pode ter configurações diferentes

**Solução**:
1. Verifique logs do workflow no repositório que falhou
2. Verifique se `GCP_SA_KEY` está configurado
3. Verifique se service account tem permissões de deploy
4. Verifique se `FUNCTION_NAME` está correto

### 🔄 Fazer Rollback

Se um deploy automático causar problemas:

```bash
# Deploy versão anterior manualmente
cd cloud-function-repo

# Atualizar requirements.txt
echo "equidade-data-package==0.2.1" > requirements.txt

# Deploy manual
gcloud functions deploy FUNCTION_NAME \
  --region=REGION \
  --runtime=python311 \
  --trigger-http \
  --source=.
```

## 📝 Exemplo de Fluxo Completo

```bash
# 1. Fazer mudança no pacote
cd equidade-data-package
# ... editar código ...

# 2. Testar localmente
pytest tests/

# 3. Atualizar versão
# Editar pyproject.toml: version = "0.3.0"

# 4. Commit e tag
git add .
git commit -m "feat: add new BigQuery loader feature"
git tag v0.3.0
git push && git push --tags

# 5. Criar release
gh release create v0.3.0 --generate-notes

# 6. GitHub Actions automaticamente:
#    - Dispara deploy em cloud-function-1 ✅
#    - Dispara deploy em cloud-function-2 ✅
#    - Dispara deploy em cloud-function-3 ✅

# 7. Verificar deploys
gh run list --repo your-org/cloud-function-1
gh run list --repo your-org/cloud-function-2
```

## 🎯 Boas Práticas

### Versionamento Semântico

Use [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features (backwards compatible)
- **PATCH** (0.0.1): Bug fixes

### Testes Antes de Release

```bash
# Sempre testar antes de criar release
pytest tests/ -v
python -m build
twine check dist/*
```

### Deploy Gradual (Opcional)

Para projetos críticos, considere deploy gradual:

```yaml
strategy:
  matrix:
    repo:
      - 'org/cloud-function-staging'  # Deploy primeiro
      # Depois adicionar prod
      # - 'org/cloud-function-prod'
```

### Changelog

Mantenha `CHANGELOG.md` atualizado:

```bash
# Gerar automaticamente com release
gh release create v0.3.0 --generate-notes
```

## 🔐 Segurança

### Proteção de Branches

Configure branch protection em repositórios críticos:
1. **Settings** → **Branches** → **Add rule**
2. Branch name: `main`
3. Habilitar:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass
   - ✅ Do not allow bypassing the above settings

### Rotação de Tokens

- Rotacionar PAT a cada 6-12 meses
- Usar tokens com menor prazo de expiração possível
- Auditar uso do token regularmente

### Service Accounts

- Usar service accounts dedicadas por ambiente (dev/staging/prod)
- Princípio do menor privilégio
- Auditar permissões regularmente

## 📚 Recursos

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Repository Dispatch Events](https://docs.github.com/en/rest/repos/repos#create-a-repository-dispatch-event)
- [Google Cloud Functions Deploy](https://cloud.google.com/functions/docs/deploy)
- [Semantic Versioning](https://semver.org/)

## ❓ FAQ

**P: Posso desabilitar o deploy automático temporariamente?**

R: Sim, duas opções:
1. Desabilitar o workflow: **Actions** → **Trigger Deploys** → **⋯** → **Disable workflow**
2. Remover repositórios temporariamente da matrix em `trigger-deploys.yml`

**P: Como testar sem fazer deploy em produção?**

R: Configure repositórios de staging primeiro na matrix, teste, depois adicione produção.

**P: Quanto tempo leva o deploy completo?**

R: ~3-5 minutos por Cloud Function (em paralelo). Com 10 funções, ~5 minutos total.

**P: Posso usar isso com outros serviços (não Cloud Functions)?**

R: Sim! Adapte o workflow de exemplo para Cloud Run, App Engine, etc.

---

**Última atualização**: 2024-01-08
**Versão**: 1.0.0
