# EnvLoader - Referência Técnica

## Arquitetura

### Fluxo de Carregamento

```
┌─────────────────────────────────────────────────────────────┐
│                      EnvLoader.__init__()                    │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       _load_all()                            │
├─────────────────────────────────────────────────────────────┤
│  1. _load_from_yaml()                                       │
│     └─> Lê env-shared.yaml                                  │
│     └─> Filtra variáveis não-sensíveis                      │
│                                                              │
│  2. _load_from_secrets()                                    │
│     └─> Busca variáveis sensíveis no Secret Manager         │
│     └─> Cache de secrets (opcional)                         │
│                                                              │
│  3. Runtime environment (os.environ)                        │
│     └─> Prioridade máxima no get()                          │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               Variáveis carregadas em _env_vars             │
└─────────────────────────────────────────────────────────────┘
```

### Prioridade de Variáveis

```python
def get(var_name: str) -> str:
    # 1. Runtime (os.environ) - MAIOR PRIORIDADE
    if var_name in os.environ:
        return os.environ[var_name]

    # 2. Loaded values (Secret Manager ou YAML)
    if var_name in self._env_vars:
        return self._env_vars[var_name]

    # 3. Default value
    return default
```

## Classes e Tipos

### EnvConfig

```python
@dataclass
class EnvConfig:
    """Configuração do EnvLoader."""

    function_name: str               # Nome da Cloud Function
    project_id: str = "equidade"    # GCP Project ID
    region: str = "southamerica-east1"
    yaml_path: Optional[str] = None  # Caminho customizado para YAML
    use_secret_manager: bool = True  # Habilitar Secret Manager
    cache_secrets: bool = True       # Cache de secrets
```

**Uso:**
```python
config = EnvConfig(
    function_name="my-function",
    project_id="my-project",
    yaml_path="/custom/path/env.yaml",
    use_secret_manager=True,
    cache_secrets=True
)
```

### EnvLoader

```python
class EnvLoader:
    """Carregador de variáveis de ambiente."""

    # Mapeamento função → variáveis necessárias
    FUNCTION_ENV_MAP: Dict[str, List[str]]

    # Mapeamento variável → nome do secret
    SECRET_NAME_MAP: Dict[str, str]

    def __init__(config: EnvConfig)
    def get(var_name: str, default=None) -> Optional[str]
    def get_json(var_name: str, default=None) -> Optional[Dict]
    def get_int(var_name: str, default=None) -> Optional[int]
    def get_bool(var_name: str, default=False) -> bool
    def set_environment() -> None
    def validate(required_vars=None) -> Tuple[bool, List[str]]
    def get_all() -> Dict[str, str]
```

## Mapeamentos

### FUNCTION_ENV_MAP

Mapeia cada Cloud Function para suas variáveis necessárias:

```python
FUNCTION_ENV_MAP = {
    "equidade-download-data": [
        "CREDENTIALS",
        "LOG_EXECUTION_ID",
        "SLACK_BOT_TOKEN",
    ],
    "access-processor": [
        "BIGQUERY_DATASET_ACCESS",
        "BIGQUERY_TABLE_LOGS",
        # ... todas as variáveis da função
    ],
    # ... outras funções
}
```

**Para adicionar nova função:**

```python
FUNCTION_ENV_MAP = {
    # ... existentes
    "my-new-function": [
        "VAR1",
        "VAR2",
        "VAR3",
    ],
}
```

### SECRET_NAME_MAP

Mapeia variáveis de ambiente para nomes de secrets no Secret Manager:

```python
SECRET_NAME_MAP = {
    # Secrets compartilhados (sem sufixo)
    "AWS_ACCESS_KEY_ID": "aws-access-key-id",
    "AWS_SECRET_ACCESS_KEY": "aws-secret-access-key",
    "DOCUSIGN_CLIENT_SECRET": "docusign-client-secret",

    # Secrets específicos (com sufixo)
    "CREDENTIALS_equidade-download-data": "credentials-equidade-download-data",
    "CREDENTIALS_pi_raw_data_function": "credentials-pi-raw-data-function",
    "SLACK_BOT_TOKEN_equidade-download-data": "slack-bot-token-equidade-download-data",
}
```

**Lógica de resolução:**

1. Tentar `{VAR_NAME}_{function_name}` (específico)
2. Tentar `{VAR_NAME}` (compartilhado)
3. Fallback: `{var_name.lower().replace('_', '-')}`

**Para adicionar novo secret:**

```python
SECRET_NAME_MAP = {
    # ... existentes
    "MY_NEW_SECRET": "my-new-secret",  # Compartilhado
    "MY_NEW_SECRET_my-function": "my-new-secret-my-function",  # Específico
}
```

## Detecção de Secrets

### _is_secret_var()

Identifica se uma variável é sensível e deve vir do Secret Manager:

```python
def _is_secret_var(var_name: str) -> bool:
    """Retorna True se variável é sensível."""
    secret_prefixes = [
        "CREDENTIALS",
        "TOKEN",
        "KEY",
        "SECRET",
        "PASSWORD",
        "AUTHORIZATION",
        "AUTORIZATION",  # Typo histórico
    ]
    return any(var_name.startswith(prefix) for prefix in secret_prefixes)
```

**Exemplos:**
- `CREDENTIALS` → True (secret)
- `SLACK_BOT_TOKEN` → True (secret)
- `AWS_ACCESS_KEY_ID` → True (secret)
- `GCP_PROJECT_ID` → False (YAML)
- `BIGQUERY_DATASET_ACCESS` → False (YAML)

## Parsing de Tipos

### get_json()

```python
def get_json(var_name: str, default=None) -> Optional[Dict]:
    """Parse JSON com tratamento de erros."""
    value = self.get(var_name)
    if value is None:
        return default

    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse JSON for '{var_name}': {e}")
        return default
```

**Uso:**
```python
# String JSON no Secret Manager ou env var
credentials = env.get_json("CREDENTIALS")
# Retorna: {"type": "service_account", "project_id": "equidade"}
```

### get_int()

```python
def get_int(var_name: str, default=None) -> Optional[int]:
    """Converte para inteiro."""
    value = self.get(var_name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError as e:
        print(f"⚠️  Failed to parse int for '{var_name}': {e}")
        return default
```

### get_bool()

```python
def get_bool(var_name: str, default=False) -> bool:
    """Converte para booleano."""
    value = self.get(var_name)
    if value is None:
        return default

    return value.lower() in ("true", "1", "yes", "on")
```

**Valores aceitos:**
- `True`: `"true"`, `"1"`, `"yes"`, `"on"` (case-insensitive)
- `False`: qualquer outro valor

## Validação

### validate()

```python
def validate(required_vars: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
    """
    Valida variáveis obrigatórias.

    Args:
        required_vars: Lista de variáveis obrigatórias.
                      Se None, usa FUNCTION_ENV_MAP.

    Returns:
        (is_valid, missing_vars)
    """
    if required_vars is None:
        required_vars = self.FUNCTION_ENV_MAP.get(self.config.function_name, [])

    missing = []
    for var_name in required_vars:
        if self.get(var_name) is None:
            missing.append(var_name)

    return len(missing) == 0, missing
```

**Exemplo de uso:**

```python
# Validar todas as variáveis da função
is_valid, missing = env.validate()
if not is_valid:
    raise EnvironmentError(f"Missing: {', '.join(missing)}")

# Validar subset customizado
custom_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
is_valid, missing = env.validate(required_vars=custom_vars)
```

## Cache de Secrets

### Comportamento

```python
if self.config.cache_secrets and secret_name in self._secrets_cache:
    secret_value = self._secrets_cache[secret_name]
else:
    secret_value = self._fetch_secret(secret_name)
    if secret_value and self.config.cache_secrets:
        self._secrets_cache[secret_name] = secret_value
```

**Benefícios:**
- ✅ Reduz chamadas ao Secret Manager
- ✅ Melhora performance
- ✅ Diminui latência

**Considerações:**
- Cache persiste durante vida do objeto `EnvLoader`
- Cada instância tem seu próprio cache
- Secrets não são recarregados automaticamente

## Integração com Secret Manager

### _fetch_secret()

```python
def _fetch_secret(secret_name: str) -> Optional[str]:
    """Busca secret do GCP Secret Manager."""
    try:
        name = f"projects/{self.config.project_id}/secrets/{secret_name}/versions/latest"
        response = self._secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"⚠️  Failed to fetch secret '{secret_name}': {e}")
        return None
```

**Formato do nome:**
```
projects/{project_id}/secrets/{secret_name}/versions/latest
```

**Exemplo:**
```
projects/equidade/secrets/slack-bot-token-equidade-download-data/versions/latest
```

## YAML Configuration

### Formato do env-shared.yaml

```yaml
# Comentários são suportados

# === GCP ===
GCP_PROJECT_ID: equidade
GCP_REGION: southamerica-east1

# === AWS ===
AWS_REGION: us-east-1

# === BigQuery ===
BIGQUERY_DATASET_ACCESS: access_logs
BIGQUERY_TABLE_LOGS: access_logs

# === Valores numéricos ===
MAX_WAITING_TIME: 3600
MIN_UPDATES_TO_TRIGGER: 3

# === Booleanos ===
LOG_EXECUTION_ID: true
DEBUG: false

# === URLs (usar aspas) ===
DOCUSIGN_BASE_URL: "https://na2.docusign.net"
STRAPI_BASE_URL: "http://cms.equidade.info"
```

### Loading do YAML

```python
def _load_from_yaml(self):
    """Carrega variáveis do YAML."""
    with open(self._yaml_path, "r", encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f) or {}

    required_vars = self.FUNCTION_ENV_MAP.get(self.config.function_name, [])

    for var_name in required_vars:
        # Pular secrets
        if self._is_secret_var(var_name):
            continue

        # Buscar no YAML
        if var_name in yaml_data:
            value = yaml_data[var_name]
            self._env_vars[var_name] = str(value) if not isinstance(value, str) else value
```

## Funções de Conveniência

### load_env()

```python
def load_env(
    function_name: str,
    project_id: str = "equidade",
    auto_set: bool = True,
    **kwargs
) -> EnvLoader:
    """
    Setup rápido.

    Args:
        function_name: Nome da Cloud Function
        project_id: GCP Project ID
        auto_set: Aplicar automaticamente a os.environ
        **kwargs: Outros argumentos para EnvConfig

    Returns:
        EnvLoader configurado
    """
    config = EnvConfig(function_name=function_name, project_id=project_id, **kwargs)
    loader = EnvLoader(config)

    if auto_set:
        loader.set_environment()

    return loader
```

**Uso:**
```python
# Forma mais simples
env = load_env("my-function")

# Com configurações customizadas
env = load_env(
    "my-function",
    project_id="my-project",
    auto_set=False,
    use_secret_manager=False
)
```

## Tratamento de Erros

### Estratégia Fail-Safe

O `EnvLoader` nunca falha ao carregar, apenas avisa sobre problemas:

```python
# YAML não encontrado
if not self._yaml_path.exists():
    print(f"⚠️  YAML file not found: {self._yaml_path}")
    print("   Continuing with Secret Manager only...")
    return  # Continua sem YAML

# Erro ao buscar secret
try:
    response = self._secret_client.access_secret_version(...)
    return response.payload.data.decode("UTF-8")
except Exception as e:
    print(f"⚠️  Failed to fetch secret '{secret_name}': {e}")
    return None  # Retorna None, não falha

# Erro ao parsear JSON
try:
    return json.loads(value)
except json.JSONDecodeError as e:
    print(f"⚠️  Failed to parse JSON for '{var_name}': {e}")
    return default  # Usa default
```

**Vantagens:**
- ✅ Função continua rodando mesmo com problemas parciais
- ✅ Warnings claros no log para debug
- ✅ Validação explícita via `validate()` quando necessário

## Performance

### Métricas Estimadas

| Operação | Tempo (ms) | Observações |
|----------|------------|-------------|
| Load YAML | ~5-10 ms | Leitura de arquivo + parse |
| Fetch Secret (sem cache) | ~50-100 ms | Chamada ao Secret Manager |
| Fetch Secret (com cache) | ~0.001 ms | Leitura de dict em memória |
| get() runtime env | ~0.001 ms | Leitura de os.environ |
| get() loaded var | ~0.001 ms | Leitura de dict |
| get_json() | ~0.1-1 ms | Parse JSON |

### Otimizações

1. **Cache de Secrets**: Habilite para reduzir latência
   ```python
   config = EnvConfig(cache_secrets=True)
   ```

2. **auto_set=True**: Carrega uma vez, usa `os.environ` depois
   ```python
   env = load_env("my-function", auto_set=True)
   # Depois use os.environ diretamente
   token = os.environ["SLACK_BOT_TOKEN"]
   ```

3. **Desabilitar Secret Manager localmente**:
   ```python
   config = EnvConfig(use_secret_manager=False)  # Dev local
   ```

## Debugging

### Informações de Debug

```python
# Ver info do loader
print(env)
# Output: EnvLoader(function=my-function, vars_loaded=15, secrets_cached=8)

# Ver todas as variáveis carregadas
all_vars = env.get_all()
print(f"Loaded {len(all_vars)} variables:")
for key, value in all_vars.items():
    print(f"  {key}: {value[:20]}...")  # Primeiros 20 chars

# Validar e ver missing
is_valid, missing = env.validate()
print(f"Valid: {is_valid}")
print(f"Missing: {missing}")
```

### Logs Úteis

O `EnvLoader` emite warnings automáticos:

```
⚠️  YAML file not found: /path/to/env-shared.yaml
   Continuing with Secret Manager only...

⚠️  Failed to fetch secret 'my-secret': 404 Secret not found

⚠️  Failed to parse JSON for 'CREDENTIALS': Expecting value: line 1 column 1 (char 0)

⚠️  Failed to parse int for 'MAX_RETRIES': invalid literal for int() with base 10: 'abc'
```

## Testes

### Unit Tests

```python
import pytest
from equidade_data_package.config import EnvLoader, EnvConfig

def test_load_yaml_only():
    """Teste carregamento apenas do YAML."""
    config = EnvConfig(
        function_name="equidade-download-data",
        use_secret_manager=False
    )
    env = EnvLoader(config)

    # Verificar variáveis do YAML
    assert env.get("GCP_PROJECT_ID") == "equidade"
    assert env.get("GCP_REGION") == "southamerica-east1"

def test_get_with_default():
    """Teste default values."""
    config = EnvConfig(function_name="test", use_secret_manager=False)
    env = EnvLoader(config)

    assert env.get("NONEXISTENT", "default") == "default"
    assert env.get_int("NONEXISTENT", 42) == 42
    assert env.get_bool("NONEXISTENT", True) is True

def test_validation():
    """Teste validação de variáveis."""
    config = EnvConfig(function_name="equidade-download-data", use_secret_manager=False)
    env = EnvLoader(config)

    required = ["GCP_PROJECT_ID", "GCP_REGION", "NONEXISTENT"]
    is_valid, missing = env.validate(required_vars=required)

    assert not is_valid
    assert "NONEXISTENT" in missing
```

## Extensibilidade

### Adicionar Novo Provider de Secrets

Atualmente suporta apenas GCP Secret Manager, mas pode ser estendido:

```python
class EnvLoader:
    def _load_from_secrets(self):
        """Carregar secrets de múltiplos providers."""
        if self.config.secret_provider == "gcp":
            self._load_from_gcp_secrets()
        elif self.config.secret_provider == "aws":
            self._load_from_aws_secrets()
        elif self.config.secret_provider == "azure":
            self._load_from_azure_secrets()

    def _load_from_aws_secrets(self):
        """Implementar AWS Secrets Manager."""
        # TODO: Implementar
        pass
```

### Adicionar Novo Formato de Config

```python
def _load_from_json(self):
    """Suportar JSON além de YAML."""
    with open(self._json_path, 'r') as f:
        json_data = json.load(f)
    # ... processar
```

## Segurança

### Best Practices

1. **Nunca commitar secrets** no YAML
   ```yaml
   # ❌ ERRADO
   SLACK_BOT_TOKEN: xoxb-1234567890-...

   # ✅ CORRETO (usar Secret Manager)
   # SLACK_BOT_TOKEN carregado do Secret Manager
   ```

2. **Usar Secret Manager para valores sensíveis**
   - Tokens
   - Passwords
   - API Keys
   - Credentials JSON

3. **YAML apenas para valores públicos**
   - Project IDs
   - Regions
   - Dataset names
   - URLs públicas

4. **Validar variáveis críticas**
   ```python
   is_valid, missing = env.validate()
   if not is_valid:
       raise EnvironmentError(f"Critical vars missing: {missing}")
   ```

## Contribuindo

Para adicionar suporte a uma nova Cloud Function:

1. Adicionar ao `FUNCTION_ENV_MAP`:
   ```python
   "my-new-function": [
       "VAR1",
       "VAR2",
   ],
   ```

2. Adicionar secrets ao `SECRET_NAME_MAP` (se necessário):
   ```python
   "MY_SECRET_my-new-function": "my-secret-my-new-function",
   ```

3. Criar secrets no GCP Secret Manager
4. Atualizar documentação
5. Testar

---

**Última atualização:** 2026-01-06
**Versão:** 0.1.0
