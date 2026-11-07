# -*- coding: utf-8 -*-
"""Genere export/tracker.html a partir de export/tracker-data.json (donnees inline, autonome)."""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "export")

with open(os.path.join(OUT, "tracker-data.json"), "r", encoding="utf-8") as fh:
    data = json.load(fh)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agenda immobilier Afrique 2026-2027</title>
<style>
  :root{
    --bg:#0e1116; --panel:#161b22; --panel2:#1c2330; --line:#2a3240;
    --ink:#e6edf3; --ink2:#9aa7b6; --ink3:#6e7b8c;
    --accent:#f0a33c; --accent2:#4da3ff;
    --ok:#3fb950; --warn:#d29922; --todo:#8b949e; --danger:#f85149;
    --radius:10px;
  }
  @media (prefers-color-scheme: light){
    :root{
      --bg:#f6f7f9; --panel:#ffffff; --panel2:#f0f2f5; --line:#dfe3e8;
      --ink:#1a1f27; --ink2:#5a6573; --ink3:#8a95a3;
      --accent:#b9700d; --accent2:#0a68c9;
      --ok:#1a7f37; --warn:#9a6700; --todo:#6e7781; --danger:#cf222e;
    }
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
    font-size:14px;line-height:1.5;-webkit-font-smoothing:antialiased}
  a{color:var(--accent2);text-decoration:none}
  a:hover{text-decoration:underline}
  .wrap{max-width:1560px;margin:0 auto;padding:0 20px 80px}

  header{border-bottom:1px solid var(--line);background:var(--panel);
    padding:26px 0 20px;margin-bottom:0}
  header .wrap{padding-bottom:0}
  .eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);
    font-weight:700;margin:0 0 6px}
  h1{margin:0 0 6px;font-size:25px;letter-spacing:-.02em;font-weight:700}
  .lede{margin:0;color:var(--ink2);max-width:78ch;font-size:13.5px}
  .stats{display:flex;flex-wrap:wrap;gap:26px;margin-top:18px}
  .stat b{display:block;font-size:22px;letter-spacing:-.02em}
  .stat span{font-size:11px;color:var(--ink3);text-transform:uppercase;letter-spacing:.07em}

  .notice{margin:20px 0 0;padding:12px 14px;border:1px solid var(--line);
    border-left:3px solid var(--warn);border-radius:0 var(--radius) var(--radius) 0;
    background:var(--panel);color:var(--ink2);font-size:12.5px}
  .notice b{color:var(--ink)}

  .toolbar{position:sticky;top:0;z-index:20;background:var(--bg);
    border-bottom:1px solid var(--line);padding:12px 0;margin-top:22px}
  .toolbar .wrap{padding-bottom:0;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
  input[type=search],select{background:var(--panel);border:1px solid var(--line);color:var(--ink);
    padding:8px 10px;border-radius:8px;font-size:13px;font-family:inherit;outline:none}
  input[type=search]{min-width:250px;flex:1 1 260px}
  input[type=search]:focus,select:focus{border-color:var(--accent2)}
  .btn{background:var(--panel);border:1px solid var(--line);color:var(--ink2);padding:8px 12px;
    border-radius:8px;font-size:12.5px;cursor:pointer;font-family:inherit;white-space:nowrap}
  .btn:hover{border-color:var(--accent);color:var(--ink)}
  .btn.primary{background:var(--accent);border-color:var(--accent);color:#1a1f27;font-weight:600}
  .count{margin-left:auto;color:var(--ink3);font-size:12.5px;white-space:nowrap}
  .count b{color:var(--ink)}

  .legend{display:flex;flex-wrap:wrap;gap:14px;margin:18px 0 14px;color:var(--ink3);font-size:11.5px}
  .legend i{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;
    vertical-align:middle}

  table{width:100%;border-collapse:collapse;background:var(--panel);
    border:1px solid var(--line);border-radius:var(--radius);overflow:hidden}
  thead th{background:var(--panel2);text-align:left;font-size:11px;letter-spacing:.06em;
    text-transform:uppercase;color:var(--ink3);padding:10px 12px;font-weight:600;
    border-bottom:1px solid var(--line);white-space:nowrap;cursor:pointer;user-select:none}
  thead th:hover{color:var(--ink)}
  thead th .arrow{opacity:.35;font-size:9px;margin-left:3px}
  tbody td{padding:11px 12px;border-bottom:1px solid var(--line);vertical-align:top}
  tbody tr:last-child td{border-bottom:none}
  tbody tr.ev{cursor:pointer}
  tbody tr.ev:hover{background:var(--panel2)}
  tbody tr.open{background:var(--panel2)}
  .detail td{background:var(--panel2);padding:0 12px 14px 12px;border-bottom:1px solid var(--line)}
  .detail.hide{display:none}
  .ev-name{font-weight:600;color:var(--ink)}
  .ev-edition{display:block;color:var(--ink3);font-size:11.5px;font-weight:400;margin-top:1px}
  .date-cell{white-space:nowrap}
  .date-main{font-weight:600;font-variant-numeric:tabular-nums}
  .muted{color:var(--ink3)}
  .badge{display:inline-block;padding:2px 7px;border-radius:99px;font-size:10.5px;
    font-weight:600;letter-spacing:.03em;white-space:nowrap;border:1px solid transparent}
  .b-confirmed{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 40%,transparent);
    background:color-mix(in srgb,var(--ok) 12%,transparent)}
  .b-probable{color:var(--warn);border-color:color-mix(in srgb,var(--warn) 40%,transparent);
    background:color-mix(in srgb,var(--warn) 12%,transparent)}
  .b-to_confirm{color:var(--todo);border-color:var(--line);background:var(--panel2)}
  .cat{display:inline-block;font-size:10.5px;color:var(--ink2);background:var(--panel2);
    border:1px solid var(--line);padding:2px 7px;border-radius:5px;white-space:nowrap}
  .score{display:inline-flex;gap:2px;vertical-align:middle}
  .score s{width:5px;height:13px;border-radius:1px;background:var(--line);text-decoration:none}
  .score s.on{background:var(--accent)}
  .conflicts{display:inline-block;margin-top:5px;font-size:11px;color:var(--danger);
    border:1px solid color-mix(in srgb,var(--danger) 40%,transparent);
    background:color-mix(in srgb,var(--danger) 10%,transparent);
    padding:1px 6px;border-radius:5px}
  .notes{display:inline-block;margin-top:5px;font-size:11px;color:var(--ink3);
    border:1px solid var(--line);background:var(--panel2);padding:1px 6px;border-radius:5px}
  .meta{font-size:12px;color:var(--ink2)}
  .meta div{margin-bottom:3px}
  .grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}
  .block{border:1px solid var(--line);border-radius:8px;padding:12px 14px;background:var(--panel)}
  .block h4{margin:0 0 7px;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--ink3)}
  .block p{margin:0 0 8px}
  .block ul{margin:0;padding-left:17px}
  .block li{margin-bottom:3px}
  .empty{padding:50px;text-align:center;color:var(--ink3)}
  footer{margin-top:34px;color:var(--ink3);font-size:11.5px;border-top:1px solid var(--line);padding-top:16px}
  .hide{display:none}
  @media (max-width:1400px){ .hide-md{display:none} }
  @media (max-width:1100px){ .hide-sm{display:none} }
  @media (max-width:760px){ .hide-xs{display:none} }
</style>
</head>
<body>
<header>
  <div class="wrap">
    <p class="eyebrow">Suivi de march&eacute; &middot; Afrique</p>
    <h1>Agenda des &eacute;v&eacute;nements immobiliers en Afrique &mdash; 2026-2027</h1>
    <p class="lede">
      Agenda de travail destin&eacute; aux investisseurs et financiers. Les dates non confirm&eacute;es
      sont signal&eacute;es explicitement&nbsp;: v&eacute;rifiez toujours sur le site officiel avant
      de d&eacute;placer ou de payer.
    </p>
    <div class="stats">
      <div class="stat"><b id="s-all">0</b><span>&eacute;v&eacute;nements retenus</span></div>
      <div class="stat"><b id="s-dated">0</b><span>dat&eacute;s</span></div>
      <div class="stat"><b id="s-unc">0</b><span>date &agrave; confirmer</span></div>
      <div class="stat"><b id="s-conf">0</b><span>avec conflit de sources</span></div>
      <div class stat><b id="s-ctry">&mdash;</b><span>pays couverts</span></div>
    </div>
    <div class="notice">
      <b>P&eacute;rim&egrave;tre.</b> Uniquement les &eacute;v&eacute;nements organis&eacute;s sur le continent
      africain. Les rendez-vous organis&eacute;s hors d&rsquo;Afrique (Duba&iuml;, Londres, New York)
      et les expos de la diaspora sont exclus, m&ecirc;me s&rsquo;ils portent sur
      l&rsquo;immobilier africain. Filtre d&rsquo;inclusion&nbsp;: &agrave; moins deux des six
      crit&egrave;res (audience d&eacute;cisionnelle, &eacute;chelle, substance, continuit&eacute;,
      influence, port&eacute;e).
    </div>
  </div>
</header>

<div class="toolbar">
  <div class="wrap">
    <input type="search" id="q" placeholder="Rechercher un &eacute;v&eacute;nement, une ville, un organisateur, un th&egrave;me&hellip;">
    <select id="f-cat"><option value="">Toutes cat&eacute;gories</option></select>
    <select id="f-status"><option value="">Tous les statuts</option></select>
    <select id="f-country"><option value="">Tous les pays</option></select>
    <select id="f-zone"><option value="">Toutes les zones</option></select>
    <select id="f-score"><option value="0">Score investisseur &ge; 0</option>
      <option value="3">&ge; 3</option><option value="4">&ge; 4</option><option value="5">= 5</option></select>
    <button class="btn" id="reset">R&eacute;initialiser</button>
    <button class="btn primary" id="dl-csv">CSV</button>
    <button class="btn primary" id="dl-ics">ICS</button>
    <span class="count"><b id="shown">0</b> / <span id="total">0</span> affich&eacute;s</span>
  </div>
</div>

<div class="wrap">
  <div class="legend">
    <span><i style="background:var(--ok)"></i>Date confirm&eacute;e</span>
    <span><i style="background:var(--warn)"></i>Date probable / conflictuelle</span>
    <span><i style="background:var(--todo)"></i>Date &agrave; confirmer</span>
    <span><i style="background:var(--danger)"></i>Conflit entre sources</span>
  </div>
  <table>
    <thead>
      <tr>
        <th data-sort="start">Date <span class="arrow"></span></th>
        <th data-sort="name">&Eacute;v&eacute;nement <span class="arrow"></span></th>
        <th data-sort="category">Cat&eacute;gorie <span class="arrow"></span></th>
        <th data-sort="city">Lieu <span class="arrow"></span></th>
        <th class="hide-sm">&Eacute;chelle</th>
        <th data-sort="score" class="hide-sm">Score inv. <span class="arrow"></span></th>
        <th class="hide-md">Acteurs du capital</th>
        <th class="hide-xs">Source</th>
      </tr>
    </thead>
    <tbody id="rows"></tbody>
  </table>
  <div class="empty hide" id="empty">Aucun &eacute;v&eacute;nement ne correspond aux filtres.</div>
  <footer>
    <p><b>Sources.</b> Chaque ligne porte l&rsquo;URL de la source r&eacute;ellement consult&eacute;e et la date de
    v&eacute;rification. Les conflits entre sources sont conserv&eacute;s plut&ocirc;t que masqu&eacute;s&nbsp;: ils
    signalent o&ugrave; l&rsquo;information est encore fragile.</p>
    <p>Les salons de construction et de mat&eacute;riaux sont isol&eacute;s en cat&eacute;gorie
    <i>adjacente</i>&nbsp;: ils ne sont pas des &eacute;v&eacute;nements immobiliers, mais ils p&egrave;sent sur la
    faisabilit&eacute; et la marge des projets.</p>
    <p>Exports&nbsp;: <a href="agenda-immobilier-afrique.csv">agenda-immobilier-afrique.csv</a> &middot;
    <a href="agenda-immobilier-afrique.ics">agenda-immobilier-afrique.ics</a></p>
  </footer>
</div>

<script id="payload" type="application/json">__DATA__</script>
<script>
(function(){
  var DATA = JSON.parse(document.getElementById('payload').textContent);
  var EV = DATA.events || [];
  var state = {q:'', cat:'', status:'', country:'', zone:'', score:0, sort:'start', dir:1};

  function esc(s){return String(s==null?'':s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');}

  function uniq(arr){var o=[],s={};arr.forEach(function(v){if(v&&!s[v]){s[v]=1;o.push(v);}});return o;}

  function fillSelect(id, values, labels){
    var el = document.getElementById(id);
    values.forEach(function(v){
      var o=document.createElement('option'); o.value=v; o.textContent=(labels&&labels[v])||v;
      el.appendChild(o);
    });
  }

  var catLabels={}, statusLabels={};
  EV.forEach(function(e){ if(e.category_label) catLabels[e.category]=e.category_label;
    if(e.status_label) statusLabels[e.status]=e.status_label; });

  fillSelect('f-cat', uniq(EV.map(function(e){return e.category;})), catLabels);
  fillSelect('f-status', uniq(EV.map(function(e){return e.status;})), statusLabels);
  fillSelect('f-country', uniq(EV.map(function(e){return e.country;})).sort());
  fillSelect('f-zone', uniq(EV.map(function(e){return e.zone;})).sort());

  document.getElementById('s-all').textContent = EV.length;
  document.getElementById('s-dated').textContent = EV.filter(function(e){return e.start;}).length;
  document.getElementById('s-unc').textContent = EV.filter(function(e){return e.status==='to_confirm';}).length;
  document.getElementById('s-conf').textContent = EV.filter(function(e){return e.has_conflict;}).length;
  document.getElementById('s-ctry').textContent = uniq(EV.map(function(e){return e.country;})).length;
  document.getElementById('total').textContent = EV.length;

  function scoreBar(n){
    var h=''; for(var i=1;i<=5;i++){ h += '<s class="'+(i<=n?'on':'')+'"></s>'; }
    return '<span class="score" title="Score '+n+'/5">'+h+'</span>';
  }

  function detailHtml(e){
    var h = '<div class="grid2">';
    h += '<div class="block"><h4>Pertinence investisseur</h4><p>'+esc(e.why||'&mdash;')+'</p>';
    if(e.themes) h += '<p style="margin-bottom:0"><b>Th&egrave;mes&nbsp;:</b> '+esc(e.themes)+'</p>';
    h += '</div>';
    h += '<div class="block"><h4>Organisation</h4>';
    h += '<div class="meta"><div><b>Organisateur&nbsp;:</b> '+esc(e.organizer||'&mdash;')+'</div>';
    h += '<div><b>Lieu&nbsp;:</b> '+esc(e.venue||'&mdash;')+'</div>';
    h += '<div><b>Acteurs du capital&nbsp;:</b> '+esc(e.actors||'&mdash;')+'</div>';
    h += '<div><b>Zone&nbsp;:</b> '+esc(e.zone)+'</div>';
    h += '<div><b>V&eacute;rifi&eacute; le&nbsp;:</b> '+esc(e.last_verified||'&mdash;')+'</div></div>';
    h += '</div>';
    h += '<div class="block"><h4>Sources</h4><ul>';
    if(e.source_url) h += '<li><a href="'+esc(e.source_url)+'" target="_blank" rel="noopener">'+esc(e.source_name||e.source_url)+'</a></li>';
    else h += '<li>'+esc(e.source_name||'&mdash;')+'</li>';
    if(e.ticket_url) h += '<li><a href="'+esc(e.ticket_url)+'" target="_blank" rel="noopener">Billetterie / inscription</a></li>';
    h += '</ul>';
    if(e.conflicts) h += '<p style="margin:10px 0 0"><b style="color:var(--danger)">Conflits&nbsp;:</b> '+esc(e.conflicts)+'</p>';
    if(e.notes) h += '<p style="margin:6px 0 0"><b>Signaux et lacunes&nbsp;:</b> '+esc(e.notes)+'</p>';
    h += '</div>';
    h += '</div>';
    return h;
  }

  function rowHtml(e){
    var st = e.status==='confirmed'?'b-confirmed':(e.status==='probable'?'b-probable':'b-to_confirm');
    var src = e.source_url
      ? '<a href="'+esc(e.source_url)+'" target="_blank" rel="noopener" onclick="event.stopPropagation()">source</a>'
      : '<span class="muted">'+esc(e.source_name||'&mdash;')+'</span>';
    var conf = e.has_conflict ? '<div class="conflicts">conflit de sources</div>'
      : (e.notes ? '<div class="notes">signalement</div>' : '');
    return '<tr class="ev" data-i="'+e.__i+'">'
      + '<td class="date-cell"><div class="date-main">'+esc(e.display_date)+'</div>'
      + '<div><span class="badge '+st+'">'+esc(e.status_label)+'</span></div>'+conf+'</td>'
      + '<td><div class="ev-name">'+esc(e.name)+'</div>'
      + (e.edition?'<span class="ev-edition">'+esc(e.edition)+'</span>':'')+'</td>'
      + '<td><span class="cat">'+esc(e.category_label)+'</span></td>'
      + '<td>'+esc(e.city||'')+(e.country?'<br><span class="muted">'+esc(e.country)+'</span>':'')+'</td>'
      + '<td class="hide-sm meta">'+(e.attendees?esc(e.attendees):'')
      + (e.exhibitors?'<br><span class="muted">'+esc(e.exhibitors)+' exposants</span>':'')+'</td>'
      + '<td class="hide-sm">'+scoreBar(e.score)+'</td>'
      + '<td class="hide-md meta">'+esc(e.actors||'&mdash;')+'</td>'
      + '<td class="hide-xs meta">'+src+'</td>'
      + '</tr><tr class="detail hide" data-d="'+e.__i+'"><td colspan="8">'+detailHtml(e)+'</td></tr>';
  }

  EV.forEach(function(e,i){e.__i=i;});

  var tbody = document.getElementById('rows');

  function matches(e){
    if(state.cat && e.category!==state.cat) return false;
    if(state.status && e.status!==state.status) return false;
    if(state.country && e.country!==state.country) return false;
    if(state.zone && e.zone!==state.zone) return false;
    if(state.score && (e.score||0) < state.score) return false;
    if(state.q){
      var hay = [e.name,e.edition,e.city,e.country,e.venue,e.organizer,e.themes,e.actors,e.why,e.source_name].join(' ').toLowerCase();
      if(hay.indexOf(state.q.toLowerCase())===-1) return false;
    }
    return true;
  }

  function sortRows(list){
    var k=state.sort, dir=state.dir;
    return list.slice().sort(function(a,b){
      var va,vb;
      if(k==='score'){ va=a.score||0; vb=b.score||0; }
      else if(k==='name'){ va=(a.name||'').toLowerCase(); vb=(b.name||'').toLowerCase(); }
      else if(k==='city'){ va=(a.city||'').toLowerCase(); vb=(b.city||'').toLowerCase(); }
      else if(k==='category'){ va=a.category_label; vb=b.category_label; }
      else { va=a.start||'9999-99-99'; vb=b.start||'9999-99-99'; }
      if(va<vb) return -1*dir; if(va>vb) return 1*dir;
      return 0;
    });
  }

  function render(){
    var list = sortRows(EV.filter(matches));
    tbody.innerHTML = list.map(rowHtml).join('');
    document.getElementById('shown').textContent = list.length;
    document.getElementById('empty').classList.toggle('hide', list.length>0);
  }

  tbody.addEventListener('click', function(ev){
    var tr = ev.target.closest ? ev.target.closest('tr.ev') : null;
    if(!tr) return;
    var d = tbody.querySelector('tr.detail[data-d="'+tr.getAttribute('data-i')+'"]');
    if(d){ d.classList.toggle('hide'); tr.classList.toggle('open'); }
  });

  ['cat','status','country','zone','score'].forEach(function(f){
    document.getElementById('f-'+f).addEventListener('change', function(){
      state[f] = f==='score' ? parseInt(this.value,10) : this.value; render();
    });
  });
  var qt = null;
  document.getElementById('q').addEventListener('input', function(){
    var v=this.value; clearTimeout(qt); qt=setTimeout(function(){state.q=v;render();},140);
  });
  document.getElementById('reset').addEventListener('click', function(){
    state={q:'',cat:'',status:'',country:'',zone:'',score:0,sort:'start',dir:1};
    document.getElementById('q').value='';
    ['cat','status','country','zone'].forEach(function(f){document.getElementById('f-'+f).value='';});
    document.getElementById('f-score').value='0'; render();
  });

  Array.prototype.forEach.call(document.querySelectorAll('th[data-sort]'), function(th){
    th.addEventListener('click', function(){
      var k=th.getAttribute('data-sort');
      if(state.sort===k) state.dir=-state.dir; else {state.sort=k; state.dir=1;}
      render();
    });
  });

  document.getElementById('dl-csv').addEventListener('click', function(){
    window.location.href='agenda-immobilier-afrique.csv';
  });
  document.getElementById('dl-ics').addEventListener('click', function(){
    window.location.href='agenda-immobilier-afrique.ics';
  });

  render();
})();
</script>
</body>
</html>
"""

out = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
path = os.path.join(OUT, "tracker.html")
with open(path, "w", encoding="utf-8") as fh:
    fh.write(out)
print("  -> %s (%d evenements, %d octets)" % (path, len(data.get("events", [])), len(out)))
