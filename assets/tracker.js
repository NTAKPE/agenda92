(function(){
  var rows = Array.prototype.slice.call(document.querySelectorAll('tr.ev'));
  var q = document.getElementById('q');
  var filters = {
    cat: document.getElementById('f-cat'),
    status: document.getElementById('f-status'),
    country: document.getElementById('f-country'),
    zone: document.getElementById('f-zone'),
    period: document.getElementById('f-period'),
    score: document.getElementById('f-score')
  };
  var shown = document.getElementById('shown');
  var total = document.getElementById('total');
  if(total) total.textContent = rows.length;

  // Semaine ISO courante, calculee dans le navigateur : le filtre reste juste
  // meme si la page a ete generee il y a plusieurs semaines.
  var WEEK = (function(){
    var now = new Date();
    var d = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    var day = (d.getDay() + 6) % 7;
    var mon = new Date(d); mon.setDate(d.getDate() - day);
    var sun = new Date(mon); sun.setDate(mon.getDate() + 6);
    function iso(x){
      return x.getFullYear() + '-' + String(x.getMonth()+1).padStart(2,'0')
        + '-' + String(x.getDate()).padStart(2,'0');
    }
    function fr(x){ return x.toLocaleDateString('fr-FR', {day:'numeric', month:'short'}); }
    var nmon = new Date(sun); nmon.setDate(sun.getDate() + 1);
    var nsun = new Date(nmon); nsun.setDate(nmon.getDate() + 6);
    return {
      start: iso(mon), end: iso(sun), label: fr(mon) + ' – ' + fr(sun),
      nextStart: iso(nmon), nextEnd: iso(nsun), nextLabel: fr(nmon) + ' – ' + fr(nsun)
    };
  })();
  var periodSel = document.getElementById('f-period');
  if(periodSel){
    var wo = periodSel.querySelector('option[value="week"]');
    if(wo) wo.textContent = 'Cette semaine (' + WEEK.label + ')';
    var no = periodSel.querySelector('option[value="nextweek"]');
    if(no) no.textContent = 'Semaine prochaine (' + WEEK.nextLabel + ')';
  }
  function inRange(tr, start, end){
    var raw = tr.getAttribute('data-sessions') || '';
    if(raw){
      var parts = raw.split('|');
      for(var i=0;i<parts.length;i++){
        var p = parts[i].split('/');
        if(p[0] <= end && (p[1] || p[0]) >= start) return true;
      }
      return false;
    }
    var s = tr.getAttribute('data-start') || '';
    var e = tr.getAttribute('data-end') || s;
    return !!s && s <= end && e >= start;
  }
  function inWeek(tr){ return inRange(tr, WEEK.start, WEEK.end); }
  function inNextWeek(tr){ return inRange(tr, WEEK.nextStart, WEEK.nextEnd); }

  function haystack(tr){
    if(tr._hay) return tr._hay;
    tr._hay = (tr.getAttribute('data-search') || '').toLowerCase();
    return tr._hay;
  }

  function apply(){
    var state = {q: q ? q.value.trim().toLowerCase() : ''};
    for(var k in filters){ if(filters[k]) state[k] = filters[k].value; }
    var n = 0;
    rows.forEach(function(tr){
      var ok = true;
      if(state.q && haystack(tr).indexOf(state.q) === -1) ok = false;
      if(ok && state.cat && tr.getAttribute('data-cat') !== state.cat) ok = false;
      if(ok && state.status && tr.getAttribute('data-status') !== state.status) ok = false;
      if(ok && state.country && tr.getAttribute('data-country') !== state.country) ok = false;
      if(ok && state.zone && tr.getAttribute('data-zone') !== state.zone) ok = false;
      if(ok && state.score && parseInt(tr.getAttribute('data-score')||'0',10) < parseInt(state.score,10)) ok = false;
      if(ok && state.period){
        var isPast = tr.getAttribute('data-past') === '1';
        if(state.period === 'upcoming' && isPast) ok = false;
        if(state.period === 'past' && !isPast) ok = false;
        if(state.period === 'week' && !inWeek(tr)) ok = false;
        if(state.period === 'nextweek' && !inNextWeek(tr)) ok = false;
      }
      tr.hidden = !ok;
      var d = document.querySelector('tr.detail[data-d="'+tr.getAttribute('data-i')+'"]');
      if(d) d.hidden = !ok;
      if(ok) n++;
    });
    if(shown) shown.textContent = n;
    var empty = document.getElementById('empty');
    if(empty) empty.classList.toggle('hide', n > 0);
  }

  if(q) q.addEventListener('input', function(){ apply(); });
  for(var k in filters){
    if(filters[k]) filters[k].addEventListener('change', apply);
  }
  var reset = document.getElementById('reset');
  if(reset) reset.addEventListener('click', function(){
    if(q) q.value = '';
    for(var k in filters){
      if(!filters[k]) continue;
      filters[k].value = (k==='score' ? '0' : (k==='period' ? 'upcoming' : ''));
    }
    apply();
  });

  Array.prototype.forEach.call(document.querySelectorAll('th[data-sort]'), function(th){
    th.addEventListener('click', function(){
      var key = th.getAttribute('data-sort');
      var dir = th.getAttribute('data-dir') === 'asc' ? -1 : 1;
      var tbody = document.getElementById('rows');
      var sorted = rows.slice().sort(function(a,b){
        var va = a.getAttribute('data-'+key) || '', vb = b.getAttribute('data-'+key) || '';
        if(key === 'score'){ va = parseInt(va||'0',10); vb = parseInt(vb||'0',10); }
        if(va < vb) return -1*dir;
        if(va > vb) return 1*dir;
        return 0;
      });
      sorted.forEach(function(tr){
        var d = document.querySelector('tr.detail[data-d="'+tr.getAttribute('data-i')+'"]');
        tbody.appendChild(tr);
        if(d) tbody.appendChild(d);
      });
      Array.prototype.forEach.call(document.querySelectorAll('th[data-sort]'), function(o){
        o.removeAttribute('data-dir');
      });
      th.setAttribute('data-dir', dir === 1 ? 'asc' : 'desc');
    });
  });

  var tbody = document.getElementById('rows');
  if(tbody) tbody.addEventListener('click', function(ev){
    var tr = ev.target.closest ? ev.target.closest('tr.ev') : null;
    if(!tr) return;
    if(ev.target.tagName === 'A') return;
    var d = document.querySelector('tr.detail[data-d="'+tr.getAttribute('data-i')+'"]');
    if(d){ d.classList.toggle('hide'); tr.classList.toggle('open'); }
  });

  apply();

  // Copie du lien de la fiche courante
  var copyBtn = document.querySelector('[data-copy]');
  if(copyBtn){
    copyBtn.addEventListener('click', function(){
      var url = copyBtn.getAttribute('data-copy');
      var done = function(){
        copyBtn.textContent = 'Lien copié';
        copyBtn.classList.add('ok');
        setTimeout(function(){ copyBtn.textContent = 'Copier le lien'; copyBtn.classList.remove('ok'); }, 2000);
      };
      if(navigator.clipboard && navigator.clipboard.writeText){
        navigator.clipboard.writeText(url).then(done, function(){});
      } else {
        var ta = document.createElement('textarea');
        ta.value = url; ta.setAttribute('readonly',''); ta.style.position='absolute'; ta.style.left='-9999px';
        document.body.appendChild(ta); ta.select();
        try { document.execCommand('copy'); done(); } catch(err) {}
        document.body.removeChild(ta);
      }
    });
  }
})();
