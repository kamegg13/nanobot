# Tasks: Authentification Claude via OAuth Token

**Input**: Design documents from `/specs/001-claude-oauth-token/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Tests**: Non demandés explicitement — non inclus dans le scope.

**Organization**: Tasks groupées par user story pour implémentation et test indépendants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallélisable (fichiers différents, pas de dépendances incomplètes)
- **[Story]**: User story correspondante (US1, US2, US3)

---

## Phase 1: Setup

**Purpose**: Pas de nouvelles dépendances ni de structure à créer — projet existant, modification de fichiers existants uniquement.

_Aucune tâche de setup requise._

---

## Phase 2: Fondation (Prérequis bloquants)

**Purpose**: Étendre `ProviderConfig` pour supporter `oauth_token` — bloque US1 et US2 car les deux dépendent de ce champ.

**⚠️ CRITIQUE**: US1 et US2 ne peuvent démarrer qu'après cette phase.

- [x] T001 Ajouter `oauth_token: str = ""` à `ProviderConfig` dans `nanobot/config/schema.py`
- [x] T002 Mettre à jour les deux conditions `if spec.is_oauth or p.api_key:` en `if spec.is_oauth or p.api_key or p.oauth_token:` dans `_match_provider()` de `nanobot/config/schema.py`

**Checkpoint**: `ProviderConfig` accepte `oauth_token` — `_match_provider` le reconnaît comme credential valide.

---

## Phase 3: User Story 1 — Utiliser son abonnement Claude existant (Priority: P1) 🎯 MVP

**Goal**: Qu'un utilisateur avec `CLAUDE_OAUTH_TOKEN` défini puisse lancer nanobot avec Claude sans clé API.

**Independent Test**: Définir uniquement `CLAUDE_OAUTH_TOKEN=sk-ant-oaut01-...` et lancer `nanobot chat` → la session démarre et Claude répond normalement.

### Implémentation US1

- [x] T003 [US1] Dans `_make_provider()` de `nanobot/cli/commands.py`, lire le token OAuth : `oauth_token = os.environ.get("CLAUDE_OAUTH_TOKEN") or (p.oauth_token if p else "")`
- [x] T004 [US1] Dans `_make_provider()` de `nanobot/cli/commands.py`, ajouter le bloc conditionnel qui construit le `LiteLLMProvider` avec `Authorization: Bearer` dans `extra_headers` et `api_key="claude-oauth"` quand `oauth_token` est présent
- [x] T005 [US1] Dans `_make_provider()` de `nanobot/cli/commands.py`, adapter la condition de validation api_key pour inclure `oauth_token` : `and not oauth_token` ajouté à la condition existante

**Checkpoint**: `CLAUDE_OAUTH_TOKEN` suffit pour lancer une session Claude — aucune clé API requise.

---

## Phase 4: User Story 2 — Configuration simple du token (Priority: P2)

**Goal**: Que l'utilisateur puisse stocker le token dans `~/.nanobot/config.json` pour éviter de redéfinir la variable d'env à chaque session.

**Independent Test**: Sans `CLAUDE_OAUTH_TOKEN` défini, avec `providers.anthropic.oauthToken` dans `config.json` → `nanobot chat` fonctionne.

### Implémentation US2

- [x] T006 [US2] Dans `_make_provider()` de `nanobot/cli/commands.py`, vérifier que le fallback sur `p.oauth_token` (config fichier) est bien inclus dans la résolution de `oauth_token` (déjà couvert par T003, vérifier uniquement)
- [x] T007 [US2] Mettre à jour le message d'erreur dans `nanobot/cli/commands.py` pour mentionner les deux options de configuration : `"Set CLAUDE_OAUTH_TOKEN env var or add providers.anthropic.oauthToken in ~/.nanobot/config.json"`

**Checkpoint**: Config persistante via `~/.nanobot/config.json` fonctionne sans variable d'env.

---

## Phase 5: User Story 3 — Feedback clair en cas d'erreur (Priority: P3)

**Goal**: Qu'un token invalide ou expiré produise un message d'erreur explicite, distinct d'une erreur de clé API.

**Independent Test**: Avec `CLAUDE_OAUTH_TOKEN=invalid-token`, lancer `nanobot chat` → le message d'erreur mentionne "OAuth token" et non une erreur générique API.

### Implémentation US3

- [x] T008 [US3] Dans le bloc `except Exception` de `LiteLLMProvider.chat()` dans `nanobot/providers/litellm_provider.py`, détecter les erreurs d'authentification Anthropic (code 401) et retourner un message spécifique si `extra_headers` contient `Authorization: Bearer`

**Checkpoint**: Token invalide → message "Authentication failed: OAuth token invalid or expired" lisible.

---

## Phase 6: Polish & Cross-Cutting

**Purpose**: Tests, documentation et affichage dans `nanobot status`.

- [x] T009 [P] Créer `tests/test_claude_oauth.py` avec tests unitaires couvrant : (1) résolution env var, (2) fallback config fichier, (3) construction des headers Bearer, (4) priorité oauth > api_key
- [x] T010 [P] Mettre à jour l'affichage `nanobot status` dans `nanobot/cli/commands.py` pour indiquer `"Anthropic (OAuth)"` quand `oauth_token` est utilisé
- [x] T011 Vérifier le quickstart `specs/001-claude-oauth-token/quickstart.md` en suivant les instructions end-to-end

---

## Dépendances & Ordre d'exécution

### Dépendances entre phases

- **Phase 2 (Fondation)**: Démarre immédiatement — BLOQUE US1 et US2
- **Phase 3 (US1)**: Dépend de Phase 2 — MVP livrable
- **Phase 4 (US2)**: Dépend de Phase 2 — T006 dépend de T003 (US1)
- **Phase 5 (US3)**: Indépendante de US1/US2 côté code — peut démarrer après Phase 2
- **Phase 6 (Polish)**: Après toutes les user stories désirées

### Dépendances inter-tâches

- T002 → T001 (doit avoir `oauth_token` dans `ProviderConfig` avant d'y accéder)
- T004 → T003 (le bloc injection dépend de la variable `oauth_token` résolue)
- T005 → T003 (la condition dépend de la variable `oauth_token` résolue)
- T006 → T003 (vérification du fallback config)
- T009 → T003, T004, T005 (tests des comportements implémentés)

### Opportunités de parallélisme

- T001 et T002 dans le même fichier → séquentiels
- Phase 3 (US1) et Phase 5 (US3) peuvent démarrer en parallèle après Phase 2
- T009 et T010 (Polish) sont parallélisables

---

## Exemple d'exécution parallèle : Phase 6

```bash
# Ces tâches touchent des fichiers différents, parallélisables :
Task A: "Créer tests/test_claude_oauth.py" (T009)
Task B: "Mettre à jour nanobot status dans commands.py" (T010)
```

---

## Stratégie d'implémentation

### MVP (User Story 1 uniquement)

1. Phase 2 : T001 → T002
2. Phase 3 : T003 → T004 → T005
3. **STOP et VALIDER** : tester avec `CLAUDE_OAUTH_TOKEN` réel

### Livraison incrémentale

1. Phase 2 + Phase 3 → **MVP : variable d'env fonctionne**
2. - Phase 4 → Config persistante fonctionne
3. - Phase 5 → Erreurs lisibles
4. - Phase 6 → Tests + polish

---

## Notes

- Toutes les modifications sont dans des fichiers existants — 0 nouveau fichier créé (sauf tests)
- Scope total : ~20 lignes de code réparties sur 2 fichiers (`schema.py` + `commands.py`)
- T008 est optionnel si US3 est dépriorisé — les autres stories fonctionnent sans lui
- Backward-compatible : aucun changement de comportement pour les configs existantes sans `oauth_token`
