import itertools
import json
import numpy as np
from latent_art_bench import painter_cross_cohort_v1 as m
rng=np.random.default_rng(2026092107)
checks=[]
def ok(name, cond):
    if not cond:
        raise AssertionError(name)
    checks.append(name)
def U(v):
    return np.mean([np.sum(v[i]*v[j],axis=-1) for i in range(len(v)) for j in range(len(v)) if i != j],axis=0)
for k in [2,3,25]:
    v=rng.normal(size=(k,4,31))
    ok(f'ordered_pairs_K{k}',np.allclose(m.u_product(v),U(v),rtol=1e-12,atol=1e-12))
    ok(f'order_invariant_K{k}',np.allclose(m.u_product(v[::-1]),U(v),rtol=1e-12,atol=1e-12))
z=rng.normal(size=(25,3,5,31))
means=rng.normal(size=(4,31))
r=m.summarize(z,means)
for family,section in m.VIEWS.items():
    zz=z[...,section]; mu=means[...,section]; rr=mu-mu.mean(axis=0)
    delta=(zz[:,:,1:]-zz[:,:,:1]).mean(axis=1); c=delta.mean(axis=1); d=delta-c[:,None]
    H=np.sum(rr*rr)
    p=r['families'][family]['pooled']
    ok(f'{family}:C',np.isclose(p['C'],4*U(c)))
    ok(f'{family}:L',np.isclose(p['L'],U(d).sum()))
    ok(f'{family}:D',np.isclose(p['D'],U(d-rr).sum()/H))
    ds=zz[:,:,1:]-zz[:,:,:1]; ds=ds-ds.mean(axis=2,keepdims=True)
    ok(f'{family}:sceneD',np.isclose(r['families'][family]['within_scene']['D'],U(ds-rr).sum(axis=-1).mean()/H))
    for pidx,(a,b) in enumerate(itertools.combinations(range(4),2)):
        q=mu[a]-mu[b]; g=zz[:,:,a+1]-zz[:,:,b+1]; ph=np.sum(q*q)
        pair=r['families'][family]['pairs'][pidx]
        ok(f'{family}:pair{pidx}:amplitude',np.isclose(pair['aligned_amplitude'],np.sum(g.mean(axis=(0,1))*q)/ph))
        ok(f'{family}:pair{pidx}:sceneD',np.isclose(pair['scene_D'],U(g-q).mean()/ph))
ok('25_deletions',len(r['leave_one_block_out'])==25)
for i,row in enumerate(r['leave_one_block_out']):
    delta=np.delete(z,i,axis=0)[:,:,1:]-np.delete(z,i,axis=0)[:,:,:1]
    ok(f'delete{i}:K24',np.isclose(row['families']['all31']['pooled']['N'],U(delta.mean(axis=1)).sum()))
# The generic control changes common response only; paired named correlations remain in U.
z=np.zeros((3,1,5,31)); z[:,0,0,0]=[1,2,3]
r=m.summarize(z,np.zeros((4,31)))['families']['all31']['pooled']
ok('paired_control_common',np.isclose(r['C'],4*22/6))
ok('paired_control_centered',r['L']==0)
ok('zero_reference',r['beta'] is None and r['D'] is None)
v=np.array([[1.0],[-1.0]])
ok('negative_unclipped',m.u_product(v)==-1)
print(json.dumps({'status':'passed','constructed_only':True,'checks':checks,'count':len(checks)},indent=2))
