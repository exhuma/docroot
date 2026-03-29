# Was ist Docroot?

**Docroot** ist ein leichtgewichtiger, selbst gehosteter
Dokumentationsserver. Er speichert versionierte
Dokumentationsarchive (ZIP-Dateien mit einer `index.html`) und stellt
sie über eine Web-Oberfläche und eine REST-API bereit.

## Kernkonzepte

| Konzept | Beschreibung |
|---|---|
| **Namensraum** | Eine übergeordnete Gruppierung — meist eine Organisation oder ein Team. |
| **Projekt** | Eine einzelne Dokumentationsquelle innerhalb eines Namensraums. |
| **Version** | Ein Snapshot der Dokumentation für eine bestimmte Version. |
| **Locale** | Eine Sprachvariante einer Version (`en`, `fr`, `de`, …). |

## Einstieg

1. **Durchsuchen** — die Startseite listet alle zugänglichen Namensräume.
   Klicken Sie auf Namensraum → Projekt → Version, um den Viewer zu
   öffnen.
2. **Anmelden** — klicken Sie oben rechts auf **Anmelden**.  Wenn OIDC
   konfiguriert ist, werden Sie zu Ihrem Identitätsanbieter
   weitergeleitet und danach automatisch angemeldet.
3. **Hochladen** — navigieren Sie zu einem Projekt und klicken Sie auf
   **Hochladen** (sichtbar nach Anmeldung mit Schreibzugriff).  Das ZIP
   muss eine `index.html` im Archivstamm enthalten.
4. **Automatisieren** — nutzen Sie die REST-API mit einem OAuth2-Token
   ([client-credentials](https://oauth.net/2/grant-types/client-credentials/))
   für CI/CD-Pipelines.  Das Benutzerhandbuch enthält Curl-Beispiele.
