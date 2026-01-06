# Setup de Secrets no GCP Secret Manager

Este documento explica como configurar os secrets no GCP Secret Manager para uso com o `EnvLoader`.

## 📋 Pré-requisitos

1. Conta GCP com permissões para criar secrets
2. `gcloud` CLI instalado e autenticado
3. Secret Manager API habilitada no projeto

## 🔧 Habilitar Secret Manager API

```bash
# Habilitar API
gcloud services enable secretmanager.googleapis.com --project=equidade

# Verificar status
gcloud services list --enabled --filter="name:secretmanager" --project=equidade
```

## 🔐 Lista de Secrets Necessários

### Secrets Compartilhados (usados por múltiplas funções)

| Secret Name | Variável de Ambiente | Usado Por |
|-------------|---------------------|-----------|
| `aws-access-key-id` | `AWS_ACCESS_KEY_ID` | etl-surveycto-function, check-s3-files, iu-process-dataset-updates, consistency_checker_function |
| `aws-secret-access-key` | `AWS_SECRET_ACCESS_KEY` | etl-surveycto-function, check-s3-files, iu-process-dataset-updates, consistency_checker_function |
| `docusign-client-secret` | `DOCUSIGN_CLIENT_SECRET` | access-processor, access-manager, access-revocation, slack-notifier, docusign-webhook |
| `docusign-integration-key` | `DOCUSIGN_INTEGRATION_KEY` | access-processor, access-manager, access-revocation, slack-notifier, docusign-webhook |
| `gmail-token-data` | `GMAIL_TOKEN_DATA` | access-processor, access-manager, access-revocation, slack-notifier, docusign-webhook |
| `google-service-account-key` | `GOOGLE_SERVICE_ACCOUNT_KEY` | access-processor, access-manager, access-revocation, slack-notifier, docusign-webhook |
| `slack-bot-token-access` | `SLACK_BOT_TOKEN_ACCESS` | access-processor, access-manager, access-revocation, slack-notifier, docusign-webhook |
| `strapi-token` | `STRAPI_TOKEN` | access-processor, access-manager, access-revocation, slack-notifier, docusign-webhook |
| `surveycto-password` | `SURVEYCTO_PASSWORD` | etl-surveycto-function, gf_raw_data_function, pi_raw_data_function |
| `token-github` | `TOKEN_GITHUB` | check-and-trigger-deploy, process-table-update |
| `authorization-key-blip` | `AUTHORIZATION_KEY_BLIP` | gf_raw_data_function, pi_raw_data_function, consistency_checker_function |

### Secrets Específicos por Função

| Secret Name | Variável de Ambiente | Usado Por |
|-------------|---------------------|-----------|
| `credentials-equidade-download-data` | `CREDENTIALS` | equidade-download-data |
| `credentials-pi-raw-data-function` | `CREDENTIALS` | pi_raw_data_function |
| `slack-bot-token-equidade-download-data` | `SLACK_BOT_TOKEN` | equidade-download-data, check-s3-files, iu-process-dataset-updates, gf_raw_data_function, gf_treatment_data_function, process-dataset-updates, pi_treatment_data_function, pi_raw_data_function |
| `slack-bot-token-consistency-checker-function` | `SLACK_BOT_TOKEN` | consistency_checker_function |

**Nota:** Para `CREDENTIALS` e `SLACK_BOT_TOKEN`, cada função pode ter seu próprio secret específico.

## 📝 Criando Secrets

### Opção 1: Via gcloud CLI (Recomendado)

#### Secrets de Texto Simples

```bash
# AWS Credentials
echo -n "AKIA..." | gcloud secrets create aws-access-key-id \
    --data-file=- \
    --replication-policy="user-managed" \
    --locations="southamerica-east1" \
    --project=equidade

echo -n "oPXv..." | gcloud secrets create aws-secret-access-key \
    --data-file=- \
    --replication-policy="user-managed" \
    --locations="southamerica-east1" \
    --project=equidade

# DocuSign
echo -n "0db5..." | gcloud secrets create docusign-integration-key \
    --data-file=- \
    --replication-policy="user-managed" \
    --locations="southamerica-east1" \
    --project=equidade

echo -n "6710..." | gcloud secrets create docusign-client-secret \
    --data-file=- \
    --replication-policy="user-managed" \
    --locations="southamerica-east1" \
    --project=equidade

# SurveyCTO
echo -n "Dado..." | gcloud secrets create surveycto-password \
    --data-file=- \
    --replication-policy="user-managed" \
    --locations="southamerica-east1" \
    --project=equidade

# GitHub
echo -n "ghp_..." | gcloud secrets create token-github \
    --data-file=- \
    --replication-policy="user-managed" \
    --locations="southamerica-east1" \
    --project=equidade

# Blip Authorization
echo -n "Key ..." | gcloud secrets create authorization-key-blip \
    --data-file=- \
    --replication-policy="user-managed" \
    --locations="southamerica-east1" \
    --project=equidade

# Strapi
echo -n "1403..." | gcloud secrets create strapi-token \
    --data-file=- \
    --replication-policy="user-managed" \
    --locations="southamerica-east1" \
    --project=equidade

# Slack Tokens (específicos por função)
echo -n "xoxb..." | gcloud secrets create slack-bot-token-equidade-download-data \
    --data-file=- \
    --replication-policy="user-managed" \
    --locations="southamerica-east1" \
    --project=equidade

echo -n "xoxb..." | gcloud secrets create slack-bot-token-consistency-checker-function \
    --data-file=- \
    --replication-policy="user-managed" \
    --locations="southamerica-east1" \
    --project=equidade

echo -n "xoxb..." | gcloud secrets create slack-bot-token-access \
    --data-file=- \
    --replication-policy="user-managed" \
    --locations="southamerica-east1" \
    --project=equidade
```

#### Secrets JSON (de arquivo)

```bash
# Google Service Account Key
gcloud secrets create google-service-account-key \
    --data-file=/path/to/service-account-key.json \
    --replication-policy="user-managed" \
    --locations="southamerica-east1" \
    --project=equidade

# Gmail Token Data
gcloud secrets create gmail-token-data \
    --data-file=/path/to/gmail-token.json \
    --replication-policy="user-managed" \
    --locations="southamerica-east1" \
    --project=equidade

# Credentials (específicos por função)
gcloud secrets create credentials-equidade-download-data \
    --data-file=/path/to/credentials-download.json \
    --replication-policy="user-managed" \
    --locations="southamerica-east1" \
    --project=equidade

gcloud secrets create credentials-pi-raw-data-function \
    --data-file=/path/to/credentials-pi.json \
    --replication-policy="user-managed" \
    --locations="southamerica-east1" \
    --project=equidade
```

### Opção 2: Via Console GCP

1. Acesse: https://console.cloud.google.com/security/secret-manager
2. Selecione projeto `equidade`
3. Clique em "CREATE SECRET"
4. Preencha:
   - **Name**: `aws-access-key-id` (seguir convenção)
   - **Secret value**: Cole o valor
   - **Replication**: `User-managed`
   - **Locations**: `southamerica-east1`
5. Clique em "CREATE"

### Opção 3: Via Script Automatizado

Crie um arquivo `create_secrets.sh`:

```bash
#!/bin/bash

PROJECT_ID="equidade"
REGION="southamerica-east1"

# Função para criar secret
create_secret() {
    local secret_name=$1
    local secret_value=$2

    echo "Creating secret: $secret_name"

    echo -n "$secret_value" | gcloud secrets create "$secret_name" \
        --data-file=- \
        --replication-policy="user-managed" \
        --locations="$REGION" \
        --project="$PROJECT_ID" 2>&1

    if [ $? -eq 0 ]; then
        echo "✅ Secret $secret_name created successfully"
    else
        echo "❌ Failed to create secret $secret_name"
    fi
}

# Criar secrets (SUBSTITUA OS VALORES REAIS)
create_secret "aws-access-key-id" "AKIA..."
create_secret "aws-secret-access-key" "oPXv..."
create_secret "docusign-integration-key" "0db5..."
create_secret "docusign-client-secret" "6710..."
create_secret "surveycto-password" "Dado..."
create_secret "token-github" "ghp_..."
create_secret "authorization-key-blip" "Key ..."
create_secret "strapi-token" "1403..."
create_secret "slack-bot-token-equidade-download-data" "xoxb..."
create_secret "slack-bot-token-consistency-checker-function" "xoxb..."
create_secret "slack-bot-token-access" "xoxb..."

echo "✅ All secrets created!"
```

Executar:
```bash
chmod +x create_secrets.sh
./create_secrets.sh
```

## 🔄 Atualizar Secrets

```bash
# Atualizar secret com novo valor
echo -n "new-value" | gcloud secrets versions add aws-access-key-id \
    --data-file=- \
    --project=equidade

# Atualizar de arquivo
gcloud secrets versions add google-service-account-key \
    --data-file=/path/to/new-key.json \
    --project=equidade
```

## 🗑️ Deletar Secrets

```bash
# Deletar secret completamente
gcloud secrets delete aws-access-key-id --project=equidade

# Deletar apenas uma versão
gcloud secrets versions destroy 1 --secret=aws-access-key-id --project=equidade
```

## 👁️ Listar e Visualizar Secrets

```bash
# Listar todos os secrets
gcloud secrets list --project=equidade

# Ver versões de um secret
gcloud secrets versions list aws-access-key-id --project=equidade

# Ver valor de um secret (requer permissão)
gcloud secrets versions access latest --secret=aws-access-key-id --project=equidade
```

## 🔒 Permissões

### Dar acesso à Service Account da Cloud Function

```bash
# Service Account padrão: PROJECT_ID@appspot.gserviceaccount.com
SERVICE_ACCOUNT="equidade@appspot.gserviceaccount.com"

# Dar permissão de leitura em um secret específico
gcloud secrets add-iam-policy-binding aws-access-key-id \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --project=equidade

# Dar permissão em todos os secrets (mais fácil)
for SECRET in $(gcloud secrets list --project=equidade --format="value(name)")
do
    gcloud secrets add-iam-policy-binding $SECRET \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" \
        --project=equidade
done
```

## ✅ Verificar Setup

Script para validar que todos os secrets existem:

```bash
#!/bin/bash

PROJECT_ID="equidade"

# Lista de secrets esperados
EXPECTED_SECRETS=(
    "aws-access-key-id"
    "aws-secret-access-key"
    "docusign-integration-key"
    "docusign-client-secret"
    "gmail-token-data"
    "google-service-account-key"
    "slack-bot-token-access"
    "strapi-token"
    "surveycto-password"
    "token-github"
    "authorization-key-blip"
    "credentials-equidade-download-data"
    "credentials-pi-raw-data-function"
    "slack-bot-token-equidade-download-data"
    "slack-bot-token-consistency-checker-function"
)

echo "🔍 Verificando secrets no projeto $PROJECT_ID..."
echo ""

# Obter lista de secrets existentes
EXISTING_SECRETS=$(gcloud secrets list --project=$PROJECT_ID --format="value(name)")

MISSING_COUNT=0
for SECRET in "${EXPECTED_SECRETS[@]}"
do
    if echo "$EXISTING_SECRETS" | grep -q "^$SECRET$"; then
        echo "✅ $SECRET"
    else
        echo "❌ $SECRET - MISSING!"
        MISSING_COUNT=$((MISSING_COUNT + 1))
    fi
done

echo ""
if [ $MISSING_COUNT -eq 0 ]; then
    echo "✅ Todos os secrets estão configurados!"
else
    echo "❌ $MISSING_COUNT secrets faltando"
fi
```

Salve como `verify_secrets.sh` e execute:
```bash
chmod +x verify_secrets.sh
./verify_secrets.sh
```

## 🧪 Testar Localmente

Para testar o acesso aos secrets localmente:

```python
from google.cloud import secretmanager

def test_secret(project_id: str, secret_name: str):
    """Testa acesso a um secret."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"

    try:
        response = client.access_secret_version(request={"name": name})
        value = response.payload.data.decode("UTF-8")
        print(f"✅ Secret '{secret_name}': {value[:20]}..." )
        return True
    except Exception as e:
        print(f"❌ Secret '{secret_name}': {e}")
        return False

# Testar
test_secret("equidade", "aws-access-key-id")
test_secret("equidade", "slack-bot-token-equidade-download-data")
```

## 📚 Boas Práticas

1. **Usar user-managed replication**
   - Controle sobre localização dos dados
   - Melhor performance (região próxima)
   - Compliance com LGPD

2. **Nunca commitar secrets no Git**
   - Adicionar ao `.gitignore`
   - Usar variáveis de ambiente locais

3. **Rotacionar secrets regularmente**
   - Tokens: a cada 90 dias
   - Passwords: a cada 180 dias
   - Service Account Keys: anualmente

4. **Monitorar acesso**
   ```bash
   # Ver logs de acesso a secrets
   gcloud logging read "resource.type=secret_manager" \
       --project=equidade \
       --limit=50
   ```

5. **Usar versionamento**
   - Nunca deletar versões antigas imediatamente
   - Manter últimas 3 versões
   - Facilita rollback

## 🔧 Troubleshooting

### "Permission denied" ao criar secret

**Problema:** Não tem permissão.

**Solução:**
```bash
# Adicionar role de Admin do Secret Manager
gcloud projects add-iam-policy-binding equidade \
    --member="user:seu-email@example.com" \
    --role="roles/secretmanager.admin"
```

### "Secret already exists"

**Problema:** Secret já foi criado.

**Solução:**
```bash
# Atualizar ao invés de criar
echo -n "new-value" | gcloud secrets versions add secret-name \
    --data-file=- \
    --project=equidade
```

### Cloud Function não consegue acessar secret

**Problema:** Service Account sem permissão.

**Solução:**
```bash
# Dar permissão à Service Account
gcloud secrets add-iam-policy-binding secret-name \
    --member="serviceAccount:PROJECT_ID@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=equidade
```

## 📞 Suporte

Dúvidas ou problemas? Entre em contato com o time Equidade.

---

**Última atualização:** 2026-01-06
