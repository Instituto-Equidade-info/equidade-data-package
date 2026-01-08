# Scripts Auxiliares

Scripts para facilitar o gerenciamento de releases e deploys automatizados.

## 📦 release.sh

Script interativo para criar releases de forma automatizada.

### Uso

```bash
./scripts/release.sh
```

### O que faz

1. ✅ Verifica se `gh` (GitHub CLI) está instalado e autenticado
2. 🔢 Mostra versão atual e pede nova versão
3. ✅ Valida formato da versão (semantic versioning)
4. 🧪 Roda testes com pytest
5. 📦 Faz build do pacote
6. 💾 Cria commit com a nova versão
7. 🏷️ Cria tag (v0.x.x)
8. ⬆️ Faz push do commit e tag
9. 📝 Cria release no GitHub com notas automáticas
10. 🚀 Dispara deploys em todas as Cloud Functions configuradas

### Requisitos

```bash
# Instalar GitHub CLI
brew install gh

# Autenticar
gh auth login

# Instalar dependências Python (opcional, para testes e build)
pip install pytest build
```

### Exemplo

```bash
$ ./scripts/release.sh

ℹ Current version: 0.2.2

Enter new version (e.g., 0.2.3): 0.2.3

Select release type:
  1) patch (bug fixes)
  2) minor (new features, backwards compatible)
  3) major (breaking changes)
Enter choice [1-3]: 2

ℹ Release type: minor

⚠ This will:
  1. Update version in pyproject.toml to 0.2.3
  2. Run tests
  3. Build package
  4. Commit changes
  5. Create and push tag v0.2.3
  6. Create GitHub release
  7. Trigger deploys in all configured Cloud Functions

Continue? [y/N] y

ℹ Updating version in pyproject.toml...
✓ Version updated
ℹ Running tests...
✓ Tests passed
ℹ Building package...
✓ Package built
ℹ Committing changes...
✓ Changes committed
ℹ Creating tag v0.2.3...
✓ Tag created
ℹ Pushing to remote...
✓ Pushed to remote
ℹ Creating GitHub release...
✓ GitHub release created

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Release v0.2.3 created successfully!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🗂️ manage-repos.sh

Script interativo para gerenciar a lista de repositórios que recebem deploy automático.

### Uso

```bash
./scripts/manage-repos.sh
```

### O que faz

- 📋 **Listar**: Mostra todos os repositórios configurados
- ➕ **Adicionar**: Adiciona novo repositório à lista
- ➖ **Remover**: Remove repositório da lista
- 🔄 **Mudar org**: Altera o nome da organização
- 🧪 **Testar**: Verifica acesso a todos os repositórios

### Exemplo - Adicionar Repositório

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
ℹ Don't forget to:
  1. Configure workflow in cloud-function-3
  2. Add GCP_SA_KEY secret to cloud-function-3
  3. Commit and push changes
```

### Exemplo - Testar Acesso

```bash
Enter choice [1-6]: 5

ℹ Testing repository access...

✓ equidade-info/cloud-function-1 - accessible
✓ equidade-info/cloud-function-2 - accessible
✗ equidade-info/cloud-function-3 - NOT accessible or doesn't exist
```

### Exemplo - Mudar Organização

```bash
Enter choice [1-6]: 4

Enter new organization name: my-new-org
✓ Changed organization from 'equidade-info' to 'my-new-org'
⚠ Don't forget to commit and push changes
```

---

## 🚨 Troubleshooting

### Erro: "gh: command not found"

Instale o GitHub CLI:

```bash
brew install gh
```

### Erro: "Not authenticated with GitHub CLI"

Faça login:

```bash
gh auth login
```

### Erro: "Tests failed"

O script automaticamente reverte mudanças se os testes falharem. Corrija os testes e tente novamente.

### Erro: "Build failed"

Verifique se as dependências estão instaladas:

```bash
pip install build
```

### Script não é executável

Torne o script executável:

```bash
chmod +x scripts/release.sh
chmod +x scripts/manage-repos.sh
```

---

## 📚 Mais Informações

Veja a documentação completa em [DEPLOY_AUTOMATION.md](../DEPLOY_AUTOMATION.md)
