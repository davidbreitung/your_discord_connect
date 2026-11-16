const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const path = require('node:path');
const fs = require('node:fs');
let browser;
before(async () => {
  browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH || undefined, headless:true});
});
after(async () => { await browser?.close(); });
async function setup() {
  const page = await browser.newPage({viewport:{width:1080,height:850}});
  await page.route('https://**/*', route => route.abort());
  await page.setContent('<body style="background:#1e1f22;margin:24px;font-family:system-ui"><main style="display:grid;grid-template-columns:380px 1fr;gap:20px"></main></body>');
  await page.addScriptTag({path:path.resolve('custom_components/your_discord_connect/frontend/discord-cards.js')});
  await page.evaluate(() => {
    window.calls = []; window.unsubscribed = 0;
    window.overview = {available:true,server:'Home · Community',text_channels:[{id:'30',name:'allgemein',category:'Community'}],groups:[
      {id:null,name:null,channels:[{id:'10',name:'Lobby',members:[]}]},
      {id:'1',name:'Community',channels:[{id:'20',name:'Wohnzimmer',members:[
        {id:'1',name:'Mara',username:'mara',avatar:null,presence:'online'},
        {id:'2',name:'Jonas',username:'jonas',avatar:null,presence:'idle',microphone_muted:true},
        {id:'3',name:'Home Assistant',username:'ha_bot',avatar:null,presence:'online',bot:true,speaker_muted:true}
      ]},{id:'21',name:'Gaming',members:[{id:'4',name:'Lena',username:'lena',avatar:null,presence:'dnd',microphone_muted:true,speaker_muted:true}]}]},
      {id:'2',name:'Ruhebereich',channels:[{id:'22',name:'AFK',members:[{id:'5',name:'Alex',username:'alex',avatar:null,presence:'offline',afk:true}]}]}
    ]};
    window.feed = {channel:'allgemein',messages:[
      {id:'1',author:'Mara',avatar:null,timestamp:'2026-11-16T18:30:00Z',content:'Hey zusammen! 👋\nWer kommt heute ins **Wohnzimmer**?',attachments:[],embeds:[]},
      {id:'2',author:'Jonas',avatar:null,timestamp:'2026-11-16T18:31:00Z',reply_to:'mara',content:'Bin dabei — noch kurz das Mikro einschalten 🎙️',attachments:[],embeds:[]},
      {id:'3',author:'Home Assistant',avatar:null,bot:true,timestamp:'2026-11-16T18:32:00Z',content:'Die nächste Durchsage ist vorbereitet.',attachments:[],embeds:[{title:'Abendrunde',description:'Heute um **20:00 Uhr** im Wohnzimmer.'}]},
      {id:'4',author:'Lena',avatar:null,timestamp:'2026-11-16T18:33:00Z',edited:'2026-11-16T18:34:00Z',content:'Perfekt. Bis gleich! ✨',attachments:[],embeds:[]}
    ]};
    window.hass = {locale:{language:'de'},connection:{subscribeMessage:async(callback,message)=>{window.callback=callback;queueMicrotask(()=>callback(structuredClone(window.overview)));return ()=>{window.unsubscribed++;};}},callWS:async message=>{window.calls.push(message);return message.type.endsWith('/servers')?[{id:'server',name:'Home · Community'}]:structuredClone(window.feed);}};
    window.voiceCard = document.createElement('discord-channel-overview');
    voiceCard.setConfig({type:'custom:discord-channel-overview',entry_id:'server'}); voiceCard.hass=hass;
    window.feedCard = document.createElement('discord-text-channel-feed');
    feedCard.setConfig({type:'custom:discord-text-channel-feed',entry_id:'server',channel_id:'30'}); feedCard.hass=hass;
    document.querySelector('main').append(voiceCard,feedCard);
  });
  await page.locator('discord-channel-overview .member').first().waitFor();
  await page.locator('discord-text-channel-feed .message').first().waitFor();
  return page;
}
test('renders hierarchy, flags and feed; updates voice and cleans up subscription', async () => {
  const page = await setup();
  assert.equal(await page.locator('discord-channel-overview .channel').count(),4);
  assert.equal(await page.locator('discord-channel-overview .member').count(),5);
  assert.equal(await page.locator('discord-channel-overview [aria-label="Mikrofon stumm"]').count(),2);
  assert.equal(await page.locator('discord-text-channel-feed .message').count(),4);
  await page.evaluate(()=>{overview.groups[1].channels[0].members=[];callback(overview);});
  assert.equal(await page.locator('discord-channel-overview .member').count(),2);
  await page.evaluate(()=>voiceCard.remove());
  assert.equal(await page.evaluate(()=>window.unsubscribed),1);
  await page.close();
});
test('message HTML and unsafe links are inert', async () => {
  const page = await setup();
  await page.evaluate(()=>{
    feed.messages[0].content='<img src=x onerror="window.pwned=true"> **safe**';
    feed.messages[0].attachments=[{name:'unsafe',url:'javascript:alert(1)',image:true}];
    feedCard._data=feed;feedCard._render();
  });
  assert.equal(await page.locator('discord-text-channel-feed .content img').count(),0);
  assert.equal(await page.locator('discord-text-channel-feed a[href^="javascript"]').count(),0);
  assert.equal(await page.evaluate(()=>window.pwned),undefined);
  assert.match(await page.locator('discord-text-channel-feed .content').first().textContent(),/<img/);
  await page.close();
});
test('channel selection in visual editor emits configuration', async () => {
  const page = await setup();
  await page.evaluate(()=>{window.editor=document.createElement('discord-text-channel-feed-editor');editor.setConfig({type:'custom:discord-text-channel-feed',entry_id:'server',channel_id:'30'});editor.hass=hass;editor.addEventListener('config-changed',event=>window.selected=event.detail.config);document.body.append(editor);});
  const selects=page.locator('discord-text-channel-feed-editor select');
  await selects.nth(1).locator('option[value="30"]').waitFor({state:'attached'});
  await selects.nth(1).selectOption('30');
  assert.equal(await page.evaluate(()=>selected.channel_id),'30');
  await page.close();
});
test('mobile layout does not overflow and produces demo screenshot', async () => {
  const page = await setup();
  const errors=[];page.on('pageerror',error=>errors.push(error));
  fs.mkdirSync('test-results',{recursive:true});
  await page.screenshot({path:'test-results/discord-cards.png',fullPage:true});
  await page.setViewportSize({width:375,height:850});
  await page.evaluate(()=>{document.body.style.margin='8px';document.querySelector('main').style.gridTemplateColumns='1fr';});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=375));
  assert.equal(errors.length,0);
  await page.close();
});
test('failed feed request removes stale content', async () => {
  const page=await setup();
  await page.evaluate(async()=>{hass.callWS=async()=>{throw Error('Access denied');};await feedCard._start();});
  assert.equal(await page.locator('discord-text-channel-feed .message').count(),0);
  assert.match(await page.locator('discord-text-channel-feed .error').textContent(),/Access denied/);
  await page.close();
});
test('feed always scrolls to newest messages after refresh and delayed image loading', async () => {
  const page = await setup();
  const atBottom = () => page.evaluate(() => {
    const body = feedCard.shadowRoot.querySelector('.body');
    return body.scrollHeight > body.clientHeight && Math.abs(body.scrollHeight - body.clientHeight - body.scrollTop) <= 1;
  });
  await page.evaluate(async () => {
    feed.messages = Array.from({length:50}, (_, i) => ({...feed.messages[0],id:String(i),content:`Message ${i}`}));
    await feedCard._start();
  });
  await page.waitForFunction(() => {
    const body = feedCard.shadowRoot.querySelector('.body');
    return body.scrollTop > 0;
  });
  assert.ok(await atBottom());
  await page.evaluate(async () => {
    feedCard.shadowRoot.querySelector('.body').scrollTop = 0;
    feed.messages.push({...feed.messages[0],id:'new',content:'Newest message'});
    await feedCard._start();
  });
  assert.ok(await atBottom());
  // Simulate an attachment gaining its natural height after the render frame.
  await page.evaluate(() => {
    const body = feedCard.shadowRoot.querySelector('.body');
    const image = document.createElement('img');
    image.style.cssText = 'display:block;height:400px;width:100px';
    body.append(image);
    image.dispatchEvent(new Event('load'));
  });
  assert.ok(await atBottom());
  await page.close();
});
