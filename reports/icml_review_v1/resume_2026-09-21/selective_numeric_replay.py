"""Independent selective-attribution numeric audit from raw retained embeddings.

No import of the study implementation and no compute_real/evaluate_model call.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
ARTISTS=('claude_monet','alfred_sisley','camille_pissarro','paul_cezanne')
MODELS=('gpt-image-1','gpt-image-2','gpt-image-2.5-flare','gpt-image-2.5-sunburst','google/gemini-3.1-flash-image','black-forest-labs/flux.2-max')
ARMS=('free','generic',*ARTISTS)
INPUT_SHA='f9d6b94e19d8004463f7b0524dd72865e22c18b0786cf48387cb9257e0528826'
AUDIT_SHA='e3f26efb7286ad592e5ec30a50dd937690c29852d690c94b3baf09f31ae22569'
PRIMARY='csd/original/primary'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
def rate(a,b):return None if b==0 else a/b
def difference(a,b):return None if a is None or b is None else a-b
def mean(vals):
    vals=list(vals)
    return None if not vals or any(v is None for v in vals) else sum(vals)/len(vals)
def span(vals):
    vals=list(vals);missing=sum(v is None for v in vals)
    return dict(values=vals,missing_count=missing,range=None if missing or not vals else [min(vals),max(vals)])
def named_summary(rows,chosen):
    accepted=[r for r in rows if r['id'] in chosen]; rejected=[r for r in rows if r['id'] not in chosen]
    def wrong(rr):return sum(r['pred']!=r['truth'] for r in rr)
    def confusion(rr):return [[sum(r['truth']==a and r['pred']==b for r in rr) for b in range(4)] for a in range(4)]
    n=len(rows);k=len(accepted);bad=wrong(rows);ab=wrong(accepted);rb=wrong(rejected)
    per=[]
    for a in range(4):
        rr=[r for r in rows if r['truth']==a]; aa=[r for r in accepted if r['truth']==a]; bb=[r for r in rejected if r['truth']==a]
        per.append(dict(painter=ARTISTS[a],count=len(rr),accepted_count=len(aa),coverage=rate(len(aa),len(rr)),unrestricted_error=rate(wrong(rr),len(rr)),accepted_error=rate(wrong(aa),len(aa)),abstained_error=rate(wrong(bb),len(bb))))
    return dict(count=n,accepted_count=k,abstained_count=n-k,coverage=rate(k,n),correct_count=n-bad,incorrect_count=bad,accepted_correct=k-ab,accepted_incorrect=ab,abstained_correct=n-k-rb,abstained_incorrect=rb,unrestricted_error=rate(bad,n),accepted_error=rate(ab,k),abstained_error=rate(rb,n-k),confusion=confusion(rows),accepted_confusion=confusion(accepted),abstained_confusion=confusion(rejected),per_painter=per)
def control_summary(rows,chosen,cutoff_ties):
    accepted=[r for r in rows if r['id'] in chosen]
    return dict(count=len(rows),accepted_count=len(accepted),attribution_rate=rate(len(accepted),len(rows)),predicted_artist_counts=[sum(r['pred']==a for r in rows) for a in range(4)],accepted_artist_counts=[sum(r['pred']==a for r in accepted) for a in range(4)],numeric_cutoff_ties=cutoff_ties)
def pool(allrows,scenes):
    rows=[r for r in allrows if r['scene'] in scenes];named=[r for r in rows if r['truth'] is not None]
    gate_ids={r['id'] for r in rows if r['gate']};K=sum(r['gate'] for r in named)
    ranked=sorted(named,key=lambda r:(-r['margin'],r['id']));margin_ids={r['id'] for r in ranked[:K]}
    cutoff=ranked[K-1]['margin'] if K else None
    gate=named_summary(named,gate_ids);margin=named_summary(named,margin_ids)
    controls={}
    for arm in ARMS[:2]:
        rr=[r for r in rows if r['arm']==arm]
        chosen={r['id'] for r in rr if K and r['margin']>=cutoff}
        margin_ids|=chosen
        controls[arm]=dict(reference_gate=control_summary(rr,gate_ids,None),margin_comparator=control_summary(rr,chosen,sum(r['margin']==cutoff for r in rr) if K else 0))
    return dict(retained_scenes=scenes,reference_gate=gate,margin_comparator=margin,baseline_minus_gate_risk=difference(gate['unrestricted_error'],gate['accepted_error']),margin_minus_gate_risk=difference(margin['accepted_error'],gate['accepted_error']),comparator_cutoff=dict(k=K,cutoff=cutoff,boundary_id=ranked[K-1]['id'] if K else None,cutoff_ties=sum(r['margin']==cutoff for r in named) if K else 0,cutoff_ties_accepted=sum(r['margin']==cutoff for r in ranked[:K]) if K else 0),controls=controls,named_reason_counts={reason:sum(r['reason']==reason for r in named) for reason in ('accepted','empty_set','multiple_labels','singleton_disagrees_with_top1')},named_top_ties=sum(r['tie'] for r in named)),margin_ids

def model_outcome(rows,vectors,prototypes,thresholds,model):
    indices=[i for i,r in enumerate(rows) if r['role']=='generated' and r['model']==model]
    indices.sort(key=lambda i:(rows[i]['scene'],rows[i]['repeat'],ARMS.index(rows[i]['arm'])))
    if len(indices)!=168:raise ValueError('incorrect generated model count')
    xx=vectors[indices];scores=xx@prototypes.T
    computed=[]
    for i,score in zip(indices,scores):
        r=rows[i];ss=score.tolist();pred=ss.index(max(ss));nc=[max(ss[b] for b in range(4) if b!=a)-ss[a] for a in range(4)]
        members=[a for a in range(4) if nc[a]<=thresholds[a]];gate=members==[pred]
        reason='accepted' if gate else ('empty_set' if not members else ('multiple_labels' if len(members)>1 else 'singleton_disagrees_with_top1'))
        computed.append(dict(id=r['id'],scene=r['scene'],repeat=r['repeat'],arm=r['arm'],truth=ARMS.index(r['arm'])-2 if r['arm'] in ARTISTS else None,pred=pred,scores=ss,nc=nc,members=members,gate=gate,reason=reason,margin=sorted(ss)[-1]-sorted(ss)[-2],tie=ss.count(max(ss))>1))
    full,margin_ids=pool(computed,list(range(14)));observations=[]
    for r in computed:
        observations.append(dict(id=r['id'],scene=r['scene'],repeat=r['repeat'],arm=r['arm'],prompted_artist=None if r['truth'] is None else ARTISTS[r['truth']],scores=r['scores'],nonconformity=r['nc'],candidates=[ARTISTS[a] for a in r['members']],top1=ARTISTS[r['pred']],top_score_tie=r['tie'],ordinary_margin=r['margin'],reference_gate_accept=r['gate'],gate_reason=r['reason'],margin_comparator_accept=r['id'] in margin_ids))
    deletions=[dict(deleted_scene=s,**pool(computed,[a for a in range(14) if a!=s])[0]) for s in range(14)]
    influence={key:span(d[key] for d in deletions) for key in ('baseline_minus_gate_risk','margin_minus_gate_risk')}
    influence['gate_coverage']=span(d['reference_gate']['coverage'] for d in deletions)
    influence['gate_accepted_error']=span(d['reference_gate']['accepted_error'] for d in deletions)
    return dict(model=model,**full,observations=observations,scene_deletions=deletions,influence=influence)
def overall(models):
    if [m['model'] for m in models]!=list(MODELS):raise ValueError('all six configurations required')
    base=mean(m['baseline_minus_gate_risk'] for m in models);margin=mean(m['margin_minus_gate_risk'] for m in models)
    criteria=dict(every_configuration_coverage_at_least_half=all(m['reference_gate']['coverage'] is not None and m['reference_gate']['coverage']>=.5 for m in models),every_painter_accepted_in_every_configuration=all(p['accepted_count']>=1 for m in models for p in m['reference_gate']['per_painter']),positive_mean_baseline_minus_gate=base is not None and base>0,positive_mean_margin_minus_gate=margin is not None and margin>0)
    return dict(configuration_count=6,mean_baseline_minus_gate_risk=base,mean_margin_minus_gate_risk=margin,mean_coverage=mean(m['reference_gate']['coverage'] for m in models),mean_gate_accepted_error=mean(m['reference_gate']['accepted_error'] for m in models),missing_means=[k for k,v in (('baseline_minus_gate',base),('margin_minus_gate',margin)) if v is None],criteria=criteria,failed_criteria=[k for k,v in criteria.items() if not v],joint_usefulness=all(criteria.values()),adverse_baseline_configurations=[m['model'] for m in models if m['baseline_minus_gate_risk'] is not None and m['baseline_minus_gate_risk']<0],adverse_margin_configurations=[m['model'] for m in models if m['margin_minus_gate_risk'] is not None and m['margin_minus_gate_risk']<0])
def setting(rows,vectors,view,target):
    lookup={(r['id'],r['view']):i for i,r in enumerate(rows)}
    if len(lookup)!=2009:raise ValueError('original/view identities differ')
    groups={role:[[] for a in ARTISTS] for role in ('reference','development')};memberships={role:[[] for a in ARTISTS] for role in ('reference','development')}
    for i,r in enumerate(rows):
        if r['role'] not in groups or r['view']!='original':continue
        role=r['role'];a=ARTISTS.index(r['painter']);selected=lookup.get((r['id'],'audited_region'),i) if view=='audited_region' else i
        groups[role][a].append(vectors[selected]);memberships[role][a].append(dict(id=r['id'],original_row=i,selected_row=selected,selected_view=rows[selected]['view']))
    for role,counts in [('reference',[297,106,141,105]),('development',[101,36,48,36])]:
        if list(map(len,groups[role]))!=counts:raise ValueError('historical class counts differ')
    rr='reference' if target=='primary' else 'development';cr='development' if target=='primary' else 'reference'
    raw=np.stack([np.array(g).mean(axis=0) for g in groups[rr]]);norms=np.sqrt(np.sum(raw*raw,axis=1));prototypes=raw/norms[:,None]
    thresholds=[];quantiles=[];cal_scores=[]
    for a in range(4):
        sc=np.array(groups[cr][a])@prototypes.T
        nc=[max(row[b] for b in range(4) if b!=a)-row[a] for row in sc];n=len(nc)
        # Integer ceiling independent of floating quantile utilities.
        k=(9*(n+1))//10+int((9*(n+1))%10>0);q=sorted(nc)[k-1] if k<=n else None
        thresholds.append(np.inf if q is None else q);quantiles.append(dict(n=n,rank=k,infinite=k>n,threshold=q));cal_scores.append(nc)
    cal=dict(alpha=.10,reference_counts=list(map(len,groups[rr])),calibration_counts=list(map(len,groups[cr])),raw_reference_means=raw.tolist(),reference_mean_norms=norms.tolist(),prototypes=prototypes.tolist(),quantiles=quantiles,calibration_scores=cal_scores,generated_image_coverage_guarantee=False)
    models=[model_outcome(rows,vectors,prototypes,thresholds,m) for m in MODELS]
    deleted=[dict(deleted_scene=s,**overall([dict(model=m['model'],**m['scene_deletions'][s]) for m in models])) for s in range(14)]
    return dict(reference_role=rr,calibration_role=cr,memberships=memberships,calibration=cal,models=models,summary=overall(models),scene_deletion_summaries=deleted,influence={name:span(d[name] for d in deleted) for name in ('mean_baseline_minus_gate_risk','mean_margin_minus_gate_risk','mean_coverage','mean_gate_accepted_error')})
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    inp=ROOT/'reports/painter_selective_attribution_v1/inputs.json';audit=ROOT/'reports/icml_review_v1/resume_2026-09-21/selective_preoutcome_audit.json'
    if sha(inp)!=INPUT_SHA or sha(audit)!=AUDIT_SHA:raise ValueError('external freeze/audit digest differs')
    freeze=read(inp)
    for rel,digest in freeze['bindings'].items():
        p=(ROOT/rel).resolve()
        if not p.is_relative_to(ROOT) or sha(p)!=digest:raise ValueError('frozen binding differs: '+rel)
    retained=ROOT/'reports/painter_learned_audit_v1';manifestp=retained/'inputs.json';rows=read(manifestp)['rows']
    archives=[retained/f'embeddings_{e}.npz' for e in ('clip','csd')]
    actualp=ROOT/'reports/painter_selective_attribution_v1/analysis.json';actual=read(actualp)
    if actual['inputs_sha256']!=INPUT_SHA or actual['audit_sha256']!=AUDIT_SHA:raise ValueError('result provenance differs')
    expected={};counts=0;errors=[];maxabs=0.;maxrel=0.
    def compare(path,e,a):
        nonlocal counts,maxabs,maxrel
        if isinstance(e,dict):
            if set(e)!=set(a):raise AssertionError('mapping fields differ '+path)
            for k,v in e.items():compare(path+'.'+k,v,a[k])
        elif isinstance(e,list):
            if len(e)!=len(a):raise AssertionError('sequence count differs '+path)
            for i,v in enumerate(e):compare(f'{path}[{i}]',v,a[i])
        else:
            counts+=1
            if e is None or isinstance(e,(str,bool,int,np.integer)):
                if e!=a:errors.append(dict(path=path,expected=e,actual=a))
            else:
                delta=abs(e-a);maxabs=max(maxabs,delta);maxrel=max(maxrel,delta/max(abs(e),abs(a),1e-300))
                if not np.isclose(e,a,rtol=1e-10,atol=1e-12):errors.append(dict(path=path,expected=float(e),actual=a))
    for encoder,p in zip(('clip','csd'),archives):
        with np.load(io.BytesIO(p.read_bytes()),allow_pickle=False) as archive:
            if archive.files!=['embeddings']:raise ValueError('archive member mismatch')
            x=archive['embeddings'].astype(np.float64)
        if x.shape!=(2009,768) or not np.isfinite(x).all() or not np.allclose(np.linalg.norm(x,axis=1),1,rtol=0,atol=1e-4):raise ValueError('archive vector census differs')
        for view in ('original','audited_region'):
            for target in ('primary','development'):
                key=f'{encoder}/{view}/{target}';out=setting(rows,x,view,target);compare(key,out,actual['settings'][key]);expected[key]=out
    compare('primary_joint_usefulness',expected[PRIMARY]['summary']['joint_usefulness'],actual['primary_joint_usefulness'])
    bound=[inp,audit,manifestp,*archives,actualp,Path(__file__).resolve()]
    result=dict(status='passed' if not errors else 'failed',audit_kind='independent numerical verification after frozen real execution; not scientific rating',method='raw retained archives and manifest; independent prototype/calibration, Python-count gate/comparator aggregation and every scene deletion; no study implementation import',compared_values=counts,rtol=1e-10,atol=1e-12,max_absolute_difference=maxabs,max_relative_difference=maxrel,errors=errors,settings=8,configurations_per_setting=6,query_rows_per_setting=1008,scene_deletions_per_setting=14,primary_joint_usefulness=expected[PRIMARY]['summary']['joint_usefulness'],all_setting_joint_usefulness={k:v['summary']['joint_usefulness'] for k,v in expected.items()},primary_summary=expected[PRIMARY]['summary'],primary_by_model=[dict(model=m['model'],coverage=m['reference_gate']['coverage'],baseline_risk=m['reference_gate']['unrestricted_error'],gate_risk=m['reference_gate']['accepted_error'],margin_risk=m['margin_comparator']['accepted_error'],accepted_painter_counts=[p['accepted_count'] for p in m['reference_gate']['per_painter']],baseline_minus_gate=m['baseline_minus_gate_risk'],margin_minus_gate=m['margin_minus_gate_risk']) for m in expected[PRIMARY]['models']],bindings=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in bound],limitations=['Retrospective standard selective classification; no generated-image conformal guarantee.','Numerical agreement is not a scientific rating, evidence of perceptual fidelity, or fresh-session replication.','Primary failures and every adverse sensitivity remain part of the result.'])
    with args.output.open('x') as out:json.dump(result,out,indent=2,sort_keys=True);out.write('\n')
    print(json.dumps({k:result[k] for k in ('status','compared_values','max_absolute_difference','max_relative_difference','primary_joint_usefulness')},indent=2))
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
