# Bot-Gerät, Kanalauswahl und TTS-Durchsagen

Ab Version **0.4.0** gibt es in der Untergruppe **zentrale Konfiguration** zusätzlich
ein Gerät **Bot: <Bot-Name>**. Es besitzt drei Entitäten:

| Entität | Funktion |
| --- | --- |
| Sprachkanal | Dropdown zum Beitreten, Wechseln und Verlassen. |
| TTS-Nachricht | Eingabefeld für bis zu 255 Zeichen, entsprechend Home Assistants Zustandslängenlimit. |
| TTS ausführen | Erzeugt mit Home Assistants Standard-TTS-Anbieter Sprache und spielt sie im gewählten Kanal ab. |

Der eigene Bot wird anhand der ID des authentifizierten Discord-Benutzers erkannt,
nicht anhand seines Namens. Nur dieses Mitglied wird aus der Gruppe **Benutzer**
ausgenommen; andere Bots bleiben sichtbar. Wenn keine eindeutige ID verfügbar ist,
wird kein Mitglied ausgeblendet. Die Serverzähler enthalten weiterhin alle Mitglieder,
einschließlich des eigenen Bots. Vorhandene Mitgliederentitäten des eigenen Bots
werden entfernt und durch das zentrale Bot-Gerät ersetzt; darauf verweisende
Automationen gegebenenfalls anpassen. Die übrigen Mitgliedergeräte behalten ihre IDs.

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
4. **FFmpeg mit Opus-Unterstützung** muss verfügbar sein. Die Integration verwendet
   den in Home Assistants FFmpeg-Integration konfigurierten Programm-Pfad.
   Home Assistant OS/Container bringt FFmpeg üblicherweise mit. Bei eigener
   Python-Installation FFmpeg zusätzlich installieren. Es wird kein FFmpeg über
   einen frei eingebbaren Nachrichtenparameter ausgeführt.
5. Discord-Voice braucht neben HTTPS und Gateway-WSS **ausgehendes UDP** zum von
   Discord ausgehandelten Voice-Server/Port und dessen Voice-WebSocket. Eine reine
   HTTPS-Proxy-Freigabe genügt nicht. Bei Verbindungsproblemen Firewall/Container-Netz
   prüfen. Es wird kein eingehender Port zur Home-Assistant-Oberfläche benötigt.

Die Integration installiert `discord.py[voice]==2.7.1` mit der Voice-Unterstützung
einschließlich PyNaCl und DAVE. Discord-Verbindung und Audioübertragung bleiben
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
HA-TTS-Unterbau. Beliebige Audiostreams, Lautstärkeregelung und Video sind nicht Teil
dieser Version.

## Stand der Prüfung

Automatisierte Tests prüfen Gerätezuordnung, Kanalauswahl/-wechsel, Kanaländerungen,
Queue/Abbruch, Rechtefehler, den HA-TTS-Aufruf und die tatsächliche WAV-zu-Opus-
Verarbeitung mit FFmpeg. Discord-Verbindungen und TTS-Anbieter werden simuliert.
Ein vollständiger Hörtest mit echtem Bot, Voice-Netzwerk und Deiner HA-TTS-Stimme
steht noch aus.
