import json, math
from fractions import Fraction
import numpy as np
from latent_art_bench import painter_selective_attribution_v1 as m
rng=np.random.default_rng(2026092119)
checks=[]
def ok(name,condition):
    if not condition: raise AssertionError(name)
    checks.append(name)
def norm(x):return x/np.linalg.norm(x,axis=-1,keepdims=True)
for n in range(1,101):
    values=rng.normal(size=n); q=m.fixed_quantile(values); k=math.ceil(Fraction(9*(n+1),10))
    ok(f'quantile{n}',q['rank']==k and q['infinite']==(k>n) and (q['threshold'] is None if k>n else q['threshold']==sorted(values)[k-1]))
q=[dict(n=20,rank=19,infinite=False,threshold=t) for t in [-.3,-.2,.2,.4]]
scores=rng.normal(size=(1000,4));scores[:20,1]=scores[:20,0]
d=m.decide(scores,q)
for i,ss in enumerate(scores):
    nc=[max(ss[b] for b in range(4) if b!=a)-ss[a] for a in range(4)]
    members=[a for a in range(4) if nc[a] <= q[a]['threshold']]
    prediction=list(ss).index(max(ss))
    ok(f'decision{i}',list(np.flatnonzero(d['members'][i]))==members and d['predictions'][i]==prediction and d['accepted'][i]==(members==[prediction]))
refs=[np.repeat(np.eye(4)[a:a+1],20,axis=0) for a in range(4)]
cals=[norm(rng.normal(size=(20,4))+.7*np.eye(4)[a]) for a in range(4)]
cal=m.calibrate(refs,cals)
for a in range(4):
    nc=[max(x[b] for b in range(4) if b != a)-x[a] for x in cals[a]]
    ok(f'calibration{a}',np.isclose(cal['quantiles'][a]['threshold'],sorted(nc)[18]))
x=norm(rng.normal(size=(5,2,6,4))); ids=np.array([f'i{i:03d}' for i in range(60)],dtype=object).reshape(5,2,6)
e=m.evaluate_model(x,ids,cal)
for deleted in [None,*range(5)]:
    scenes=[s for s in range(5) if s!=deleted]; loc=[(s,r,a) for s in scenes for r in range(2) for a in range(2,6)]
    rows=[]
    for s,r,a in loc:
        ss=x[s,r,a]; pred=list(ss).index(max(ss)); members=[j for j in range(4) if max(ss[b] for b in range(4) if b!=j)-ss[j] <= cal['quantiles'][j]['threshold']]
        rows.append(dict(id=ids[s,r,a],pred=pred,truth=a-2,accepted=members==[pred],margin=sorted(ss)[-1]-sorted(ss)[-2]))
    K=sum(t['accepted'] for t in rows); chosen=sorted(rows,key=lambda t:(-t['margin'],t['id']))[:K]
    bad=sum(t['pred']!=t['truth'] for t in rows if t['accepted']); mbad=sum(t['pred']!=t['truth'] for t in chosen)
    out=e if deleted is None else e['scene_deletions'][deleted]
    ok(f'evaluate{deleted}:count',out['reference_gate']['accepted_count']==K and out['margin_comparator']['accepted_count']==K)
    ok(f'evaluate{deleted}:risk',out['reference_gate']['accepted_error']==(bad/K if K else None) and out['margin_comparator']['accepted_error']==(mbad/K if K else None))
    cutoff=chosen[-1]['margin'] if K else None
    for a,arm in enumerate(m.ARMS[:2]):
        margins=[sorted(x[s,r,a])[-1]-sorted(x[s,r,a])[-2] for s in scenes for r in range(2)]
        count=sum(t>=cutoff for t in margins) if K else 0
        ok(f'evaluate{deleted}:{arm}:inclusive',out['controls'][arm]['margin_comparator']['accepted_count']==count)
# Exact margin ties: ascending ID selection; controls use numeric cutoff inclusively.
mm=m.margin_match([.4,.4,.4],['b','c','a'],2)
ok('margin_tie_ids',mm['accepted'].tolist()==[True,False,True] and mm['boundary_id']=='b' and mm['cutoff_ties_accepted']==2)
mask,ties=m.control_margin_mask([.3,.4,.5],mm)
ok('control_ties',mask.tolist()==[False,True,True] and ties.tolist()==[False,True,False])
ok('undefined_complete_mean',m.complete_mean([.2,None,.3]) is None)
print(json.dumps({'status':'passed','constructed_only':True,'count':len(checks),'checks':checks},indent=2))
