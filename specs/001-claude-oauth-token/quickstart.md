# Quickstart: Utiliser nanobot avec un abonnement Claude

## Option 1 : Variable d'environnement (recommandée)

Récupérez votre token depuis `~/.claude/.credentials.json` :

```bash
cat ~/.claude/.credentials.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('claudeAiOauth',{}).get('accessToken',''))"
```

Puis définissez la variable :

```bash
export CLAUDE_OAUTH_TOKEN="votre-token-ici"
nanobot chat
```

## Option 2 : Config persistante

```bash
nanobot config set providers.anthropic.oauthToken "votre-token-ici"
```

## Vérification

```bash
nanobot status   # doit afficher "Anthropic (OAuth)" dans les providers actifs
```

## Notes

- Le token d'abonnement Claude est différent d'une clé API — il ne génère pas de frais à l'usage
- Si votre token expire, re-récupérez-le depuis `~/.claude/.credentials.json` après une reconnexion Claude Code
- Si les deux (`CLAUDE_OAUTH_TOKEN` et une clé API) sont définis, le token d'abonnement a la priorité
