# Änderungen

## Unveröffentlicht – Diagnose bei DAVE-Timeout

- Tatsächlich geladene Discord-/davey-Version und DAVE-Sitzungszustand am Wiedergabestatus anzeigen, auch wenn vor dem ersten Paket abgebrochen wird.
- Benutzer meldet nach 1.0.2 weiterhin fehlende DAVE-Bereitschaft; erfolgreicher Hörtest bleibt offen.

## 1.0.2

- DAVE-Kompatibilität: davey auf 0.1.7 festgelegt. 0.2.0 benötigt explizite Übergangsaufrufe, die discord.py 2.7.1 nicht ausführt.
- Vor TTS bis zu zehn Sekunden auf Verschlüsselungsbereitschaft warten; bei fehlender Bereitschaft Fehler statt scheinbar erfolgreicher Ausgabe. Unbereite DAVE-Sendeversuche werden blockiert.
- Reale Hörbestätigung nach Installation steht noch aus.

### Voice-Transportdiagnose

- Paket-Submits, lokale UDP-Sendefehler und DAVE-Bereitschaft pro Durchsage messen, ohne Verschlüsselung oder Wiederholungen zu ändern.
- Tatsächlichen Opus-/Paketverschlüsselungs-/Sendepfad mit simuliertem Socket testen; Diagnose enthält keine Paketdaten oder Schlüssel.
- Benutzerwerte 100 PCM-Frames und Peak 8708 grenzen den offenen TTS-Fehler hinter der lokalen PCM-Verarbeitung ein.

### Audio-Diagnose

- FFmpeg-Dekodierungsfehler und fehlende Audioframes werden durch den Lautstärke-Wrapper nicht mehr als erfolgreiches Wiedergabeende verdeckt.
- Wiedergabestatus um lokale Audioframe-/Pegelwerte ergänzt; keine Texte oder Audiodaten protokolliert.
- Native Audiotests verwenden ein echtes Testsignal mit WAV/MP3/Cloud-Streaming-WAV, Lautstärke 0/50/100 % und Opus-Rückdekodierung statt ausschließlich Stille.
- Die gemeldete lautlose Ausgabe bei grünem Discord-Sprechring ist damit noch nicht als behoben bestätigt.

## 1.0.1

- Text-Channel-Feed scrollt nach jeder Aktualisierung und nach dem Laden von Bildern zuverlässig zu den neuesten Nachrichten.

## 1.0.0

- Discord-Channel-Overview mit Kategorie-/Kanalhierarchie, Avataren, Presence und Mute-Anzeigen; Live-Daten über authentifizierte WebSockets.
- Discord-Text-Channel-Feed mit visuellem Kanalwähler, den letzten 50 Nachrichten und begrenztem 15-Sekunden-Cache.
- Pro Mitglied Textfeld „Private Nachricht“ und Button „Private Nachricht senden“, inklusive Fehler- und Doppelversandschutz.
- Bot-Lautstärke 0–100 % mit gespeichertem Standardwert 50 % sowie Wiedergabestatus; deutsche/englische Beschriftungen ergänzt.
- Dashboard-Installation, Zugriffsmodell, zusätzliche Discord-Rechte und Darstellungsgrenzen dokumentiert.

- Konflikt zwischen Discords Voice-Extra und Home Assistants PyNaCl 1.6.2 behoben: Discord, PyNaCl und DAVE separat deklariert.
- Paketauflösung gegen Home-Assistant-Installationsvorgaben in CI ergänzt; Vorgaben von 2026.10.4 und 2026.11.1 geprüft.
- Regressionstest für Discord-Voice-Paketverschlüsselung und Hinweise zur Fehlerbehebung ergänzt.

## 0.4.0

- Eigenes Bot-Gerät in zentraler Konfiguration; eindeutige eigene Bot-ID aus Benutzergeräten ausgeblendet.
- Sprach-/Stage-Kanalauswahl mit erstem Eintrag „alle verlassen“, Beitritt und Kanalwechsel.
- Kanalliste bei jedem Vollabgleich per API erneuert und zusätzlich durch Gateway-Ereignisse aktualisiert.
- TTS-Textfeld und Ausführungsbutton mit Home Assistants Standard-TTS-Anbieter.
- Begrenzte Durchsagewarteschlange; Abbruch bei Kanalwechsel, Disconnect oder Unload.
- Discord-Voice mit DAVE-Unterstützung, FFmpeg-Opus-Verarbeitung und nativer Audioprüfung.
- Voice-/TTS-Anleitung, Automationsbeispiele, Rechte- und Netzwerkhinweise ergänzt.

## 0.3.0

- Gruppen „zentrale Konfiguration“ und „Benutzer“ mit zentralem Gerät und Geräteverknüpfung.
- Zentraler Knopf „Benutzer jetzt synchronisieren“ sowie Mitglieder-, Online- und Sprachkanalzähler.
- Presence und Sprachstatus werden sofort per Gateway aktualisiert; Vollabgleich standardmäßig alle 30 Minuten.
- Mikrofon-Mute, Lautsprecher-Mute und konfigurierter AFK-Kanal als Binärsensoren.
- Persistente Zeitstempel für erkannte An-/Abwesenheit und letztes Benutzer-Gateway-Ereignis.
- Sprachverbindung zählt als Anwesenheit, auch bei offline/unsichtbar; keine Abwesenheit bei Bot-Ausfällen.
- Bestehende Geräte-/Entitäts-IDs und explizite Synchronisationsintervalle bleiben erhalten.
- Aktion `send_direct_message` und öffentliche Python-Funktion für private Textnachrichten an Benutzergeräte.
- Installations-, Bedienungs-, Schnittstellen- und Entwicklerdokumentation sowie Tests ergänzt.

## 0.2.0

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
