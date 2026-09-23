"""Read-only independent reconstruction from canonical retained feature arrays."""
import hashlib
import itertools
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from latent_art_bench.painter_specificity_measurement_v1.workflow import load
from latent_art_bench.painter_specificity_v2 import study

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/painter_repeat_covariance_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
frozen=read(OUT/'analysis.json'); inputs=read(OUT/'inputs.json')
primary=read(study.DATA/'analysis.json')
previous=read(ROOT/'reports/painter_specificity_review_v2/analysis.json')
initial_sha=sha(OUT/'analysis.json')
for path,digest in inputs['bindings'].items(): assert sha(ROOT/path)==digest
assert frozen['inputs_sha256']==sha(OUT/'inputs.json')
assert frozen['rho_grid']==[0.,.1,.25,.5,.75]
assert inputs['rho_grid']==frozen['rho_grid']
assert len(frozen['models'])==6 and len(frozen['pairs'])==15
assert [r['model'] for r in frozen['models']]==list(study.MODELS)
assert [r['title'] for r in frozen['models']]==list(study.TITLES)
assert frozen['reference_counts']==[297,106,141,105]
assert frozen['generated_shape']==[6,14,2,6,31]
x,refs=load(square=False)
assert x.shape==(6,14,2,6,31) and np.isfinite(x).all()
assert [len(r) for r in refs]==[297,106,141,105]
# Independent centering and direct scalar sums, without the new module or canonical estimator.
mu=np.stack([sum(group)/len(group) for group in refs])
ref=mu-sum(mu)/4
h=sum(float(np.dot(v,v)) for v in ref)
assert h>0 and np.isfinite(h)
checks=0; max_error=0.; model_rows=[]; pair_rows=[]
def close(actual,expected):
 global checks,max_error
 actual,expected=np.asarray(actual),np.asarray(expected)
 assert actual.shape==expected.shape
 assert np.isfinite(actual).all() and np.isfinite(expected).all()
 np.testing.assert_allclose(actual,expected,atol=1e-12,rtol=1e-12)
 max_error=max(max_error,float(np.max(np.abs(actual-expected))))
 checks+=1
for mi,record in enumerate(frozen['models']):
 scene_d=[]; scene_q=[]
 for s in range(14):
  a=x[mi,s,0,2:]; b=x[mi,s,1,2:]
  a=a-sum(a)/4; b=b-sum(b)/4
  ds=sum(float(np.dot(a[k]-ref[k],b[k]-ref[k])) for k in range(4))/h
  qs=sum(float(np.dot(a[k]-b[k],a[k]-b[k])) for k in range(4))/(2*h)
  scene_d.append(ds); scene_q.append(qs)
 d=sum(scene_d)/14; q=sum(scene_q)/14
 close(record['reference_h'],h)
 close(record['scene_d'],scene_d); close(record['scene_q'],scene_q)
 close(record['d'],d); close(record['q'],q)
 close(primary['models'][mi]['scene_distortion'],scene_d)
 close(primary['models'][mi]['distortion']['mean'],d)
 close(previous['models'][mi]['centered_repeat_noise_power']['direct'],q)
 assert [v['rho'] for v in record['grid']]==frozen['rho_grid']
 scenarios=[]
 for actual,rho in zip(record['grid'],frozen['rho_grid']):
  alpha=rho/(1-rho); bias=alpha*q; adjusted=d-bias
  close(actual['alpha'],alpha); close(actual['implied_bias'],bias); close(actual['adjusted_d'],adjusted)
  assert actual['negative_adjusted_d']==bool(adjusted<0)
  scenarios.append(dict(rho=rho,alpha=alpha,implied_bias=bias,adjusted_d=adjusted,negative_adjusted_d=bool(adjusted<0)))
 model_rows.append(dict(model=record['model'],title=record['title'],d=d,q=q,scene_d=scene_d,scene_q=scene_q,scenarios=scenarios))
for actual,(ia,ib) in zip(frozen['pairs'],itertools.combinations(range(6),2)):
 a,b=model_rows[ia],model_rows[ib]
 assert (actual['model_a'],actual['model_b'])==(a['model'],b['model'])
 assert (actual['title_a'],actual['title_b'])==(a['title'],b['title'])
 # Threshold sign/tie classifications must use the exact frozen unrounded D/q.
 # Raw-array recomputations above independently verify those values within floating arithmetic.
 da=frozen['models'][ia]['d']; db=frozen['models'][ib]['d']
 qa=frozen['models'][ia]['q']; qb=frozen['models'][ib]['q']
 delta_d=da-db; delta_q=qa-qb
 close(actual['delta_d'],delta_d); close(actual['delta_q'],delta_q)
 close(actual['delta_d'],a['d']-b['d']); close(actual['delta_q'],a['q']-b['q'])
 assert [v['rho'] for v in actual['grid']]==frozen['rho_grid']
 grid=[]
 for row,rho in zip(actual['grid'],frozen['rho_grid']):
  alpha=rho/(1-rho)
  adjusted=(da-alpha*qa)-(db-alpha*qb)
  bias=(alpha*qa)-(alpha*qb)
  close(row['adjusted_difference'],adjusted)
  close(row['implied_bias_difference'],bias)
  # Additional recomputation using independent model quantities.
  close(row['adjusted_difference'],a['d']-alpha*a['q']-(b['d']-alpha*b['q']))
  grid.append(dict(rho=rho,adjusted_difference=adjusted,implied_bias_difference=bias))
 crossing=actual['crossing']
 if delta_d==0 and delta_q==0: status='tied_for_all_rho'
 elif delta_d==0: status='initial_tie_separates'
 elif delta_q!=0 and delta_d/delta_q>0: status='positive_interior_crossing'
 else: status='no_positive_interior_crossing'
 assert crossing['status']==status
 if status=='positive_interior_crossing':
  alpha=delta_d/delta_q; rho=alpha/(1+alpha)
  assert 0<rho<1
  close(crossing['alpha'],alpha); close(crossing['rho'],rho)
  close(crossing['rho'],(a['d']-b['d'])/(a['d']-b['d']+a['q']-b['q']))
  close(crossing['implied_bias_a'],alpha*qa)
  close(crossing['implied_bias_b'],alpha*qb)
  close(da-alpha*qa,db-alpha*qb)
  # Strict signs on each side validate this is a crossing, not merely a touching point.
  before=delta_d-(rho/2)/(1-rho/2)*delta_q
  after=delta_d-((rho+1)/2)/(1-(rho+1)/2)*delta_q
  assert before*after<0
 else:
  assert all(crossing[k] is None for k in ['rho','alpha','implied_bias_a','implied_bias_b'])
 pair_rows.append(dict(title_a=a['title'],title_b=b['title'],delta_d=delta_d,delta_q=delta_q,grid=grid,crossing=crossing))
for path,digest in inputs['bindings'].items(): assert sha(ROOT/path)==digest
assert sha(OUT/'analysis.json')==initial_sha
assert 'latent_art_bench.painter_repeat_covariance_v1' not in __import__('sys').modules
receipt=dict(status='PASS',completed_utc=datetime.now(timezone.utc).isoformat(),result_sha256=initial_sha,inputs_sha256=sha(OUT/'inputs.json'),report_sha256=sha(OUT/'REPORT.md'),script_sha256=sha(Path(__file__)),bindings_checked=len(inputs['bindings']),numeric_assertions=checks,max_absolute_numeric_error=max_error,canonical_reader='painter_specificity_measurement_v1.workflow.load(square=False)',forbidden_module_imported=False,generated_shape=list(x.shape),reference_counts=[len(r) for r in refs],reference_energy=h,rho_grid=frozen['rho_grid'],scene_statistics_per_kind=84,model_grid_points=30,pair_grid_points=75,model_count=6,pair_count=15,crossing_status_counts=dict(Counter(v['crossing']['status'] for v in pair_rows)),crossings_above_grid=sum(v['crossing']['rho'] is not None and v['crossing']['rho']>.75 for v in pair_rows),negative_model_scenarios=sum(v['negative_adjusted_d'] for row in model_rows for v in row['scenarios']),models=model_rows,pairs=pair_rows)
print(json.dumps(receipt,indent=2,allow_nan=False))
