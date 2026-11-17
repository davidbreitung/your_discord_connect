# Bot-Gerät, Kanalauswahl und TTS-Durchsagen

Ab Version **0.4.0** gibt es in der Untergruppe **zentrale Konfiguration** zusätzlich
ein Gerät **Bot: <Bot-Name>**. Es besitzt fünf Entitäten:

| Entität | Funktion |
| --- | --- |
| Sprachkanal | Dropdown zum Beitreten, Wechseln und Verlassen. |
| TTS-Nachricht | Eingabefeld für bis zu 255 Zeichen, entsprechend Home Assistants Zustandslängenlimit. |
| TTS ausführen | Erzeugt mit Home Assistants Standard-TTS-Anbieter Sprache und spielt sie im gewählten Kanal ab. |
| Wiedergabestatus | Nicht verbunden, bereit, Vorbereitung, Wiedergabe oder Fehler; zusätzlich Anzahl wartender Durchsagen. |
| Lautstärke | 0–100 %, voreingestellt auf 50 %. Änderungen gelten auch während der Wiedergabe und bleiben nach Neustarts erhalten. |

Der eigene Bot wird anhand der ID des authentifizierten Discord-Benutzers erkannt,
nicht anhand seines Namens. Nur dieses Mitglied wird aus der Gruppe **Benutzer**
ausgenommen; andere Bots bleiben sichtbar. Wenn keine eindeutige ID verfügbar ist,
wird kein Mitglied ausgeblendet. Die Serverzähler enthalten weiterhin alle Mitglieder,
einschließlich des eigenen Bots. Vorhandene Mitgliederentitäten des eigenen Bots
werden entfernt und durch das zentrale Bot-Gerät ersetzt; darauf verweisende
Automationen gegebenenfalls anpassen. Die übrigen Mitgliedergeräte behalten ihre IDs.

0 % schaltet nur die Audioausgabe stumm; der Bot bleibt im Kanal.

## Voraussetzungen

1. **Server Members Intent** und **Presence Intent** wie bisher aktivieren.
2. Dem Bot für die gewünschten Sprachkanäle **Kanal ansehen / View Channel**,
   **Verbinden / Connect** und **Sprechen / Speak** erlauben. Kanalüberschreibungen
   berücksichtigen. Administratorrechte sind nicht erforderlich.
3. Einen funktionierenden TTS-Anbieter in Home Assistant einrichten, z. B. Piper
   oder Home Assistant Cloud. Die Integration nutzt Home Assistants Funktion
   `async_default_engine`: aktuell bevorzugt sie die Cloud-TTS-Entität, ansonsten
   die erste verfügbare TTS-Entität beziehungsweise einen vorhandenen Legacy-Anbieter.
   Dies ist keine eigene Auswahl der Integration und nicht zwingend dieselbe
   Stimme wie die einer individuell konfigurierten Assist-Pipeline.
4. **FFmpeg und die native Opus-Bibliothek (libopus)** muss verfügbar sein. Die Integration verwendet
   den in Home Assistants FFmpeg-Integration konfigurierten Programm-Pfad.
   Home Assistant OS/Container bringt FFmpeg üblicherweise mit. Bei eigener
   Python-Installation FFmpeg zusätzlich installieren. Es wird kein FFmpeg über
   einen frei eingebbaren Nachrichtenparameter ausgeführt.
5. Discord-Voice braucht neben HTTPS und Gateway-WSS **ausgehendes UDP** zum von
   Discord ausgehandelten Voice-Server/Port und dessen Voice-WebSocket. Eine reine
   HTTPS-Proxy-Freigabe genügt nicht. Bei Verbindungsproblemen Firewall/Container-Netz
   prüfen. Es wird kein eingehender Port zur Home-Assistant-Oberfläche benötigt.

Die Integration installiert `discord.py==2.7.1`, `PyNaCl==1.6.2` und
`davey==0.1.7` ausdrücklich als getrennte Abhängigkeiten. Das Voice-Extra von
discord.py verlangt PyNaCl < 1.6 und kollidiert damit mit Home Assistants
Vorgabe PyNaCl 1.6.2. Die getrennte Deklaration erhält die Voice-Unterstützung
einschließlich DAVE; Home Assistants Paketvorgaben bleiben wirksam. Discord-Verbindung und Audioübertragung bleiben
verschlüsselt; die Verschlüsselung wird nicht deaktiviert.

Fehlender TTS-Anbieter oder fehlendes FFmpeg blockiert nicht die normale Mitglieder-
synchronisation. Der TTS-Button meldet in diesem Fall den Fehler beim Aufruf.

## Kanal auswählen

Unter **Einstellungen → Geräte & Dienste → Your Discord Connect → zentrale
Konfiguration → Bot: <Name>** die Entität **Sprachkanal** öffnen.

- Der erste Eintrag ist immer **alle verlassen**.
- Danach folgen alle vom Bot abrufbaren **Sprach- und Stage-Kanäle** des Servers,
  sortiert nach Discord-Position und ID. Textkanäle und Kategorien können keine
  Sprachausgabe aufnehmen und werden nicht angeboten.
- Die Kanal-ID wird zum Namen angezeigt, damit gleichnamige Kanäle eindeutig bleiben.
- Auswahl eines Kanals verbindet den Bot; eine andere Auswahl verschiebt die Verbindung.
- **alle verlassen** beendet die Sprachverbindung dieses Servereintrags und bricht
  dessen laufende und wartende Durchsagen ab. Ein Bot kann pro Server nur mit einem
  Sprachkanal gleichzeitig verbunden sein. Andere Servereinträge werden nicht getrennt.
- Die Auswahl spiegelt die tatsächliche Verbindung wider; ein fehlgeschlagener
  Beitritt wird nicht als erfolgreicher Kanalwechsel angezeigt.

Die Kanalliste wird bei **jedem vollständigen Mitgliederabgleich** erneut per
Discord-API geladen – automatisch, manuell und nach Wiederverbindung. Zusätzlich
werden Gateway-Ereignisse zu neuen, geänderten und gelöschten Kanälen sofort
übernommen. Bei Umbenennung bleibt die Kanal-ID ausgewählt; kein erneuter Beitritt
ist nötig. Gelöschte Kanäle werden entfernt. Bei einem fehlgeschlagenen Abruf bleibt
die bisherige Liste erhalten und der Abgleich meldet den Fehler.

Auf einer **Stage** benötigt der Bot zusätzlich die Freigabe zum Sprechen durch
die Stage-Moderation. Ein stummgeschalteter oder unterdrückter Bot kann keine
Durchsage machen. Die Integration erteilt sich keine Moderationsrechte und umgeht
keine Stage-Freigabe.

## Durchsage ausführen

1. Sprachkanal wählen.
2. **TTS-Nachricht** bearbeiten und speichern.
3. **TTS ausführen** drücken.

Die Nachricht wird bei jedem Knopfdruck erfasst und mit dem Standard-TTS-Anbieter
erzeugt. Änderungen am Textfeld starten keine Wiedergabe. Bis zu **fünf** laufende
oder wartende Durchsagen werden nacheinander abgearbeitet. Jede verwendet den Text
und Zielkanal vom Zeitpunkt ihres Knopfdrucks. Weitere Aufrufe erhalten eine
Fehlermeldung, statt unbegrenzt Nachrichten anzusammeln.

Kanalwechsel, „alle verlassen“, verlorene Verbindung, externe Kanalwechsel und
Entladen der Integration brechen offene Durchsagen ab. Eine wartende Nachricht wird
nicht automatisch in einem anderen Kanal abgespielt. Nach erfolgreicher Wiedergabe
bleibt der Bot im gewählten Kanal, bis die Auswahl geändert wird.

Nach Neustart/Neuladen bleibt der Bot zunächst getrennt und das Textfeld ist leer.
Es werden keine alten Durchsagen wiederholt. Der Bot tritt mit deaktiviertem Empfang
(`self_deaf`) bei; diese Integration zeichnet keine Gespräche auf.

Für eine reine Sprachgenerierung muss Home Assistant keine öffentlich erreichbare
Audio-URL bereitstellen. Die Audiodaten werden intern vom HA-TTS-Dienst abgerufen,
über FFmpeg in Opus umgewandelt und an Discord gesendet. Der Text kann entsprechend
dem gewählten TTS-Anbieter extern verarbeitet werden. Home Assistants Recorder oder
Automations-Traces können den Inhalt der Textentität speichern.

## Beispielautomation

Die tatsächlichen Entitäts-IDs aus Deiner Installation einsetzen:

```yaml
sequence:
  - action: select.select_option
    target:
      entity_id: select.mein_discord_bot_sprachkanal
    data:
      option: "Allgemein (123456789012345678)"
  - action: text.set_value
    target:
      entity_id: text.mein_discord_bot_tts_nachricht
    data:
      value: "Die Waschmaschine ist fertig."
  - action: button.press
    target:
      entity_id: button.mein_discord_bot_tts_ausfuhren
  - action: select.select_option
    target:
      entity_id: select.mein_discord_bot_sprachkanal
    data:
      option: "alle verlassen"
```

Der Button-Aufruf wartet auf das Ende seiner Durchsage. Bei mehreren gleichzeitig
laufenden Automationen kann ein abschließendes „alle verlassen“ die Durchsagen der
anderen Automation abbrechen. Solche Abläufe bei Bedarf in einem gemeinsamen
Home-Assistant-Skript mit `mode: queued` koordinieren.

Es gibt noch keine `media_player`-Entität: `tts.speak` mit dem Bot als Media-Player
wird daher nicht angeboten. Die Text-/Button-Kombination verwendet bereits denselben
HA-TTS-Unterbau. Beliebige Audiostreams und Video sind nicht Teil
dieser Version.

## Stand der Prüfung

Automatisierte Tests prüfen Gerätezuordnung, Kanalauswahl/-wechsel, Kanaländerungen,
Queue/Abbruch, Rechtefehler, den HA-TTS-Aufruf und die tatsächliche WAV-zu-Opus-
Verarbeitung mit FFmpeg. Discord-Verbindungen und TTS-Anbieter werden simuliert.
Ein vollständiger Hörtest mit echtem Bot, Voice-Netzwerk und Deiner HA-TTS-Stimme
steht noch aus.

## Fehlersuche: grüner Sprechring, aber kein Ton

Der grüne Discord-Ring bestätigt die Sprechsignalisierung, nicht die hörbare
Audioübertragung. Zuerst die Entität **Lautstärke** (z. B. 50 %), die lokale
Discord-Benutzerlautstärke des Bots sowie Stummschaltung/Deafen beim Zuhörer prüfen.
Danach die Vorschau des verwendeten TTS-Anbieters in Home Assistant abspielen.
Bei Stage-Kanälen außerdem die Sprecherfreigabe prüfen. Kanal einmal über
**alle verlassen** verlassen und erneut auswählen; keine laufende Durchsage dabei.

Die ergänzte Audio-Diagnose im aktuellen main-Stand ergänzt am **Wiedergabestatus**
nach einem Durchsageversuch zwei Attribute:

- `last_audio_frames`: gelesene 20-ms-PCM-Blöcke; 50 entsprechen etwa einer Sekunde.
- `last_audio_peak`: größter absoluter 16-Bit-PCM-Samplewert **nach** Lautstärkeregelung
  (0–32768). 0 bedeutet digitale Stille, z. B. durch Lautstärke 0 oder stumme TTS-Daten.

Die Attribute sind vor dem nächsten Audio-Lauf unbekannt und werden beim Start
eines Auftrags zurückgesetzt. Sie enthalten weder Nachrichtentext noch Audio.
Gelesene Blöcke/Peak > 0 belegen nur den lokalen PCM-Pfad, nicht erfolgreiche
UDP-Übertragung, DAVE-Entschlüsselung oder Wiedergabe beim Zuhörer.

Ein FFmpeg-Fehler oder eine Quelle ohne vollständige PCM-Blöcke wird mit dieser
Diagnose als Dekodierungsfehler gemeldet, statt hinter dem Lautstärke-Wrapper als
normales Ende zu erscheinen. Ein stilles, aber gültiges Audiosignal wird nicht als
Decoderfehler eingestuft. Optionales Debug-Logging ausschließlich für
`custom_components.your_discord_connect.voice` protokolliert Blockzahl, Peak und
Lautstärke; keine umfassenden Discord-Handshake-/Token-Logs weitergeben.

Für einen Fehlerbericht genügen TTS-Anbieter, Ergebnis seiner HA-Vorschau,
Bot-Lautstärke, normaler Sprachkanal/Stage und die Fehlermeldung bzw. nach Installation
dieser Diagnose die beiden Attribute. Keine Tokens oder privaten Nachrichten senden.

Home Assistant Cloud wird von der geprüften HA-Standard-Engine-Auswahl bevorzugt.
Sein Streaming-WAV-Format (WAV-Header mit zunächst null Frames, danach PCM-Daten)
ist ebenfalls im lokalen Audiotest enthalten. Ein bestandener Format-Test oder
eine hörbare HA-Vorschau beweist dennoch keine erfolgreiche Discord-Übertragung.

### Erweiterung: tatsächlicher Voice-Sendepfad

Wenn `last_audio_frames` und `last_audio_peak` größer null sind, gibt es lokal
nicht-stumme PCM-Daten. Eine optionale Fehlermeldung allein genügt dann nicht:
discord.py 2.7.1 kann UDP-OSErrors pro Paket abfangen und die Wiedergabe trotzdem
normal beenden. Die zusätzliche Transportdiagnose ergänzt deshalb:

| Attribut | Bedeutung |
| --- | --- |
| `last_voice_packets_submitted` | Vom lokalen Socket ohne Fehler angenommene Pakete. **Keine** Empfangsbestätigung von Discord oder Zuhörern. |
| `last_voice_send_errors` | Lokale OSErrors beim Senden, auch wenn discord.py diese abfängt. |
| `last_dave_protocol` | Zuletzt beim Paketversand beobachtete DAVE-Protokollversion; null vor erstem Paket, 0 bedeutet keine aktive DAVE-Protokollversion. |
| `last_dave_unready_packets` | Sendeversuche bei DAVE-Protokoll > 0 ohne bereite Session; ab 1.0.2 werden diese vor dem Socket blockiert. |

Die Werte gelten pro Durchsageversuch und werden beim nächsten Versuch
zurückgesetzt. Discords abschließende Stille-Pakete zählen mit; die Anzahl kann
daher z. B. fünf höher sein als `last_audio_frames`. Es werden nur Zähler und die
Protokollversion erfasst, keine Paketbytes, Adressen, Schlüssel oder Session-IDs.
Die Diagnose deaktiviert keine Verschlüsselung; ab 1.0.2 werden unbereite DAVE-Sendeversuche blockiert.

Viele Sendefehler grenzen auf ein lokales Transportproblem ein. DAVE-unbereite
Pakete sind ein Hinweis auf die Aushandlung, kein Beweis über den Zustand beim
Empfänger. Erfolgreiche lokale Submits und DAVE-Bereitschaft schließen spätere
Netzwerk-/Empfangsprobleme nicht aus. Ein zweiter Discord-Client als Zuhörer hilft,
eine lokale Wiedergabeeinstellung zu unterscheiden.

Die Erweiterung verwendet einen kleinen Adapter der fest gepinnten discord.py-
Verbindungsklasse. Für die Messung ist nach Installation ein Neustart von HA bzw.
ein vollständiges Neuladen der Integration und Neuverbinden des Bots erforderlich.


### Korrektur in 1.0.2

Die Kombination discord.py 2.7.1 / davey 0.2.0 kann die DAVE-Sitzung unbereit
lassen. 1.0.2 verwendet die kompatible davey-Version 0.1.7. Vor der Wiedergabe
wartet der Bot bis zu zehn Sekunden auf Bereitschaft. Bleibt sie aus, zeigt HA
einen Fehler; während der Wiedergabe werden ebenfalls keine unbereiten
DAVE-Pakete mehr gesendet. Verschlüsselung bleibt aktiv.

Nach Bereitstellung Version 1.0.2 installieren und **Home Assistant vollständig
neu starten**, damit die geänderte native Abhängigkeit geladen wird. Bot wieder
in einen Sprachkanal verbinden und kurze TTS-Nachricht testen. Erwartet:
hörbarer Ton, `last_dave_protocol: 1`, `last_dave_unready_packets: 0`,
`last_voice_send_errors: 0`. Diese Zahlen allein ersetzen den Hörtest nicht.
Die erfolgreiche Wiedergabe in der Benutzerinstallation steht noch aus.


### Diagnose nach DAVE-Timeout

Die zusätzliche Diagnose nach 1.0.2 zeigt auch bei einem Timeout vor dem ersten
Paket `loaded_discord_version`, `loaded_davey_version`, `dave_protocol_version`,
`dave_session_ready` und `dave_session_status`. Es sind Versionen der tatsächlich
geladenen Module, keine Aussage allein aus dem Manifest oder Paket-Metadaten.
Erwartet werden Discord 2.7.1 und davey 0.1.7. Ein bereits geladenes natives Modul
kann bis zu einem vollständigen HA-Neustart im Prozess bleiben. Die Sitzungswerte
sind eine Momentaufnahme beim Ende/Abbruch des Versuchs, keine Live-Sensoren.
`last_dave_protocol` bleibt ohne Sendeversuch weiterhin unbekannt.
