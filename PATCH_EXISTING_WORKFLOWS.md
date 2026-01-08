# 🔧 Como Adicionar Trigger nos Workflows Existentes

Seus repositórios já têm workflows de deploy. Você só precisa adicionar o trigger `repository_dispatch` para que eles respondam ao evento disparado pelo `equidade-data-package`.

## 📝 O que adicionar

Em **cada repositório** de Cloud Function, edite o arquivo `.github/workflows/deploy.yml` (ou como for chamado o workflow de deploy):

### Antes:
```yaml
name: Deploy Cloud Function

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  deploy:
    # ... seu deploy atual
```

### Depois:
```yaml
name: Deploy Cloud Function

on:
  push:
    branches:
      - main
  workflow_dispatch:

  # ⭐ ADICIONE ESTAS LINHAS ⭐
  repository_dispatch:
    types: [package-updated]

jobs:
  deploy:
    # ... seu deploy atual (não muda nada aqui)
```

## 📋 Checklist por Repositório

- [ ] equidade-download-data-function
- [ ] iu-file-checker-function
- [ ] gf_treatment_data_function
- [ ] gf_raw_data_function
- [ ] iu-dataset-update-function
- [ ] consistency_checker_function
- [ ] pi_treatment_data_function
- [ ] pi_raw_data_function
- [ ] etl-surveycto-function
- [ ] dataset-update-function
- [ ] equidade-access-cloud-functions
- [ ] trigger-dash

## 💡 Bonus: Atualizar requirements.txt automaticamente

Se você quiser que o workflow **também atualize** o `requirements.txt` antes de fazer deploy, adicione este step ANTES do deploy:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      # ⭐ ADICIONE ESTE STEP ⭐
      - name: Update package version (if triggered by package update)
        if: github.event_name == 'repository_dispatch'
        run: |
          VERSION="${{ github.event.client_payload.version }}"
          if [ "${VERSION}" != "latest" ]; then
            VERSION_NUM="${VERSION#v}"  # Remove 'v' prefix
            sed -i "s/equidade-data-package.*/equidade-data-package==${VERSION_NUM}/" requirements.txt
          fi
          echo "Updated requirements.txt:"
          grep equidade-data-package requirements.txt || echo "Package not found in requirements.txt"

      # ... resto do seu deploy existente
      - name: Deploy to Cloud Functions
        run: |
          gcloud functions deploy ...
```

## 🚀 Forma Rápida: Script para Adicionar em Todos

Se quiser automatizar, você pode usar este script:

```bash
#!/bin/bash
# add-trigger.sh

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
  "trigger-dash"
)

ORG="Instituto-Equidade-info"

for REPO in "${REPOS[@]}"; do
  echo "Processing $REPO..."

  # Clone temporário
  git clone "git@github.com:${ORG}/${REPO}.git" "/tmp/${REPO}"
  cd "/tmp/${REPO}"

  # Encontra o workflow (assume que está em .github/workflows/)
  WORKFLOW_FILE=$(find .github/workflows -name "*.yml" -o -name "*.yaml" | head -1)

  if [ -n "$WORKFLOW_FILE" ]; then
    echo "Found workflow: $WORKFLOW_FILE"

    # Adiciona o trigger se ainda não existe
    if ! grep -q "repository_dispatch" "$WORKFLOW_FILE"; then
      # Adiciona após a linha 'on:'
      sed -i '' '/^on:/a\
  repository_dispatch:\
    types: [package-updated]
' "$WORKFLOW_FILE"

      # Commit e push
      git add "$WORKFLOW_FILE"
      git commit -m "feat: add repository_dispatch trigger for package updates"
      git push

      echo "✓ Updated $REPO"
    else
      echo "⚠ $REPO already has repository_dispatch trigger"
    fi
  else
    echo "✗ No workflow found in $REPO"
  fi

  cd -
  rm -rf "/tmp/${REPO}"
done
```

## ⚡ Opção Mais Simples: Commit Vazio

Se você **não quiser** que os workflows respondam automaticamente ao pacote, e preferir disparar manualmente, você pode:

### Opção A: Push vazio em todos os repos
```bash
#!/bin/bash
# trigger-all-deploys.sh

REPOS=(...)  # sua lista

for REPO in "${REPOS[@]}"; do
  cd "/path/to/${REPO}"
  git commit --allow-empty -m "chore: trigger deploy"
  git push
done
```

### Opção B: Usar workflow_dispatch
Se seus workflows já têm `workflow_dispatch`, você pode usar o GitHub CLI:

```bash
#!/bin/bash
# trigger-all-manually.sh

REPOS=(...)  # sua lista
ORG="Instituto-Equidade-info"

for REPO in "${REPOS[@]}"; do
  echo "Triggering deploy for $REPO..."
  gh workflow run deploy.yml --repo "${ORG}/${REPO}"
done
```

## 🎯 Recomendação

**Use a Opção 1** (adicionar `repository_dispatch`):
- ✅ Automatizado
- ✅ Rastreável (sabe qual versão do pacote disparou)
- ✅ Não precisa lembrar de fazer deploy manual
- ✅ Fácil de adicionar (só 3 linhas em cada workflow)

**Use commit vazio/workflow_dispatch** se:
- ❌ Quer controle manual de quando fazer deploy
- ❌ Nem sempre quer atualizar o pacote em todos os repos
- ❌ Prefere disparar deploys seletivamente

## ❓ FAQ

**P: Preciso mudar mais alguma coisa no workflow de deploy?**
R: Não! Seu deploy continua exatamente igual. Só está adicionando mais um evento que dispara ele.

**P: O que acontece se eu não adicionar o repository_dispatch?**
R: Nada! O workflow do equidade-data-package vai tentar disparar, mas o repo vai ignorar. Sem erros.

**P: Posso testar sem afetar produção?**
R: Sim! Teste primeiro com um repo só, veja se funciona, depois adiciona nos outros.

**P: E se eu quiser que alguns repos atualizem automaticamente e outros manualmente?**
R: Adicione `repository_dispatch` só nos que quer automatizar!

---

**Próximo passo**: Escolha uma abordagem e teste com 1 repositório primeiro!
