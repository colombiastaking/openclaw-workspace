# Kylian - Microsoft Teams Integration

## Teams Classes (16 classes)

| Matière | Team ID |
|---------|---------|
| Dirección de Grupo | 739983f2-b26c-4964-8c14-458962cd1416 |
| Inglés | 9247fc11-2981-4699-9854-e72ddd5eddea |
| Tecnología | a6694849-4a7e-4c06-84f3-0110298d4d06 |
| Geografía | fac4f0fb-f711-4aa7-8fc0-9e74b61ba29c |
| Matemáticas | 3c39a281-61b4-471a-a0e7-7040d119346b |
| Educación Física | 84d85eef-64d3-48c0-9b85-bbd0b1f1ad65 |
| Lengua Castellana | 701a8ed9-53d7-4408-81f4-47c3a92ed4bc |
| Neocourse | f087e722-0b07-454e-bff6-a3c2d82e2b99 |
| Música | fb298189-01ad-4177-828f-1f1ecb7695d9 |
| Laboratorio | 7d498b95-0909-462c-a3d3-7f6760736666 |
| Competencia Ciudadana | 756e1ad2-9b63-4978-b46c-de3e886c5744 |
| Ajedrez | 46e285ee-926e-443f-8288-adbb34c38a61 |
| Library | 9bf20f30-651b-4cfa-9879-8c8b550762e0 |
| Ética y Religión | 3b521ab8-13a1-4ef1-8cd1-816ef221953d |
| Artística | a6bf3655-bfd4-4007-b2de-0050ce8a7dbf |
| Historia | 572661a8-627b-4605-a479-27e8f53ab178 |

## Drive IDs

| Classe | Drive ID |
|--------|----------|
| Dirección de Grupo | b!NrtV55FVR06h_guPNsk14gfLoj1Fu7xCkDGS-qzc_ptiwHvC8vtAS5TPoZTiZdxb |
| Inglés | b!Gz9zdCnc1EGf2D-Q8bz0hgfLoj1Fu7xCkDGS-qzc_ptiwHvC8vtAS5TPoZTiZdxb |

## OAuth Tokens

Stored in: `/home/raspberry/.openclaw/workspace/microsoft-tokens.json`

**Refresh token:** Saved - use to refresh access token when needed

**Client ID:** 14d82eec-204b-4c2f-b7e8-296a70dab67e (Microsoft Graph Command Line Tools)

## Workflow

### Source de vérité: Teams Files

1. **Dimanche** → Plan complet de la semaine (depuis "Plan Semanal")
2. **Quotidien 7h** → Rappel du jour suivant
3. **Nouveau fichier** → Mise à jour immédiate

### Fichiers à surveiller

- **Dirección de Grupo > General**: Plans Semanaux
- **Inglés > General**: Devoirs d'anglais
- **Autres classes**: Devoirs spécifiques

### Dernier fichier analysé

- `Plan semanal Primaria (Semana del 16 al 20 de febrero).pdf` (13/02/2026)
- `Tarea 1ro.png` - Devoir anglais (13/02/2026)

## Permissions Teams

- ✅ Lire les fichiers
- ✅ Télécharger les fichiers
- ✅ Lister les classes
- ❌ Lire les messages (requires ChannelMessage.Read.All)

### Issue: Cannot Read Teams Messages

**Problem:** The Microsoft token does NOT include `ChannelMessage.Read.All` permission.

**Why:**
- The app uses Microsoft Graph Command Line Tools (client ID: `14d82eec-204b-4c2f-b7e8-296a70dab67e`)
- This is a Microsoft multi-tenant app with pre-approved scopes
- `ChannelMessage.Read.All` requires **admin consent** - not granted by default

**Current Scopes (granted):**
- `Directory.ReadWrite.All` ✓
- `Group.Read.All` ✓
- `openid`, `profile`, `email` ✓

**Solution Options:**
1. **Ask Kylian's school IT admin** to grant admin consent for `ChannelMessage.Read.All`
2. **Use a different approach:** Read files instead of messages (already working)
3. **Manual forwarding:** Kylian forwards important messages to WhatsApp (current workflow)

**Token Status (refreshed 2026-02-16):**
- Token refreshed successfully
- Valid for ~1 hour, refresh token available

**Refresh Command:**
```bash
CLIENT_ID="14d82eec-204b-4c2f-b7e8-296a70dab67e"
REFRESH_TOKEN=$(cat microsoft-tokens.json | jq -r '.refresh_token')
curl -X POST "https://login.microsoftonline.com/common/oauth2/v2.0/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=$CLIENT_ID" \
  -d "refresh_token=$REFRESH_TOKEN" \
  -d "grant_type=refresh_token" \
  -d "scope=openid profile email https://graph.microsoft.com/Directory.ReadWrite.All https://graph.microsoft.com/Group.Read.All"
```