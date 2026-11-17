# Architektur- und Produktentscheidungen

Rekonstruiert am 17.11.2026 aus zugänglicher Unterhaltung und Code bis `f1e59cc`.
Keine erfundenen historischen Entscheidungsdaten. „Benutzerentscheidung“ bedeutet
im zugänglichen Chat ausdrücklich gewünscht/bestätigt; technische Ausgestaltung
kann eine anschließend im Code getroffene Implementierungsentscheidung sein.

| ID | Status / Herkunft | Entscheidung und Begründung |
| --- | --- | --- |
| D01 | Bestätigt, Benutzer | Eigenständige HA-Integration, von Dritten nutzbar, Anleitung von Beginn an mitpflegen. Kein Add-on oder separater Bot-Prozess nötig. |
| D02 | Implementiert | Stabile Server-/Mitglieds-/Kanal-IDs; Namen sind änderbar und können mehrfach vorkommen. Geräte-/Entitätsidentität bei Erweiterungen erhalten. |
| D03 | Bestätigt, Benutzer | Standard-Vollsync von ursprünglich 15 auf **30 Minuten** erhöhen, da Presence/Voice zusätzlich per Gateway abonniert werden. Manueller Sync bleibt verfügbar; eigene Intervalle bleiben erhalten. |
| D04 | Bestätigt, Benutzer; Semantik implementiert | Pro Mitglied Namen, Presence, Sprachkanal, Mute, AFK und Beobachtungszeitpunkte. Sprachverbindung zählt auch bei unsichtbarer Presence als beobachtete Anwesenheit; Presence-Sensor bleibt offline. Discord liefert keinen verlässlichen rückwirkenden Login-Zeitpunkt. Zeitstempel daher erste Beobachtung/Zustandswechsel statt erfundener Anmeldezeit. |
| D05 | Bestätigt, Benutzer | Letztes mitgliedsbezogenes Gateway-Ereignis als zusätzlicher Timestamp. Kein Heartbeat-/Polling-Zeitstempel; ein alter Wert ist nicht automatisch ein Fehler. |
| D06 | Bestätigt, Benutzer; HA-Grenze dokumentiert | Zentrale Gruppe mit Sync und drei Zählern, zweite Gruppe Benutzer. Zentrale zuerst anlegen, aber HA-Sortierung nicht erzwingen. Zähler schließen Bots ein und berücksichtigen sichtbare Presence oder Voice. |
| D07 | Bestätigt, Benutzer | Gemeinsame DM-Funktion für andere Integrationen. Vorhandenes Mitgliedsgerät als Ziel; Aufrufer braucht keinen Bot-Token. Keine automatischen Nachrichten oder unsicheren Wiederholungen. |
| D08 | Bestätigt, Benutzer | Eigenes zentrales Bot-Gerät; nur bei eindeutiger Bot-ID aus Benutzergruppe ausblenden. Kanal-Select mit `alle verlassen`; Kanalwechsel bewegt den Bot. Kanalliste bei jedem Sync und per Gateway aktualisieren. |
| D09 | Bestätigt, Benutzer | TTS-Nachricht und Ausführungsbutton über Standard-TTS von HA; Wiedergabestatus und einstellbare Lautstärke. Implementierter sinnvoller Standard 50 %, dauerhaft gespeichert; Texte/Kanal nicht restaurieren. |
| D10 | Implementiert | Begrenzte Voice-Queue, getrennte Locks für Verbindungen/Ausgaben, Abbruch bei Kanalwechsel/Unload. Verhindert Ausgabe im falschen Kanal und verwaiste Tasks/Subprozesse. PCM-Lautstärkeregelung plus Opus statt direkt durchgereichter FFmpeg-Opus-Daten. |
| D11 | Behobener Kompatibilitätsfehler | `discord.py[voice]==2.7.1` verlangt PyNaCl <1.6, HA 2026.10.4/2026.11.1 pinnt 1.6.2. Deshalb Discord, PyNaCl und davey getrennt deklarieren; HA-Constraints nicht entfernen/herabstufen. Paketauflösung und native Krypto-/Audiotests ergänzen. |
| D12 | Bestätigt, Benutzer; Details implementiert | Zwei Discord-nahe Karten: Sprachhierarchie mit Mitgliedern/Avataren/Mute und konfigurierbarer Textkanal-Feed. Eigene lokale Web Components, HA-WebSockets, keine Tokens im Browser, kein externer Frontend-Dienst. Keine Zusage einer pixelgenauen vollständigen Discord-Kopie. |
| D13 | Implementiert | Voice-Karte per Gateway-Push, Feed per REST (15 Sekunden, 50 Nachrichten, acht Cache-Kanäle). Kein Message-Intent im Gateway angefordert; Message Content-Freigabe für REST-Inhalte trotzdem nötig. Beschränkte Markdown-/Embed-Darstellung bewusst dokumentiert. |
| D14 | Bestätigt, Benutzer | Pro Benutzer Textfeld „Private Nachricht“ und Button „Private Nachricht senden“, Absender Bot. 255 Zeichen als HA-Textzustand; 2000 weiterhin per Aktion/API. Nur expliziter Knopfdruck, Fehler erhält Entwurf, paralleler Doppelaufruf gesperrt. |
| D15 | Bestätigt, Benutzer, zuletzt 1.0.1 | Text-Feed soll **nach jedem Update ganz unten** stehen, auch nach manuellem Scrollen nach oben. Vorherige Scrollposition nicht bewahren. Später geladene Bilder berücksichtigen. |
| D16 | Bestätigt, Benutzer | Versionsformat 1.0.0 eingeführt; Scroll-Korrektur als Patch 1.0.1. Repo-Version ist nicht gleich GitHub-Release/Tag oder installierter HA-Version. |
| D17 | Zurückgestellt, Benutzer | Music Assistant ausdrücklich noch nicht umsetzen. Zweiter Musik-Bot wurde besprochen, nicht beauftragt. Eine Discord-App hat einen Bot-Benutzer; mehrere Bots benötigen getrennte Anwendungen/Tokens. Integration erlaubt bisher nur einen Entry pro Server. |
| D18 | Auftrag vom 17.11.2026 | GitHub als zentrale Quelle für Code und Projektwissen; pro Rechner eigener Checkout. Übergabe in Markdown statt Manipulation lokaler Codex-Sitzungsdatenbanken. Keine produktiven Änderungen im Rahmen dieser Kontext-Sicherung. |

## Nicht als Entscheidung behandeln

- Ein Kamerastream oder allgemeines Musik-Streaming wurde erfragt, aber nicht als
  Implementierungsauftrag bestätigt. Keine automatische Erweiterung daraus ableiten.
- Es liegt keine Zustimmung zu einer selbstgebauten Synchronisierung von Codex-
  internen Dateien, Auth-Daten oder Datenbanken vor.
- HA 2026.11.1 ist die vom Benutzer genannte Laufzeit; die automatisierte
  HA-Testbasis wurde dadurch nicht auf 2026.11.1 umgestellt.
- „Umgebung veröffentlicht“ im Chat bezeichnete Cloud-Umgebungsstände, nicht
  automatisch Git-Commits, GitHub-Releases oder HA-Deployments.

## Ergänzung 17.11.2026: Diagnose statt spekulativer Transportänderung

Nach real gemessenen 100 PCM-Frames und Peak 8708 wird der unveränderte
Discord-Sendepfad mit einem kleinen, zur gepinnten Bibliotheksversion getesteten
Adapter beobachtet. Hintergrund: Socket-OSErrors können von discord.py unterdrückt
werden, und „verbunden“ garantiert keine bereite DAVE-Session. Nur Zähler/Protokoll-
version erfassen; keine Verschlüsselung deaktivieren und keine Empfangsbestätigung
aus einem lokalen Socket-Submit ableiten. Die konkrete Fehlerursache bleibt offen.

## DAVE-Kompatibilität in 1.0.2 (17.11.2026)

Die Benutzerinstallation meldete 105 Socket-Submits, keine lokalen Sendefehler,
aber **105 unbereite DAVE-Pakete bei Protokoll 1**. PCM: 100 Frames, Peak 8708;
auch ein zweiter Discord-Client blieb stumm.

Quellcodevergleich der offiziellen PyPI-Sdists bestätigt: davey 0.1.7 aktiviert
nach `process_welcome`/`process_commit` die Schlüssel über `update_ratchets`.
davey 0.2.0 verlangt dafür zusätzliche `prepare_transition`/`execute_transition`-
Aufrufe. discord.py 2.7.1 führt diese davey-Methoden nicht aus. Das ist eine
konkrete API-Unverträglichkeit und passt zum gemessenen Zustand; ein erfolgreicher
Hörtest nach der Korrektur ist noch nicht bestätigt.

1.0.2 pinnt daher **davey 0.1.7**, behält Discord 2.7.1/PyNaCl 1.6.2 und die
Verschlüsselung bei. Vor Wiedergabe bis zu zehn Sekunden auf DAVE warten; bei
Timeout gezielter HA-Fehler. Der Transportadapter blockiert auch spätere
unbereite DAVE-Sendeversuche, statt transportverschlüsselte Daten ohne die
vereinbarte zusätzliche DAVE-Verschlüsselung zu senden. Kein eigener MLS-Stack,
kein Protokoll-Downgrade und keine automatische Wiederholung einer Durchsage.

Quellen: [davey 0.1.7](https://pypi.org/project/davey/0.1.7/),
[davey 0.2.0](https://pypi.org/project/davey/0.2.0/), jeweils `davey/src/session.rs`
im Source-Archiv; [discord.py 2.7.1](https://pypi.org/project/discord.py/2.7.1/),
`discord/gateway.py` und `discord/voice_state.py`.
