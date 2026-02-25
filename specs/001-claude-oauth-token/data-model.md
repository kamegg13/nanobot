# Data Model: Authentification Claude via OAuth Token

**Feature**: 001-claude-oauth-token
**Date**: 2026-02-25

---

## Entités modifiées

### ProviderConfig (modifiée)

Fichier: `nanobot/config/schema.py`

**Champs actuels:**

```
api_key: str = ""
api_base: str | None = None
extra_headers: dict[str, str] | None = None
```

**Nouveau champ ajouté:**

```
oauth_token: str = ""   # Token d'abonnement Claude (Bearer), alternative à api_key
```

**Règles de validation:**

- `oauth_token` et `api_key` sont mutuellement exclusifs pour l'authentification Claude
- `oauth_token` prend priorité sur `api_key` quand les deux sont définis pour le provider Anthropic
- Une chaîne vide `""` signifie "non configuré" (comportement existant)

**Représentation JSON (config persistante):**

```json
{
  "providers": {
    "anthropic": {
      "apiKey": "",
      "oauthToken": "sk-ant-oaut01-..."
    }
  }
}
```

---

## Flux de résolution des credentials

```
CLAUDE_OAUTH_TOKEN (env var)
        │
        ▼ si présent
providers.anthropic.oauth_token (config)
        │
        ▼ sinon
providers.anthropic.api_key (config)
        │
        ▼ sinon
ANTHROPIC_API_KEY (env var, géré par LiteLLM)
        │
        ▼ sinon
→ Erreur : authentification manquante
```

**Priorité des credentials:**

1. `CLAUDE_OAUTH_TOKEN` (variable d'env) → override toujours
2. `providers.anthropic.oauth_token` (config fichier)
3. `providers.anthropic.api_key` (config fichier)
4. `ANTHROPIC_API_KEY` (variable d'env, via LiteLLM)

---

## Transformation vers LiteLLM

Quand un OAuth token est résolu, la transformation appliquée dans `_make_provider()` :

```
oauth_token = "sk-ant-oaut01-..."
                    │
                    ▼
extra_headers["Authorization"] = "Bearer sk-ant-oaut01-..."
api_key = "claude-oauth"   ← placeholder, ignoré par Anthropic
```

LiteLLM reçoit donc :

- `api_key`: `"claude-oauth"` (satisfait la validation interne LiteLLM, ignoré par Anthropic)
- `extra_headers`: `{"Authorization": "Bearer sk-ant-oaut01-..."}` (utilisé par Anthropic pour auth)
