"""Checks the sound/UI/meditation/fish stabilization brief on both layouts.
Run with a static server on port 8000. Requires Playwright and Chromium.
"""
from pathlib import Path
import runpy
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE=runpy.run_path(str(ROOT/'tools/check_survival_presentation.py'))
EXTRA=r'''
window.__stable={
 setup(id,automatic=false){
  if(v504Meditation.active)v504MeditationStop();
  __brief.setup(2,12,id,0);hinaControlUnlocked=true;sharedHomeActive=false;state='explore';sleepingPose=false;
  if(id==='hina')hinaManual=!automatic;else daeun.auto=automatic;
  for(const r of characterAnimation.rigs){characterAnimation.cancel(r.id);r.release=0;}
  fireSuccess=true;fireKnowledge=80;campfire.visible=true;daeun.inventory.fuel=80;daeunResources.fire.group.visible=true;nextDaeunSnakeAt=Infinity;
  const p=v504ActorPosition(id),f=v507FirePos(id);p.set(f.x+2,terrainTopAt(f.x+2,f.z,0),f.z);
  if(id==='daeun'&&!safeRestPoint(p)){let found=false;for(let r=1;r<7&&!found;r++)for(let i=0;i<16;i++){const x=f.x+Math.cos(i*Math.PI/8)*r,z=f.z+Math.sin(i*Math.PI/8)*r;const q=new THREE.Vector3(x,terrainTopAt(x,z,0),z);if(safeRestPoint(q)){p.copy(q);found=true;break;}}if(!found)throw new Error('No safe meditation fixture location');}
  if(id==='hina'){stats.will=20;stats.hunger=50;carriedBerries=2;selectedHinaQuickFood='berries';}else{daeun.stats.will=20;daeun.stats.hunger=50;daeun.inventory.berries=2;daeun.inventory.fish=0;selectedQuickFood='berries';daeun.action='manual';daeun.restLocked=false;}
  refreshCharacterUI(performance.now(),true);v504MeditationTick(0);
 },
 meditation(){const id=observedId;return {active:v504Meditation.active,duration:v504Meditation.duration,will:characters.get(id).stats.will,action:id==='hina'?state:daeun.action,automatic:v504Meditation.automatic,completed:v504Meditation.completed,eligible:v504MeditationEligible(id),sleeping:v504ActorSleeping(id),distance:v504ActorPosition(id).distanceTo(v507FirePos(id)),lit:v507FireLit(id),button:v504MeditationButton.style.display};},
 startMed:()=>v504MeditationStart(),stopMed:()=>v504MeditationStop(),
 nearComplete(){elapsed=v504Meditation.start+v504Meditation.duration-.001;v504MeditationTick(0);},
 complete(){elapsed=v504Meditation.start+v504Meditation.duration+.001;v504MeditationTick(0);},
 tickMed(){v504MeditationTick(0);},
 leave(){v504ActorPosition(observedId).x+=1;v504MeditationTick(0);},
 pose(){if(observedId==='hina')updateCharacterPose();else updateDaeun(0,0);const rig=characterAnimation.byId[observedId];return {root:rig.root.rotation.x,leg:rig.legs[0].rotation.x};},
 meal(){quickEatDaeun();return characterAnimation.active(observedId);},
 finishMeal(){const r=characterAnimation.byId[observedId];if(r.meal){r.meal.time=2;r.meal.last=performance.now();characterAnimation.updateMeal(r,performance.now());}},
 fullFood(){characters.get(observedId).stats.hunger=100;},
 noFood(){characters.get(observedId).stats.hunger=50;if(observedId==='hina')carriedBerries=0;else daeun.inventory.berries=0;},
 threat(source,before,after){return threatWillLossSound(observedId,source,before,after);},
 snake(id){observedId=id;characters.get(id).stats.will=80;const p=characters.get(id).mesh.position;const snake=makeSnake(p.x,p.z);snake.expiresAt=Infinity;snake.habitatLeaveAt=Infinity;snake.wanderSpeed=0;snake.roamTarget=null;clockParts();elapsed=DAY_SECONDS*3;day=4;if(id==='daeun'){snakes.splice(snakes.indexOf(snake),1);daeunSnakes.push(snake);updateDaeunSnakes(0);}else{explored.clear();for(const key of hinaFogKeys)explored.add(key);nextSnakeSpawn=Infinity;updateSnakes(0);}return characters.get(id).stats.will;},
 bear(id){observedId=id;for(const other of characters.values())if(other.id!==id)other.mesh.position.set(1000,0,1000);const ch=characters.get(id);ch.stats.will=80;middleBear.position.set(bearTerritory.x,terrainTopAt(bearTerritory.x,bearTerritory.z),bearTerritory.z);ch.mesh.position.copy(middleBear.position).add(new THREE.Vector3(1,0,0));bearState.target=null;updateMiddleBear(1);return ch.stats.will;},
 aiMental(){this.setup('hina',true);Object.assign(stats,{hunger:90,thirst:90,energy:90,will:20});lastWashDay=clockParts().day;lastWashAttemptDay=clockParts().day;mentalRestCooldown=0;fireEverLit=true;fireKnowledge=100;fireDryStock=4;carriedFish.length=0;retreatPoints.length=0;chooseNextDayAction();const chosen=state;elapsed=mentalRestStart+38.1;dayTwoPlusDecide(0);return {chosen,will:stats.will,timed:v504Meditation.active};},
 fish(){const save=Math.random;Math.random=()=>.5;const count=fishes.length;const e=elapsed;fishNextVisit=0;updateFishVisit();const duration=fishVisitEnd-elapsed,cycle=fishNextVisit-elapsed;let minWait=Infinity;for(let i=0;i<200;i++){elapsed=fishNextVisit;updateFishVisit();minWait=Math.min(minWait,fishNextVisit-fishVisitEnd);}Math.random=save;elapsed=e;return {duration,cycle,oldCycle:DAY_SECONDS/24*(1.2+.5*.675+FISH_VISIT_MIN+.5*FISH_VISIT_SPAN),count,after:fishes.length,minWait,practice:DAEUN_DAILY_PRACTICE_LIMIT.fish,hinaWindows:hinaFishOpportunities.fish?.windows.length};},
 select(id){selectCharacter(id);syncCharacterLights();},
 autoRecovery(id){observedId=id;if(id==='hina'){hinaManual=false;state='mentalRest';mentalRestStart=elapsed;mentalRestCooldown=elapsed+115;}else{daeun.auto=true;daeun.action='rest';daeun.stats.will=20;}v510SyncMeditationUI();return {detected:v504AutomaticMeditation(id),timedRewardActive:v504Meditation.active};}
};
'''
BODY=BASE['BODY'].replace('window.__hinaClockAuditStart=performance.now();','window.__hinaClockAuditStart=performance.now();'+EXTRA,1)

def run():
 BASE['check_scripts']()
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  for mobile in [True,False]:
   page=browser.new_page(viewport={'width':390 if mobile else 1280,'height':844},is_mobile=mobile,has_touch=mobile)
   page.set_default_timeout(6000)
   errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.add_init_script('window.requestAnimationFrame=()=>0;')
   page.route('http://127.0.0.1:8000/',lambda route:route.fulfill(status=200,content_type='text/html',body=BODY))
   page.goto('http://127.0.0.1:8000/',wait_until='domcontentloaded');page.wait_for_function('!!window.__stable',polling=50)
   def attempts(kind):return page.evaluate('(k)=>HinaInteractionSFX.audioStatus().attempts[k]||0',kind)
   def transition(selector):
    page.wait_for_timeout(160);before=attempts('ui')
    if selector=='map-outside':page.mouse.click(5,400)
    else:page.locator(selector).click()
    page.wait_for_function('(n)=>(HinaInteractionSFX.audioStatus().attempts.ui||0)>n',arg=before,polling=50,timeout=3000)
    page.wait_for_timeout(120);assert attempts('ui')==before+1,(selector,before,page.evaluate('HinaInteractionSFX.audioStatus()'))
   # Native open/close of all high-use menus uses the skills sound, exactly once.
   transition('#v498SkillToggle');transition('#v498SkillClose')
   transition('#v493CraftToggle');transition('#v493CraftClose')
   transition('#daeunItemToggle');transition('#daeunItemToggle')
   if mobile:
    transition('#mobileMenu');transition('#v5261MenuShell [data-pane="settings"]');transition('#mobileMenu')
    transition('#mobileMenu');transition('#v521MobileMap');transition('map-outside')
   else:
    transition('#v521PcMenu');transition('#v521Menu [data-v521="settings"]');page.mouse.click(900,700);page.wait_for_timeout(700)
    transition('#v523Map');transition('map-outside')
   if mobile and page.locator('#v5261MenuShell').get_attribute('data-open')=='1':transition('#mobileMenu')
   assert not any(attempts(k) for k in ['step','inventory','water','wood','craft','rustle','wash','fireAmbient'])
   print('PASS real UI open/close, shared skill sound and no duplicates',mobile,flush=True)
   assert page.evaluate("['step','inventory','water','wood','craft','rustle','wash','fireAmbient'].every(k=>!HinaInteractionSFX.play(k,1,true))")
   # Manual and automatic-mode explicit meditation keep the original 25min/+6 contract.
   for actor in ['hina','daeun']:
    for automatic in [False,True]:
     page.evaluate('([id,auto])=>__stable.setup(id,auto)',[actor,automatic]);assert page.locator('#v504MeditationButton').is_visible(), (actor,automatic,page.evaluate('__stable.meditation()'))
     before=page.evaluate('__stable.meditation()');assert page.evaluate('__stable.startMed()')
     pose=page.evaluate('__stable.pose()');assert abs(pose['root'])<.01 and pose['leg']<-.8,pose
     page.evaluate('__stable.nearComplete()');assert page.evaluate('__stable.meditation().will')==before['will']
     page.evaluate('__stable.complete()');after=page.evaluate('__stable.meditation()');assert after['will']==before['will']+6,after
     assert abs(after['duration']-25*1200/1440)<.001
     page.evaluate('__stable.tickMed()');assert page.evaluate('__stable.meditation().will')==after['will']
     if automatic:assert not after['active']
     else:page.evaluate('__stable.stopMed()');assert not page.evaluate('__stable.meditation().active')
    page.evaluate('(id)=>__stable.setup(id,false)',actor);page.evaluate('__stable.startMed();__stable.leave()');assert not page.evaluate('__stable.meditation().active')
    page.evaluate('(id)=>__stable.setup(id,false)',actor);page.evaluate('__stable.startMed()');page.evaluate('(id)=>__brief.ring(id,true)',actor);page.evaluate('__stable.tickMed()');assert not page.evaluate('__stable.meditation().active')
    page.evaluate('(id)=>__stable.setup(id,true)',actor);assert page.evaluate('(id)=>__stable.autoRecovery(id)',actor)=={'detected':True,'timedRewardActive':False}
   print('PASS meditation UI/pose/reward/duration/interrupt and existing AI recovery without double rewards',mobile,flush=True)
   # Accepted meal start, never an empty/repeated click or meal completion.
   for actor in ['hina','daeun']:
    page.wait_for_timeout(500);page.evaluate('(id)=>__stable.setup(id,false)',actor);before=attempts('eat');assert page.evaluate('__stable.meal()')
    assert attempts('eat')==before+1
    page.evaluate('__stable.meal()');assert attempts('eat')==before+1
    page.evaluate('__stable.finishMeal()');assert attempts('eat')==before+1
    page.evaluate('__stable.fullFood();__stable.meal()');assert attempts('eat')==before+1
    page.evaluate('__stable.noFood();__stable.meal()');assert attempts('eat')==before+1
   print('PASS meal-start sound, duplicate/empty meals rejected, no completion replay',mobile,flush=True)
   # Common actual-loss gate, including cross-threat cooldown, no night-only cues.
   page.evaluate("__stable.setup('daeun',false)");n=attempts('threat');assert not page.evaluate("__stable.threat('night',50,49)");assert not page.evaluate("__stable.threat('snake',50,50)")
   assert page.evaluate("__stable.threat('snake',50,20)");assert attempts('threat')==n+1
   assert not page.evaluate("__stable.threat('bear',50,49)");assert attempts('threat')==n+1
   page.wait_for_timeout(2600);assert page.evaluate("__stable.threat('bear',50,49)");assert attempts('threat')==n+2
   for actor in ['hina','daeun']:
    page.wait_for_timeout(2600);page.evaluate('(id)=>__stable.setup(id,false)',actor);n=attempts('threat')
    assert page.evaluate('(id)=>__stable.snake(id)',actor)==50
    assert attempts('threat')==n+1
    page.wait_for_timeout(2600);n=attempts('threat');will=page.evaluate('(id)=>__stable.bear(id)',actor)
    assert abs(will-79.4)<.0001,will
    assert attempts('threat')==n+1
   mental=page.evaluate('__stable.aiMental()');assert mental=={'chosen':'mentalRest','will':27,'timed':False},mental
   print('PASS actual threat-loss gating and global cooldown',mobile,flush=True)
   for actor in ['hina','daeun','hina','daeun']:
    page.evaluate('(id)=>__stable.select(id)',actor);page.wait_for_timeout(250)
    selected=page.locator('#characterBar [data-selected="true"]');assert selected.count()==1
    assert selected.get_attribute('id')==('observeHina' if actor=='hina' else 'observeDaeun')
    other=page.locator('#observeDaeun' if actor=='hina' else '#observeHina');assert other.evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(53, 76, 71)'
   info=page.evaluate('__stable.fish()');assert abs(info['oldCycle']/info['cycle']-1.5)<1e-10,info
   assert info['count']==info['after'] and info['minWait']>0 and info['practice']==4,info
   print('PASS mutually-exclusive selection and exact 1.5x visit rate with fixed cap',mobile,info,flush=True)
   assert not errors,errors
   assert not page.evaluate('HinaInteractionSFX.audioStatus().errors')
   page.close()
  browser.close()
 print('PASS stabilization brief checks',flush=True)
if __name__=='__main__':run()
