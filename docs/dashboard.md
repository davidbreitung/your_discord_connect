# Dashboard-Karten und private Nachrichten (1.0.2)

Die Integration enthält zwei eigene Lovelace-Karten. Es ist kein weiteres
HACS-Frontend-Repository nötig. Beide Karten verwenden die bestehende Integration;
Bot-Token gehören niemals in die Kartenkonfiguration.

## 1. Kartenressource registrieren

1. Die vollständige Integration einschließlich des Ordners `frontend` installieren
   und Home Assistant neu starten.
2. Im Benutzerprofil **Erweiterter Modus** aktivieren.
3. Unter **Einstellungen → Dashboards → ⋮ → Ressourcen** eine Ressource hinzufügen:
   - URL: `/your_discord_connect/discord-cards.js?v=1.0.2`
   - Typ: **JavaScript-Modul**
4. Dashboard im Browser neu laden. Bei Updates die Versionsangabe in dieser URL
   ändern, falls der Browser noch die alte Datei verwendet.
5. **Dashboard bearbeiten → Karte hinzufügen** öffnen. Nach
   **Discord-Channel-Overview** oder **Discord-Text-Channel-Feed** suchen.
6. Im visuellen Editor den eingerichteten Discord-Server und beim Feed zusätzlich
   den Textkanal auswählen. Speichern.

Bei YAML-Dashboards die Ressource stattdessen in der bestehenden
`lovelace.resources`-Liste ergänzen:

```yaml
lovelace:
  resources:
    - url: /your_discord_connect/discord-cards.js?v=1.0.2
      type: module
```

Die Ressource wird absichtlich nicht automatisch in die Dashboard-Konfiguration
hineingeschrieben. Sie wird von Home Assistant lokal ausgeliefert; es gibt keine
extern geladenen JavaScript-Bibliotheken. Profil- und Anhangsbilder lädt der Browser
von Discords CDN, wofür die jeweiligen Endgeräte Internetzugang benötigen.

## Discord-Channel-Overview

- Kategorien, Sprach- und Stage-Kanäle folgen den Discord-Positionen, bei gleichen
  Positionen der Kanal-ID. Kanäle ohne Kategorie stehen zuerst. Textkanäle werden
  in dieser Karte ausgeblendet; Kategorien ohne Sprachkanäle ebenfalls.
- Jeder Kanal zeigt die aktuell bekannten Mitglieder, einschließlich des eigenen Bots.
  Die Zuordnung erfolgt über IDs und bleibt auch bei gleichen Kanalnamen korrekt.
- Server-Anzeigename, Server-/Profilavatar, Presence-Punkt, Mikrofon-Mute,
  Lautsprecher-Mute und AFK sind sichtbar. Mute umfasst Selbst- und Server-Mute.
- Presence und Kanalwechsel werden per Gateway und Home-Assistant-WebSocket
  aktualisiert. Neue Mitglieder werden beim nächsten vollständigen Sync entdeckt.
- Kategorien lassen sich einklappen. Kanaländerungen werden über das Gateway und
  beim vollständigen Benutzersync übernommen. Bei Verbindungsverlust wird eine
  Fehlermeldung statt eines vermeintlich aktuellen Kanalbilds angezeigt.

```yaml
type: custom:discord-channel-overview
title: Discord-Channel-Overview
entry_id: DEINE_CONFIG_ENTRY_ID
height: 520
```

`entry_id` ist die ID des **Home-Assistant-Integrationseintrags**, nicht die
Discord-Server-ID. Der visuelle Editor setzt sie automatisch; bei Bedarf dort
anschließend in den Code-Editor wechseln und die fertige Konfiguration kopieren.
`height` begrenzt den scrollbaren Inhalt auf 150–1600 Pixel.

Die Darstellung orientiert sich an Discords dunkler Oberfläche. Mitglieder werden
je Kanal alphabetisch nach Anzeigenamen sortiert. Discord-interne Sortieroptionen,
Sprechaktivitätsrahmen, Bildschirmübertragungen und Rollenfarben sind nicht enthalten.
Ein unsichtbares Mitglied bleibt als offline markiert, kann aber im Sprachkanal
sichtbar sein – genau die Daten, die Discord dem Bot bereitstellt.

## Discord-Text-Channel-Feed

Vor der Verwendung für die gewünschten Kanäle konfigurieren:

1. Discord-Berechtigungen **View Channel / Kanal ansehen** und
   **Read Message History / Nachrichtenverlauf anzeigen** für den Bot erlauben.
   Kanalüberschreibungen beachten. **Send Messages** wird für diesen Feed nicht benötigt.
2. Im [Discord Developer Portal](https://discord.com/developers/applications)
   die Anwendung öffnen und unter **Bot → Privileged Gateway Intents** den
   **Message Content Intent** aktivieren. Bei verifizierten/größeren Bots kann eine
   Genehmigung von Discord erforderlich sein. Diese Freigabe betrifft auch die
   per REST gelesenen Inhalte; die Integration abonniert dafür keine Nachrichten-Events.
3. Im Karteneditor einen normalen Text- oder Ankündigungskanal auswählen.

```yaml
type: custom:discord-text-channel-feed
title: Discord-Text-Channel-Feed
entry_id: DEINE_CONFIG_ENTRY_ID
channel_id: "123456789012345678"
height: 520
refresh_interval: 15
```

IDs im YAML als Zeichenketten schreiben. Die Karte zeigt die **letzten 50 Nachrichten**
in zeitlicher Reihenfolge, mit Namen, Avataren, Zeitangaben, Antwortverweis,
Bearbeitungsmarkierung, Bildern/Anhangslinks und einfachen Embeds. Sie aktualisiert
sich standardmäßig alle **15 Sekunden** (einstellbar bis 300). Bearbeitungen und
Löschungen erscheinen beim nächsten erfolgreichen Abruf. Gleichzeitige Karten
teilen einen 15-Sekunden-Cache pro Kanal; maximal acht Kanäle bleiben im Cache.
Nach jedem Abruf scrollt die Karte automatisch ganz nach unten zu den neuesten
Nachrichten, auch wenn zuvor nach oben gescrollt wurde. Nachgeladene Bilder werden
berücksichtigt. Geschlossene Karten beenden ihre Aktualisierung.

Der Feed ist **nur lesend**. Er unterstützt einfache Fettschrift, Kursivschrift,
Inline-Code und HTTPS-Links. Benutzertext wird nicht als HTML ausgeführt. Discords
vollständiges Markdown, aufgelöste Erwähnungen, Reaktionen, Sticker, Threads,
interaktive Komponenten, Videos und endloses Nachladen sind nicht enthalten.
Ein leerer Nachrichteninhalt kann auch eine Systemnachricht sein; bei vielen leeren
Nachrichten den Message Content Intent prüfen. Dies ist eine Discord-nahe
Darstellung, keine eingebettete Discord-App.

## Zugriff und Speicherung

Die Daten-API erfordert eine angemeldete Home-Assistant-WebSocket-Verbindung.
Kartenbenutzer brauchen Leserechte auf die Entität **Benutzer jetzt synchronisieren**
des jeweiligen Servers. Damit können sie in der Feed-Karte die für den Bot lesbaren
Textkanäle dieses Servers auswählen. Es gibt keine Verknüpfung zwischen einem
Home-Assistant-Konto und dessen persönlichen Discord-Kanalrechten. Für eingeschränkte
Dashboards die Kanalrechte des Bots und die HA-Zugriffsrechte entsprechend wählen.
In der Sprachkanal-Karte werden zusätzlich die Leserechte auf die Anzeigenamen-
Entität jedes Mitglieds berücksichtigt.

Feed-Inhalte liegen nur im begrenzten Arbeitsspeicher-Cache und werden nicht als
Entitäten oder in der Recorder-Historie gespeichert. Bot-Token und private
Direktnachrichten werden über diese Karten-API nicht ausgegeben.

## Private Nachricht pro Mitglied

In **Geräte & Dienste → Your Discord Connect → Benutzer → Mitglied** stehen jetzt:

- **Private Nachricht**: Textfeld für bis zu **255 Zeichen** (Home-Assistant-Zustandslimit).
- **Private Nachricht senden**: sendet den eingegebenen Text einmalig als
  Discord-Direktnachricht an genau dieses Mitglied. Absender ist der konfigurierte Bot.

Texteingabe allein sendet nichts. Nach bestätigtem Versand wird das Feld geleert.
Bei einem Fehler bleibt es erhalten; es gibt keine automatische Wiederholung.
Eine während des Versands neu eingegebene Nachricht wird nicht gelöscht.
Gleichzeitige doppelte Button-Aufrufe werden abgewiesen. Discord kann DMs aufgrund
von Privatsphäre-Einstellungen oder einer Blockierung ablehnen.

Entwürfe werden beim Neuladen/Neustart nicht wiederhergestellt. Das Textfeld ist
jedoch ein regulärer HA-Zustand und kann in Verlauf/Recorder erscheinen. Falls
gewünscht, diese Textentitäten in der eigenen Recorder-Konfiguration ausschließen.
Für längere Nachrichten bis 2000 Zeichen weiterhin die vorhandene Aktion
`your_discord_connect.send_direct_message` verwenden; siehe [API-Anleitung](api.md).
Der eigene Bot hat kein Benutzergerät und erhält daher keine DM-Bedienelemente.

## Fehlerbehebung

| Problem | Prüfung |
| --- | --- |
| Custom element doesn't exist | Ressource als JavaScript-Modul registrieren, URL prüfen und Browser neu laden. |
| Server fehlt im Editor | Integration muss geladen sein; HA-Leserechte auf die zentrale Sync-Entität prüfen. |
| Textkanal fehlt | Bot-Kanalrechte prüfen, dann **Benutzer jetzt synchronisieren** und Editor neu öffnen. Threads sind nicht unterstützt. |
| Nachrichten fehlen | Message Content Intent und Nachrichtenverlauf-Recht prüfen. Bot muss den Kanal sehen können. |
| Avatar fehlt | Browser-Zugriff auf `cdn.discordapp.com` bzw. `media.discordapp.net` prüfen. |
| DM schlägt fehl | Benutzer erlaubt möglicherweise keine DMs oder blockiert den Bot; Fehler am Button beachten. |
