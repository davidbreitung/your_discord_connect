# Schnittstelle für andere Integrationen und Automationen

Ab Version 0.3.0 kann eine andere Integration die konfigurierten Discord-Bots zum
Versand privater **Textnachrichten** nutzen. Sie benötigt keine eigene Bot-Anmeldung
und keinen Zugriff auf Tokens. Audio, TTS-Wiedergabe, Dateianhänge und Video sind
nicht Bestandteil dieser DM-Schnittstelle. Für TTS-Durchsagen im Sprachkanal gibt es
seit 0.4.0 die separaten [Bot-Entitäten](voice.md).

## Empfänger

Als Empfänger dient die Home-Assistant-**Geräte-ID** eines Mitgliedsgeräts aus der
Gruppe **Benutzer**. Keine Discord-Benutzer-ID, kein Anzeigename und keine Entitäts-ID
übergeben. Das zentrale Konfigurationsgerät ist kein gültiger Empfänger.

Über das Gerät ermittelt die Integration den zugehörigen Servereintrag, dessen Bot
und die Discord-Benutzer-ID. Bei Mitgliedschaft auf mehreren Servern entscheidet
das ausgewählte Mitgliedsgerät, welcher Bot verwendet wird. Der Servereintrag muss
geladen sein und das Mitglied im letzten erfolgreichen Mitgliederabgleich enthalten
sein. Der Empfänger muss nicht online sein. Discord kann DMs dennoch verweigern,
z. B. aufgrund von Privatsphäre-Einstellungen, Blockierung oder fehlendem gemeinsamen
Server. Bots sind zwar Geräte in der Liste, aber kein verlässliches DM-Ziel.

## Home-Assistant-Aktion

Unter **Entwicklerwerkzeuge → Aktionen** die Aktion
`your_discord_connect.send_direct_message` auswählen. Das Formular bietet eine
Geräteauswahl für Benutzergeräte und ein Textfeld.

```yaml
action: your_discord_connect.send_direct_message
data:
  device_id: "HIER_DIE_HOME_ASSISTANT_GERAETE_ID"
  content: "Die Waschmaschine ist fertig."
response_variable: discord_result
```

`response_variable` ist optional. Bei Erfolg enthält die Antwort:

```json
{"message_id": "123456789012345678", "recipient_id": "234567890123456789"}
```

Das ist eine Discord-Annahmebestätigung, keine Lese- oder Zustellbestätigung auf
dem Endgerät. Die Nachricht muss 1 bis 2000 Zeichen enthalten und darf nicht nur
aus Leerraum bestehen. Erwähnungsbenachrichtigungen sind über `allowed_mentions`
deaktiviert; der Aufrufer kann diese Vorgabe nicht überschreiben.

## Aufruf aus einer anderen Integration

Die Home-Assistant-Service-Schnittstelle vermeidet direkte Abhängigkeiten von
internen Python-Klassen:

```python
from homeassistant.exceptions import HomeAssistantError

if not hass.services.has_service("your_discord_connect", "send_direct_message"):
    raise HomeAssistantError("Your Discord Connect ist nicht verfügbar")

result = await hass.services.async_call(
    "your_discord_connect",
    "send_direct_message",
    {"device_id": selected_member_device_id, "content": text},
    blocking=True,
    return_response=True,
)
```

Bei einer ausdrücklich abhängigen Custom Integration ist auch der öffentliche
Python-Einstiegspunkt verfügbar:

```python
from custom_components.your_discord_connect.services import async_send_direct_message

result = await async_send_direct_message(hass, selected_member_device_id, text)
```

Die abhängige Integration muss sicherstellen, dass Your Discord Connect installiert
und der ausgewählte Server eingerichtet ist. Sie kann in ihrem Manifest
`"dependencies": ["your_discord_connect"]` deklarieren. Keine Coordinator-Interna,
gespeicherten Tokens oder privaten Methoden verwenden. Zur Auswahl der Mitglieder
den normalen HA-Geräteselektor mit Integration `your_discord_connect` und Modell
`Benutzer` nutzen; Namen sind keine stabilen Identifikatoren.

## Fehler und Wiederholungen

- Ungültige Texte, unbekannte/zentrale Geräte oder ungeladene Servereinträge führen
  zu `ServiceValidationError`.
- Discord-Fehler führen zu `HomeAssistantError` mit übersetzbarer Fehlermeldung:
  ungültiges Token, verweigerte DM, Ratenbegrenzung oder fehlgeschlagene Anfrage.
- Es erfolgen **keine automatischen Sende-Wiederholungen**. Bei Timeout oder einer
  unlesbaren Bestätigung kann die Nachricht bereits versendet worden sein.
  Automatisches Wiederholen könnte doppelte Nachrichten erzeugen.
- Pro Aufruf wird genau ein Empfänger adressiert. Keine impliziten Rundnachrichten,
  Hintergrundnachrichten oder Nachrichten beim Einrichten der Integration.

Die Aktion selbst legt den Nachrichtentext nicht als eigenen HA-Zustand oder
eigenen Protokolleintrag ab. Das separate Benutzer-Textfeld ab 1.0.0 ist dagegen
ein regulärer HA-Zustand und kann im Recorder erscheinen (siehe [Dashboard-Anleitung](dashboard.md)).
Home-Assistant-Automations-Traces können Aktionsdaten enthalten;
der aufrufende Dienst sollte entsprechend mit vertraulichen Texten umgehen.

## Beobachten von Benutzerzuständen

Andere Integrationen und Automationen können die regulären HA-Entitäten beobachten.
Presence, Sprachkanal, Mute und AFK werden per Gateway sofort aktualisiert.
Für Zustandsautomationen sind keine eigenen Discord-Abonnements erforderlich.
Die drei Zeitstempel sind Beobachtungsdaten; ihre genaue Bedeutung steht in der README.
