// Independent timing prototype. No game state, inventory or proficiency dependencies.
(()=>{
 'use strict';
 const tiers={common:{name:'흔함',period:3,width:.3},normal:{name:'보통',period:2.3,width:.25},rare:{name:'희귀',period:1.5,width:.2},legendary:{name:'전설',period:.9,width:.15}};
 const style=document.createElement('style');style.textContent=`
 #timingFishingOverlay[hidden]{display:none!important}
 #timingFishingOverlay{position:fixed;inset:0;z-index:2147483001;display:grid;place-items:center;padding:16px;box-sizing:border-box;background:#06161299;touch-action:manipulation}
 #timingFishingPanel{width:min(440px,100%);box-sizing:border-box;padding:20px;border:1px solid #a4c8ad;border-radius:18px;background:rgba(28,53,46,.97);color:#eff9ef;box-shadow:0 8px 35px #0008;font:14px system-ui;max-height:90dvh;overflow:auto}
 #timingFishingPanel header{display:flex;align-items:center;justify-content:space-between;gap:12px}#timingFishingPanel h2{font-size:18px;margin:0}
 #timingFishingPanel button{background:#324e4b;color:white;border:1px solid #a4c8ad;border-radius:10px;padding:10px 12px;cursor:pointer;font:inherit;min-height:42px}
 #timingFishingPanel button:focus-visible{outline:2px solid #ffdc63;outline-offset:3px}
 #timingFishingTiers{display:flex;gap:6px;margin:18px 0;flex-wrap:wrap}#timingFishingTiers button{flex:1}#timingFishingTiers button[aria-pressed=true]{background:#468b70;border-color:#d4efae}
 #timingFishingInfo{line-height:1.6;color:#c7dfd0}
 #timingFishingBar{position:relative;height:42px;margin:24px 0;border:1px solid #78998b;border-radius:8px;background:#132b27;overflow:hidden}
 #timingFishingHit{position:absolute;top:0;bottom:0;background:#438e55;display:grid;place-items:center;color:#edffdf;font-weight:800;font-size:12px}
 #timingFishingCursor{position:absolute;top:0;bottom:0;width:4px;background:#ffdf43;transform:translateX(-50%);box-shadow:0 0 7px #ffdf43;pointer-events:none}
 #timingFishingResult{min-height:24px;text-align:center;font-weight:700}#timingFishingActions{display:flex;gap:8px;margin-top:16px}#timingFishingActions button{flex:1}#timingFishingPress{background:#468b70!important}
 #timingFishingPanel small{display:block;margin-top:14px;color:#bdd2c5;line-height:1.6}
 `;document.head.appendChild(style);
 const overlay=document.createElement('div');overlay.id='timingFishingOverlay';overlay.hidden=true;
 overlay.innerHTML=`<section id="timingFishingPanel" role="dialog" aria-modal="true" aria-labelledby="timingFishingTitle"><header><h2 id="timingFishingTitle">🎣 타이밍 낚시 테스트</h2><button id="timingFishingClose" type="button" aria-label="낚시 테스트 닫기">✕</button></header><div id="timingFishingTiers">${Object.entries(tiers).map(([key,t])=>`<button type="button" data-tier="${key}" aria-pressed="false">${t.name}</button>`).join('')}</div><p id="timingFishingInfo"></p><div id="timingFishingBar" aria-label="노란 커서가 초록 HIT 영역에 있을 때 누르세요"><div id="timingFishingHit">HIT</div><div id="timingFishingCursor"></div></div><div id="timingFishingResult" role="status" aria-live="polite"></div><div id="timingFishingActions"><button id="timingFishingPress" type="button">🎣 낚기</button><button id="timingFishingRetry" type="button">재도전</button></div><small>PC: 스페이스바 또는 낚기 버튼 · 모바일: 버튼 터치<br>테스트 전용 — 아이템 획득·소모와 숙련도 변화 없음</small></section>`;document.body.appendChild(overlay);
 const $=id=>document.getElementById(id),hit=$('timingFishingHit'),cursor=$('timingFishingCursor'),result=$('timingFishingResult'),press=$('timingFishingPress');
 let tier='common',left=0,phase=0,startedAt=0,running=false,raf=0,returnFocus=null;
 function position(now){const cycle=((phase+(now-startedAt)/(tiers[tier].period*1000))%1+1)%1;return cycle<=.5?cycle*2:2-cycle*2;}
 function draw(now){cursor.style.left=position(now)*100+'%';}
 function animate(now){if(overlay.hidden||!running){raf=0;return;}draw(now);raf=requestAnimationFrame(animate);}
 function retry(){
  cancelAnimationFrame(raf);const t=tiers[tier];left=Math.random()*(1-t.width);
  const before=Math.max(0,left-.025),after=Math.min(1,left+t.width+.025),span=before+1-after;
  const sample=Math.random()*span,start=sample<before?sample:after+sample-before;
  phase=Math.random()<.5?start/2:1-start/2;startedAt=performance.now();running=true;
  hit.style.left=left*100+'%';hit.style.width=t.width*100+'%';
  $('timingFishingInfo').textContent=`${t.name} · 왕복 ${t.period.toFixed(1)}초 · 성공 범위 ${Math.round(t.width*100)}%`;
  overlay.querySelectorAll('[data-tier]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.tier===tier)));
  result.textContent='HIT 영역에 맞춰 누르세요';result.style.color='';press.textContent='🎣 낚기';draw(startedAt);raf=requestAnimationFrame(animate);
 }
 function attempt(){if(!running){retry();return;}const now=performance.now(),p=position(now),success=p>=left&&p<=left+tiers[tier].width;running=false;cancelAnimationFrame(raf);draw(now);result.textContent=success?'🐟 성공!':'💨 실패!';result.style.color=success?'#b9f3a9':'#ffc0ac';press.textContent='다시 도전';}
 function close(){overlay.hidden=true;running=false;cancelAnimationFrame(raf);returnFocus?.focus();}
 document.addEventListener('click',e=>{if(!e.target.closest('[data-fishing-test]'))return;e.preventDefault();e.stopImmediatePropagation();returnFocus=e.target.closest('button');$('timingFishingPanel').style.display='block';overlay.hidden=false;retry();press.focus();},true);
 overlay.addEventListener('pointerdown',e=>e.stopPropagation());overlay.addEventListener('click',e=>{e.stopPropagation();if(e.target===overlay)close();});
 $('timingFishingClose').addEventListener('click',close);$('timingFishingRetry').addEventListener('click',retry);press.addEventListener('click',attempt);
 $('timingFishingTiers').addEventListener('click',e=>{const b=e.target.closest('[data-tier]');if(b){tier=b.dataset.tier;retry();}});
 window.addEventListener('keydown',e=>{
  if(overlay.hidden)return;
  if(e.code==='Space'){e.preventDefault();e.stopImmediatePropagation();if(!e.repeat)attempt();}
  else if(e.code==='Escape'){e.preventDefault();e.stopImmediatePropagation();close();}
  else if(e.key==='Tab'){const buttons=[...overlay.querySelectorAll('button')],first=buttons[0],last=buttons.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}
 },true);
 window.addEventListener('keyup',e=>{if(!overlay.hidden&&e.code==='Space'){e.preventDefault();e.stopImmediatePropagation();}},true);
})();
