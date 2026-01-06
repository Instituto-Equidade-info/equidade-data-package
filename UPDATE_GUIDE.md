# Guia de Atualização - v0.2.1

## 🎯 Problema Resolvido

**Erro anterior nas Cloud Functions:**
```
❌ Erro ao criar tabela: 400 POST ... projects/None/datasets/access_logs/tables
Invalid resource name projects/None; Project id: None
```

**Causa raiz:** O `EnvLoader` não estava encontrando o arquivo `env-shared.yaml` porque o caminho estava sendo calculado incorretamente.

## 🔧 Correção Aplicada

**Arquivo alterado:** `equidade_data_package/config/env_loader.py` (linha 321)

**Mudança:**
```python
# ANTES (❌ ERRADO)
package_dir = Path(__file__).parent.parent.parent
# Isso resulta em: /caminho/projeto/ (projeto root)

# DEPOIS (✅ CORRETO)  
package_dir = Path(__file__).parent.parent
# Isso resulta em: /caminho/projeto/equidade_data_package/ (package root)
```

## 📦 Como Atualizar suas Cloud Functions

### Opção 1: Via requirements.txt (Recomendado)

1. Atualizar `requirements.txt`:
```txt
equidade-data-package==0.2.1
```

2. Fazer deploy:
```bash
gcloud functions deploy access-processor \
  --source . \
  --runtime python311 \
  --trigger-http
```

### Opção 2: Via pip direto

```bash
pip install --upgrade equidade-data-package==0.2.1
```

### Opção 3: Build local e deploy

```bash
# No diretório do pacote
python3 -m build --wheel

# Copiar wheel para sua Cloud Function
cp dist/equidade_data_package-0.2.1-py3-none-any.whl /path/to/cloud-function/

# No requirements.txt da Cloud Function
./equidade_data_package-0.2.1-py3-none-any.whl
```

## ✅ Verificação

Após o deploy, verifique os logs da Cloud Function:

**✅ Sucesso (esperado):**
```
✅ Usando project_id do EnvLoader: equidade
✅ BigQuery Logger inicializado - Event-Based (sem updates)
   Project: equidade
   Dataset: access_logs
```

**❌ Ainda com problema (não esperado):**
```
❌ AVISO: GCP_PROJECT_ID não encontrado no EnvLoader
⚠️ Usando project_id hardcoded: equidade
```

Se ainda aparecer o aviso, verifique:
1. A versão instalada: `pip show equidade-data-package` deve mostrar `Version: 0.2.1`
2. Se o arquivo YAML está no pacote: `python3 -c "import equidade_data_package.config; print(equidade_data_package.config.__file__)"`

## 🔍 Debugging

Se precisar debugar o carregamento:

```python
from equidade_data_package.config import load_env

env = load_env("access-processor", project_id="equidade", auto_set=True)

# Debug info
print(f"YAML Path: {env._yaml_path}")
print(f"YAML Exists: {env._yaml_path.exists()}")
print(f"Vars loaded: {len(env._env_vars)}")
print(f"GCP_PROJECT_ID: {env.get('GCP_PROJECT_ID')}")
```

## 📋 Checklist de Migração

- [ ] Atualizar versão do pacote para 0.2.1
- [ ] Deploy da Cloud Function
- [ ] Verificar logs para confirmar carregamento do YAML
- [ ] Testar funcionalidade (criar request, enviar envelope, etc.)
- [ ] Remover qualquer workaround temporário que estava usando

## 🚀 Próximos Passos

Após confirmar que funciona em uma Cloud Function:

1. Atualizar todas as outras Cloud Functions que usam o pacote
2. Remover fallbacks hardcoded (se existirem)
3. Opcionalmente: adicionar validação `env.validate()` para garantir que todas as vars necessárias foram carregadas

## 💡 Dica

Para evitar problemas futuros, sempre use:

```python
env = load_env(
    function_name="sua-funcao",
    project_id="equidade",  # ✅ Sempre passar explicitamente
    auto_set=True
)
```

Mesmo que agora o YAML carregue corretamente, passar `project_id` explicitamente garante que o Secret Manager funcione corretamente.
