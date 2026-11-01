/* 깜빡임 진단 — 주소에 ?diag=1 을 붙였을 때만 boot.js 가 불러온다. 평소에는 로드되지 않는다.
   무엇을 재나: render() 호출 횟수와 부른 곳, DOM 변경 수, 500ms 이상 걸린 긴 작업(longtask), 오류, CSS 애니메이션 시작 수.
   개인정보는 모으지 않는다(화면 이름·횟수·스택 위치만). 서버로 보내지 않고 화면에 보여 주기만 한다. */
(function () {
  'use strict';
  var log = [], now = function () { return Math.round(performance.now()); };
  var cnt = { render: 0, mut: 0, anim: 0, long: 0, err: 0 };
  var win = [];   /* 최근 5초 렌더 시각 */
  function push(kind, msg) { log.push(now() + 'ms ' + kind + ' ' + msg); if (log.length > 200) log.shift(); }

  function wrapRender() {
    if (typeof window.render !== 'function' || window.render.__diag) return;
    var orig = window.render;
    var w = function () {
      cnt.render++; win.push(now());
      var t0 = performance.now(), r = orig.apply(this, arguments), dt = Math.round(performance.now() - t0);
      var st = (new Error().stack || '').split('\n').slice(2, 5).map(function (s) { return s.trim().replace(/https?:\/\/[^/]+\//, '').replace(/^at /, ''); }).join(' < ');
      push('render', (typeof S !== 'undefined' && S.screen ? S.screen : '?') + ' ' + dt + 'ms ' + st);
      return r;
    };
    w.__diag = true; window.render = w;
  }
  try { new MutationObserver(function (l) { cnt.mut += l.length; }).observe(document.documentElement, { childList: true, subtree: true }); } catch (e) { /* 미지원 */ }
  try { new PerformanceObserver(function (l) { l.getEntries().forEach(function (e) { cnt.long++; push('longtask', Math.round(e.duration) + 'ms'); }); }).observe({ entryTypes: ['longtask'] }); } catch (e) { push('info', 'longtask 미지원 브라우저'); }
  document.addEventListener('animationstart', function (e) { cnt.anim++; push('anim', e.animationName); }, true);
  addEventListener('error', function (e) { cnt.err++; push('error', String(e.message).slice(0, 120) + ' @' + String(e.filename || '').split('/').pop() + ':' + e.lineno); });
  addEventListener('unhandledrejection', function (e) { cnt.err++; push('reject', String(e.reason && e.reason.message || e.reason).slice(0, 120)); });
  document.addEventListener('click', function (e) { var t = e.target; push('click', (t && t.tagName || '?') + (t && t.dataset && t.dataset.act ? ' act=' + t.dataset.act : '')); }, true);

  var box = document.createElement('div');
  box.setAttribute('style', 'position:fixed;left:4px;top:4px;z-index:2147483647;background:rgba(0,0,0,.82);color:#7CFC9A;font:11px/1.35 monospace;padding:6px 8px;border-radius:6px;max-width:92vw;pointer-events:none');
  var btn = document.createElement('button');
  btn.textContent = '로그 복사';
  btn.setAttribute('style', 'position:fixed;right:4px;top:4px;z-index:2147483647;font:12px sans-serif;padding:6px 10px');
  btn.addEventListener('click', function (e) {
    e.stopPropagation();
    var txt = ['diag v1', navigator.userAgent, 'viewport ' + innerWidth + 'x' + innerHeight + ' dpr ' + devicePixelRatio, JSON.stringify(cnt)].concat(log).join('\n');
    var done = function () { btn.textContent = '복사됨'; setTimeout(function () { btn.textContent = '로그 복사'; }, 1500); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(done, function () { prompt('복사해 주세요', txt); });
    else prompt('복사해 주세요', txt);
  }, true);
  function paint() {
    var t = now(); while (win.length && t - win[0] > 5000) win.shift();
    var storm = win.length >= 8;
    box.style.color = storm ? '#ff6b6b' : '#7CFC9A';
    box.textContent = 'render 5s:' + win.length + (storm ? ' ⚠폭주' : '') + ' 누적:' + cnt.render + ' DOM변경:' + cnt.mut + ' 긴작업:' + cnt.long + ' 애니:' + cnt.anim + ' 오류:' + cnt.err;
  }
  function start() {
    document.body.appendChild(box); document.body.appendChild(btn);
    wrapRender(); setInterval(paint, 500); paint();
    push('info', 'diag 시작 screen=' + (typeof S !== 'undefined' ? S.screen : '?'));
  }
  if (document.readyState === 'complete') start(); else addEventListener('load', start);
  window.__diag = { cnt: cnt, log: log };
})();
