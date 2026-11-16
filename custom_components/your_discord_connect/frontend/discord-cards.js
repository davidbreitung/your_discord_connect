/* Your Discord Connect 1.0.0 — no external libraries or bot credentials. */
const DOMAIN = "your_discord_connect";
const CSS = `
:host{display:block;color:#dbdee1;font-family:var(--primary-font-family,system-ui,sans-serif)}
ha-card{display:block;background:#2b2d31;color:#dbdee1;border:1px solid #3f4147;border-radius:12px;overflow:hidden;box-shadow:none}
header{display:flex;align-items:center;gap:10px;padding:17px 18px;border-bottom:1px solid #1e1f22;font-weight:700;color:#f2f3f5;background:#313338}
header ha-icon{color:#949ba4}header small{margin-left:auto;color:#949ba4;font-size:11px;font-weight:500}
.body{overflow:auto;max-height:var(--discord-height,520px);padding:10px 8px 16px;scrollbar-width:thin;scrollbar-color:#1a1b1e transparent}
.notice{padding:14px 18px;color:#b5bac1;font-size:13px;line-height:1.6}.error{color:#f5b5b8;background:#3e2b30}
details{margin-top:12px}summary{cursor:pointer;font-size:11px;letter-spacing:.7px;text-transform:uppercase;font-weight:700;color:#949ba4;padding:9px 7px;user-select:none}
.channel{padding:6px 9px;display:flex;align-items:center;gap:8px;color:#b5bac1;font-weight:600;font-size:14px;border-radius:4px}
.channel:hover,.member:hover{background:#35373c;color:#f2f3f5}.channel ha-icon{--mdc-icon-size:20px;color:#949ba4}.count{margin-left:auto;font-size:11px;color:#949ba4}
.member{display:flex;align-items:center;gap:9px;margin:1px 3px 1px 28px;padding:5px 8px;border-radius:4px;font-size:14px;min-height:28px}
.name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.avatar{position:relative;width:28px;height:28px;flex-shrink:0;border-radius:50%;background:#5865f2;display:grid;place-items:center;color:white;font-size:12px;font-weight:700;overflow:visible}
.avatar img{width:100%;height:100%;border-radius:50%;object-fit:cover}.presence{position:absolute;right:-2px;bottom:-2px;width:8px;height:8px;border:3px solid #2b2d31;border-radius:50%;background:#80848e}
.online{background:#23a55a}.idle{background:#f0b232}.dnd{background:#f23f43}.badges{margin-left:auto;display:flex;align-items:center;gap:5px}.badges ha-icon{--mdc-icon-size:17px;color:#f23f43}.tag{background:#5865f2;color:white;font-size:9px;border-radius:3px;padding:2px 4px;font-weight:600}.afk{background:#41434a;color:#b5bac1}
.feed{background:#313338;padding:12px 0}.message{display:flex;gap:14px;padding:6px 18px}.message:hover{background:#2e3035}.message .avatar{width:36px;height:36px;margin-top:3px}.message-main{min-width:0;flex:1}.byline{display:flex;align-items:baseline;gap:7px;flex-wrap:wrap}.author{color:#f2f3f5;font-weight:600;font-size:14px}.time,.edited{color:#949ba4;font-size:10px;font-weight:400}.content{font-size:14px;line-height:1.55;white-space:pre-wrap;overflow-wrap:anywhere;margin-top:3px}.content code{background:#1e1f22;padding:1px 4px;border-radius:3px;font-size:12px}.content a,.attachment{color:#00a8fc;text-decoration:none}.content a:hover,.attachment:hover{text-decoration:underline}
.reply{font-size:11px;color:#b5bac1;margin-bottom:4px}.day{display:flex;align-items:center;gap:8px;color:#949ba4;font-size:10px;font-weight:600;margin:14px 18px}.day:before,.day:after{content:"";height:1px;flex:1;background:#41434a}.embed{margin-top:8px;border-left:4px solid #5865f2;border-radius:4px;background:#2b2d31;padding:10px;max-width:420px}.embed>strong{display:block;margin-bottom:4px}.attachment{display:block;margin-top:8px;font-size:13px;overflow-wrap:anywhere}.attachment img{display:block;max-width:100%;max-height:240px;border-radius:6px;margin-top:6px}.empty{color:#949ba4;font-size:12px;padding:4px 0 10px 46px}.footer{padding:9px 18px;font-size:10px;color:#949ba4;border-top:1px solid #3f4147}.placeholder{font-style:italic;color:#949ba4}
`;
function node(tag, text, cls) {
  const el = document.createElement(tag);
  if (text !== undefined && text !== null) el.textContent = text;
  if (cls) el.className = cls;
  return el;
}
function icon(name, title) {
  const el = node("ha-icon"); el.setAttribute("icon", `mdi:${name}`);
  if (title) { el.title = title; el.setAttribute("aria-label", title); }
  return el;
}
function safeURL(value, image = false) {
  try {
    const url = new URL(value);
    if (url.protocol !== "https:") return null;
    if (image && !["cdn.discordapp.com", "media.discordapp.net"].includes(url.hostname)) return null;
    return url.href;
  } catch { return null; }
}
function avatar(url, name, presence) {
  const box = node("span", (name || "?").slice(0, 1).toUpperCase(), "avatar");
  const src = safeURL(url, true);
  if (src) {
    const img = node("img"); img.src = src; img.alt = ""; img.loading = "lazy";
    img.referrerPolicy = "no-referrer";
    img.addEventListener("error", () => img.remove(), {once: true});
    box.append(img); box.firstChild.remove();
  }
  if (presence) {
    const dot = node("span", null, `presence ${["online", "idle", "dnd"].includes(presence) ? presence : "offline"}`);
    dot.title = {online:"Online",idle:"Abwesend",dnd:"Nicht stören",offline:"Offline / unsichtbar"}[presence] || "Unbekannt";
    box.append(dot);
  }
  return box;
}
function link(url, label) {
  const target = safeURL(url);
  if (!target) return node("span", label);
  const a = node("a", label); a.href = target; a.target = "_blank"; a.rel = "noopener noreferrer";
  return a;
}
function content(value) {
  // Parse only a small, safe inline subset; user text is never used as HTML.
  const el = node("div", null, "content");
  const tokens = String(value || "").split(/(https:\/\/[^\s<>]+|\*\*[^*\n]+\*\*|`[^`\n]+`|\*[^*\n]+\*)/g);
  for (const part of tokens) {
    if (part.startsWith("https://")) el.append(link(part, part));
    else if (/^\*\*.+\*\*$/.test(part)) el.append(node("strong", part.slice(2,-2)));
    else if (/^`.+`$/.test(part)) el.append(node("code", part.slice(1,-1)));
    else if (/^\*.+\*$/.test(part)) el.append(node("em", part.slice(1,-1)));
    else el.append(document.createTextNode(part));
  }
  return el;
}
class DiscordCard extends HTMLElement {
  constructor() { super(); this.attachShadow({mode:"open"}); this._generation = 0; }
  setConfig(config) {
    if (config.height !== undefined && (!Number.isFinite(config.height) || config.height < 150 || config.height > 1600)) throw Error("height: 150–1600 Pixel");
    if (config.refresh_interval !== undefined && (!Number.isFinite(config.refresh_interval) || config.refresh_interval < 15 || config.refresh_interval > 300)) throw Error("refresh_interval: 15–300 Sekunden");
    this._config = {...config}; this._data = null; this._error = ""; this._stop(); this._render(); this._start();
  }
  set hass(hass) {
    const changed = this._hass?.connection !== hass.connection;
    this._hass = hass;
    if (changed) { this._stop(); this._start(); }
  }
  connectedCallback() { this._start(); }
  disconnectedCallback() { this._stop(); }
  getCardSize() { return Math.ceil((this._config?.height || 520) / 50); }
  _stop() {
    this._generation++; clearTimeout(this._timer); this._running = false;
    if (this._unsubscribe) { Promise.resolve(this._unsubscribe()).catch(()=>{}); this._unsubscribe = null; }
  }
  _shell(title, glyph, subtitle) {
    const style = node("style", CSS); const card = node("ha-card");
    card.style.setProperty("--discord-height", `${this._config?.height || 520}px`);
    const header = node("header"); header.append(icon(glyph), node("span", title));
    if (subtitle) header.append(node("small", subtitle)); card.append(header);
    if (this._error) card.append(node("div", this._error, "notice error"));
    else if (!this._config?.entry_id) card.append(node("div", "Bitte in der Kartenkonfiguration einen Discord-Server auswählen.", "notice"));
    this.shadowRoot.replaceChildren(style, card); return card;
  }
  _fail(err) { this._data = null; this._error = err?.message || "Discord-Daten nicht verfügbar. Verbindung und Berechtigungen prüfen."; this._render(); }
}
class DiscordChannelOverview extends DiscordCard {
  static getConfigElement() { return document.createElement("discord-channel-overview-editor"); }
  static getStubConfig() { return {type:"custom:discord-channel-overview", title:"Discord-Channel-Overview", entry_id:""}; }
  async _start() {
    if (this._running || !this.isConnected || !this._hass || !this._config?.entry_id) return;
    this._running = true; clearTimeout(this._timer); const generation = this._generation;
    try {
      const unsubscribe = await this._hass.connection.subscribeMessage(data => {
        if (generation !== this._generation) return;
        this._data = data; this._error = data.available ? "" : "Discord-Verbindung nicht verfügbar."; this._render();
      }, {type:`${DOMAIN}/overview`, entry_id:this._config.entry_id});
      if (generation !== this._generation) unsubscribe(); else this._unsubscribe = unsubscribe;
    } catch (err) {
      if (generation !== this._generation) return;
      this._running = false; this._fail(err); this._timer = setTimeout(()=>this._start(), 15000);
    }
  }
  _render() {
    const collapsed = new Set([...this.shadowRoot.querySelectorAll("details")].filter(el=>!el.open).map(el=>el.dataset.id));
    const scroll = this.shadowRoot.querySelector(".body")?.scrollTop || 0;
    const card = this._shell(this._config?.title || "Discord-Channel-Overview", "discord", this._data?.server);
    if (!this._data || this._error) {
      if (this._config?.entry_id && !this._error) card.append(node("div", "Discord-Daten werden geladen …", "notice"));
      return;
    }
    const body = node("div", null, "body");
    for (const group of this._data.groups) {
      let container = body;
      if (group.name) {
        container = node("details"); container.dataset.id = group.id; container.open = !collapsed.has(group.id);
        container.append(node("summary", group.name)); body.append(container);
      }
      for (const channel of group.channels) {
        const row = node("div", null, "channel"); row.append(icon(channel.stage ? "account-voice" : "volume-high"), node("span", channel.name, "name"), node("span", channel.members.length, "count"));
        container.append(row);
        for (const member of channel.members) {
          const item = node("div", null, "member"); item.title = member.username;
          item.append(avatar(member.avatar, member.name, member.presence), node("span", member.name, "name"));
          if (member.bot) item.append(node("span", "BOT", "tag"));
          const badges = node("span", null, "badges");
          if (member.afk) badges.append(node("span", "AFK", "tag afk"));
          if (member.microphone_muted) badges.append(icon("microphone-off", "Mikrofon stumm"));
          if (member.speaker_muted) badges.append(icon("headphones-off", "Lautsprecher stumm"));
          item.append(badges); container.append(item);
        }
      }
    }
    if (!this._data.groups.length) body.append(node("div", "Keine sichtbaren Sprachkanäle.", "notice"));
    card.append(body); body.scrollTop = scroll;
  }
}
class DiscordTextChannelFeed extends DiscordCard {
  static getConfigElement() { return document.createElement("discord-text-channel-feed-editor"); }
  static getStubConfig() { return {type:"custom:discord-text-channel-feed", title:"Discord-Text-Channel-Feed", entry_id:"", channel_id:""}; }
  async _start() {
    if (this._running || !this.isConnected || !this._hass || !this._config?.entry_id || !this._config?.channel_id) return;
    this._running = true; clearTimeout(this._timer); const generation = this._generation;
    try {
      const data = await this._hass.callWS({type:`${DOMAIN}/feed`, entry_id:this._config.entry_id, channel_id:String(this._config.channel_id)});
      if (generation !== this._generation) return;
      this._data = data; this._error = ""; this._render();
    } catch (err) { if (generation === this._generation) this._fail(err); }
    finally {
      if (generation === this._generation) {
        this._running = false;
        this._timer = setTimeout(()=>this._start(), (this._config.refresh_interval || 15)*1000);
      }
    }
  }
  _render() {
    const previous = this.shadowRoot.querySelector(".body");
    const bottom = !previous || previous.scrollHeight - previous.scrollTop - previous.clientHeight < 70;
    const scroll = previous?.scrollTop || 0;
    const card = this._shell(this._config?.title || "Discord-Text-Channel-Feed", "pound", this._data ? `# ${this._data.channel}` : "");
    if (!this._config?.channel_id) { card.append(node("div", "Bitte einen Textkanal auswählen.", "notice")); return; }
    if (!this._data || this._error) {
      if (this._config?.entry_id && !this._error) card.append(node("div", "Discord-Daten werden geladen …", "notice"));
      return;
    }
    const body = node("div", null, "body feed"); let day = "";
    for (const message of this._data.messages) {
      const date = new Date(message.timestamp); const label = date.toLocaleDateString(this._hass?.locale?.language || "de", {day:"numeric",month:"long",year:"numeric"});
      if (label !== day) { body.append(node("div", label, "day")); day = label; }
      const row = node("article", null, "message"); row.append(avatar(message.avatar, message.author));
      const main = node("div", null, "message-main");
      if (message.reply_to) main.append(node("div", `↳ Antwort an ${message.reply_to}`, "reply"));
      const byline = node("div", null, "byline"); byline.append(node("span", message.author, "author"));
      if (message.bot) byline.append(node("span", "BOT", "tag"));
      const time = node("time", date.toLocaleTimeString(this._hass?.locale?.language || "de", {hour:"2-digit",minute:"2-digit"}), "time"); time.dateTime = message.timestamp; time.title = date.toLocaleString(); byline.append(time); main.append(byline);
      if (message.content) main.append(content(message.content));
      else if (!message.attachments.length && !message.embeds.length) main.append(node("div", "Inhalt nicht verfügbar (z. B. Systemnachricht oder fehlender Message Content Intent).", "content placeholder"));
      if (message.edited) main.append(node("span", "(bearbeitet)", "edited"));
      for (const embed of message.embeds) {
        const box = node("div", null, "embed"); box.append(node("strong", embed.title), content(embed.description));
        if (embed.url) box.append(link(embed.url, "Öffnen ↗")); main.append(box);
      }
      for (const attachment of message.attachments) {
        const a = link(attachment.url, attachment.name); a.className = "attachment";
        const src = attachment.image && safeURL(attachment.url, true);
        if (src) { const img = node("img"); img.src = src; img.alt = attachment.name; img.loading = "lazy"; img.referrerPolicy = "no-referrer"; a.append(img); }
        main.append(a);
      }
      row.append(main); body.append(row);
    }
    if (!this._data.messages.length) body.append(node("div", "Noch keine Nachrichten in diesem Kanal.", "notice"));
    card.append(body, node("div", `Letzte 50 Nachrichten · Aktualisierung alle ${this._config.refresh_interval || 15} Sekunden · Nur lesen`, "footer"));
    body.scrollTop = bottom ? body.scrollHeight : scroll;
  }
}
class DiscordCardEditor extends HTMLElement {
  constructor() { super(); this.attachShadow({mode:"open"}); this._servers = []; this._channels = []; this._generation = 0; }
  setConfig(config) { this._config = {...config}; this._render(); this._load(); }
  set hass(hass) { this._hass = hass; this._load(); }
  connectedCallback() { this._load(); }
  disconnectedCallback() { this._generation++; this._loading = false; this._loaded = null; }
  async _load() {
    if (!this.isConnected || !this._hass || !this._config || this._loading) return;
    const key = this._config.entry_id || "none";
    if (this._loaded === key) return;
    this._loading = true; const generation = this._generation;
    try {
      this._servers = await this._hass.callWS({type:`${DOMAIN}/servers`});
      if (generation !== this._generation) return;
      this._channels = [];
      if (this._config.entry_id && this.feed) {
        const data = await new Promise((resolve, reject) => {
          let cleanup; let received = false;
          const timeout = setTimeout(()=>{ received = true; if (cleanup) cleanup(); reject(Error("Kanalliste nicht verfügbar")); }, 10000);
          this._hass.connection.subscribeMessage(value => {
            received = true; clearTimeout(timeout); resolve(value); if (cleanup) cleanup();
          }, {type:`${DOMAIN}/overview`, entry_id:this._config.entry_id}).then(unsubscribe => {
            cleanup = unsubscribe; if (received) unsubscribe();
          }).catch(err=>{clearTimeout(timeout);reject(err);});
        });
        if (generation !== this._generation) return;
        this._channels = data.text_channels || [];
      }
      this._loaded = key; this._error = "";
    } catch(err) { if (generation === this._generation) this._error = err.message || "Daten konnten nicht geladen werden."; }
    finally { if (generation === this._generation) {this._loading = false; this._render();} }
  }
  _change(key, value) {
    this._config = {...this._config, [key]:value};
    if (key === "entry_id") { this._config.channel_id = ""; this._loaded = null; this._generation++; this._loading = false; this._load(); }
    this.dispatchEvent(new CustomEvent("config-changed", {detail:{config:this._config}, bubbles:true, composed:true}));
  }
  _render() {
    if (!this._config) return;
    const style = node("style", ":host{display:block}label{display:block;margin:14px 0;font-size:14px}input,select{box-sizing:border-box;width:100%;margin-top:6px;padding:12px;border:1px solid var(--divider-color,#888);border-radius:6px;background:var(--card-background-color,#fff);color:var(--primary-text-color,#222);font:inherit}p{font-size:12px;line-height:1.5;color:var(--secondary-text-color)}");
    const form = node("div");
    const field = (key, title, options) => {
      const label = node("label", title); const input = node(options ? "select" : "input");
      if (options) {
        const empty = node("option", "Bitte auswählen"); empty.value = ""; input.append(empty);
        for (const option of options) { const el = node("option", option.name); el.value = option.id; input.append(el); }
      }
      input.value = this._config[key] ?? "";
      input.addEventListener("change", ()=>this._change(key, input.value)); label.append(input); form.append(label);
    };
    field("title", "Titel"); field("entry_id", "Discord-Server", this._servers);
    if (this.feed) field("channel_id", "Textkanal", this._channels.map(c=>({id:c.id,name:`${c.category ? c.category+" / " : ""}# ${c.name}`})));
    form.append(node("p", this.feed ? "Der Bot benötigt Kanal ansehen, Nachrichtenverlauf anzeigen und den Message Content Intent. Aktualisierung: 15 Sekunden." : "Sprachkanäle und Kategorien werden in Discord-Reihenfolge angezeigt. Änderungen kommen über das Gateway."));
    if (this._error) form.append(node("p", this._error)); this.shadowRoot.replaceChildren(style, form);
  }
}
class OverviewEditor extends DiscordCardEditor { get feed() {return false;} }
class FeedEditor extends DiscordCardEditor { get feed() {return true;} }
for (const [name, component] of [["discord-channel-overview",DiscordChannelOverview],["discord-text-channel-feed",DiscordTextChannelFeed],["discord-channel-overview-editor",OverviewEditor],["discord-text-channel-feed-editor",FeedEditor]]) {
  if (!customElements.get(name)) customElements.define(name, component);
}
window.customCards = window.customCards || [];
for (const card of [
  {type:"discord-channel-overview",name:"Discord-Channel-Overview",description:"Sprachkanäle, Mitglieder, Avatare und Mute-Status in Discord-Optik."},
  {type:"discord-text-channel-feed",name:"Discord-Text-Channel-Feed",description:"Die letzten Nachrichten eines konfigurierbaren Discord-Textkanals."}
]) { if (!window.customCards.some(existing=>existing.type===card.type)) window.customCards.push(card); }
