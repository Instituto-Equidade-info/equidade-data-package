# 🚀 Quick Start - Deploy Automation

Guia rápido de 5 minutos para configurar deploys automatizados.

## ✅ Checklist de Setup

### 1. Criar Personal Access Token (2 min)

```bash
# 1. Acesse: https://github.com/settings/tokens
# 2. Generate new token (classic)
# 3. Selecione scopes: repo, workflow
# 4. Copie o token
```

### 2. Adicionar Secret (1 min)

```bash
# No GitHub, neste repositório:
# Settings → Secrets → Actions → New repository secret
# Name: DEPLOY_TRIGGER_TOKEN
# Value: [cole o token]
```

### 3. Configurar Repositórios (2 min)

Edite [`.github/workflows/trigger-deploys.yml`](.github/workflows/trigger-deploys.yml):

```yaml
env:
  GITHUB_ORG: 'sua-org'  # ⚠️ MUDAR

strategy:
  matrix:
    repo:
      - 'cloud-function-1'  # ⚠️ ADICIONAR seus repos
      - 'cloud-function-2'
```

**Ou use o script:**

```bash
./scripts/manage-repos.sh
```

### 4. Adicionar Trigger nos Workflows Existentes (SUPER RÁPIDO!)

Seus repositórios já têm workflows de deploy! Você só precisa adicionar o evento `repository_dispatch`.

**Opção A - Automatizado (1 min):**

```bash
# Este script adiciona o trigger em todos os repos automaticamente
./scripts/patch-workflows.sh
```

**Opção B - Manual (30 seg por repo):**

Em cada repositório, edite `.github/workflows/deploy.yml` e adicione:

```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:
  # ⭐ ADICIONE ESTAS 3 LINHAS ⭐
  repository_dispatch:
    types: [package-updated]
```

Pronto! Não precisa mudar mais nada no workflow.

### 5. Testar! (1 min)

```bash
# Opção A: Script automatizado (mais fácil)
./scripts/release.sh

# Opção B: Manual
git tag v0.2.3
git push --tags
gh release create v0.2.3 --generate-notes
```

## ✨ Pronto!

Agora toda vez que você criar um release:

1. ✅ GitHub Action dispara automaticamente
2. ✅ Todas as Cloud Functions atualizam o pacote
3. ✅ Deploy é feito automaticamente
4. ✅ Você monitora tudo no GitHub Actions

## 📊 Monitorar Deploys

```bash
# Ver deploys disparados
gh run list

# Ver logs de um deploy específico
gh run view <run-id> --log

# Verificar Cloud Functions
gcloud functions list
```

## 🔧 Comandos Úteis

```bash
# Fazer release (interativo)
./scripts/release.sh

# Gerenciar repositórios
./scripts/manage-repos.sh

# Listar repositórios configurados
grep -A 10 "repo:" .github/workflows/trigger-deploys.yml

# Testar acesso aos repos
gh repo list your-org

# Ver últimos releases
gh release list
```

## 📚 Documentação Completa

- [DEPLOY_AUTOMATION.md](DEPLOY_AUTOMATION.md) - Guia completo
- [scripts/README.md](scripts/README.md) - Documentação dos scripts

## 🆘 Problemas?

### Deploy não disparou

1. Verifique se o secret `DEPLOY_TRIGGER_TOKEN` está configurado
2. Verifique se a organização está correta no workflow
3. Veja logs em: **Actions** → **Trigger Deploys on Package Update**

### Cloud Function não atualizou

1. Verifique se o workflow existe no repo da função
2. Verifique se `GCP_SA_KEY` está configurado
3. Veja logs em: **Actions** no repo da função

### "Not authenticated"

```bash
gh auth login
```

---

**🎉 Tudo funcionando?** Agora você pode:

1. Fazer mudanças no pacote
2. Rodar `./scripts/release.sh`
3. ☕ Tomar um café enquanto tudo deploya automaticamente!
