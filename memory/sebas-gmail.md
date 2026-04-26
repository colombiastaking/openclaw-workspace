# Sebas - Gmail Configuration

## Email Personnel

- **Email:** sebastien.hondaa@gmail.com
- **Tokens:** `/home/raspberry/.openclaw/workspace/sebas-gmail-tokens.json`
- **Scope:** Gmail (read-only) + Calendar

## Surveillance École

- **Expéditeur surveillé:** *@lanuevaesperanza.edu.co
- **Fréquence:** 8h et 18h chaque jour

### Mots-clés réunions
- reunión, reunión de padres, cita, encuentro
- fecha, hora, lugar, auditorio, salón
- obligatorio, asistencia

## Calendriers cibles

| Calendrier | Qui voit |
|------------|----------|
| **Familia** | Sebas + Diana (partagé) |
| sebastien.hondaa@gmail.com | Sebas |

**Priorité:** Ajouter au calendrier Familia pour que Diana voie aussi.

## Actions automatiques

Quand nouvel email contient une réunion:
1. Extraire date, heure, lieu
2. Créer événement dans calendrier **Familia**
3. Ajouter alerte 1 jour avant + 2h avant
4. Notifier groupe WhatsApp Devoirs de Kylian

## Derniers emails école

| Date | Sujet |
|------|-------|
| 13/02/2026 | Reunión Inicial Padres 2026 |
| 13/02/2026 | Directorio Staff y Protocolo 2026 |
| 10/02/2026 | St. Valentine's Day |