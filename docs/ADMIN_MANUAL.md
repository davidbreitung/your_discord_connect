# Administrationshandbuch – Your Discord Connect

> Betriebsanleitung auf Grundlage der vorhandenen Projektunterlagen. Ergänzende Dokumente: [Installation](installation.md), [Entwicklung](development.md), [Voice/TTS](voice.md), [Architektur](ARCHITECTURE.md), [Status](STATUS.md).

## Architektur
Home-Assistant-Custom-Integration `your_discord_connect` mit einem Config Entry je Discord-Server, Coordinator und Gateway-Client. Keine eigenständige Bot-Anwendung. Die Integration nutzt Discord-HTTPS-/Gateway-Zugriffe und für Voice zusätzlich UDP und DAVE.

## Installation und Voraussetzungen
- Integration über HACS als benutzerdefiniertes Repository oder manuell unter `/config/custom_components/your_discord_connect` installieren; danach Home Assistant neu starten.
- Discord-Bot erstellen, Server Members Intent und Presence Intent aktivieren; für den Textkanal-Feed ggf. Message Content Intent.
- Bot in den Server einladen und benötigte Rechte für Kanäle, DMs und Voice erteilen.
- Für TTS: Home-Assistant-TTS-Anbieter, FFmpeg/Opus-Unterstützung, Voice-Rechte und ausgehendes UDP sicherstellen.

## Sicherheit und Berechtigungen
- Bot-Token nur in der Home-Assistant-Konfiguration speichern; Backups entsprechend schützen.
- Keine Tokens in Logs, Browser-Daten, Git, Screenshots oder öffentlichen Issues.
- Dashboard-Feed verwendet HA-Authentifizierung und Bot-Kanalberechtigungen; persönliche Discord-Rechte des einzelnen HA-Benutzers werden nicht automatisch gespiegelt.
- Nachrichten und Audio werden nur nach expliziter Aktion gesendet.

## Betrieb und Überwachung
- Vollabgleich beim Start, manuell und in konfigurierbarem Intervall (Standard 30 Minuten).
- Gateway-Ereignisse aktualisieren Presence und Voice zwischen Vollabgleichen.
- Bei API-/Gateway-Ausfällen Geräte nicht als verschwunden behandeln; unbekannte Werte nicht durch Null oder offline ersetzen.
- Bei Problemen Home-Assistant-Logs und die Wiedergabestatus-/Diagnoseattribute prüfen; sensible Werte vor Weitergabe entfernen.

## Updates, Backup und Rollback
- Vor Updates ein Home-Assistant-Backup erstellen und die bisherige Integrationsversion dokumentieren.
- HACS-Update oder kontrollierten Austausch des Integrationsordners durchführen; Home Assistant neu starten.
- Bei Regression auf die vorherige bekannte Version zurückgehen und Fehlerbilder dokumentieren. Die Wiederherstellung wurde in dieser Dokumentationsmigration nicht praktisch getestet.
- Abhängigkeiten und Home-Assistant-Constraints beachten; insbesondere die dokumentierte davey-/discord.py-Kompatibilität nicht ungeprüft ändern.

## Bekannte Risiken und Teststand
- Stand der Dokumentation: Version 1.0.2; Home-Assistant-Testbasis 2026.10.4, Python >= 3.14.2.
- Projektunterlagen berichten automatisierte Python-/Browserprüfungen, aber keine vollständige reale Discord-/TTS-Abnahme.
- Die DAVE-Aushandlung und hörbare TTS-Ausgabe sind weiterhin offen. Eine lokale Diagnose oder bestandene Simulation ist kein Nachweis einer erfolgreichen realen Sprachausgabe.
- Keine produktiven Neustarts, Bot-Nachrichten oder Deployments ohne entsprechenden Auftrag.

## Weiterführende Dokumentation
[Installation](installation.md) · [Voice](voice.md) · [Dashboard](dashboard.md) · [API](api.md) · [Entscheidungen](DECISIONS.md) · [Offene Aufgaben](TODO.md)
