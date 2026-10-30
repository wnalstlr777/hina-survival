"""Fixed-scene content comparisons using the existing game loop (software Chromium).
Requires an HTTP server on 8000 and Playwright. Does not change saved game code.
"""
from pathlib import Path
import argparse,json,statistics,time,hashlib
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
PROBE=r'''
const environmentAudit={flowerRender:true,flowerAnimation:true,insects:true,bendMs:[],insectMs:[],gpuMs:[]};
const originalFlowerUpdate=updateDaeunFlowerBends,originalInsectUpdate=updateFlowerBees;
updateDaeunFlowerBends=function(...args){const start=performance.now();if(environmentAudit.flowerAnimation)originalFlowerUpdate(...args);environmentAudit.bendMs.push(performance.now()-start);};
updateFlowerBees=function(...args){const start=performance.now();if(environmentAudit.insects)originalInsectUpdate(...args);environmentAudit.insectMs.push(performance.now()-start);};
const renderOriginal=renderer.render.bind(renderer),flowerRoot=scene.getObjectByName('ISLAND_REACTIVE_FLOWER_CLUSTERS');
const auditGL=renderer.getContext(),auditGPU=auditGL.getExtension('EXT_disjoint_timer_query_webgl2'),gpuPending=[];
function pollAuditGPU(){
 if(!auditGPU)return;
 const disjoint=auditGL.getParameter(auditGPU.GPU_DISJOINT_EXT);
 for(let i=gpuPending.length-1;i>=0;i--){const q=gpuPending[i];if(auditGL.getQueryParameter(q,auditGL.QUERY_RESULT_AVAILABLE)){if(!disjoint)environmentAudit.gpuMs.push(auditGL.getQueryParameter(q,auditGL.QUERY_RESULT)/1e6);auditGL.deleteQuery(q);gpuPending.splice(i,1);}}
}
renderer.render=function(...args){
 flowerRoot.visible=environmentAudit.flowerRender;if(!environmentAudit.insects)flowerBeeRoot.visible=false;
 pollAuditGPU();let query=null;
 if(auditGPU&&gpuPending.length<8){query=auditGL.createQuery();auditGL.beginQuery(auditGPU.TIME_ELAPSED_EXT,query);}
 try{return renderOriginal(...args);}finally{if(query){auditGL.endQuery(auditGPU.TIME_ELAPSED_EXT);gpuPending.push(query);}}
};
window.__environmentAudit={
 setup(){paused=true;followCamera=false;orbit.enabled=false;orbit.enableDamping=false;elapsed=DAY_SECONDS;day=2;window.__hinaExplicitDayTest=true;highQuality=false;ultraLowPower=false;applyQuality();
  const center=new THREE.Vector3(DAEUN_ZONE.cave.x+6,terrainTopAt(DAEUN_ZONE.cave.x+6,DAEUN_ZONE.cave.z+12,0),DAEUN_ZONE.cave.z+12);
  camera.position.copy(center).add(new THREE.Vector3(13,15,21));orbit.target.copy(center);camera.lookAt(center);camera.updateMatrixWorld(true);flowerGridCellX=NaN;flowerGridCellZ=NaN;updateCameraFlowerPatches();
  return {width:innerWidth,height:innerHeight,pixelRatio:renderer.getPixelRatio(),quality:'medium',mobileFPSLimit:mobileTargetFPS,context:renderer.getContext().getParameter(renderer.getContext().RENDERER),gpuTimerAvailable:!!renderer.getContext().getExtension('EXT_disjoint_timer_query_webgl2')};},
 scenario(mode){Object.assign(environmentAudit,{flowerRender:!['flowers_off','all_off'].includes(mode),flowerAnimation:!['flower_animation_off','all_off'].includes(mode),insects:!['insects_off','all_off'].includes(mode)});},
 mark(){environmentAudit.bendMs=[];environmentAudit.insectMs=[];environmentAudit.gpuMs=[];for(const query of gpuPending)auditGL.deleteQuery(query);gpuPending.length=0;return performance.now();},
 collect(since){pollAuditGPU();const samples=window.hinaPerformance.samples().filter(sample=>sample.time>=since);let objects=0,meshes=0;scene.traverseVisible(o=>{objects++;if(o.isMesh)meshes++;});return {samples,gpuMs:environmentAudit.gpuMs,bendMs:environmentAudit.bendMs,insectMs:environmentAudit.insectMs,heapBytes:performance.memory?.usedJSHeapSize??null,objects,meshes};},
 inventory(){scene.updateMatrixWorld(true);camera.updateMatrixWorld(true);const frustum=new THREE.Frustum().setFromProjectionMatrix(new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse));
  const geometryTriangles=m=>m.geometry.index?m.geometry.index.count/3:m.geometry.attributes.position.count/3;
  const mats=new Set(),geometries=new Set();let flowerMeshes=0,totalTriangles=0,visibleTriangles=0,visibleMeshes=0,shownFlowers=0,hiddenFlowers=0,offscreenFlowers=0;
  const perFlower=[];for(const f of daeunFlowerBends){let tris=0;if(f.flower.visible)shownFlowers++;else hiddenFlowers++;let inFrame=false;f.flower.traverse(m=>{if(!m.isMesh)return;flowerMeshes++;tris+=geometryTriangles(m);mats.add(m.material.uuid);geometries.add(m.geometry.uuid);if(f.flower.visible&&frustum.intersectsObject(m)){visibleMeshes++;visibleTriangles+=geometryTriangles(m);inFrame=true;}});totalTriangles+=tris;perFlower.push(tris);if(f.flower.visible&&!inFrame)offscreenFlowers++;}
  return {flowers:daeunFlowerBends.length,flowerMeshes,flowerMaterials:mats.size,sharedGeometries:geometries.size,perFlowerTriangles:perFlower[0],totalFlowerTriangles:totalTriangles,perPatchTriangles:cameraFlowerPatches.map(p=>p.flowers.reduce((sum,f)=>sum+perFlower[daeunFlowerBends.indexOf(f)],0)),shownFlowers,hiddenFlowers,offscreenFlowers,frustumFlowerMeshes:visibleMeshes,frustumFlowerTriangles:visibleTriangles,insects:flowerBeeFlights.reduce((r,f)=>{r[f.kind]=(r[f.kind]||0)+1;if(f.active!==false)r.active++;if(f.active!==false&&frustum.intersectsSphere(new THREE.Sphere(f.bee.position,1)))r.frustum++;return r;},{active:0,frustum:0})};}
};
'''
def mean(values):return statistics.mean(values) if values else None
def summarize(raw):
 samples=raw['samples'];frames=[s['frameMs'] for s in samples if s['frameMs']>0];slow=sorted(frames,reverse=True)[:max(1,int(len(frames)*.01))]
 return dict(frames=len(frames),averageFPS=1000/mean(frames) if frames else None,low1PercentFPS=1000/mean(slow) if slow else None,cpuFrameMs=mean([s['cpuFrameMs'] for s in samples]),cpuSubmitMs=mean([s['cpuSubmitMs'] for s in samples]),flowerUpdateMs=mean(raw['bendMs']),insectUpdateMs=mean(raw['insectMs']),drawCalls=mean([s['calls'] for s in samples]),triangles=mean([s['triangles'] for s in samples]),geometryCount=mean([s['geometries'] for s in samples]),textureCount=mean([s['textures'] for s in samples]),hierarchyVisibleObjects=raw['objects'],hierarchyVisibleMeshes=raw['meshes'],jsHeapBytes=raw['heapBytes'],gpuFrameMs=mean(raw.get('gpuMs',[])),gpuSamples=len(raw.get('gpuMs',[])),deviceTemperature=None)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--source',default=str(ROOT/'index.html'));parser.add_argument('--output',default='/tmp/hina-environment-profile.json');parser.add_argument('--seconds',type=int,default=10);parser.add_argument('--steady-seconds',type=int,default=120);args=parser.parse_args()
 source=Path(args.source).read_text();marker='}progressStore.initialize();requestAnimationFrame(animate);';assert marker in source
 body=source.replace(marker,'}'+PROBE+'progressStore.initialize();requestAnimationFrame(animate);',1)
 result={'sourceSHA256':hashlib.sha256(source.encode()).hexdigest(),'method':'paused AI, fixed camera/time/medium quality; actual game RAF and renderSamples; headless Chromium SwiftShader, not a physical phone','scenarioSeconds':args.seconds,'steadySeconds':args.steady_seconds,'gpuFrameMs':'WebGL timer query where supported; software renderer','deviceTemperature':None,'layouts':{}}
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--enable-precise-memory-info'])
  for mobile in [False,True]:
   page=browser.new_page(viewport={'width':390 if mobile else 1280,'height':844 if mobile else 800},is_mobile=mobile,has_touch=mobile,user_agent='Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/130.0.0.0 Mobile Safari/537.36' if mobile else None)
   page.route('http://127.0.0.1:8000/',lambda route:route.fulfill(status=200,content_type='text/html',body=body));page.goto('http://127.0.0.1:8000/',wait_until='domcontentloaded');page.wait_for_function('!!window.__environmentAudit');page.wait_for_timeout(2000)
   layout={'settings':page.evaluate('__environmentAudit.setup()'),'scenarios':{}};page.wait_for_timeout(2500);layout['inventory']=page.evaluate('__environmentAudit.inventory()')
   for mode in ['all_on','flowers_off','flower_animation_off','insects_off','all_off']:
    page.evaluate('(mode)=>__environmentAudit.scenario(mode)',mode);page.wait_for_timeout(1500);start=page.evaluate('__environmentAudit.mark()');page.wait_for_timeout(args.seconds*1000);layout['scenarios'][mode]=summarize(page.evaluate('(since)=>__environmentAudit.collect(since)',start));print('PROFILE',mobile,mode,layout['scenarios'][mode],flush=True)
   page.evaluate('__environmentAudit.scenario("all_on")');page.wait_for_timeout(1500);layout['steadyTrend']=[]
   for i in range(max(0,args.steady_seconds//30)):
    start=page.evaluate('__environmentAudit.mark()');page.wait_for_timeout(min(30,args.steady_seconds)*1000);entry=summarize(page.evaluate('(since)=>__environmentAudit.collect(since)',start));entry['segment']=i;layout['steadyTrend'].append(entry);print('STEADY',mobile,i,entry,flush=True)
   result['layouts']['mobile' if mobile else 'desktop']=layout;Path(args.output).write_text(json.dumps(result,indent=2));page.close()
  browser.close()
 print('SAVED',args.output,flush=True)
if __name__=='__main__':main()
