"""Browser regression checks. Requires Python Playwright and /usr/bin/chromium.
Run a static server for the repository on port 8000, then run this script.
Game controls below are injected into test responses only, never the saved app.
"""
from pathlib import Path
import subprocess
import re
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'index.html').read_text()
FIXTURE = r'''
window.__brief={
 now:()=>performance.now(),
 advance(ms){window.__briefTime+=ms;},
 clock(d,h){elapsed=(d-1)*DAY_SECONDS+((h<6?h+24:h)-12)*DAY_SECONDS/24;day=clockParts().day;},
 setup(d=1,h=21,id='daeun',distance=30){
  this.clock(d,h);observedId=id;hinaManual=false;daeun.auto=true;state='explore';target=null;daeun.action='explore';daeun.path=[];daeun.manualTask=null;sharedDaeunResourceTask=null;hinaManualTask=null;hinaCookingTask=null;
  for(const ch of characters.values()){if(ch.stats)Object.assign(ch.stats,{health:100,energy:90,hunger:90,thirst:90,will:80});}
  middleBear.position.set(-1000,0,-1000);for(const snake of [...snakes,...daeunSnakes])snake.active=false;
  const p=characters.get(id).mesh.position,home=survivorHomeCaves.get(id);p.set(home.x+distance,terrainTopAt(home.x+distance,home.z,0),home.z);
  survivorSpeech.clear();companionSpeech.until=0;meetingFollowUntil=0;companionChat.pending=null;companionChat.nextAt=Infinity;
  resetSurvivalPresentation();
  Object.values(v517ObjectiveProgress).forEach(rec=>{rec.nightSeconds=0;rec.nightSurvived=false;rec.fireCompleted=false;});
 },
 guide(yaw=0){v517UpdateObjectives(0);const p=characters.get(observedId).mesh.position;camera.position.set(p.x+Math.cos(yaw)*20,p.y+20,p.z+Math.sin(yaw)*20);camera.lookAt(p);camera.updateMatrixWorld(true);updateFirstNightGuide();return {hidden:survivalGuide.hidden,angle:parseFloat(survivalGuide.querySelector('.cave-guide-arrow').style.transform.match(/[-\d.]+/)?.[0]),text:v517ObjectiveMessage.textContent};},
 ring(id,auto){if(id==='hina')hinaManual=!auto;else daeun.auto=auto;syncCharacterLights();},
 begin(){return beginHinaFlower(cameraFlowerPatches[0],performance.now());},
 flowerTick(){updateHinaFlower(performance.now());},
 flower(){return {visible:!!survivalFlower.mesh?.visible,expires:survivalFlower.expiresAt,elapsed,generation:survivalFlower.generation,seen:[...survivalFlower.seen],reply:!!survivalFlower.reply,count:head.children.filter(ch=>ch.name==='HinaHairFlower').length,uuid:survivalFlower.mesh?.uuid};},
 manual(value){hinaManual=value;},
 expire(){elapsed=survivalFlower.expiresAt+.01;updateHinaFlower(performance.now());},
 unsafe(value){stats.thirst=value?5:90;},
 clearSpeech(){survivorSpeech.clear();survivalSocialUntil=0;companionSpeech.until=0;},
 nearFriend(id='daeun'){let ch=characters.get(id);if(!ch){ch={id,name:id,mesh:new THREE.Group(),auto:true,stats:{health:100,energy:90,hunger:90,thirst:90,will:80}};characters.set(id,ch);}ch.mesh.position.copy(hana.position).add(new THREE.Vector3(3,0,0));return ch;},
 praise(){updateFlowerCompliments(performance.now());return [...characters.keys()].map(id=>({id,speech:survivorSpeech.current(id)?.text}));},
 important(){survivorSpeech.post('daeun','위험! 도망가야 해!');},
 mood(id,context,last){return selectSurvivalMoodLine(id,context,last);},
 pose(){const r=characterAnimation.byId.hina;characterAnimation.beginFrame();characterAnimation.apply(r,.05,performance.now());return {arm:r.arms[1].rotation.x,elbow:r.elbow1};},
 snapshot(){return {position:hana.position.toArray(),state,path:navPath.length,target};},
 sleep(value){state=value?'sleep':'explore';sleepingPose=value;target=null;},
 approach(roll,reset=true){const patch=cameraFlowerPatches[0];hana.position.set(patch.cx,terrainTopAt(patch.cx,patch.cz,0),patch.cz);survivalFlower.nextCheck=0;if(reset)survivalFlower.patch=null;const original=Math.random;try{Math.random=()=>roll;updateHinaFlower(performance.now());}finally{Math.random=original;}return !!survivalFlower.motion;},
 drawCost(){const mesh=survivalFlower.mesh,wasVisible=mesh.visible;camera.position.copy(hana.position).add(new THREE.Vector3(8,8,8));camera.lookAt(hana.position);camera.updateMatrixWorld(true);mesh.visible=false;renderer.render(scene,camera);const before={...renderer.info.render};mesh.visible=true;renderer.render(scene,camera);const after={...renderer.info.render};mesh.visible=wasVisible;return {calls:after.calls-before.calls,triangles:after.triangles-before.triangles};},
 render(){renderer.render(scene,camera);},
 runSound(h){this.clock(2,h);const c=clockParts();updateSound(.05,c.h>=20||c.h<4);},
 socialTick(){updateSurvivalMoods(performance.now());return [...characters.keys()].map(id=>({id,text:survivorSpeech.current(id)?.text}));}
};
'''
BODY = SOURCE.replace('window.__hinaClockAuditStart=performance.now();', 'window.__hinaClockAuditStart=performance.now();' + FIXTURE, 1)


def check_scripts():
    for attrs, script in re.findall(r'<script([^>]*)>(.*?)</script>', SOURCE, re.S):
        if 'importmap' in attrs:
            continue
        file = Path('/tmp/hina-check.mjs' if 'module' in attrs else '/tmp/hina-check.js')
        file.write_text(script)
        subprocess.run(['node', '--check', str(file)], check=True, capture_output=True)
    assert (ROOT / 'sounds/step.wav').is_file() and (ROOT / 'sounds/inventory.wav').is_file()


def run():
    check_scripts()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        for mobile in ([False] if os.environ.get('HINA_CHECK_DESKTOP_ONLY') else [True, False]):
            page = browser.new_page(viewport={'width': 390 if mobile else 1280, 'height': 844}, is_mobile=mobile, has_touch=mobile)
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            # Deterministic logic checks; the initial game render and CSS still run.
            page.add_init_script('window.requestAnimationFrame=()=>0;')
            page.route('http://127.0.0.1:8000/', lambda route: route.fulfill(status=200, content_type='text/html', body=BODY))
            page.goto('http://127.0.0.1:8000/', wait_until='domcontentloaded')
            page.wait_for_function('!!window.__brief && !!window.HinaInteractionSFX')
            page.locator('#mobileMenu' if mobile else '#v521PcMenu').click()
            page.evaluate('window.__briefTime=100000;Object.defineProperty(performance,"now",{configurable:true,value:()=>window.__briefTime});')
            # Every entry point, even force-play, must reject sand/footstep feedback.
            assert page.evaluate("['step','footstep','sand','walk','run','inventory'].every(kind=>!HinaInteractionSFX.play(kind,1,true))")
            page.evaluate("for(const id of ['hina','daeun'])for(let n=0;n<30;n++)HinaInteractionSFX.movement(id,{x:n,z:0},'explore')")
            assert not page.evaluate('HinaInteractionSFX.audioStatus().attempts.step')
            for sound in ['water', 'fire', 'craft', 'eat', 'sleep', 'ui']:
                played=page.evaluate('(kind)=>{__brief.advance(1000);return HinaInteractionSFX.play(kind);}', sound)
                assert played, (sound,page.evaluate('HinaInteractionSFX.audioStatus()'))
                try:
                    page.wait_for_function('(kind)=>HinaInteractionSFX.audioStatus().started[kind]>=1', arg=sound, polling=50, timeout=5000)
                except Exception:
                    print('AUDIO FAILURE',sound,page.evaluate('HinaInteractionSFX.audioStatus()'),flush=True)
                    raise
                page.wait_for_timeout(600)
            print('PASS sound policy and preserved unique action sounds', mobile, flush=True)
            # Shared scheduler: 15-35 real seconds AFTER actual completion.
            for night in [False, True]:
                page.evaluate('(night)=>{__brief.advance(100000);HinaInteractionSFX.wildlife(night,__brief.now());}', night)
                state = page.evaluate('HinaInteractionSFX.audioStatus().wildlife')
                assert 15000 <= state['nextAt'] - page.evaluate('__brief.now()') <= 35000
                for _ in range(2):
                    page.evaluate('(night)=>{window.__briefTime=HinaInteractionSFX.audioStatus().wildlife.nextAt+1;HinaInteractionSFX.wildlife(night,__brief.now());}', night)
                    assert page.evaluate('HinaInteractionSFX.audioStatus().wildlife.waiting')
                    page.wait_for_timeout(1400)
                    page.evaluate('(night)=>HinaInteractionSFX.wildlife(night,__brief.now())', night)
                    state = page.evaluate('HinaInteractionSFX.audioStatus().wildlife')
                    assert not state['waiting']
                    assert 15000 <= state['nextAt'] - page.evaluate('__brief.now()') <= 35000
            for hour, kind in [(19, 'bird'), (20, 'owl'), (3, 'owl'), (4, 'bird')]:
                page.evaluate('(h)=>__brief.runSound(h)', hour)
                assert page.evaluate('HinaInteractionSFX.audioStatus().wildlife.phase') == kind
            print('PASS randomized wildlife completion intervals and 20:00-04:00 boundary', mobile, flush=True)
            # Tutorial trigger conditions, own caves, arrival/reappearance and camera heading.
            for actor in ['hina', 'daeun']:
                page.evaluate('(id)=>__brief.setup(1,12,id,30)', actor)
                assert page.evaluate('__brief.guide().hidden')
                page.evaluate('(id)=>__brief.setup(1,19,id,30)', actor)
                assert page.evaluate('__brief.guide().text') == '동굴로 가야합니다.'
                assert page.locator('#v517ObjectiveUI').evaluate('(e)=>getComputedStyle(e).animationDuration') == '1.2s'
                page.evaluate('(id)=>__brief.setup(1,21,id,30)', actor)
                a = page.evaluate('__brief.guide(0)')
                b = page.evaluate('__brief.guide(Math.PI/2)')
                assert not a['hidden'] and not b['hidden']
                assert abs(abs(a['angle'] - b['angle']) - 90) < .01
                assert b['text'] == '밤에 동굴을 벗어나면 의지력이 빠르게 감소합니다.'
                assert page.locator('.v517Message').evaluate('(e)=>getComputedStyle(e).color') == 'rgb(255, 255, 255)'
                page.evaluate('(id)=>__brief.setup(1,21,id,10)', actor)
                assert page.evaluate('__brief.guide().hidden')
                page.evaluate('(id)=>__brief.setup(1,21,id,11)', actor)
                assert not page.evaluate('__brief.guide().hidden')
                page.evaluate('(id)=>__brief.setup(2,21,id,30)', actor)
                assert page.evaluate('__brief.guide().hidden')
            print('PASS first-night tutorial, shared pulse, own cave, 10m threshold and camera rotation', mobile, flush=True)
            for actor, selector in [('hina', '#observeHina'), ('daeun', '#observeDaeun')]:
                page.evaluate('(id)=>__brief.ring(id,true)', actor)
                ring = page.locator(selector + ' .character-orbit')
                assert ring.is_visible()
                assert page.locator(selector).evaluate('(e)=>getComputedStyle(e).backgroundColor') == 'rgb(70, 139, 112)'
                style = page.locator(selector + ' rect').evaluate('(e)=>({width:getComputedStyle(e).strokeWidth,color:getComputedStyle(e).stroke,duration:getComputedStyle(e).animationDuration})')
                assert style == {'width': '5px', 'color': 'rgb(156, 233, 192)', 'duration': '3s'}, style
                button_box = page.locator(selector).bounding_box(); ring_box = ring.bounding_box()
                assert abs(ring_box['x'] - (button_box['x'] - 2.5)) < 1
                assert abs(ring_box['width'] - (button_box['width'] + 5)) < 1
                page.evaluate('(id)=>__brief.ring(id,false)', actor)
                assert not ring.is_visible()
            print('PASS exact exterior 5px mint border, 3s clockwise cycle and both modes', mobile, flush=True)
            # Flowers never alter navigation, and only reuse one small existing mesh.
            page.evaluate("__brief.setup(1,12,'hina',30)")
            assert not page.evaluate('__brief.begin()')
            page.evaluate("__brief.setup(2,12,'hina',30);__brief.unsafe(true)")
            assert not page.evaluate('__brief.begin()')
            page.evaluate('__brief.unsafe(false);__brief.manual(true)')
            assert not page.evaluate('__brief.begin()')
            page.evaluate('__brief.manual(false)')
            before = page.evaluate('__brief.snapshot()')
            assert page.evaluate('__brief.begin()')
            assert not page.evaluate('__brief.begin()')
            page.evaluate('__brief.advance(900);__brief.flowerTick()')
            flower = page.evaluate('__brief.flower()')
            assert flower['visible'] and flower['count'] == 1
            assert abs(flower['expires'] - flower['elapsed'] - 1200) < .001
            assert page.evaluate('__brief.pose().elbow') < -.1
            assert page.evaluate('__brief.snapshot()') == before
            page.evaluate('__brief.manual(true);__brief.advance(2000);__brief.flowerTick()')
            assert page.evaluate('__brief.flower().visible')
            page.evaluate('__brief.sleep(true);__brief.flowerTick()')
            assert page.evaluate('__brief.flower().visible')
            page.evaluate('__brief.sleep(false)')
            cost=page.evaluate('__brief.drawCost()')
            assert 0 <= cost['calls'] <= 1 and 0 <= cost['triangles'] <= 160, cost
            print('FLOWER RENDER COST', cost, mobile, flush=True)
            # New/future registered friends share one sequential praise/reply queue.
            page.evaluate("for(const id of ['daeun','seoyeon','jiyu','mina'])__brief.nearFriend(id);__brief.clearSpeech();__brief.advance(4000)")
            for count in range(1, 5):
                page.evaluate('__brief.praise()')
                assert len(page.evaluate('__brief.flower().seen')) == count
                page.evaluate('__brief.advance(3400);__brief.praise()')
                assert not page.evaluate('__brief.flower().reply')
                page.evaluate('__brief.advance(3400)')
            page.evaluate('__brief.praise()')
            assert len(page.evaluate('__brief.flower().seen')) == 4
            uuid = flower['uuid']
            page.evaluate('__brief.expire()')
            assert not page.evaluate('__brief.flower().visible')
            page.evaluate("__brief.setup(3,12,'hina',30);__brief.begin();__brief.advance(900);__brief.flowerTick()")
            assert page.evaluate('__brief.flower().uuid') == uuid
            assert page.evaluate('__brief.flower().count') == 1
            assert page.evaluate('__brief.flower().seen.length') == 0
            page.evaluate('__brief.clearSpeech();__brief.important();__brief.advance(1);__brief.praise()')
            assert page.evaluate('__brief.flower().seen.length') == 0
            print('PASS safe flower animation, no navigation change, manual retention, 24h expiry and per-friend sequential praise', mobile, flush=True)
            page.evaluate("__brief.setup(3,12,'hina',30)")
            assert not page.evaluate('__brief.approach(.9)')
            assert not page.evaluate('__brief.approach(.1,false)')  # no repeated roll while staying in one patch
            assert page.evaluate('__brief.approach(.1,true)')
            page.evaluate("__brief.setup(1,12,'hina',30);__brief.manual(true);__brief.socialTick();__brief.advance(20000)")
            emitted=page.evaluate('__brief.socialTick()')
            assert any(row.get('text') for row in emitted)
            for actor in ['hina', 'daeun', 'seoyeon', 'jiyu', 'mina']:
                context = {'day': 1, 'night': False, 'alone': True, 'met': False, 'will': 80, 'sheltered': False}
                first = page.evaluate('([id,ctx])=>__brief.mood(id,ctx)', [actor, context])
                second = page.evaluate('([id,ctx,last])=>__brief.mood(id,ctx,last)', [actor, context, first])
                assert first and second and first != second
                context.update(day=3, will=20, alone=False, met=True)
                low = page.evaluate('([id,ctx])=>__brief.mood(id,ctx)', [actor, context])
                context.update(will=80, sheltered=True)
                safe = page.evaluate('([id,ctx])=>__brief.mood(id,ctx)', [actor, context])
                assert low != safe
            assert not errors, errors
            assert not page.evaluate('HinaInteractionSFX.audioStatus().errors')
            print('PASS five-character shared mood selection, no repeated line and will/safety adaptation', mobile, flush=True)
            page.screenshot(path=f'/tmp/hina-brief-{"mobile" if mobile else "desktop"}.png')
            page.close()
        browser.close()
    print('PASS selected brief regression layouts', flush=True)


if __name__ == '__main__':
    run()
