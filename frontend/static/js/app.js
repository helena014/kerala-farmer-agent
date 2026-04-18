/* Kerala Farmer Advisory Agent — app.js
   Connects to FastAPI backend at http://localhost:8000
*/

'use strict';

const API = 'https://kerala-farmer-agent.onrender.com';
let farmers       = [];
let selFarmer     = null;   // composer tab
let qaFarmer      = null;   // Q&A tab
let qaHistory     = [];     // conversation history for Gemini
let allMessages   = [];     // advisory feed
let selectedMsgId = null;

/* ════════════════════════════════════════════
   INIT
════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', async () => {
  updateClock();
  setInterval(updateClock, 1000);
  setupTabs();

  await checkBackend();
  await loadFarmers();
  await loadMessages();
  await loadSchedulerStatus();
  await loadEvalDataset();
});

async function checkBackend() {
  try {
    const r = await fetch(`${API}/api/scheduler/status`);
    if (r.ok) {
      document.getElementById('api-status').innerHTML =
        '<span style="color:#25d366">●</span> Backend connected · FastAPI running';
      document.getElementById('api-status').style.color = '#25d366';
    }
  } catch {
    document.getElementById('api-status').innerHTML =
      '⚠️ Backend offline — run: uvicorn main:app --reload';
    document.getElementById('api-status').style.color = '#ef4444';
  }
}

function updateClock() {
  const now = new Date();
  document.getElementById('clock').textContent =
    now.toLocaleTimeString('en-IN', {hour:'2-digit', minute:'2-digit', hour12:true});
  document.getElementById('dateline').textContent =
    now.toLocaleDateString('en-IN', {weekday:'long', day:'numeric', month:'long', year:'numeric'}) + ' · Kerala';
}

/* ════════════════════════════════════════════
   TABS
════════════════════════════════════════════ */
function setupTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
    });
  });
}

/* ════════════════════════════════════════════
   FARMERS
════════════════════════════════════════════ */
async function loadFarmers() {
  try {
    const r = await fetch(`${API}/api/farmers`);
    farmers  = await r.json();
    renderFarmerGrid();
    renderComposerFarmerRow();
    renderQASel();
    toast(`✅ ${farmers.length} farmers loaded`);
  } catch (e) {
    document.getElementById('farmer-grid').innerHTML =
      '<div class="empty-state">⚠️ Cannot reach backend. Make sure uvicorn is running.</div>';
  }
}

function renderFarmerGrid() {
  const grid = document.getElementById('farmer-grid');
  if (!farmers.length) {
    grid.innerHTML = '<div class="empty-state">No farmers yet. Click + Add Farmer.</div>';
    return;
  }
  grid.innerHTML = farmers.map(f => `
    <div class="fc ${selFarmer?.id===f.id?'sel':''}" onclick="selectFarmerCard('${f.id}')">
      <div class="fact">
        <button style="background:#fee2e2;color:#dc2626;border:none;border-radius:6px;padding:3px 8px;font-size:10px;font-weight:700;cursor:pointer"
          onclick="event.stopPropagation();deleteFarmer('${f.id}')">✕</button>
      </div>
      <div class="fa">${f.emoji||'👨‍🌾'}</div>
      <div class="fn">${f.name}</div>
      <div class="fm">
        <span>📍 ${f.district}</span>
        <span>📱 ${f.phone||'—'}</span>
        <span>🗺️ ${f.land} acres · ${f.lang}</span>
      </div>
      <span class="ct c-${(f.crop||'').toLowerCase()}">${f.crop}</span>
    </div>
  `).join('');
}

function selectFarmerCard(id) {
  selFarmer = farmers.find(f => f.id === id) || null;
  renderFarmerGrid();
  renderComposerFarmerRow();
}

function toggleAddForm() {
  document.getElementById('add-form').classList.toggle('open');
}

async function addFarmer() {
  const name = document.getElementById('f-name').value.trim();
  if (!name) { toast('⚠️ Please enter farmer name'); return; }
  const emojis = ['👨‍🌾','👩‍🌾','🧑‍🌾'];
  const payload = {
    name,
    district: document.getElementById('f-district').value,
    crop:     document.getElementById('f-crop').value,
    phone:    document.getElementById('f-phone').value || '',
    lang:     document.getElementById('f-lang').value,
    land:     document.getElementById('f-land').value || '1',
    emoji:    emojis[Math.floor(Math.random()*emojis.length)],
  };
  try {
    const r = await fetch(`${API}/api/farmers`, {
      method:  'POST',
      headers: {'Content-Type':'application/json'},
      body:    JSON.stringify(payload),
    });
    if (!r.ok) throw new Error(await r.text());
    toast('✅ Farmer saved!');
    document.getElementById('f-name').value  = '';
    document.getElementById('f-phone').value = '';
    document.getElementById('f-land').value  = '';
    document.getElementById('add-form').classList.remove('open');
    await loadFarmers();
    // Re-select the newly added farmer in composer
    const newF = farmers[farmers.length - 1];
    if (newF) { selFarmer = newF; renderComposerFarmerRow(); }
  } catch (e) { toast('❌ Error: ' + e.message); }
}

async function deleteFarmer(id) {
  if (!confirm('Remove this farmer?')) return;
  try {
    await fetch(`${API}/api/farmers/${id}`, {method:'DELETE'});
    if (selFarmer?.id === id) selFarmer = null;
    await loadFarmers();
    toast('🗑️ Farmer removed');
  } catch (e) { toast('❌ ' + e.message); }
}

async function triggerAllAdvisories() {
  toast('🚀 Generating advisories for all farmers...');
  try {
    const r    = await fetch(`${API}/api/advisory/generate-all`, {method:'POST'});
    const data = await r.json();
    toast(`✅ ${data.count} advisories generated!`);
    await loadMessages();
    // Switch to advisory feed tab
    document.querySelector('[data-tab="advisory"]').click();
  } catch (e) { toast('❌ ' + e.message); }
}

/* ════════════════════════════════════════════
   ADVISORY FEED
════════════════════════════════════════════ */
async function loadMessages() {
  try {
    const r = await fetch(`${API}/api/messages`);
    allMessages = await r.json();
    renderMessageFeed();
    if (allMessages.length > 0 && !selectedMsgId) {
      showMessageDetail(allMessages[0].id); // auto-show first message
    }
  } catch (e) {
    document.getElementById('msg-feed').innerHTML =
      '<div class="empty-state">⚠️ Cannot load messages — is backend running?</div>';
  }
}

function renderMessageFeed() {
  const feed = document.getElementById('msg-feed');
  if (!allMessages.length) {
    feed.innerHTML = '<div class="empty-state">📭 No messages yet.<br>Click "Send All Advisories Now" to generate.</div>';
    return;
  }
  feed.innerHTML = allMessages.map(m => `
    <div class="msg-card ${selectedMsgId===m.id?'selected':''}" onclick="showMessageDetail('${m.id}')">
      <div class="msg-card-top">
        <span class="msg-farmer">${m.farmer_name||'Farmer'}</span>
        <span class="msg-type-badge ${m.type==='qa'?'badge-qa':'badge-advisory'}">${m.type==='qa'?'Q&A':'Advisory'}</span>
      </div>
      <div style="font-size:10px;color:var(--tl);margin-bottom:4px">
        🌾 ${m.crop} · 📍 ${m.district} · ${formatTime(m.created_at)}
      </div>
      <div class="msg-preview qml">${(m.message||'').substring(0,80)}...</div>
    </div>
  `).join('');
}

function showMessageDetail(id) {
  selectedMsgId = id;
  renderMessageFeed();
  const m = allMessages.find(x => x.id === id);
  if (!m) return;
  const formatted = (m.message||'').replace(/\*(.*?)\*/g,'<strong>$1</strong>').replace(/\n/g,'<br>');
  const time = formatTime(m.created_at);
  document.getElementById('msg-detail').innerHTML = `
    <div class="detail-wp">
      <div class="detail-wp-header">
        <div class="detail-wp-av">🌾</div>
        <div>
          <div class="detail-wp-name">Kerala Krishi Agent</div>
          <div style="font-size:10px;opacity:.75">→ ${m.farmer_name}</div>
        </div>
      </div>
      <div class="detail-wp-body">
        <div class="wp-bubble">
          <div class="wp-text">${formatted}</div>
          <div class="wpt">${time} ✓✓</div>
        </div>
      </div>
    </div>
    <div style="margin-top:12px;font-size:12px;color:var(--tm);display:flex;flex-direction:column;gap:4px">
      <div>👤 <strong>${m.farmer_name}</strong> · ${m.crop} · ${m.district}</div>
      <div>🕐 Generated: ${time}</div>
      <div>📋 Type: ${m.type==='qa'?'Q&A Response':'Morning Advisory'}</div>
    </div>
  `;
}

async function clearMessages() {
  if (!confirm('Clear all messages?')) return;
  try {
    await fetch(`${API}/api/messages`, {method:'DELETE'});
    allMessages = [];
    selectedMsgId = null;
    renderMessageFeed();
    document.getElementById('msg-detail').innerHTML = '<div class="empty-state">Messages cleared.</div>';
    toast('🗑️ All messages cleared');
  } catch (e) { toast('❌ ' + e.message); }
}

/* ════════════════════════════════════════════
   SCHEDULER
════════════════════════════════════════════ */
async function loadSchedulerStatus() {
  try {
    const r    = await fetch(`${API}/api/scheduler/status`);
    const data = await r.json();
    document.getElementById('sched-badge').textContent =
      `⏰ Advisory scheduled: ${data.scheduled_time} daily`;
    document.getElementById('sched-hour').value  = data.hour;
    document.getElementById('sched-min').value   = data.minute;
    document.getElementById('st-sched').textContent =
      `⏰ Next: ${data.next_run?.substring(11,16)||data.scheduled_time}`;
  } catch { }
}

async function updateSchedule() {
  const hour = parseInt(document.getElementById('sched-hour').value);
  const min  = parseInt(document.getElementById('sched-min').value);
  if (isNaN(hour)||hour<0||hour>23) { toast('⚠️ Hour must be 0–23'); return; }
  if (isNaN(min)||min<0||min>59)    { toast('⚠️ Minute must be 0–59'); return; }
  try {
    const r = await fetch(`${API}/api/scheduler/set-time?hour=${hour}&minute=${min}`, {method:'POST'});
    const d = await r.json();
    toast(`✅ Advisory time updated to ${d.time}`);
    await loadSchedulerStatus();
  } catch (e) { toast('❌ ' + e.message); }
}

/* ════════════════════════════════════════════
   COMPOSER TAB
════════════════════════════════════════════ */
function renderComposerFarmerRow() {
  const row = document.getElementById('comp-farmer-row');
  if (!row) return;
  row.innerHTML = farmers.map(f => `
    <button onclick="pickComposerFarmer('${f.id}')"
      style="padding:8px 16px;border-radius:20px;
             border:2px solid ${selFarmer?.id===f.id?'var(--gl)':'rgba(64,145,108,0.2)'};
             background:${selFarmer?.id===f.id?'var(--gl)':'#fff'};
             color:${selFarmer?.id===f.id?'#fff':'var(--gd)'};
             font-weight:700;font-size:12px;cursor:pointer;transition:all .2s;font-family:Lato,sans-serif;">
      ${f.emoji||'👨‍🌾'} ${f.name}
    </button>
  `).join('');
}

async function pickComposerFarmer(id) {
  selFarmer = farmers.find(f => f.id === id) || null;
  renderComposerFarmerRow();
  if (!selFarmer) return;
  document.getElementById('comp-gbtn').disabled = false;
  document.getElementById('comp-wpb').innerHTML =
    '<div class="wpbu" style="color:var(--tl);font-size:12px;font-style:italic">Loading data feeds...</div>';

  try {
    // Load prices, weather, pest in parallel
    const [pricesR, weatherR, pestR] = await Promise.all([
      fetch(`${API}/api/data/prices/${encodeURIComponent(selFarmer.crop)}/${encodeURIComponent(selFarmer.district)}`),
      fetch(`${API}/api/data/weather/${encodeURIComponent(selFarmer.district)}`),
      fetch(`${API}/api/data/pest/${encodeURIComponent(selFarmer.crop)}/${encodeURIComponent(selFarmer.district)}`),
    ]);
    const prices  = await pricesR.json();
    const weather = await weatherR.json();
    const pest    = await pestR.json();

    renderPrices(prices);
    renderWeather(weather);
    renderPest(pest);
    document.getElementById('st-prices').textContent  = '📡 Agmarknet: ✅';
    document.getElementById('st-weather').textContent = '🌤️ IMD: ✅';
  } catch (e) {
    toast('⚠️ Could not load data: ' + e.message);
  }
  document.getElementById('comp-wpb').innerHTML =
    `<div class="wpbu" style="color:var(--tl);font-size:12px;font-style:italic">Click "Generate Advisory" to compose the AI message for ${selFarmer.name}.</div>`;
}

function renderPrices(prices) {
  const mandis = prices.mandis || [];
  document.getElementById('price-data').innerHTML = mandis.map(m => `
    <div class="pr">
      <span style="color:var(--tm)">🏪 ${m.mandi}</span>
      <span>
        <span class="pv">₹${(m.price||0).toLocaleString('en-IN')}</span>
        <span class="${m.trend==='up'?'tu':m.trend==='down'?'td2':'tf'}" style="margin-left:5px;font-size:12px">
          ${m.trend==='up'?'↑':m.trend==='down'?'↓':'→'}
        </span>
      </span>
    </div>
  `).join('') + `<div style="font-size:11px;color:var(--tl);padding:6px 0">${prices.sell_advice||''}</div>`;
}

function renderWeather(weather) {
  const days = weather.forecast || [];
  document.getElementById('weather-row').innerHTML = days.map(d => `
    <div class="wd">
      <div class="wdn">${d.day}</div>
      <div class="wdi">${d.icon}</div>
      <div class="wdt">${d.temp}</div>
      <div class="wdr">💧${d.rain_pct}%</div>
    </div>
  `).join('');
}

function renderPest(pest) {
  document.getElementById('pest-data').innerHTML = `
    <div class="palert">
      <div class="pat">${pest.title||'No active alerts'}</div>
      <div class="qml" style="font-size:12px;margin-bottom:4px">${pest.symptoms||''}</div>
      <div style="font-size:12px;color:#5d4037"><strong>Action:</strong> ${pest.action||''}</div>
    </div>
  `;
}

async function composeAdvisory() {
  if (!selFarmer) return;
  const btn = document.getElementById('comp-gbtn');
  const prog = document.getElementById('comp-aprog');
  const apf  = document.getElementById('comp-apf');
  const stat = document.getElementById('comp-gstat');
  const wpb  = document.getElementById('comp-wpb');

  btn.disabled  = true;
  btn.innerHTML = '<span class="spin"></span> Generating with Gemini...';
  prog.classList.add('on');
  let pct = 0;
  const ticker = setInterval(() => { pct = Math.min(pct + Math.random()*12, 90); apf.style.width = pct+'%'; }, 300);
  wpb.innerHTML  = '<div class="wpbu"><span class="typing"><span></span><span></span><span></span></span></div>';
  stat.textContent = '⏳ Gemini AI composing advisory in Malayalam...';

  try {
    const r    = await fetch(`${API}/api/advisory/generate/${selFarmer.id}`, {method:'POST'});
    const data = await r.json();
    clearInterval(ticker); apf.style.width = '100%';
    setTimeout(() => prog.classList.remove('on'), 600);

    const msg = data.message || 'Advisory generated.';
    const fmt = msg.replace(/\*(.*?)\*/g,'<strong>$1</strong>').replace(/\n/g,'<br>');
    const time = new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',hour12:true});
    wpb.innerHTML  = `<div class="wpbu" style="animation:fi .4s ease"><div class="wpm">${fmt}</div><div class="wpt">${time} ✓✓</div></div>`;
    stat.textContent = '✅ Generated · Saved to message feed';
    btn.innerHTML    = '✅ Generated — Click to Regenerate';
    toast('✅ Advisory generated for ' + selFarmer.name);
    await loadMessages();
  } catch (e) {
    clearInterval(ticker); prog.classList.remove('on');
    wpb.innerHTML    = `<div class="wpbu" style="color:#dc2626">❌ Error: ${e.message}</div>`;
    stat.textContent = '';
    btn.innerHTML    = '🤖 Generate Advisory with Gemini AI';
    toast('❌ ' + e.message);
  }
  btn.disabled = false;
}

/* ════════════════════════════════════════════
   Q&A TAB
════════════════════════════════════════════ */
function renderQASel() {
  const sel = document.getElementById('qa-farmer-sel');
  if (!sel) return;
  const cur = sel.value; // remember current selection
  sel.innerHTML = '<option value="">— Select a farmer —</option>' +
    farmers.map(f => `<option value="${f.id}">${f.emoji||'👨‍🌾'} ${f.name} · ${f.crop} · ${f.district}</option>`).join('');
  if (cur) {
    sel.value = cur; // restore selection
    // If farmer is already selected, don't wipe the chat
  }
}

function selectQAFarmer() {
  const id = document.getElementById('qa-farmer-sel').value;
  if (!id) return; // nothing selected, do nothing
  const found = farmers.find(f => f.id === id);
  if (!found) {
    // Farmer not in local array yet — reload farmers then retry
    loadFarmers().then(() => {
      qaFarmer = farmers.find(f => f.id === id) || null;
      if (qaFarmer) _startQAChat();
    });
    return;
  }
  qaFarmer  = found;
  qaHistory = [];
  _startQAChat();
}

function _startQAChat() {
  const msgs = document.getElementById('qmsgs');
  document.getElementById('qhead').textContent =
    `💬 ${qaFarmer.name} · ${qaFarmer.crop} · ${qaFarmer.district}`;
  const time = new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',hour12:true});
  msgs.innerHTML = `
    <div class="qmsg qa2">
      <div class="qml">🌅 <strong>ഗുഡ് മോർണിംഗ് ${qaFarmer.name} ജി!</strong><br>
      ഇന്നത്തെ ${qaFarmer.crop} advisory ready ആണ്. ഏതെങ്കിലും ചോദ്യം ഉണ്ടെങ്കിൽ reply ചെയ്യൂ 🙏</div>
      <div class="wpt">${time} ✓✓</div>
    </div>`;
}

function quickQ(q) {
  document.getElementById('qinp').value = q;
  sendQA();
}

async function sendQA() {
  const inp  = document.getElementById('qinp');
  const text = inp.value.trim();
  if (!text) return;
  if (!qaFarmer) { toast('⚠️ Select a farmer first'); return; }
  inp.value = '';
  const msgs = document.getElementById('qmsgs');
  const time = new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',hour12:true});

  msgs.innerHTML += `<div class="qmsg qf qml">${text}<div class="wpt" style="color:rgba(255,255,255,.7)">${time}</div></div>`;
  const tid = 'typ_' + Date.now();
  msgs.innerHTML += `<div id="${tid}" class="qmsg qa2"><span class="typing"><span></span><span></span><span></span></span></div>`;
  msgs.scrollTop = msgs.scrollHeight;

  qaHistory.push({role:'user', text});

  try {
    const r    = await fetch(`${API}/api/qa`, {
      method:  'POST',
      headers: {'Content-Type':'application/json'},
      body:    JSON.stringify({
        farmer_id:            qaFarmer.id,
        question:             text,
        conversation_history: qaHistory,
      }),
    });
    const data  = await r.json();
    const reply = data.answer || 'No response.';
    qaHistory.push({role:'assistant', text:reply});
    const fmt    = reply.replace(/\*(.*?)\*/g,'<strong>$1</strong>').replace(/\n/g,'<br>');
    const tNow   = new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',hour12:true});
    document.getElementById(tid)?.remove();
    msgs.innerHTML += `<div class="qmsg qa2 qml">${fmt}<div class="wpt">${tNow} ✓✓</div></div>`;
    msgs.scrollTop  = msgs.scrollHeight;
  } catch (e) {
    document.getElementById(tid)?.remove();
    msgs.innerHTML += `<div class="qmsg qa2" style="color:#dc2626">❌ ${e.message}</div>`;
    msgs.scrollTop  = msgs.scrollHeight;
  }
}

document.addEventListener('keydown', e => {
  if (e.key === 'Enter' && document.activeElement.id === 'qinp') sendQA();
});

/* ════════════════════════════════════════════
   EVALUATION
════════════════════════════════════════════ */
async function loadEvalDataset() {
  try {
    const r    = await fetch(`${API}/api/evaluation/dataset`);
    const data = await r.json();
    renderEvalTable(data);
  } catch { }
}

function renderEvalTable(data) {
  document.getElementById('eval-tbody').innerHTML = (data||[]).map(r => `
    <tr>
      <td>${r.crop}</td>
      <td>${r.district}</td>
      <td style="font-family:'IBM Plex Mono',monospace;font-weight:700">₹${(r.avg_price||0).toLocaleString('en-IN')}</td>
      <td style="color:${r.trend==='↑'?'#28a745':r.trend==='↓'?'#dc3545':'#888'};font-weight:700">${r.trend}</td>
    </tr>
  `).join('');
}

async function runEvaluation() {
  toast('▶ Running evaluation simulation...');
  ['rel-bar','trans-bar','price-bar','comp-bar'].forEach(id => {
    document.getElementById(id).style.width = '0%';
  });
  ['rel-score','trans-score','price-score','comp-score'].forEach(id => {
    document.getElementById(id).textContent = '...';
  });
  try {
    const r    = await fetch(`${API}/api/evaluation/run`, {method:'POST'});
    const data = await r.json();
    const m    = data.metrics || {};

    setTimeout(() => {
      const pairs = [
        ['rel-bar','rel-score','message_relevance'],
        ['trans-bar','trans-score','translation_quality'],
        ['price-bar','price-score','price_accuracy'],
        ['comp-bar','comp-score','user_comprehension'],
      ];
      pairs.forEach(([bar, score, key]) => {
        const val = m[key]?.mean || 0;
        document.getElementById(bar).style.width   = val + '%';
        document.getElementById(score).textContent = val + '%';
      });
    }, 200);

    renderEvalTable(data.dataset);
    document.getElementById('eval-desc').innerHTML =
      `✅ Evaluated ${data.num_combinations} combinations · ${data.total_messages} messages · ${data.evaluated_at?.substring(0,10)}`;
    toast('✅ Evaluation complete!');
  } catch (e) { toast('❌ ' + e.message); }
}

/* ════════════════════════════════════════════
   UTILITIES
════════════════════════════════════════════ */
function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('on');
  setTimeout(() => t.classList.remove('on'), 3200);
}

function formatTime(iso) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',hour12:true}) +
           ' · ' + d.toLocaleDateString('en-IN',{day:'numeric',month:'short'});
  } catch { return iso.substring(0,16); }
}
