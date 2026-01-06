# Examples - EnvLoader Usage

Esta pasta contém exemplos práticos de uso do `EnvLoader` em diferentes cenários.

## 📁 Arquivos

### [cloud_function_example.py](./cloud_function_example.py)
**Exemplos de integração com Cloud Functions**

Mostra 3 formas de usar o EnvLoader em Cloud Functions:
1. **Setup Simples** - Para a maioria dos casos
2. **Setup Avançado** - Com configuração customizada
3. **Setup Minimalista** - Apenas carregar e usar `os.environ`

**Quando usar:** Implementação em produção de Cloud Functions

### [local_development.py](./local_development.py)
**Desenvolvimento local sem GCP**

6 exemplos de desenvolvimento local:
1. YAML only (sem Secret Manager)
2. Mock secrets com env vars
3. Uso de `.env` file
4. Validação parcial
5. Carregamento seletivo
6. GCP emulators

**Quando usar:** Desenvolvimento local, testes, CI/CD

### [migration_guide.md](./migration_guide.md)
**Guia completo de migração**

- Comparação antes/depois
- Passo a passo de migração
- Padrões comuns
- Troubleshooting
- Checklist de migração

**Quando usar:** Migrando código existente para usar EnvLoader

## 🚀 Quick Start

### Cloud Function Básica

```python
from equidade_data_package.config import load_env

env = load_env("equidade-download-data", auto_set=True)

# Usar variáveis
slack_token = env.get("SLACK_BOT_TOKEN")
credentials = env.get_json("CREDENTIALS")
```

### Desenvolvimento Local

```python
from equidade_data_package.config import EnvLoader, EnvConfig

config = EnvConfig(
    function_name="my-function",
    use_secret_manager=False  # Desabilitar para dev local
)
env = EnvLoader(config)
```

## 📖 Documentação Completa

- [QUICKSTART.md](../QUICKSTART.md) - Início rápido
- [TECHNICAL_REFERENCE.md](../TECHNICAL_REFERENCE.md) - Referência técnica
- [SETUP_SECRETS.md](../SETUP_SECRETS.md) - Configuração de secrets no GCP
- [README.md](../README.md) - Documentação do pacote completo

## 🧪 Testando os Exemplos

### 1. Instalar o pacote

```bash
pip install git+https://github.com/your-org/equidade-data-package.git
```

### 2. Executar exemplo local

```bash
cd examples
python local_development.py
```

### 3. Executar com Cloud Function (localmente)

```bash
# Instalar Functions Framework
pip install functions-framework

# Rodar função
functions-framework --target=main --source=cloud_function_example.py
```

### 4. Testar com curl

```bash
curl http://localhost:8080
```

## 🔧 Customizar Exemplos

Todos os exemplos podem ser customizados para seu caso de uso:

### Trocar nome da função

```python
# De:
env = load_env("equidade-download-data")

# Para:
env = load_env("my-custom-function")
```

### Adicionar validação customizada

```python
env = load_env("my-function")

# Validar apenas variáveis específicas
required = ["VAR1", "VAR2", "VAR3"]
is_valid, missing = env.validate(required_vars=required)

if not is_valid:
    raise EnvironmentError(f"Missing: {missing}")
```

### Usar projeto GCP diferente

```python
env = load_env(
    "my-function",
    project_id="my-other-project",
    region="us-central1"
)
```

## 💡 Padrões Recomendados

### Pattern 1: Setup no Início da Função

```python
import functions_framework
from equidade_data_package.config import load_env

@functions_framework.http
def main(request):
    # Carregar env vars no início
    env = load_env("my-function", auto_set=True)

    # Validar
    is_valid, missing = env.validate()
    if not is_valid:
        return {"error": f"Config error: {missing}"}, 500

    # Resto da lógica...
```

### Pattern 2: Lazy Loading

```python
from equidade_data_package.config import load_env

_env = None

def get_env():
    """Singleton para EnvLoader."""
    global _env
    if _env is None:
        _env = load_env("my-function", auto_set=True)
    return _env

# Usar
env = get_env()
token = env.get("SLACK_BOT_TOKEN")
```

### Pattern 3: Type-Safe Config Class

```python
from dataclasses import dataclass
from equidade_data_package.config import load_env

@dataclass
class AppConfig:
    """Configuração type-safe da aplicação."""
    slack_token: str
    credentials: dict
    max_retries: int
    debug: bool

    @classmethod
    def from_env(cls, function_name: str):
        env = load_env(function_name)
        return cls(
            slack_token=env.get("SLACK_BOT_TOKEN"),
            credentials=env.get_json("CREDENTIALS"),
            max_retries=env.get_int("MAX_RETRIES", 3),
            debug=env.get_bool("DEBUG", False)
        )

# Usar
config = AppConfig.from_env("my-function")
print(config.slack_token)  # Type-safe!
```

## ❓ FAQ

### Como testar localmente sem GCP credentials?

Use `use_secret_manager=False`:
```python
config = EnvConfig(
    function_name="my-function",
    use_secret_manager=False
)
env = EnvLoader(config)
```

### Como mock secrets em testes?

Use environment variables:
```python
import os
os.environ["SLACK_BOT_TOKEN"] = "mock-token"
os.environ["CREDENTIALS"] = '{"type":"mock"}'

env = load_env("my-function", use_secret_manager=False)
```

### Como adicionar nova variável?

1. Adicionar ao `FUNCTION_ENV_MAP` em `env_loader.py`
2. Se for secret, criar no Secret Manager
3. Se não for secret, adicionar ao `env-shared.yaml`

### Como debugar variáveis não carregadas?

```python
env = load_env("my-function")

# Ver todas carregadas
print(env.get_all())

# Ver status
print(env)  # EnvLoader(function=..., vars_loaded=15, ...)

# Validar
is_valid, missing = env.validate()
print(f"Missing: {missing}")
```

## 🐛 Problemas Comuns

### ImportError: No module named 'equidade_data_package'

**Solução:** Instalar o pacote:
```bash
pip install git+https://github.com/your-org/equidade-data-package.git
```

### ModuleNotFoundError: No module named 'yaml'

**Solução:** Instalar PyYAML:
```bash
pip install pyyaml
```

### Secret not found

**Solução:** Verificar que o secret existe no Secret Manager:
```bash
gcloud secrets list --project=equidade
```

## 📞 Suporte

- **Bug reports:** Abra uma issue no repositório
- **Dúvidas:** Entre em contato com o time Equidade
- **Contribuições:** Pull requests são bem-vindos!

---

**Happy coding!** 🎉
