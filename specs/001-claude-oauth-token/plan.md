# Implementation Plan: Authentification Claude via OAuth Token

**Branch**: `001-claude-oauth-token` | **Date**: 2026-02-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-claude-oauth-token/spec.md`

## Summary

Permettre aux utilisateurs ayant un abonnement Claude (Claude Code, Claude Pro) d'utiliser nanobot sans clé API Anthropic, en configurant un token OAuth via `CLAUDE_OAUTH_TOKEN` (variable d'env) ou `providers.anthropic.oauthToken` (config persistante). Le token est transmis à l'API Anthropic via le header `Authorization: Bearer`, qui prend priorité sur `x-api-key`. Le changement est minimal : 2 fichiers modifiés, aucun nouveau provider créé.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: LiteLLM (routage LLM), Pydantic v2 + pydantic-settings (config), Typer (CLI)
**Storage**: `~/.nanobot/config.json` (JSON) — champ `providers.anthropic.oauthToken` ajouté
**Testing**: pytest
**Target Platform**: Cross-platform (Linux, macOS, Windows)
**Project Type**: CLI + library
**Performance Goals**: Aucun impact — le token OAuth est transmis comme header HTTP, latence identique à une clé API
**Constraints**: Changement backward-compatible — les configs existantes avec `api_key` continuent de fonctionner
**Scale/Scope**: 2 fichiers modifiés, ~20 lignes de code, 0 nouvelles dépendances

## Constitution Check

_Constitution template vide — pas de gates spécifiques au projet. Principes appliqués par défaut :_

- ✅ **Simplicité** : Minimal change (2 fichiers), pas de nouveau provider, pas de nouvelles dépendances
- ✅ **Backward-compatible** : Les configs existantes ne sont pas cassées
- ✅ **Testable** : Comportement vérifié via mocks LiteLLM dans les tests unitaires existants

## Project Structure

### Documentation (this feature)

```text
specs/001-claude-oauth-token/
├── plan.md              # Ce fichier
├── spec.md              # Feature spec
├── research.md          # Décisions techniques (Phase 0)
├── data-model.md        # Modèle de données (Phase 1)
├── quickstart.md        # Guide utilisateur (Phase 1)
├── checklists/
│   └── requirements.md  # Checklist qualité spec
└── tasks.md             # Phase 2 (/speckit.tasks — non encore créé)
```

### Source Code (repository root)

```text
nanobot/
├── config/
│   └── schema.py            # MODIFIÉ: + oauth_token dans ProviderConfig + _match_provider
└── cli/
    └── commands.py           # MODIFIÉ: _make_provider() lit CLAUDE_OAUTH_TOKEN + injecte Bearer

tests/
└── test_claude_oauth.py      # NOUVEAU: tests unitaires OAuth flow
```

**Structure Decision**: Single project, modification minimale de fichiers existants. Aucun nouveau module créé.

---

## Phase 0: Research (complétée)

→ Voir [research.md](./research.md)

**Décisions clés:**

1. Header `Authorization: Bearer <token>` transmis via `extra_headers` LiteLLM
2. `CLAUDE_OAUTH_TOKEN` lu dans `_make_provider()` (env direct, pas via Pydantic Settings)
3. Placeholder `api_key = "claude-oauth"` pour satisfaire validation LiteLLM interne
4. `oauth_token: str = ""` ajouté à `ProviderConfig` pour config persistante
5. Check api_key dans `commands.py` adapté pour accepter `oauth_token`

---

## Phase 1: Design & Contracts (complétée)

→ Voir [data-model.md](./data-model.md)

### Contrats (interfaces impactées)

**Pas de contrat externe exposé** — nanobot est un CLI, pas un service HTTP. Les seuls "contrats" sont :

1. **Variable d'environnement** : `CLAUDE_OAUTH_TOKEN` (string, Bearer token Anthropic OAuth)
2. **Config JSON** : `providers.anthropic.oauthToken` (camelCase via alias Pydantic)

### Changements détaillés par fichier

#### `nanobot/config/schema.py`

```python
# Avant
class ProviderConfig(Base):
    api_key: str = ""
    api_base: str | None = None
    extra_headers: dict[str, str] | None = None

# Après
class ProviderConfig(Base):
    api_key: str = ""
    api_base: str | None = None
    extra_headers: dict[str, str] | None = None
    oauth_token: str = ""   # Token d'abonnement (Bearer), alternative à api_key
```

```python
# Dans _match_provider, les deux checks existants acceptent maintenant oauth_token :
# Avant : if spec.is_oauth or p.api_key:
# Après : if spec.is_oauth or p.api_key or p.oauth_token:
```

#### `nanobot/cli/commands.py` — `_make_provider()`

```python
# Résolution OAuth token (env var > config fichier)
oauth_token = os.environ.get("CLAUDE_OAUTH_TOKEN") or (p.oauth_token if p else "")

# Bypass check api_key si oauth_token disponible
if not model.startswith("bedrock/") and not (p and p.api_key) and not (spec and spec.is_oauth) and not oauth_token:
    console.print("[red]Error: No API key configured.[/red]")
    console.print("Set CLAUDE_OAUTH_TOKEN env var or add providers.anthropic.oauthToken in config")
    raise typer.Exit(1)

# Construction du provider avec Bearer token
if oauth_token:
    merged_headers = dict(p.extra_headers or {})
    merged_headers["Authorization"] = f"Bearer {oauth_token}"
    return LiteLLMProvider(
        api_key="claude-oauth",   # placeholder pour LiteLLM
        api_base=config.get_api_base(model),
        default_model=model,
        extra_headers=merged_headers,
        provider_name=provider_name,
    )
```

---

## Complexity Tracking

Aucune violation de principes de simplicité.

| Violation                            | Justification                                                                                                                                                                            |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| placeholder `api_key="claude-oauth"` | Nécessaire car LiteLLM rejette api_key vide côté Anthropic. Anthropic ignore x-api-key quand Authorization Bearer est présent. Alternative (modifier litellm_provider.py) plus complexe. |
