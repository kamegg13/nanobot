# Feature Specification: Authentification Claude via Abonnement Personnel

**Feature Branch**: `001-claude-oauth-token`
**Created**: 2026-02-25
**Status**: Draft
**Input**: User description: "je veux ajouter la possibilité d'utiliser le CLAUDE_OAUTH_TOKEN à la place de la clé api de claude, car je ne veux pas payer, j'ai deja un abonnement claude code. C'est clairement possible de faire cela. Je veux le faire le plus simplement possible"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Utiliser son abonnement Claude existant (Priority: P1)

Un utilisateur possède un abonnement Claude (Claude Code, Claude Pro, etc.) et veut utiliser nanobot sans avoir à payer séparément pour une clé API Anthropic. Il dispose d'un token d'authentification issu de son abonnement, et veut le fournir à nanobot pour authentifier ses requêtes vers Claude.

**Why this priority**: C'est l'objectif central de la feature — permettre à un abonné Claude de ne pas doubler ses coûts. Sans cette story, la feature n'existe pas.

**Independent Test**: Peut être testé complètement en configurant uniquement le token d'abonnement et en lançant une conversation avec un modèle Claude — nanobot doit répondre normalement sans clé API.

**Acceptance Scenarios**:

1. **Given** un utilisateur a configuré son token d'abonnement Claude mais aucune clé API Anthropic, **When** il démarre une session nanobot avec un modèle Claude, **Then** la session fonctionne et Claude répond normalement.
2. **Given** un utilisateur a configuré les deux (token d'abonnement ET clé API), **When** il démarre une session, **Then** le token d'abonnement prend priorité sur la clé API pour le provider Claude.
3. **Given** un utilisateur n'a ni clé API ni token d'abonnement configuré, **When** il tente d'utiliser un modèle Claude, **Then** nanobot affiche un message clair indiquant qu'une authentification est requise.

---

### User Story 2 - Configuration simple du token (Priority: P2)

Un utilisateur veut pouvoir configurer son token d'abonnement Claude de la même façon qu'il configure une clé API : soit via une variable d'environnement, soit via la configuration persistante de nanobot.

**Why this priority**: La facilité de configuration est essentielle pour l'adoption. Si configurer le token est compliqué, la feature perd son intérêt.

**Independent Test**: Peut être testé en définissant uniquement la variable d'environnement `CLAUDE_OAUTH_TOKEN` et en vérifiant que nanobot l'utilise automatiquement sans autre configuration.

**Acceptance Scenarios**:

1. **Given** la variable d'environnement `CLAUDE_OAUTH_TOKEN` est définie, **When** nanobot démarre, **Then** il détecte et utilise automatiquement ce token pour les modèles Claude, sans configuration supplémentaire.
2. **Given** un utilisateur souhaite stocker le token de façon persistante, **When** il le sauvegarde dans la configuration nanobot, **Then** il n'a plus besoin de définir la variable d'environnement à chaque session.

---

### User Story 3 - Feedback clair en cas d'erreur d'authentification (Priority: P3)

Un utilisateur dont le token d'abonnement a expiré ou est invalide reçoit un message d'erreur compréhensible, distinct d'une erreur générique.

**Why this priority**: L'expérience utilisateur en cas d'erreur est importante mais non bloquante pour le MVP.

**Independent Test**: Peut être testé en fournissant un token invalide et en vérifiant le message affiché.

**Acceptance Scenarios**:

1. **Given** un token d'abonnement expiré ou invalide est configuré, **When** nanobot tente d'appeler Claude, **Then** nanobot affiche un message indiquant que l'authentification par abonnement a échoué (et non une erreur cryptique de l'API).

---

### Edge Cases

- Que se passe-t-il si le token expire en cours de session ?
- Comment nanobot se comporte-t-il si le token est présent mais vide (chaîne vide) ?
- Que se passe-t-il si l'utilisateur configure un token d'abonnement pour un modèle non-Claude (ex: GPT-4) ?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: Le système DOIT accepter un token d'abonnement Claude comme alternative à une clé API Anthropic pour authentifier les requêtes vers les modèles Claude.
- **FR-002**: Le système DOIT lire le token d'abonnement depuis la variable d'environnement `CLAUDE_OAUTH_TOKEN`.
- **FR-003**: Le système DOIT permettre de stocker le token d'abonnement dans la configuration persistante de nanobot (aux côtés des autres clés provider).
- **FR-004**: Lorsque les deux sont présents, le token d'abonnement DOIT avoir la priorité sur la clé API Anthropic pour les modèles Claude.
- **FR-005**: Le système DOIT n'appliquer le token d'abonnement qu'aux requêtes vers les modèles Claude — les autres providers ne doivent pas être affectés.
- **FR-006**: En cas d'échec d'authentification via token d'abonnement, le système DOIT afficher un message d'erreur explicite différenciant ce cas d'une erreur de clé API.

### Key Entities

- **Token d'abonnement Claude** : Credential issu d'un abonnement Claude (Claude Code, Claude Pro), représente l'identité de l'utilisateur auprès d'Anthropic sans nécessiter une clé API facturée à l'usage.
- **Configuration provider** : Ensemble des paramètres d'un provider LLM dans nanobot (clé API, URL de base, headers, etc.) — étendu pour inclure le token d'abonnement.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Un utilisateur avec un abonnement Claude peut utiliser nanobot avec un modèle Claude en moins de 2 minutes de configuration (uniquement en définissant la variable d'environnement).
- **SC-002**: Aucune clé API Anthropic n'est requise lorsqu'un token d'abonnement valide est configuré — zéro erreur de facturation API lors des tests.
- **SC-003**: 100% des requêtes utilisant le token d'abonnement aboutissent de la même façon que celles utilisant une clé API classique (même qualité de réponse, mêmes modèles disponibles).
- **SC-004**: En cas de token invalide, l'utilisateur comprend l'erreur et sait comment la corriger sans consulter la documentation (message auto-explicatif).

## Assumptions

- Le token d'abonnement Claude (`CLAUDE_OAUTH_TOKEN`) est un Bearer token compatible avec l'API Anthropic, utilisé à la place du header `x-api-key` standard.
- Le projet suit déjà un pattern OAuth similaire pour d'autres providers (OpenAI Codex, GitHub Copilot) — cette feature s'inscrit dans ce pattern existant.
- L'utilisateur sait comment obtenir son token d'abonnement depuis son compte Claude (hors scope de cette feature).
- La feature ne couvre pas la gestion du renouvellement automatique de token expiré (out of scope pour le MVP).
