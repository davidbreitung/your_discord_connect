# Offene Aufgaben

Stand: 17.11.2026. P1 = nächster sinnvoller Schritt; P2 = nach Abnahme;
„Zurückgestellt“ ist ausdrücklich **kein** aktueller Implementierungsauftrag.
Keine erfundenen Termine, Verantwortlichen oder Fehlerberichte.

## P1 – Übergabe und reale Bestätigung

- [ ] **DAVE-Korrektur 1.0.2 real bestätigen.** Die Messwerte 105/105 unbereite
  DAVE-Pakete passen zur verifizierten API-Unverträglichkeit davey 0.2.0 mit
  discord.py 2.7.1. Lokal korrigiert: davey 0.1.7, Bereitschaftswarten/Sendesperre.
  Commit/Push ist beauftragt; Benutzer installiert danach und startet HA neu.
  Fertig: hörbare Cloud-TTS-Ausgabe und keine unbereiten DAVE-Sendeversuche.
  Noch kein realer Hörtest, keine automatische Änderung der HA-Installation.

- [ ] Zweiten Windows-Rechner nach [WINDOWS.md](WINDOWS.md) einrichten; Checkout,
  Login, Branch, WSL-/Toolversionen und Einstieg mit `HANDOVER.md` bestätigen.
  Fertig: A/B zeigen denselben Commit, passende Tests lassen sich dort starten.
- [ ] Version 1.0.1 im Benutzer-Dashboard bestätigen: aktualisierte Ressource
  `?v=1.0.1`, neues Modul geladen, bei Feed-Update und späteren Bildern ganz unten.
  Fertig: tatsächliche HA-Beobachtung dokumentiert, nicht nur Browsertest.
- [ ] Reale Abnahme auf separater Testinstallation vervollständigen:
  Start/PyNaCl-Fix auf HA 2026.11.1, Presence/Voice/Mute/AFK/Timer, Kanaländerungen,
  TTS-Hörtest inkl. Volume/Abbruch/Stage/UDP, DM mit eigenem Testempfänger,
  Feed-Berechtigungen/Inhalte und Wiederverbindung. Keine echten Nachrichten
  ohne passenden Testauftrag senden; produktives HA nicht automatisch verändern.
- [ ] Installation/Update über HACS oder manuelle Kopie nach Anleitung verifizieren;
  insbesondere Frontend-Ressource, native Voice-Pakete und Neustart. Git-Push ist
  keine Bestätigung einer gelungenen Installation.

## P2 – Wartung nach Bedarf

- [ ] Installierte HA-/Discord-Kompatibilität bei späteren Versionswechseln prüfen;
  Testbasis 2026.10.4 ggf. bewusst erweitern. HA 2026.11.1 ist bisher keine zweite
  vollständige Funktionstestmatrix. PyNaCl-Konflikt nicht wieder einführen.
- [ ] discord.py-Deprecation vor einem Wechsel auf Python 3.16 bewerten;
  heute kein beobachteter Testfehler.
- [ ] Bei neuer Codex-Desktop-Version offizielle Geräte-/Sitzungsfunktionen prüfen;
  diese Recherche konnte keine belastbare lokale Chat-Synchronisierung bestätigen.
  Keine internen Dateien/DBs migrieren. Nur dokumentierte, tatsächlich verfügbare
  Produktfunktionen erwägen; Git-Übergabe bleibt unabhängig davon nutzbar.

## Zurückgestellt – nur nach neuem Auftrag

- Music-Assistant-Anbindung / `media_player` / allgemeines Musik-Streaming.
- Zweiter Musik-Bot auf demselben Server (neue App/Token plus geänderte Entry-Identität).
- Kamera-/Videoübertragung oder sonstige neue Stream-Funktionen.
- Vollständiges Discord-Markdown, Threads, Reaktionen, Sprechaktivität oder
  zusätzliche Kartenfunktionen: bisher dokumentierte Grenzen, keine beauftragten Tasks.

## Abgeschlossen / nicht erneut umsetzen

- [x] Mitgliederintegration, Echtzeit-Gateway, Geräte-Gruppen und Beobachtungszeitpunkte.
- [x] Öffentliche DM-Schnittstelle und DM-Bedienung an Benutzergeräten.
- [x] Bot-Voice/TTS, Lautstärke, Status und Kanallisten-Synchronisierung.
- [x] Installationskonflikt `discord.py[voice]` behoben und Constraint-Prüfung ergänzt.
- [x] Zwei Dashboard-Karten mit Konfiguration und Dokumentation, Version 1.0.0.
- [x] Feed-Scroll-Korrektur 1.0.1 mit sechs erfolgreichen Browsertests; nach `main` gepusht.
- [x] Persistenter Kontext, Architekturentscheidungen und Windows-/Git-Übergabe beschrieben.

Bei Abschluss die zugehörige Evidenz (Commit, Test oder Benutzerbestätigung) in
STATUS/HANDOVER aktualisieren. Neue Ideen nicht als bereits vereinbarte Aufgaben ausgeben.
