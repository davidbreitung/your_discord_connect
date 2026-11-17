# Projektstatus – Your Discord Connect

> Kompakte Einstiegsübersicht; Details unter [docs/STATUS.md](docs/STATUS.md), [docs/TODO.md](docs/TODO.md) und [docs/HANDOVER.md](docs/HANDOVER.md).

## Aktueller dokumentierter Stand
- Integration: `your_discord_connect`, Version **1.0.2**.
- Implementiert laut Projektunterlagen: UI-Einrichtung, Mitgliedsgeräte, Presence-/Voice-Status, manuelle und automatische Synchronisierung, Direktnachrichten, Bot-TTS und Dashboard-Karten.
- Projektstatus berichtet **116 bestandene Python-Tests** für die DAVE-Korrektur und **35 gezielte Voice-/Transporttests** für eine spätere Diagnose. Dies sind historische Ergebnisse, keine Tests dieser Dokumentationsmigration.

## Bekannte Probleme und offene Abnahme
- Die reale TTS-Sprachausgabe ist weiterhin nicht als erfolgreich hörbar bestätigt. Nach 1.0.2 wurde „DAVE ist noch nicht bereit“ gemeldet; die Diagnose wurde erweitert, tatsächlicher Laufzeitstatus bleibt zu prüfen.
- Echte Discord-/HA-End-to-End-Abnahme für Voice/UDP/Stage, DMs, Reconnect und HACS ist nicht vollständig dokumentiert.
- Neuere HA-Versionen und Windows-Testausführung nicht vollständig nachgewiesen.

## Dokumentationsmigration – 17.11.2026
- `AGENTS.md` um gemeinsame Entwicklungsregeln ergänzt.
- `REQUIREMENTS.md`, diese Statusübersicht, getrenntes Benutzer- und Administrationshandbuch sowie Dokumentationsworkflow ergänzt.
- Bestehende Detailanleitungen, Architektur- und Übergabedateien bleiben erhalten.
- Keine Laufzeitcodeänderungen und keine neuen Tests ausgeführt.
- Für diese reine Dokumentationsänderung waren keine Funktionsanpassungen der bestehenden Spezialanleitungen erforderlich.

## Nächste Schritte
- Nach Installation des aktuellen Stands DAVE-Diagnoseattribute auswerten und echten Hörtest durchführen.
- Bei weiteren Entwicklungsaufträgen Anforderungen, Status, beide Handbücher und betroffene Spezialdokumente synchron aktualisieren.
