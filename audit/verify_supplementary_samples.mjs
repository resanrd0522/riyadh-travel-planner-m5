// Independent offline reference scorer for supplementary samples only.
// Does not reconstruct or verify original 60 V2 generations.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const root = new URL('../', import.meta.url);
const source = new URL('source/05_M5_Evaluation/', root);
const read = async p => JSON.parse(await fs.readFile(new URL(p, source), 'utf8'));
function csv(s) {
  const out = []; let r = [], v = '', q = false;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (c === '"') { if (q && s[i+1] === '"') { v += '"'; i++; } else q = !q; }
    else if (c === ',' && !q) { r.push(v); v = ''; }
    else if (c === '\n' && !q) { r.push(v.replace(/\r$/, '')); out.push(r); r = []; v = ''; }
    else v += c;
  }
  if (v || r.length) { r.push(v); out.push(r); }
  const h = out.shift();
  return out.filter(r => r.length > 1).map(r => Object.fromEntries(h.map((k,i) => [k,r[i]])));
}
const datasets = {};
for (const k of ['activities','restaurants','hotels']) {
  datasets[k] = csv(await fs.readFile(new URL('data/' + k + '.csv', root), 'utf8'));
}
const look = Object.fromEntries(Object.entries(datasets).map(([k,a]) => [k,new Map(a.map(r => [r.place_id,r]))]));
const v2 = await read('baseline_v2_standardized/baseline_results_v2.json');
const samplesDir = new URL('llm_judge_evaluation/baseline_samples/', source);
const names = (await fs.readdir(samplesDir)).filter(n => n.endsWith('.json')).sort();
assert.equal(names.length, 20, 'Expected 20 supplementary samples');
const calculated = [];
for (const name of names) {
  const s = JSON.parse(await fs.readFile(new URL(name, samplesDir), 'utf8'));
  const t = s.generation_result.itinerary, u = s.user_input;
  const aa = t.days.slice(0,u.trip_duration).flatMap(d => d.activities?.slice(0,2) || []);
  const rr = t.days.slice(0,u.trip_duration).flatMap(d => d.restaurants?.slice(0,2) || []);
  const ap = 100 * [...new Set(aa)].filter(id => u.interests.includes(look.activities.get(id)?.interest_group)).length / (2*u.trip_duration);
  const rb = 100 * rr.filter(id => look.restaurants.get(id)?.budget_level === u.budget_level).length / (2*u.trip_duration);
  const hb = look.hotels.get(t.hotel_id)?.budget_level === u.budget_level ? 100 : 0;
  const fullA = t.days.flatMap(d => d.activities || []);
  const valid = look.hotels.has(t.hotel_id) && t.days.length === u.trip_duration &&
    t.days.every((d,i) => d.day === i+1 && d.activities.length === 2 && d.restaurants.length === 2 &&
      d.activities.every(id => look.activities.has(id)) && d.restaurants.every(id => look.restaurants.has(id))) &&
    new Set(fullA).size === fullA.length;
  const scores = { APM: Math.round(ap*100)/100, RBM: rb, HBM: hb, IFR: valid ? 100 : 0 };
  assert.equal(s.seed, 11);
  assert.equal(valid, s.generation_result.is_valid, s.case_id + ' saved validity differs');
  const matches = v2.filter(r => r.case_id === s.case_id && r.seed === 11);
  assert.equal(matches.length, 1, 'Expected exactly one matching seed-11 score row');
  for (const k of ['APM','RBM','HBM','IFR']) assert.equal(scores[k], matches[0][k], s.case_id + ' ' + k + ' differs');
  calculated.push({ case_id: s.case_id, ...scores });
}
assert.equal(new Set(calculated.map(c => c.case_id)).size, 20);
export const result = { status: 'PASS', supplementary_samples_checked: calculated.length, score_fields_checked: 80,
  validity_flags_checked: 20, original_v2_generations_verified: false, calculated };
console.log(JSON.stringify(result, null, 2));
