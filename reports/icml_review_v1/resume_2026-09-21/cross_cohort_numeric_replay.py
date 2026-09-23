"""Independent direct ordered-pair replay of the separately frozen SD-Turbo audit.

Does not import the analysis implementation or call summarize/load_frozen.
Run only after the pre-outcome audit and real analysis are complete.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
ARTISTS=('claude_monet','alfred_sisley','camille_pissarro','paul_cezanne')
ARMS=('artist_free',*ARTISTS)
SCENES=tuple(f'{p}{i}' for p in 'WBRL' for i in range(1,5))
FAMILIES={'all31':slice(0,31),'color':slice(0,11),'spatial':slice(11,19),'texture':slice(19,31)}
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(s) for s in p.read_text().splitlines()]
def U(v):
    # Literal ordered pairs; no centered sum-of-squares identity from audited code.
    return np.mean([np.sum(v[i]*v[j],axis=-1) for i in range(len(v))
                    for j in range(len(v)) if i!=j],axis=0)
def energy(delta,r):
    c=delta.mean(axis=-2);d=delta-c[...,None,:]
    C=4*U(c);L=U(d).sum(axis=-1);N=U(delta).sum(axis=-1);H=float(np.sum(r*r))
    beta=np.sum(d.mean(axis=0)*r,axis=(-2,-1))/H if H>0 else None
    D=U(d-r).sum(axis=-1)/H if H>0 else None
    return dict(C=C,L=L,N=N,T=C-L,H=H,beta=beta,D=D)
def scalar(x):return None if x is None else float(x)
def summary(z,mu):
    r=mu-mu.mean(axis=0);delta=z[:,:,1:]-z[:,:,:1]
    p={k:scalar(v) for k,v in energy(delta.mean(axis=1),r).items()}
    allscenes=energy(delta,r)
    w={k:scalar(None if v is None else np.mean(v)) for k,v in allscenes.items()}
    for out in (p,w):
        out['common_fraction']=out['C']/out['N'] if out['N']>0 else None
        out['common_fraction_reason']=None if out['N']>0 else 'nonpositive_total_naming_change'
        out['alignment_reason']=None if out['H']>0 else 'zero_reference_energy'
        out['common_majority_descriptive']=out['N']>0 and out['T']>0
    pairs=[]
    for a in range(4):
        for b in range(a+1,4):
            q=mu[a]-mu[b];h=float(np.sum(q*q));g=z[:,:,a+1]-z[:,:,b+1]
            pairs.append(dict(painters=[ARTISTS[a],ARTISTS[b]],reference_squared_distance=h,
                aligned_amplitude=float(np.sum(g.mean(axis=(0,1))*q)/h) if h>0 else None,
                scene_D=float(U(g-q).mean()/h) if h>0 else None,
                reason=None if h>0 else 'zero_reference_pair_distance'))
    scene_records=[]
    for s in range(z.shape[1]):
        ss={k:scalar(v if k=='H' or v is None else v[s]) for k,v in allscenes.items()}
        ss.update(scene_index=s,common_fraction=ss['C']/ss['N'] if ss['N']>0 else None,
                  common_fraction_reason=None if ss['N']>0 else 'nonpositive_total_naming_change',
                  alignment_reason=None if ss['H']>0 else 'zero_reference_energy',
                  common_majority_descriptive=ss['N']>0 and ss['T']>0)
        scene_records.append(ss)
    return dict(pooled=p,within_scene=w,pairs=pairs,scene_records=scene_records,
                scene_minus_pooled_D=None if p['D'] is None else w['D']-p['D'])
def reconstruct(z,mu):
    families={f:summary(z[...,s],mu[...,s]) for f,s in FAMILIES.items()}
    deleted=[dict(block=b,families={f:summary(np.delete(z,b,axis=0)[...,s],mu[...,s])
             for f,s in FAMILIES.items()}) for b in range(25)]
    ranges={}
    for f in FAMILIES:
        ranges[f]={}
        for kind in ('pooled','within_scene'):
            ranges[f][kind]={}
            for metric in ('C','L','N','T','common_fraction','beta','D'):
                vals=[d['families'][f][kind][metric] for d in deleted]
                finite=[v for v in vals if v is not None]
                ranges[f][kind][metric]=dict(minimum=min(finite) if finite else None,
                    maximum=max(finite) if finite else None,available=len(finite),
                    unavailable_blocks=[i for i,v in enumerate(vals) if v is None])
    return dict(families=families,leave_one_block_out=deleted,sensitivity_ranges=ranges)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--inputs-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    inp=ROOT/'reports/painter_cross_cohort_v1/inputs.json'
    if sha(inp)!=args.inputs_sha256:raise ValueError('external freeze SHA mismatch')
    frozen=read(inp)
    for b in frozen['bindings']:
        p=(ROOT/b['path']).resolve()
        if not p.is_relative_to(ROOT) or sha(p)!=b['sha256']:raise ValueError('binding differs')
    method=ROOT/'data/manifests/painter_feature_generation_v2/pfg2-method-20260905'
    gen=method/'experiments/pfg2-sd-turbo-20260905/generated_features.jsonl'
    refs=method/'confirmation_features.jsonl';scalerp=method/'scaler.json'
    scaler=read(scalerp);center=np.array(scaler['center']);scale=np.array(scaler['scale'])
    z=np.full((25,16,5,31),np.nan);seen=set()
    for row in rows(gen):
        cell=(row['block'],SCENES.index(row['template_id']),ARMS.index(row['condition']))
        if cell in seen or row['status']!='measured':raise ValueError('invalid census')
        seen.add(cell);z[cell]=(np.array(row['values'])-center)/scale
    if len(seen)!=2000 or not np.isfinite(z).all():raise ValueError('incomplete finite census')
    rr=[r for r in rows(refs) if r['status']=='measured']
    counts=[sum(r['painter_id']==a for r in rr) for a in ARTISTS]
    if counts!=[297,106,141,105]:raise ValueError('reference counts differ')
    mu=np.stack([np.mean([(np.array(r['values'])-center)/scale for r in rr
                         if r['painter_id']==a],axis=0) for a in ARTISTS])
    expected=reconstruct(z,mu);actualpath=ROOT/'reports/painter_cross_cohort_v1/analysis.json'
    actual=read(actualpath);checks=[];errors=[];maxabs=0.0;maxrel=0.0
    def compare(key,e,a):
        nonlocal maxabs,maxrel
        if isinstance(e,dict):
            for k,v in e.items():compare(f'{key}.{k}',v,a[k])
        elif isinstance(e,list):
            if len(e)!=len(a):raise AssertionError('list length differs '+key)
            for i,v in enumerate(e):compare(f'{key}[{i}]',v,a[i])
        elif e is None or isinstance(e,(str,bool,int)):
            checks.append(key)
            if e!=a:errors.append(dict(path=key,expected=e,actual=a))
        else:
            checks.append(key);delta=abs(e-a);maxabs=max(maxabs,delta)
            maxrel=max(maxrel,delta/max(abs(e),abs(a),1e-300))
            if not np.isclose(e,a,rtol=1e-10,atol=1e-10):errors.append(dict(path=key,expected=e,actual=a))
    compare('result',expected,actual)
    bound=[inp,gen,refs,scalerp,actualpath,Path(__file__).resolve()]
    result=dict(status='passed' if not errors else 'failed',audit_kind='independent numerical replay after outcomes',
                inputs_sha256=args.inputs_sha256,method='literal ordered distinct-block products; no analysis-code imports',
                compared_values=len(checks),max_absolute_difference=maxabs,max_relative_difference=maxrel,
                rtol=1e-10,atol=1e-10,errors=errors,generated_rows=2000,reference_counts=counts,
                families=4,pairs_per_family=6,all_delete_one_blocks=25,
                bindings=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in bound],
                primary={f:{**s['pooled'],'scene_D':s['within_scene']['D']} for f,s in expected['families'].items()},
                limitations=['Numerical agreement does not establish independent block errors or prospective confirmation.',
                             'Same finite four-painter historical reference target is retained.'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as out:json.dump(result,out,indent=2,sort_keys=True);out.write('\n')
    print(json.dumps({k:result[k] for k in ('status','compared_values','max_absolute_difference','max_relative_difference')}))
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
