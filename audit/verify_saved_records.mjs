import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const root = new URL('../', import.meta.url);
const read = p => fs.readFile(new URL(p, root));
const readj = async p => JSON.parse(await read(p));
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const csvParse = s=>{var rows=[],r=[],v='',q=false;for(var i=0;i<s.length;i++){var c=s[i];if(c==='"'){if(q&&s[i+1]==='"'){v+='"';i++;}else q=!q;}else if(c===','&&!q){r.push(v);v='';}else if(c==='\n'&&!q){r.push(v.replace(/\r$/,''));rows.push(r);r=[];v='';}else v+=c;}if(v||r.length){r.push(v);rows.push(r);}var h=rows.shift();return rows.filter(r=>r.length>1).map(r=>Object.fromEntries(h.map((k,i)=>[k,r[i]])));};
const mean = a => a.reduce((s,x)=>s+x,0)/a.length;
const sd = a => Math.sqrt(a.reduce((s,x)=>s+(x-mean(a))**2,0)/(a.length-1));
const dir='source/05_M5_Evaluation/baseline_v2_standardized/';
const ref = await readj(dir+'baseline_v2_implementation_reference.json');
const runs = await readj(dir+'baseline_results_v2.json');
const summary = await readj(dir+'baseline_v2_official_summary.json');
assert.equal(runs.length,60);
assert.equal(ref.golden_set.length,20);
assert.equal(new Set(runs.map(r=>r.case_id+':'+r.seed)).size,60);
for(const c of ref.golden_set) for(const seed of [11,22,33]) {
 const rr=runs.filter(r=>r.case_id===c.case_id&&r.seed===seed);
 assert.equal(rr.length,1);
 assert.equal(rr[0].trip_duration,c.trip_duration);
 assert.equal(rr[0].budget_level,c.budget_level);
 assert.deepEqual(rr[0].interests,c.interests);
}
assert.equal(hash(await read(dir+'baseline_results_v2.json')),summary.raw_results_sha256);
for(const v of Object.values(ref.function_sources)) assert.equal(hash(v.source),v.sha256);
const stats={};
for(const k of ['APM','RBM','HBM','IFR','RTC']) {
 const score=r=>k==='RTC'?100*new Set(r.tool_calls.filter(t=>['find_activities','find_restaurants','find_hotels'].includes(t))).size/3:r[k];
 const values=runs.map(score);
 assert(values.every(Number.isFinite));
 const seedMeans=[11,22,33].map(s=>mean(runs.filter(r=>r.seed===s).map(score)));
 stats[k]={mean:mean(values),runSampleSD:sd(values),seedMeans,betweenSeedSampleSD:sd(seedMeans)};
}
const activities=csvParse((await read('data/activities.csv')).toString());
const limited=ref.golden_set.map(c=>({case_id:c.case_id,required:2*c.trip_duration,candidates:activities.filter(r=>c.interests.includes(r.interest_group)).length})).filter(c=>c.candidates<c.required);
const manifest=await readj('audit/import_manifest.json');
for(const f of manifest.files) assert.equal(hash(await read(f.path)),f.sha256,f.path);
console.log(JSON.stringify({verification:'PASS for saved-record integrity and arithmetic only',runs:runs.length,stats,limitedPreferenceCases:limited,missingItineraries:runs.filter(r=>!r.itinerary).length,importFilesVerified:manifest.files.length},null,2));
