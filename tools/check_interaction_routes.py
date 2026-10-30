"""Native profile and meditation UI route checks; requires the static server on 8000."""
import runpy
from pathlib import Path
from playwright.sync_api import sync_playwright
m=runpy.run_path(str(Path(__file__).resolve().parent/'check_stabilization.py'))
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 for mobile in [True,False]:
  page=browser.new_page(viewport={'width':390 if mobile else 1280,'height':844},is_mobile=mobile,has_touch=mobile)
  page.set_default_timeout(6000);page.add_init_script('window.requestAnimationFrame=()=>0;')
  page.route('http://127.0.0.1:8000/',lambda route:route.fulfill(status=200,content_type='text/html',body=m['BODY']))
  page.goto('http://127.0.0.1:8000/',wait_until='domcontentloaded');page.wait_for_function('!!window.__stable',polling=50)
  selector='#mobileVitals .v529-face' if mobile else '#v523PcPortrait img'
  page.locator(selector).click();page.wait_for_timeout(300)
  state=page.evaluate('HinaInteractionSFX.audioStatus()');assert state['attempts'].get('ui')==1,state
  print('profile open',mobile,state,flush=True)
  page.mouse.click(5,200);page.wait_for_timeout(300)
  state=page.evaluate('HinaInteractionSFX.audioStatus()');assert state['attempts'].get('ui')==2,state
  print('PASS profile open/close uses exactly one common UI sound each',mobile,flush=True)
  for actor in ['hina','daeun']:
   page.evaluate('(id)=>__stable.setup(id,false)',actor)
   page.locator('#v504MeditationButton').click();assert page.evaluate('__stable.meditation().active')
   page.keyboard.press('w');assert not page.evaluate('__stable.meditation().active')
   page.locator('#v504MeditationButton').click();assert page.evaluate('__stable.meditation().active')
   page.locator('#v510MeditationStatus').click();assert not page.evaluate('__stable.meditation().active')
  print('PASS real meditation entry, keyboard interruption and status-button exit',mobile,flush=True)
  page.close()
 browser.close()
