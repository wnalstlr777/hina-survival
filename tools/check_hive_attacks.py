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
  paused=false;wildHiveLastSting.clear();this.now=1000;this.events=[];this.actor='hina';lastWildHiveUpdate=this.now;wildHiveClockPaused=false;
  for(const r of snakeFearReactions.values()){restoreSnakeFearOverlay(r);for(const p of r.parts)for(const m of Array.isArray(p.white)?p.white:[p.white])m.dispose();}snakeFearReactions.clear();
  const p=wildHives[0].position;
  for(const ch of characters.values())if(ch.mesh)ch.mesh.position.set(p.x+100,0,p.z+100);
  for(const id of ['hina','daeun'])Object.assign(characters.get(id).stats,{health:100,will:100});
  characters.get('hina').mesh.position.set(p.x+3,p.y-1,p.z);
  for(const hive of wildHives)hive.attack=null;
  camera.position.set(p.x+1000,p.y+1000,p.z+1000);
 },
 step(n=1,interval=50){for(let i=0;i<n;i++){
  this.now+=interval;for(const r of snakeFearReactions.values())restoreSnakeFearOverlay(r);updateSnakeFearOverlay(.05);
  const before=characters.get(this.actor).stats.health;updateWildHives(this.now);
  if(characters.get(this.actor).stats.health<before)this.events.push({now:this.now,bee:wildHives[0].attack.beeIndex,blink:snakeFearReactions.has('hina'),locked:snakeFearLocked('hina')});
 }return this.stats();},
 screenshot(){this.setup();this.actor='daeun';observedId='daeun';daeun.auto=false;__brief.clock(10,9);this.move('hina',100);this.move('daeun',6.5);Object.assign(daeun.stats,{health:47,energy:57,hunger:57,thirst:57,will:70});},
 stats(){return ['hina','daeun'].map(id=>{const s=characters.get(id).stats;return [s.health,s.will];});},
 untilHits(count){for(let i=0;i<1000&&this.events.length<count;i++)this.step();return this.state();},
 state(){const a=wildHives[0].attack;return {phase:a?.phase,hits:a?.hits,bee:a?.beeIndex,tip:a?.tip.toArray(),events:this.events};},
 move(id,distance){const p=wildHives[0].position;characters.get(id).mesh.position.set(p.x+distance,p.y-1,p.z);},
 pause(value){paused=value;},
 reset(){resetSurvivalPresentation();return wildHives.every(h=>h.attack===null)&&wildHiveLastSting.size===0;},
 low(){stats.health=2;stats.will=3;},
 blink(){const r=snakeFearReactions.get("hina");restoreSnakeFearOverlay(r);updateSnakeFearOverlay(.001);return {white:r.parts.every(p=>p.mesh.material===p.white),jump:r.jump,locked:snakeFearLocked("hina")};},
 sting(id,now){return wildHiveSting(id,now);},
 soundActor(id){observedId=id;characters.get(id).stats.will=0;characters.get(id).stats.health=100;wildHiveLastSting.clear();HinaInteractionSFX.setPaused(true);HinaInteractionSFX.setPaused(false);},
 snake(){const started=startSnakeFearReaction("hina");return {started,locked:snakeFearLocked("hina"),blinkOnly:snakeFearReactions.get("hina").blinkOnly};},
 nest(){const p=wildHives[0].position;camera.position.copy(p).add(new THREE.Vector3(0,1,8));camera.lookAt(p);camera.updateMatrixWorld(true);updateWildHives(this.now,.05);const matrix=new THREE.Matrix4();wildHivePools.get('nest').getMatrixAt(0,matrix);return new THREE.Vector3().setFromMatrixScale(matrix).toArray();},
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
   page.evaluate('__hiveCheck.screenshot()')
   screenshot=page.evaluate('__hiveCheck.step(25,200)')
   assert screenshot[1]==[44,65], ('Daeun on day 10 should be attacked inside the hive discovery radius',screenshot,page.evaluate('__hiveCheck.state()'))
   print('PASS screenshot scenario: day-10 manual Daeun, 6.5m from hive, health 47 to 44 and will 70 to 65',mobile,flush=True)
   page.evaluate('__hiveCheck.setup()')
   slow=page.evaluate('__hiveCheck.step(25,200)')
   assert slow==[[97,95],[100,100]], ('5 FPS should still deliver the first sting within 5 seconds',slow,page.evaluate('__hiveCheck.state()'))
   page.evaluate('__hiveCheck.setup()')
   assert page.evaluate('__hiveCheck.step(30)')==[[100,100],[100,100]]
   assert page.evaluate('__hiveCheck.state().phase')=='watch'
   page.evaluate('__hiveCheck.step(6)')
   assert page.evaluate('__hiveCheck.state().phase')=='dive'
   # Compare early and late equal-duration segments of the actual flight path.
   samples=page.evaluate("""()=>{const result=[];for(let i=0;i<6;i++){__hiveCheck.step(5);result.push(__hiveCheck.state().tip);}return result;}""")
   from math import dist
   assert dist(samples[0],samples[1]) < dist(samples[3],samples[4]),samples
   state=page.evaluate('__hiveCheck.untilHits(3)')
   assert page.evaluate('__hiveCheck.stats()')==[[91,85],[100,100]]
   assert state['phase']=='return' and state['hits']==3,state
   assert [e['bee'] for e in state['events']]==[0,1,2],state
   assert all(e['blink'] and not e['locked'] for e in state['events']),state
   assert all(b['now']-a['now']>=4000 for a,b in zip(state['events'],state['events'][1:])),state
   assert page.evaluate('__hiveCheck.step(25)')==[[91,85],[100,100]]
   assert page.evaluate('__hiveCheck.state().phase')=='rest'
   assert page.evaluate('__hiveCheck.step(30)')==[[91,85],[100,100]]
   page.evaluate('__hiveCheck.untilHits(4)')
   assert page.evaluate('__hiveCheck.stats()')==[[88,80],[100,100]]
   page.evaluate('__hiveCheck.move("hina",9);__hiveCheck.step(100)')
   assert page.evaluate('__hiveCheck.stats()')==[[88,80],[100,100]]
   page.evaluate('__hiveCheck.move("hina",3);__hiveCheck.untilHits(5)')
   assert page.evaluate('__hiveCheck.stats()')==[[85,75],[100,100]]
   print('PASS watch, accelerating curved single-bee dives, three sequential hits, blink without stun, cooldown and return',mobile,flush=True)
   # Escape during a dive aborts contact, returns the bee, and permits a new encounter after re-entry.
   page.evaluate('__hiveCheck.setup();__hiveCheck.step(45);__hiveCheck.move("hina",9);__hiveCheck.step()')
   assert page.evaluate('__hiveCheck.state().phase')=='return'
   assert page.evaluate('__hiveCheck.step(50)')==[[100,100],[100,100]]
   assert page.evaluate('__hiveCheck.state().phase')=='idle'
   page.evaluate('__hiveCheck.move("hina",3);__hiveCheck.step(30)')
   before=page.evaluate('__hiveCheck.state()')
   page.evaluate('__hiveCheck.pause(true);__hiveCheck.step(100)')
   assert page.evaluate('__hiveCheck.state()')==before
   page.evaluate('__hiveCheck.pause(false);__hiveCheck.step(50)')
   assert page.evaluate('__hiveCheck.stats()')==[[97,95],[100,100]]
   # Cooldown is global across hives but independent per survivor, with an exact boundary.
   page.evaluate('__hiveCheck.setup()')
   assert page.evaluate('__hiveCheck.sting("hina",10000)')
   assert not page.evaluate('__hiveCheck.sting("hina",13999)')
   assert page.evaluate('__hiveCheck.sting("daeun",10000)')
   assert page.evaluate('__hiveCheck.sting("hina",14000)')
   assert page.evaluate('__hiveCheck.stats()')==[[94,90],[97,95]]
   page.evaluate('__hiveCheck.low()')
   assert page.evaluate('__hiveCheck.sting("hina",18000)')
   assert page.evaluate('__hiveCheck.stats()[0]')==[0,0]
   assert page.evaluate('__hiveCheck.blink()')=={'white':True,'jump':0,'locked':False}
   assert page.evaluate('__hiveCheck.snake()')=={'started':True,'locked':True,'blinkOnly':False}
   assert page.evaluate('__hiveCheck.reset()')
   scale=page.evaluate('__hiveCheck.nest()')
   assert all(abs(a-b)<1e-5 for a,b in zip(scale,[1.35,1.65,1.35])),scale
   print('PASS escape cancels sting, retreat/re-entry, pause, independent cooldowns, stat floors, reset and hive scale',mobile,flush=True)
   # Real HTMLAudio playback: every hit plays even at zero will, after another threat sound,
   # and while six other voices are occupying the mixer.
   page.evaluate('__hiveCheck.setup()')
   page.locator('#mobileMenu' if mobile else '#v521PcMenu').click()
   for actor in ['hina','daeun']:
    page.evaluate('(id)=>__hiveCheck.soundActor(id)',actor)
    for hit in range(3):
     before=page.evaluate('HinaInteractionSFX.audioStatus().started.beeHit||0')
     page.evaluate("HinaInteractionSFX.play('threat',1,false,true)")
     result=page.evaluate('([id,now])=>__hiveCheck.sting(id,now)',[actor,100000+hit*4000])
     assert result
     page.wait_for_function('(n)=>(HinaInteractionSFX.audioStatus().started.beeHit||0)>n',arg=before,timeout=10000,polling=50)
     assert not page.evaluate('HinaInteractionSFX.audioStatus().errors.beeHit')
    before=page.evaluate('HinaInteractionSFX.audioStatus().started.beeHit||0')
    result=page.evaluate("""(id)=>{HinaInteractionSFX.setPaused(true);HinaInteractionSFX.setPaused(false);for(const sound of ['fire','eat','sleep','rest','success','animal'])HinaInteractionSFX.play(sound,1,true);return __hiveCheck.sting(id,116000);}""",actor)
    assert result
    page.wait_for_function('(n)=>(HinaInteractionSFX.audioStatus().started.beeHit||0)>n',arg=before,timeout=10000,polling=50)
   print('PASS first attack within 5s at 5 FPS and actual hit sound on every sting for both survivors',mobile,flush=True)
   page.locator('#mobileMenu' if mobile else '#v521PcMenu').click()
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
