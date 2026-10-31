"""Mobile/desktop diagnostic collection, clipboard fallback, and startup-failure checks.
Run the repository's static server on port 8000 first.
"""
from pathlib import Path
import json
import re
import runpy
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE=runpy.run_path(str(ROOT/'tools/check_hive_attacks.py'))['BODY']
FIXTURE=r'''
window.__diagnosticsTest={
 fresh(){lastWildHiveUpdate=performance.now();},
 state(){return JSON.stringify({paused,actor:observedId,position:characters.get(observedId).mesh.position.toArray(),stats:characters.get(observedId).stats,updates:wildHiveUpdateCount});},
 pause(value){paused=value;},
 phase(value,target='daeun'){wildHives[0].attack={phase:value,age:.25,hits:1,beeIndex:1,targetId:target};lastWildHiveUpdate=performance.now();},
 invalidVitality(){daeun.stats.energy=NaN;lastWildHiveUpdate=performance.now();},
 escape(){__hiveCheck.move('daeun',20);lastWildHiveUpdate=performance.now();}
};
'''
BODY=BASE.replace('window.__hinaClockAuditStart=performance.now();','window.__hinaClockAuditStart=performance.now();'+FIXTURE,1)

def run():
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  for mobile in [True,False]:
   context=browser.new_context(viewport={'width':390 if mobile else 1280,'height':844},is_mobile=mobile,has_touch=mobile)
   page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
   page.add_init_script('window.requestAnimationFrame=()=>0;Object.defineProperty(navigator,"clipboard",{configurable:true,value:undefined});')
   page.route('http://127.0.0.1:8000/',lambda route:route.fulfill(status=200,content_type='text/html',body=BODY))
   page.goto('http://127.0.0.1:8000/',wait_until='domcontentloaded',timeout=90000)
   page.wait_for_function('!!window.hinaHiveDiagnosticSnapshot',polling=50,timeout=90000)
   page.evaluate('__hiveCheck.screenshot();__diagnosticsTest.fresh()')
   before=page.evaluate('__diagnosticsTest.state()')
   page.locator('#mobileMenu' if mobile else '#v521PcMenu').click()
   page.locator('#mobileCategories [data-pane="settings"]' if mobile else '#v521Menu > [data-v521="settings"]').click()
   assert page.locator('#hiveDiagnosticButton').is_visible()
   page.locator('#hiveDiagnosticButton').click()
   assert page.locator('#hiveDiagnosticPanel').is_visible()
   page.locator('#hiveDiagnosticHide').click()
   assert not page.locator('#hiveDiagnosticPanel').is_visible()
   page.wait_for_timeout(1100)
   assert page.evaluate('HinaHiveDiagnostics.report().samples.length')>=2
   assert page.evaluate('__diagnosticsTest.state()')==before,'Collection must not change the game'
   page.evaluate('HinaHiveDiagnostics.open()')
   page.locator('#hiveDiagnosticCopy').click()
   assert page.locator('#hiveDiagnosticText').is_visible()
   data=json.loads(page.locator('#hiveDiagnosticText').input_value())
   assert data['current']['diagnosticVersion']=='5.2.91'
   assert data['current']['game']['selectedId']=='daeun'
   assert data['current']['game']['day']==10
   assert data['current']['game']['nearest'][0]['distance']==6.5
   assert data['current']['game']['actor']['health']==47
   assert data['current']['game']['actor']['energy']==47
   assert data['current']['game']['actor']['vitalityKey']=='energy'
   assert data['current']['gameSnapshotAvailable']
   assert '?' not in data['current']['page']
   page.evaluate('__diagnosticsTest.pause(true);__diagnosticsTest.fresh()')
   assert page.evaluate('HinaHiveDiagnostics.snapshot().game.nearest[0].reason')=='game_paused'
   page.evaluate('__diagnosticsTest.pause(false);__diagnosticsTest.phase("dive","hina")')
   assert page.evaluate('HinaHiveDiagnostics.snapshot().game.nearest[0].reason')=='attacking_other_character'
   page.evaluate('__diagnosticsTest.phase("dive")')
   assert page.evaluate('HinaHiveDiagnostics.snapshot().game.nearest[0].reason')=='diving'
   # Test the successful copy path separately, without depending on OS clipboard permission.
   page.evaluate('Object.defineProperty(navigator,"clipboard",{configurable:true,value:{writeText:async text=>{window.__copiedDiagnostic=text;}}})')
   page.locator('#hiveDiagnosticCopy').click()
   assert json.loads(page.evaluate('window.__copiedDiagnostic'))['format']=='HINA_HIVE_DIAGNOSTIC_V1'
   with page.expect_download() as info:page.locator('#hiveDiagnosticDownload').click()
   assert info.value.suggested_filename.endswith('.json')
   page.locator('#hiveDiagnosticRecord').click()
   count=page.evaluate('HinaHiveDiagnostics.report().samples.length')
   page.wait_for_timeout(1100)
   assert page.evaluate('HinaHiveDiagnostics.report().samples.length')==count
   assert not errors,errors
   page.evaluate('__diagnosticsTest.invalidVitality()')
   assert page.evaluate('HinaHiveDiagnostics.snapshot().game.nearest[0].reason')=='invalid_vitality_stat'
   print('PASS settings entry, read-only background recording, report details, stop, copy/fallback and download',mobile,flush=True)
   context.close()
  # The diagnostic script runs before the game module and survives a fatal startup error.
  page=browser.new_page()
  broken='''<!doctype html><html><head><script src="hive-diagnostics.js?v=5.2.91"></script><script>throw new Error("diagnostic startup failure fixture")</script></head><body></body></html>'''
  page.route(re.compile(r'^http://127\.0\.0\.1:8000/\?'),lambda route:route.fulfill(status=200,content_type='text/html',body=broken))
  page.goto('http://127.0.0.1:8000/?hive-debug=1&private=do-not-copy',wait_until='load')
  assert page.locator('#hiveDiagnosticPanel').is_visible()
  report=page.evaluate('HinaHiveDiagnostics.report()')
  assert not report['current']['gameSnapshotAvailable']
  assert any('startup failure fixture' in error['message'] for error in report['errors'])
  assert 'do-not-copy' not in json.dumps(report)
  print('PASS direct diagnostic link survives game startup failure, captures error, and excludes URL query',flush=True)
  browser.close()

if __name__=='__main__':run()
