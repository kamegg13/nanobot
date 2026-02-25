# Research: Authentification Claude via OAuth Token

**Feature**: 001-claude-oauth-token
**Date**: 2026-02-25

---

## Décision 1 : Format du token et protocole d'authentification Anthropic

**Decision**: Utiliser `Authorization: Bearer <token>` comme header HTTP à la place de `x-api-key`.

**Rationale**: L'API Anthropic supporte deux modes d'authentification mutuellement exclusifs :

- `x-api-key: <api_key>` — mode clé API classique
- `Authorization: Bearer <token>` — mode OAuth / abonnement

Lorsque `Authorization: Bearer` est présent et valide, Anthropic ignore `x-api-key`. C'est précisément ainsi que Claude Code CLI s'authentifie avec le compte Anthropic de l'utilisateur.

**Alternatives considered**:

- Utiliser LiteLLM `auth_token` param — non documenté pour Anthropic, non supporté de façon fiable
- Créer un provider direct (comme `openai_codex_provider.py`) — surdimensionné, LiteLLM + `extra_headers` suffit

---

## Décision 2 : Où lire `CLAUDE_OAUTH_TOKEN`

**Decision**: Lire directement depuis `os.environ` dans `_make_provider()` (commands.py), pas via Pydantic Settings.

**Rationale**:

- L'utilisateur veut `CLAUDE_OAUTH_TOKEN`, pas `NANOBOT_PROVIDERS__ANTHROPIC__OAUTH_TOKEN`
- Les deux mots de passe ont des sémantiques différentes : la variable d'env est un override rapide, la config persistante est le chemin standard
- Lire l'env directement dans `_make_provider` est le pattern déjà utilisé pour détecter les providers (voir `find_gateway`)

**Alternatives considered**:

- Ajouter un validator Pydantic qui lit `CLAUDE_OAUTH_TOKEN` — possible mais ajoute de la magie implicite
- Forcer via `NANOBOT_PROVIDERS__ANTHROPIC__OAUTH_TOKEN` — cassant pour l'utilisateur (nom trop long)

---

## Décision 3 : Gestion du `api_key` obligatoire dans LiteLLM

**Decision**: Passer une valeur placeholder `"claude-oauth"` comme `api_key` quand seul le token OAuth est disponible.

**Rationale**:

- LiteLLM valide la présence d'une api_key avant d'appeler Anthropic — une chaîne non-vide suffit, LiteLLM la met en `x-api-key`
- Anthropic ignore `x-api-key` quand `Authorization: Bearer` est présent et valide
- C'est la solution la plus simple : aucun changement dans `litellm_provider.py`

**Alternatives considered**:

- Modifier `LiteLLMProvider` pour court-circuiter la validation — fragile, couplage fort
- Utiliser `litellm.drop_params = True` — déjà activé mais ne concerne pas les headers d'auth

---

## Décision 4 : Stockage dans la config persistante

**Decision**: Ajouter `oauth_token: str = ""` à `ProviderConfig` dans `schema.py`.

**Rationale**: Permet de sauvegarder le token dans `~/.nanobot/config.json` sous `providers.anthropic.oauth_token`, comme les autres credentials. L'utilisateur peut ainsi éviter de redéfinir la variable d'env à chaque session.

**Alternatives considered**:

- Stocker dans un fichier séparé (à la `~/.claude/.credentials.json`) — incohérent avec le pattern nanobot
- Uniquement via variable d'env — moins pratique pour usage persistant

---

## Décision 5 : Bypass du check api_key dans `_make_provider`

**Decision**: Modifier la condition de validation dans `commands.py` pour accepter `oauth_token` comme credential valide (en plus de `api_key` et `is_oauth`).

**Rationale**: La ligne `if not (p and p.api_key) and not (spec and spec.is_oauth)` rejetterait sinon un utilisateur n'ayant que le token OAuth.

**Alternatives considered**:

- Marquer le provider anthropic comme `is_oauth=True` dans registry — sémantiquement incorrect, anthropic supporte les deux modes
- Ignorer le check et laisser LiteLLM échouer — mauvaise UX, message d'erreur cryptique

---

## Résumé des fichiers impactés

| Fichier                                 | Changement                                                                               |
| --------------------------------------- | ---------------------------------------------------------------------------------------- |
| `nanobot/config/schema.py`              | + `oauth_token: str = ""` dans `ProviderConfig`; `_match_provider` accepte `oauth_token` |
| `nanobot/cli/commands.py`               | Lire `CLAUDE_OAUTH_TOKEN` env; injecter Bearer dans extra_headers; adapter check api_key |
| `nanobot/providers/litellm_provider.py` | **Aucun changement** — `extra_headers` déjà géré                                         |
| `nanobot/providers/registry.py`         | **Aucun changement** — anthropic ProviderSpec reste inchangé                             |
| `tests/`                                | Nouveaux tests unitaires pour les deux flows (env var + config persistante)              |
