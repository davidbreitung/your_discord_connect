# Änderungen

## 0.2.0 – in Entwicklung

- Benutzername, Presence-Status, Sprachkanalname und Sprachverbindungs-Binärsensor pro Mitglied.
- Gateway-Verbindung mit Presence-Abfragen bei jeder Synchronisation; Presence Intent nötig.
- Manueller Synchronisationsknopf pro Server, über `button.press` automatisierbar.
- Stabile bisherige Geräte- und Entitäts-IDs; Bereinigung aller Mitgliederentitäten bei Austritt.
- Unbekannte Zustände bei fehlenden Gateway-Daten; Geräteerhalt bei Verbindungsfehlern.
- Installations-, Upgrade- und Entwicklerdokumentation sowie deutsche/englische UI ergänzt.

## 0.1.0

- Bot-Token, automatische Serverauswahl und Zugriffsprüfung in der Oberfläche.
- Virtuelle Geräte mit Anzeigenamen für alle Mitglieder einschließlich Bots.
- Vollständiger paginierter Mitgliederabgleich mit stabilen Discord-IDs.
- Intervall zentral pro Server einstellbar: 1–1440 Minuten, Standard 15 Minuten.
- Geräteanlage, Namensaktualisierung und Entfernung nach erfolgreichem Abgleich.
- Fehlerbehandlung, erneute Anmeldung, deutsche und englische Oberfläche.
- Installationsanleitung, Entwicklerdokumentation und automatisierte Tests.
