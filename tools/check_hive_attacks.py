"""Hive damage/cooldown and meditation/HUD regression checks.
Run a static server on port 8000. Requires Python Playwright and Chromium.
"""
from pathlib import Path
import runpy
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = runpy.run_path(str(ROOT / 'tools/check_stabilization.py'))
FIXTURE = r'''
window.__hiveCheck={
 setup(){
  paused=false;wildHiveLastSting.clear();
  const p=wildHives[0].position;
  for(const [id,ch] of characters){if(ch.mesh)ch.mesh.position.set(p.x+100,0,p.z+100);}
  for(const id of ['hina','daeun']){const ch=characters.get(id);ch.mesh.position.set(p.x+1,p.y-1,p.z);Object.assign(ch.stats,{health:100,will:100});}
  for(const hive of wildHives)hive.scatter=0;
  camera.position.set(p.x+1000,p.y+1000,p.z+1000);
 },
 step(now,n=1){for(let i=0;i<n;i++)updateWildHives(now+i*50,.05);return this.stats();},
 stats(){return ['hina','daeun'].map(id=>{const s=characters.get(id).stats;return [s.health,s.will];});},
 move(id,near){const p=wildHives[0].position;characters.get(id).mesh.position.set(p.x+(near?1:100),p.y-1,p.z);},
 low(){for(const ch of characters.values())if(ch.stats)Object.assign(ch.stats,{health:2,will:3});},
 pause(value){paused=value;},
 reset(){resetSurvivalPresentation();},
 nest(){const p=wildHives[0].position;camera.position.copy(p).add(new THREE.Vector3(0,1,8));camera.lookAt(p);camera.updateMatrixWorld(true);updateWildHives(30000,.05);const matrix=new THREE.Matrix4();wildHivePools.get('nest').getMatrixAt(0,matrix);const scale=new THREE.Vector3().setFromMatrixScale(matrix);return scale.toArray();},
 meditation(id){__stable.setup(id,false);observedId=id;const started=v504MeditationStart(id);refreshHinaManualEmojis();if(id==='daeun')refreshManualActionUI();return {started,hina: getComputedStyle(hinaManualMarkers.fire).display,daeun:getComputedStyle(fireEmojiMarker).display};},
 stop(){v504MeditationStop();},
 layout(){v519PositionObjective();const el=v517ObjectiveUI,s=getComputedStyle(el);return {left:parseFloat(s.left),right:parseFloat(s.right),width:innerWidth};}
};
'''
# Keep fixtures confined to served test responses.
BODY = BASE['BODY'].replace('window.__hinaClockAuditStart=performance.now();', 'window.__hinaClockAuditStart=performance.now();'+FIXTURE, 1)

def run():
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  for mobile in [True,False]:
   page=browser.new_page(viewport={'width':390 if mobile else 1280,'height':844},is_mobile=mobile,has_touch=mobile)
   errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script('window.requestAnimationFrame=()=>0;')
   page.route('http://127.0.0.1:8000/',lambda route:route.fulfill(status=200,content_type='text/html',body=BODY))
   page.goto('http://127.0.0.1:8000/',wait_until='domcontentloaded',timeout=90000)
   page.wait_for_function('!!window.__hiveCheck',timeout=90000)
   page.evaluate('__hiveCheck.setup()')
   assert page.evaluate('__hiveCheck.step(1000,10)')==[[97,95],[97,95]]
   assert page.evaluate('__hiveCheck.step(4999)')==[[97,95],[97,95]]
   # First hit occurs at 1300 after swarm approach; 5300 is the exact boundary.
   assert page.evaluate('__hiveCheck.step(5300)')==[[94,90],[94,90]]
   page.evaluate('__hiveCheck.move("hina",false)')
   assert page.evaluate('__hiveCheck.step(9300)')==[[94,90],[91,85]]
   page.evaluate('__hiveCheck.pause(true)')
   assert page.evaluate('__hiveCheck.step(14000)')==[[94,90],[91,85]]
   page.evaluate('__hiveCheck.pause(false);__hiveCheck.move("hina",true);__hiveCheck.low()')
   assert page.evaluate('__hiveCheck.step(18000)')==[[0,0],[0,0]]
   page.evaluate('__hiveCheck.setup();__hiveCheck.step(20000,10);__hiveCheck.reset()')
   assert page.evaluate('__hiveCheck.step(21000)')==[[94,90],[94,90]]
   scale=page.evaluate('__hiveCheck.nest()')
   assert all(abs(a-b)<1e-5 for a,b in zip(scale,[1.35,1.65,1.35])),scale
   print('PASS swarm approach, offscreen damage, per-character 4s cooldown, pause, floors, reset and 1.5x hive',mobile,flush=True)
   for actor in ['hina','daeun']:
    result=page.evaluate('(id)=>__hiveCheck.meditation(id)',actor)
    assert result=={'started':True,'hina':'none','daeun':'none'},result
    page.evaluate('__hiveCheck.stop()')
   layout=page.evaluate('__hiveCheck.layout()')
   assert abs(layout['left']-(118 if mobile else 628))<1,layout
   assert not errors,errors
   print('PASS meditation fire markers hidden and objective shifted 12px left',mobile,flush=True)
   page.close()
  browser.close()

if __name__=='__main__':run()
