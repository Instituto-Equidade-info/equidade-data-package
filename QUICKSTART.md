# EnvLoader - Quick Start Guide

## 🎯 O que é?

Sistema centralizado de gerenciamento de variáveis de ambiente para Cloud Functions da Equidade, eliminando duplicação e facilitando manutenção.

## 📦 Instalação

Adicione ao seu `requirements.txt`:
```txt
git+https://github.com/Instituto-Equidade-info/equidade-data-package.git
```

Ou `pyproject.toml`:
```toml
[project]
dependencies = [
    "equidade-data-package @ git+https://github.com/Instituto-Equidade-info/equidade-data-package.git",
]
```

## 🚀 Uso Rápido (3 linhas)

```python
from equidade_data_package.config import load_env

# 1. Carregar variáveis (substitua pelo nome da sua função)
env = load_env("equidade-download-data", auto_set=True)

# 2. Usar as variáveis
slack_token = env.get("SLACK_BOT_TOKEN")
credentials = env.get_json("CREDENTIALS")  # Parse JSON automático

# 3. Pronto! ✨
```

## 🔧 Como Funciona

O `EnvLoader` busca variáveis em 3 lugares (prioridade decrescente):

1. **Runtime environment** (`os.environ`) - máxima prioridade
2. **Secret Manager** (GCP) - credenciais e tokens sensíveis
3. **YAML config** (`env-shared.yaml`) - valores não sensíveis compartilhados

### Exemplo Completo

```python
import functions_framework
from equidade_data_package.config import load_env

@functions_framework.http
def main(request):
    # Carregar todas as env vars da função
    env = load_env("equidade-download-data", auto_set=True)

    # Validar variáveis obrigatórias
    is_valid, missing = env.validate()
    if not is_valid:
        return {"error": f"Missing: {missing}"}, 500

    # Obter variáveis com conversão de tipo
    credentials = env.get_json("CREDENTIALS")
    slack_token = env.get("SLACK_BOT_TOKEN")
    log_execution = env.get_bool("LOG_EXECUTION_ID", default=False)

    # Sua lógica aqui
    process_data(credentials, slack_token)

    return {"status": "ok"}, 200
```

## 📋 Funções Suportadas

O sistema já conhece as variáveis de ambiente de cada função:

- ✅ `equidade-download-data`
- ✅ `access-processor`, `access-manager`, `access-revocation`
- ✅ `etl-surveycto-function`
- ✅ `check-s3-files`
- ✅ `iu-process-dataset-updates`
- ✅ `consistency_checker_function`
- ✅ `gf_raw_data_function`, `gf_treatment_data_function`
- ✅ `pi_raw_data_function`, `pi_treatment_data_function`
- ✅ `process-dataset-updates`
- ✅ `check-and-trigger-deploy`, `process-table-update`
- ✅ `slack-notifier`, `docusign-webhook`

## 🔑 Métodos Úteis

### `env.get(var_name, default=None)`
Obter variável como string:
```python
api_url = env.get("API_URL", default="https://api.example.com")
```

### `env.get_json(var_name, default=None)`
Parse JSON automático:
```python
credentials = env.get_json("CREDENTIALS")
# Retorna dict, não string
```

### `env.get_int(var_name, default=None)`
Converter para inteiro:
```python
max_retries = env.get_int("MAX_RETRIES", default=3)
```

### `env.get_bool(var_name, default=False)`
Converter para booleano:
```python
debug = env.get_bool("DEBUG", default=False)
# Aceita: true, false, 1, 0, yes, no
```

### `env.validate(required_vars=None)`
Validar variáveis obrigatórias:
```python
is_valid, missing = env.validate()
if not is_valid:
    raise ValueError(f"Missing: {missing}")
```

### `env.set_environment()`
Aplicar ao `os.environ`:
```python
env.set_environment()
# Agora todas as libs podem usar os.environ normalmente
```

## 🏗️ Estrutura

```
equidade-data-package/
├── equidade_data_package/
│   ├── config/
│   │   ├── __init__.py
│   │   └── env_loader.py      # ⭐ Sistema principal
│   └── ...
├── env-files/
│   └── env-shared.yaml         # 📝 Valores compartilhados
├── examples/
│   ├── cloud_function_example.py   # 📘 Exemplos práticos
│   ├── local_development.py        # 🔧 Desenvolvimento local
│   └── migration_guide.md          # 📖 Guia de migração
└── README.md
```

## 🔐 Configuração de Secrets

### YAML (Valores Não Sensíveis)

Arquivo: `env-files/env-shared.yaml`

```yaml
# GCP
GCP_PROJECT_ID: equidade
GCP_REGION: southamerica-east1

# BigQuery
BIGQUERY_DATASET_ACCESS: access_logs
BIGQUERY_TABLE_LOGS: access_logs

# DocuSign
DOCUSIGN_ACCOUNT_ID: a6e54a53-8081-482c-941c-a81c38ba8811
DOCUSIGN_BASE_URL: "https://na2.docusign.net"

# ... outros valores públicos
```

### Secret Manager (Valores Sensíveis)

Secrets seguem convenção de nomenclatura:

| Variável de Ambiente | Secret Name (Secret Manager) |
|---------------------|------------------------------|
| `SLACK_BOT_TOKEN` | `slack-bot-token-{function-name}` |
| `AWS_ACCESS_KEY_ID` | `aws-access-key-id` (compartilhado) |
| `CREDENTIALS` | `credentials-{function-name}` |
| `DOCUSIGN_CLIENT_SECRET` | `docusign-client-secret` (compartilhado) |
| `GMAIL_TOKEN_DATA` | `gmail-token-data` (compartilhado) |

**Secrets específicos por função:**
- `credentials-equidade-download-data`
- `credentials-pi-raw-data-function`
- `slack-bot-token-equidade-download-data`
- `slack-bot-token-consistency-checker-function`

**Secrets compartilhados:**
- `aws-access-key-id`
- `aws-secret-access-key`
- `docusign-client-secret`
- `docusign-integration-key`
- `gmail-token-data`
- `google-service-account-key`
- `slack-bot-token-access`
- `strapi-token`
- `surveycto-password`
- `token-github`

## 🧪 Desenvolvimento Local

### Opção 1: Desabilitar Secret Manager

```python
from equidade_data_package.config import EnvLoader, EnvConfig

config = EnvConfig(
    function_name="my-function",
    use_secret_manager=False  # Apenas YAML
)
env = EnvLoader(config)
```

### Opção 2: Usar `.env` File

```bash
# .env
SLACK_BOT_TOKEN=xoxb-local-test-token
CREDENTIALS={"type":"service_account"}
```

```python
from dotenv import load_dotenv
from equidade_data_package.config import load_env

load_dotenv()  # Carrega .env
env = load_env("my-function", use_secret_manager=False)
```

### Opção 3: Environment Variables

```bash
export SLACK_BOT_TOKEN="xoxb-test"
export CREDENTIALS='{"type":"service_account"}'
python main.py
```

## 🔄 Migração de Código Existente

### Antes ❌
```python
import os
import json

CREDENTIALS = json.loads(os.environ["CREDENTIALS"])
SLACK_TOKEN = os.environ["SLACK_BOT_TOKEN"]
DEBUG = os.environ.get("DEBUG", "false") == "true"
```

### Depois ✅
```python
from equidade_data_package.config import load_env

env = load_env("my-function", auto_set=True)
CREDENTIALS = env.get_json("CREDENTIALS")
SLACK_TOKEN = env.get("SLACK_BOT_TOKEN")
DEBUG = env.get_bool("DEBUG", default=False)
```

## 🐛 Troubleshooting

### "Secret not found"
**Problema:** Secret Manager não encontra o secret.

**Solução:** Verifique o nome do secret no GCP Secret Manager. Deve seguir a convenção:
- Específico: `{var-name}-{function-name}`
- Compartilhado: `{var-name}`

### "Missing required env vars"
**Problema:** Variável não está mapeada para a função.

**Solução:** Adicione ao `FUNCTION_ENV_MAP` em `env_loader.py`:
```python
FUNCTION_ENV_MAP = {
    "my-function": [
        "EXISTING_VAR",
        "NEW_VAR",  # Adicionar aqui
    ],
}
```

### "YAML file not found"
**Problema:** Arquivo `env-shared.yaml` não encontrado.

**Solução:**
1. Verifique se existe em `env-files/env-shared.yaml` no pacote
2. Ou especifique caminho customizado:
```python
config = EnvConfig(
    function_name="my-function",
    yaml_path="/custom/path/env-shared.yaml"
)
```

## 📚 Recursos

- [📖 README Completo](./README.md)
- [📘 Exemplos de Uso](./examples/cloud_function_example.py)
- [🔧 Desenvolvimento Local](./examples/local_development.py)
- [📖 Guia de Migração](./examples/migration_guide.md)
- [🔍 Código Fonte](./equidade_data_package/config/env_loader.py)

## 💡 Próximos Passos

1. ✅ Adicionar o pacote às dependências do seu projeto
2. ✅ Substituir código manual por `load_env()`
3. ✅ Testar localmente
4. ✅ Deploy e validar

---

**Dúvidas?** Entre em contato com o time Equidade!
