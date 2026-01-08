# ✅ Setup Checklist - Deploy Automation

Imprima e marque cada item conforme completa o setup.

## 📦 Repositório: equidade-data-package

### 1. Criar Personal Access Token
- [ ] Acessar https://github.com/settings/tokens
- [ ] Clicar em "Generate new token (classic)"
- [ ] Selecionar scopes: `repo` e `workflow`
- [ ] Copiar o token (guardar em local seguro!)

### 2. Adicionar Secret no GitHub
- [ ] Ir em Settings → Secrets and variables → Actions
- [ ] New repository secret
- [ ] Name: `DEPLOY_TRIGGER_TOKEN`
- [ ] Value: [colar o PAT]
- [ ] Add secret

### 3. Configurar Workflow
- [ ] Abrir `.github/workflows/trigger-deploys.yml`
- [ ] Editar `GITHUB_ORG: 'sua-org'` com o nome correto
- [ ] Adicionar repositórios na lista:
  ```yaml
  repo:
    - 'cloud-function-1'
    - 'cloud-function-2'
    # etc
  ```
- [ ] Commit e push

### 4. Testar Scripts (Opcional mas Recomendado)
- [ ] Instalar GitHub CLI: `brew install gh`
- [ ] Autenticar: `gh auth login`
- [ ] Tornar executável: `chmod +x scripts/*.sh`
- [ ] Testar gerenciador: `./scripts/manage-repos.sh`

---

## 🔧 Para Cada Cloud Function

Repetir para cada repositório listado acima:

### Repositório: _______________________

#### 1. Copiar Workflow Template
- [ ] `mkdir -p .github/workflows`
- [ ] Copiar `example-cloud-function-workflow.yml.example`
- [ ] Renomear para `.github/workflows/deploy.yml`

#### 2. Editar Configurações
- [ ] Abrir `.github/workflows/deploy.yml`
- [ ] Editar variáveis de ambiente:
  ```yaml
  FUNCTION_NAME: ________________  # Nome correto
  REGION: us-central1              # ou outra região
  RUNTIME: python311
  ```
- [ ] Ajustar parâmetros de deploy (memory, timeout, triggers)

#### 3. Adicionar Secret do GCP
- [ ] Ir em Settings → Secrets and variables → Actions
- [ ] New repository secret
- [ ] Name: `GCP_SA_KEY`
- [ ] Value: [JSON da service account]
- [ ] Add secret

#### 4. Verificar Service Account (GCP)
- [ ] Service account tem role: Cloud Functions Developer
- [ ] Service account tem role: Service Account User
- [ ] Service account tem outras permissões necessárias

#### 5. Testar Manualmente (Opcional)
- [ ] Push para main branch
- [ ] Verificar Actions tab
- [ ] Confirmar deploy funcionou

---

## 🧪 Teste Completo do Sistema

### 1. Preparar Teste
- [ ] Escolher versão de teste (ex: v0.2.3-test)
- [ ] Ou usar workflow_dispatch para teste

### 2. Executar Teste
**Opção A - Script Automatizado:**
- [ ] Rodar: `./scripts/release.sh`
- [ ] Escolher versão de teste
- [ ] Confirmar execução

**Opção B - Manual:**
- [ ] Criar tag: `git tag v0.2.3-test`
- [ ] Push: `git push --tags`
- [ ] Criar release: `gh release create v0.2.3-test`

### 3. Verificar Triggers
- [ ] Ir em Actions → Trigger Deploys on Package Update
- [ ] Verificar se workflow rodou
- [ ] Verificar matriz de repositórios
- [ ] Confirmar todos os repository_dispatch enviados

### 4. Verificar Deploys
Para cada Cloud Function:
- [ ] Ir em Actions no repo
- [ ] Verificar workflow "Deploy Cloud Function" rodou
- [ ] Verificar logs do deploy
- [ ] Confirmar deploy completou com sucesso

### 5. Verificar no GCP
- [ ] `gcloud functions list`
- [ ] Confirmar todas as funções atualizadas
- [ ] Testar funções manualmente (opcional)

---

## 📋 Lista de Repositórios Configurados

Marque cada repositório após configuração completa:

- [ ] `_______________________`
- [ ] `_______________________`
- [ ] `_______________________`
- [ ] `_______________________`
- [ ] `_______________________`
- [ ] `_______________________`

---

## 🔍 Troubleshooting Checklist

Se algo não funcionar, verificar:

### Trigger não disparou
- [ ] Secret `DEPLOY_TRIGGER_TOKEN` configurado?
- [ ] PAT tem scopes corretos (`repo`, `workflow`)?
- [ ] Nome da org está correto no workflow?
- [ ] Repositórios existem e estão acessíveis?

### Deploy de Cloud Function falhou
- [ ] Secret `GCP_SA_KEY` configurado no repo?
- [ ] Service account tem permissões corretas?
- [ ] Nome da função está correto em `FUNCTION_NAME`?
- [ ] Workflow existe em `.github/workflows/deploy.yml`?

### Script release.sh não funciona
- [ ] GitHub CLI instalado? (`gh --version`)
- [ ] Autenticado? (`gh auth status`)
- [ ] Scripts são executáveis? (`chmod +x scripts/*.sh`)

---

## 📊 Resumo do Setup

Total de configurações necessárias:

- **equidade-data-package**: 1 secret + 1 workflow
- **Cada Cloud Function**: 1 secret + 1 workflow

**Tempo estimado**:
- Setup inicial: ~15 minutos
- Por Cloud Function: ~5 minutos cada
- Teste completo: ~5 minutos

**Total para 5 Cloud Functions**: ~45 minutos

---

## ✨ Quando Tudo Estiver Pronto

Para fazer releases no futuro:

```bash
# Opção 1 - Automatizado (recomendado)
./scripts/release.sh

# Opção 2 - Manual
git tag v0.x.x
git push --tags
gh release create v0.x.x --generate-notes
```

E então:
- ☕ Tomar um café
- 📊 Monitorar no GitHub Actions
- ✅ Confirmar deploys completaram
- 🎉 Pronto!

---

## 📚 Recursos

- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Documentação Completa**: [DEPLOY_AUTOMATION.md](DEPLOY_AUTOMATION.md)
- **Diagrama Visual**: [.github/workflows/.workflow-diagram.md](.github/workflows/.workflow-diagram.md)
- **Scripts**: [scripts/README.md](scripts/README.md)

---

**Data do Setup**: ___/___/______

**Responsável**: _______________________

**Status**: ⬜ Em Progresso | ⬜ Completo | ⬜ Testado

**Notas**:
_______________________________________________
_______________________________________________
_______________________________________________
