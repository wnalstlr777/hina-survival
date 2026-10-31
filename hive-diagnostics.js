/* Read-only, local diagnostics. Nothing is uploaded automatically. */
(()=>{
 'use strict';
 const VERSION='5.2.89',errors=[],samples=[],startedAt=performance.now();
 let recording=false,timer=null,panel=null,summary=null,output=null,status=null,toggle=null;
 const bounded=(list,item,max)=>{list.push(item);if(list.length>max)list.shift();};
 const safePath=value=>{try{const u=new URL(value,location.href);return /https?:/.test(u.protocol)?(u.origin+u.pathname).slice(0,300):u.protocol;}catch{return String(value||'').slice(0,160);}};
 const noteError=(type,message,source,line)=>bounded(errors,{timeSeconds:Math.round((performance.now()-startedAt)/1000),type,message:String(message||'').slice(0,1000),source:source?safePath(source):null,line:line||null},30);
 window.addEventListener('error',event=>{
  if(event.message)noteError('javascript',event.message,event.filename,event.lineno);
  else if(event.target?.tagName==='SCRIPT')noteError('script_load','Script could not load',event.target.src);
 },true);
 window.addEventListener('unhandledrejection',event=>noteError('promise',event.reason?.stack||event.reason?.message||event.reason));
 function snapshot(){
  let game=null;
  try{game=window.hinaHiveDiagnosticSnapshot?.()??null;}catch(error){game={snapshotError:String(error.message||error)};}
  return {diagnosticVersion:VERSION,gameSnapshotAvailable:!!window.hinaHiveDiagnosticSnapshot,page:safePath(location.href),title:document.title,visibility:document.visibilityState,userAgent:navigator.userAgent,viewport:{width:innerWidth,height:innerHeight,pixelRatio:devicePixelRatio},game};
 }
 function report(){return {format:'HINA_HIVE_DIAGNOSTIC_V1',collectedAt:new Date().toISOString(),recording,current:snapshot(),errors:[...errors],samples:[...samples]};}
 const text=()=>JSON.stringify(report(),null,2);
 const reasons={ready:'공격 준비 가능',game_paused:'게임이 일시정지됨',page_hidden:'게임 탭이 숨겨짐',selected_actor_unavailable:'선택 캐릭터가 없거나 체력이 0',hive_loop_not_started:'벌 공격 업데이트가 시작되지 않음',hive_loop_stale:'벌 공격 업데이트가 지연되거나 멈춤',attacking_other_character:'다른 캐릭터를 공격 중',rest_between_volleys:'세 번 공격 후 휴식 중',sting_cooldown:'피해 간격 4초를 기다리는 중',watching_before_dive:'돌진 전 관찰 중',diving:'캐릭터를 향해 돌진 중',returning_to_hive:'벌통으로 복귀 중',outside_attack_radius:'공격 범위 밖',inside_radius_but_idle:'범위 안인데 공격 시작 안 됨'};
 function render(){
  if(!panel||panel.hidden)return;
  const current=snapshot(),g=current.game?.snapshotError?null:current.game,h=g?.nearest?.[0];
  const lines=[`진단 ${VERSION} · 게임 ${g?.version||'상태를 읽을 수 없음'}`,recording?`수집 중 · ${samples.length}개 기록`:'수집 정지',g?`캐릭터: ${g.selectedId} · ${g.actor?.automatic?'자동':'수동'} · ${g.day}일차`:'게임 초기화 실패 또는 버전 불일치 가능',g?`체력 ${g.actor?.health} · 의지력 ${g.actor?.will}`:'',h?`가까운 벌통 #${h.id}: ${h.distance}m (공격 ${g.thresholds.attackRadius}m)`:`벌통 수: ${g?.hiveCount??'확인 불가'}`,h?`상태: ${reasons[h.reason]||h.reason}`:'',h?`단계 ${h.phase} · ${h.ageSeconds}초 · ${h.hits}회 피격`:'',g?.flowerInsects?.[0]?`꽃밭 곤충: ${g.flowerInsects[0].kind==='bee'?'벌':'나비'} ${g.flowerInsects[0].distance}m`:'',g?`업데이트 ${g.loop.updates}회 · ${g.loop.lastUpdateAgoMs??'없음'}ms 전`:'',`자바스크립트 오류 ${errors.length}개`];
  summary.textContent=lines.filter(Boolean).join('\n');
  toggle.textContent=recording?'수집 정지':'수집 시작';toggle.setAttribute('aria-pressed',String(recording));
 }
 function sample(){
  const g=snapshot().game,h=g?.nearest?.[0];
  bounded(samples,{at:new Date().toISOString(),actor:g?.selectedId??null,position:g?.actor?.position??null,health:g?.actor?.health??null,will:g?.actor?.will??null,paused:g?.paused??null,updates:g?.loop?.updates??null,lastUpdateAgoMs:g?.loop?.lastUpdateAgoMs??null,hive:h?{id:h.id,distance:h.distance,phase:h.phase,ageSeconds:h.ageSeconds,hits:h.hits,targetId:h.targetId,reason:h.reason}:null,hitSoundStarts:g?.audio?.started?.beeHit??0},60);
  render();
 }
 function start(){if(recording)return;recording=true;sample();timer=setInterval(sample,1000);render();}
 function stop(){recording=false;if(timer!==null)clearInterval(timer);timer=null;render();}
 function open(){mount();panel.hidden=false;start();render();}
 function showText(value,message){output.hidden=false;output.value=value;status.textContent=message;output.focus();output.select();}
 async function copy(){
  const value=text();
  try{
   if(!navigator.clipboard?.writeText)throw new Error('Clipboard unavailable');
   await navigator.clipboard.writeText(value);status.textContent='복사했습니다. 이 채팅에 붙여넣어 주세요.';
  }catch{showText(value,'자동 복사가 안 되면 아래 내용을 길게 눌러 전체 선택 후 복사해 주세요.');}
  return value;
 }
 function download(){
  const blob=new Blob([text()],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='hina-hive-diagnostic-'+Date.now()+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status.textContent='진단 파일을 저장했습니다. 이 채팅에 첨부해 주세요.';
 }
 function button(label,id,action){const b=document.createElement('button');b.type='button';b.id=id;b.textContent=label;b.addEventListener('click',action);return b;}
 function mount(){
  if(panel)return;
  const css=document.createElement('style');css.textContent=`
#hiveDiagnosticPanel{position:fixed;z-index:2147483647;left:8px;top:max(8px,env(safe-area-inset-top));width:min(350px,calc(100vw - 16px));max-height:65dvh;overflow:auto;box-sizing:border-box;padding:12px;border:1px solid #a7dace;border-radius:12px;background:#102820f5;color:#f1fff9;font:12px/1.5 system-ui,sans-serif;box-shadow:0 4px 20px #0008;touch-action:pan-y}
#hiveDiagnosticPanel[hidden],#hiveDiagnosticText[hidden]{display:none!important}
#hiveDiagnosticPanel pre{margin:9px 0;white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.5 system-ui,sans-serif}
#hiveDiagnosticPanel button{padding:7px 9px;margin:3px 3px 3px 0;font-size:12px;border-radius:6px}
#hiveDiagnosticPanel textarea{box-sizing:border-box;width:100%;height:130px;background:#fff;color:#111;font:11px monospace;user-select:text;-webkit-user-select:text}
#hiveDiagnosticButton{display:inline-block!important;margin-top:8px!important;font-size:13px!important}
`;
  document.head.appendChild(css);
  panel=document.createElement('section');panel.id='hiveDiagnosticPanel';panel.hidden=true;panel.setAttribute('aria-label','벌 공격 진단');
  const title=document.createElement('strong');title.textContent='🐝 벌 공격 진단 · '+VERSION;
  const help=document.createElement('p');help.textContent='창을 숨기고 벌통 옆에서 20~30초 기다린 뒤, 다시 열어 진단 정보를 복사해 주세요. 정보는 자동 전송되지 않습니다.';
  summary=document.createElement('pre');summary.id='hiveDiagnosticSummary';
  toggle=button('수집 시작','hiveDiagnosticRecord',()=>recording?stop():start());
  output=document.createElement('textarea');output.id='hiveDiagnosticText';output.readOnly=true;output.hidden=true;output.setAttribute('aria-label','복사용 진단 정보');
  status=document.createElement('p');status.id='hiveDiagnosticStatus';status.setAttribute('aria-live','polite');
  panel.append(title,help,summary,toggle,button('진단 정보 복사','hiveDiagnosticCopy',copy),button('파일 저장','hiveDiagnosticDownload',download),button('원문 보기','hiveDiagnosticShowText',()=>showText(text(),'내용을 길게 눌러 복사할 수 있어요.')),button('창 숨기기','hiveDiagnosticHide',()=>{panel.hidden=true;}),status,output);
  document.body.appendChild(panel);
  const launcher=button('🐝 벌 공격 진단','hiveDiagnosticButton',open);
  (document.getElementById('v5264SettingsControls')||document.getElementById('v522SettingItems')||document.body).appendChild(launcher);
  // A direct link works even if a game startup error prevents its normal menu from opening.
  if(new URLSearchParams(location.search).get('hive-debug')==='1'){panel.hidden=false;start();}
 }
 window.HinaHiveDiagnostics={version:VERSION,snapshot,report,text,start,stop,open,copy};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
})();
