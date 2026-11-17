# Benutzerhandbuch – Your Discord Connect

> Bedienung der bestehenden Integration. Ausführliche Spezialanleitungen: [Installation](installation.md), [Dashboard](dashboard.md), [Voice/TTS](voice.md), [Direktnachrichten-API](api.md).

## Zweck
Your Discord Connect bildet Mitglieder eines Discord-Servers in Home Assistant als Geräte ab. Anwender können Anwesenheit, Sprachkanalbelegung und weitere Zustände einsehen sowie ausdrücklich Nachrichten oder TTS-Durchsagen auslösen.

## Voraussetzungen und Ersteinrichtung
1. Integration über HACS (benutzerdefiniertes Repository) oder manuell installieren und Home Assistant neu starten.
2. Einen Discord-Bot anlegen, **Server Members Intent** und **Presence Intent** aktivieren und den Bot auf den Server einladen.
3. In Home Assistant **Einstellungen → Geräte & Dienste → Integration hinzufügen → Your Discord Connect** öffnen.
4. Bot-Token eingeben und den gewünschten Server auswählen.

Die Bot-Erstellung und Einladung müssen durch eine entsprechend berechtigte Person erfolgen.

## Bedienung
- **Zentrale Konfiguration:** Synchronisationsknopf, Mitglieder- und Anwesenheitszähler, Bot-Gerät.
- **Benutzer:** Anzeigename, Benutzername, Presence, Sprachkanal, Mikrofon-/Lautsprecherstatus, AFK und Beobachtungszeitpunkte.
- **Synchronisierung:** Standardmäßig alle 30 Minuten; Intervall unter **Konfigurieren** ändern oder per Knopf sofort synchronisieren. Presence-/Voice-Ereignisse werden zusätzlich direkt verarbeitet.
- **Private Nachrichten:** Nachricht am Benutzergerät eingeben und ausdrücklich senden; Discord kann die Zustellung je nach Empfängereinstellung ablehnen.
- **TTS:** Am Bot-Gerät Sprachkanal auswählen, Text eingeben und **TTS ausführen** betätigen. Voraussetzung ist ein konfigurierter Home-Assistant-TTS-Anbieter.
- **Dashboard-Karten:** Sprachkanalübersicht und Textkanal-Feed; Einrichtung siehe [Dashboard-Anleitung](dashboard.md).

## Wichtige Einschränkungen
- „Zuletzt anwesend“ und „Zuletzt nicht anwesend“ sind Beobachtungszeitpunkte, keine exakten Discord-Loginzeiten.
- Unsichtbare Mitglieder erscheinen im Presence-Status als offline; eine aktive Sprachverbindung kann separat als Anwesenheit zählen.
- Bei Verbindungsproblemen können Entitäten vorübergehend nicht verfügbar sein.
- **TTS ist implementiert, aber die hörbare Ausgabe wurde im dokumentierten Stand noch nicht erfolgreich live abgenommen; die DAVE-Diagnose läuft.** Nicht als garantiert funktionierend behandeln.

## Hilfe und Datenschutz
Bei Problemen [Installationshilfe](installation.md) und [Voice-Diagnose](voice.md) verwenden. Niemals Bot-Tokens oder personenbezogene Mitgliederdaten in öffentlichen Fehlerberichten teilen.
