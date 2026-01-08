# Arquivos Criados - Deploy Automation

## Resumo

Sistema completo de automação de deploys para atualizar todas as Cloud Functions quando o pacote for atualizado.

## 📁 Estrutura de Arquivos

```
equidade-data-package/
├── .github/
│   └── workflows/
│       ├── trigger-deploys.yml              # ⭐ Workflow principal
│       ├── example-cloud-function-workflow.yml.example  # Template para Cloud Functions
│       ├── .workflow-diagram.md             # Diagrama visual do fluxo
│       └── FILES_OVERVIEW.md                # Este arquivo
│
├── scripts/
│   ├── release.sh                           # ⭐ Script de release automatizado
│   ├── manage-repos.sh                      # ⭐ Gerenciar lista de repositórios
│   └── README.md                            # Documentação dos scripts
│
├── DEPLOY_AUTOMATION.md                     # 📚 Documentação completa
├── QUICKSTART.md                            # 🚀 Guia rápido (5 min)
└── README.md                                # Atualizado com link para automação
```

## 📄 Descrição dos Arquivos

### Workflows

#### `trigger-deploys.yml` ⭐ PRINCIPAL
**Localização**: `.github/workflows/trigger-deploys.yml`

**Função**: Workflow que dispara deploys em todos os repositórios configurados quando um release é publicado.

**Triggers**:
- Release publicado no GitHub
- Push de tag (v*.*.*)
- Manual (workflow_dispatch)

**Configuração necessária**:
```yaml
env:
  GITHUB_ORG: 'sua-org'  # ⚠️ MUDAR

strategy:
  matrix:
    repo:
      - 'cloud-function-1'  # ⚠️ ADICIONAR seus repos
      - 'cloud-function-2'
```

**Secrets necessários**:
- `DEPLOY_TRIGGER_TOKEN` - Personal Access Token com scopes `repo` e `workflow`

---

#### `example-cloud-function-workflow.yml.example`
**Localização**: `.github/workflows/example-cloud-function-workflow.yml.example`

**Função**: Template de workflow para copiar para cada repositório de Cloud Function.

**Como usar**:
1. Copiar para `.github/workflows/deploy.yml` em cada Cloud Function repo
2. Editar `FUNCTION_NAME`, `REGION`, `RUNTIME`
3. Adicionar secret `GCP_SA_KEY`

**Triggers**:
- `repository_dispatch` (disparado pelo trigger-deploys.yml)
- Push na branch main
- Manual (workflow_dispatch)

---

### Scripts

#### `scripts/release.sh` ⭐ RECOMENDADO
**Função**: Script interativo para criar releases automaticamente.

**O que faz**:
1. Valida versão (semantic versioning)
2. Roda testes
3. Faz build
4. Cria commit e tag
5. Push para remote
6. Cria release no GitHub
7. Dispara deploys automaticamente

**Como usar**:
```bash
./scripts/release.sh
```

**Requisitos**:
- GitHub CLI (`gh`)
- Python 3.11+ (para testes e build)

---

#### `scripts/manage-repos.sh` ⭐ ÚTIL
**Função**: Script interativo para gerenciar lista de repositórios.

**Features**:
- Listar repositórios configurados
- Adicionar novo repositório
- Remover repositório
- Mudar organização
- Testar acesso aos repositórios

**Como usar**:
```bash
./scripts/manage-repos.sh
```

---

### Documentação

#### `DEPLOY_AUTOMATION.md` 📚 COMPLETO
**Função**: Documentação completa do sistema de automação.

**Conteúdo**:
- Visão geral do sistema
- Setup passo a passo
- Configuração de repositórios
- Como usar (4 opções)
- Scripts auxiliares
- Monitoramento
- Troubleshooting
- Boas práticas
- FAQ

**Para**: Quem quer entender tudo em detalhes.

---

#### `QUICKSTART.md` 🚀 RÁPIDO
**Função**: Guia rápido de 5 minutos.

**Conteúdo**:
- Checklist de setup
- Comandos essenciais
- Links para docs completas
- Troubleshooting básico

**Para**: Quem quer começar rápido.

---

#### `scripts/README.md`
**Função**: Documentação específica dos scripts.

**Conteúdo**:
- Descrição detalhada de cada script
- Exemplos de uso
- Output esperado
- Troubleshooting

---

#### `.github/workflows/.workflow-diagram.md`
**Função**: Diagrama visual do fluxo de automação.

**Conteúdo**:
- Fluxo completo ilustrado
- Payload do repository_dispatch
- Timeline de execução
- Troubleshooting visual
- Exemplo completo real

---

## 🎯 Por Onde Começar?

### Setup Inicial (primeira vez)

1. **Ler**: [QUICKSTART.md](../../QUICKSTART.md) (5 min)
2. **Configurar**: Seguir checklist
3. **Testar**: Fazer um release de teste

### Uso Diário

```bash
# Quando fizer mudanças no pacote
./scripts/release.sh
```

### Gerenciar Repositórios

```bash
# Adicionar/remover Cloud Functions da lista
./scripts/manage-repos.sh
```

### Aprofundar

- [DEPLOY_AUTOMATION.md](../../DEPLOY_AUTOMATION.md) - Guia completo
- [.workflow-diagram.md](.workflow-diagram.md) - Entender o fluxo

---

## 🔑 Secrets Necessários

### No repositório `equidade-data-package`

| Secret | Onde obter | Scopes/Permissões |
|--------|-----------|-------------------|
| `DEPLOY_TRIGGER_TOKEN` | GitHub Settings → Tokens | `repo`, `workflow` |

### Em cada repositório de Cloud Function

| Secret | Onde obter | Scopes/Permissões |
|--------|-----------|-------------------|
| `GCP_SA_KEY` | GCP IAM → Service Accounts | Cloud Functions Developer, Service Account User |

---

## 🔄 Fluxo Típico

```bash
# 1. Fazer mudanças
vim equidade_data_package/some_file.py

# 2. Testar
pytest tests/

# 3. Fazer release (automatizado)
./scripts/release.sh
# → Escolhe versão
# → Roda testes
# → Build
# → Commit + Tag
# → Push
# → Cria release
# → Dispara deploys em todas as Cloud Functions

# 4. Monitorar
gh run list

# 5. ✅ Done!
```

---

## 📊 Status Visual

```
┌─────────────────────────────────────────┐
│  equidade-data-package                  │
│  Release v0.2.3 criado                  │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
┌────────┐┌────────┐┌────────┐
│Function││Function││Function│
│   1    ││   2    ││   3    │
│   ✅   ││   ✅   ││   ✅   │
└────────┘└────────┘└────────┘
```

---

## 🎓 Ordem de Leitura Recomendada

1. 🚀 **QUICKSTART.md** - Começar aqui (5 min)
2. 📚 **DEPLOY_AUTOMATION.md** - Quando precisar de detalhes
3. 📊 **.workflow-diagram.md** - Para entender o fluxo visualmente
4. 📄 **scripts/README.md** - Para usar os scripts efetivamente

---

## 🆘 Precisa de Ajuda?

1. **Setup**: [QUICKSTART.md](../../QUICKSTART.md)
2. **Troubleshooting**: [DEPLOY_AUTOMATION.md - Seção Troubleshooting](../../DEPLOY_AUTOMATION.md#-troubleshooting)
3. **Scripts**: [scripts/README.md](../../scripts/README.md#-troubleshooting)
4. **Entender fluxo**: [.workflow-diagram.md](.workflow-diagram.md)

---

**Criado em**: 2024-01-08
**Versão do sistema**: 1.0.0
