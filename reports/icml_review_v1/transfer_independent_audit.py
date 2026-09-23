import json, hashlib
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/painter_learned_audit_v1'
OUT=ROOT/'reports/painter_prototype_transfer_v1'
ARTISTS=('claude_monet','alfred_sisley','camille_pissarro','paul_cezanne')
MODELS=('gpt-image-1','gpt-image-2','gpt-image-2.5-flare','gpt-image-2.5-sunburst','google/gemini-3.1-flash-image','black-forest-labs/flux.2-max')
RULES=('reference_baseline','common_translation','generated_prototype')
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
manifest=read(BASE/'inputs.json'); rows=manifest['rows']
result=read(OUT/'analysis.json'); binding=read(OUT/'inputs.json'); retained=read(BASE/'analysis.json')
checks=0; max_numeric_error=0.; max_score_error=0.; tables=[]; sensitivity=[]
def equal(a,b):
 global checks
 np.testing.assert_array_equal(a,b); checks+=1
def close(a,b):
 global checks, max_numeric_error
 a,b=np.asarray(a),np.asarray(b)
 assert a.shape==b.shape, (a.shape,b.shape)
 assert np.isfinite(a).all() and np.isfinite(b).all()
 np.testing.assert_allclose(a,b,rtol=0,atol=1e-12)
 max_numeric_error=max(max_numeric_error,float(np.max(np.abs(a-b))))
 checks+=1
assert len(rows)==2009
assert Counter((r['role'],r['view']) for r in rows)=={('generated','original'):1008,('reference','original'):649,('development','original'):221,('reference','audited_region'):90,('development','audited_region'):41}
for rel,digest in binding['bindings'].items(): assert sha(ROOT/rel)==digest
assert result['inputs_sha256']==sha(OUT/'inputs.json')
for rel,digest in retained['bindings'].items(): assert sha(ROOT/rel)==digest
assert result['axes']==dict(models=list(MODELS),artists=list(ARTISTS),rules=list(RULES),scenes=list(range(14)),repeats=[0,1])
assert result['prediction_axes']==['scene','repeat','prompted_painter']
assert set(result['representations'])=={'clip','csd'}
lookup={(r['id'],r['view']):i for i,r in enumerate(rows)}
assert len(lookup)==len(rows)
generated={(r['model'],r['scene'],r['repeat'],r['arm']):i for i,r in enumerate(rows) if r['role']=='generated'}
assert len(generated)==1008
truth=np.broadcast_to(np.arange(4),(14,2,4))
all_ties=all_zeros=0; translated_min_norm=999; translated_max_norm=0
for rep in ('clip','csd'):
 with np.load(BASE/f'embeddings_{rep}.npz',allow_pickle=False) as f:
  assert f.files==['embeddings']; vectors=np.asarray(f['embeddings'],dtype=np.float64)
 assert vectors.shape==(2009,768) and np.isfinite(vectors).all()
 assert np.max(abs(np.linalg.norm(vectors,axis=1)-1))<1e-4
 assert set(result['representations'][rep])=={'original','audited_region'}
 for view in ('original','audited_region'):
  recorded_view=result['representations'][rep][view]
  assert set(recorded_view['targets'])=={'primary','development'}
  actual_generated_ids=[]
  for model in MODELS:
   ids=[[[rows[generated[(model,s,k,a)]]['id'] for a in ARTISTS] for k in range(2)] for s in range(14)]
   actual_generated_ids.append(ids)
  equal(recorded_view['generated_image_ids'],actual_generated_ids)
  for target,role,census in [('primary','reference',[297,106,141,105]),('development','development',[101,36,48,36])]:
   panel=[]; selection=[]
   for artist in ARTISTS:
    records=[r for r in rows if r['view']=='original' and r['role']==role and r['painter']==artist]
    selected=[dict(id=r['id'],view='audited_region' if view=='audited_region' and (r['id'],'audited_region') in lookup else 'original') for r in records]
    selection.append(selected)
    panel.append(vectors[[lookup[(r['id'],r['view'])] for r in selected]])
   assert recorded_view['source_selections'][role]==selection
   equal([len(v) for v in panel],census)
   prototype=np.stack([sum(v)/len(v) for v in panel])
   target_mean=prototype.sum(axis=0)/4
   units=prototype/np.linalg.norm(prototype,axis=1)[:,None]
   target_result=recorded_view['targets'][target]
   equal(target_result['counts'],census)
   close(target_result['reference_prototypes'],prototype)
   assert [v['model'] for v in target_result['models']]==list(MODELS)
   deltas=[]; g_deltas=[]
   for model in MODELS:
    recorded=next(v for v in target_result['models'] if v['model']==model)
    assert set(recorded['rules'])==set(RULES) and len(recorded['folds'])==14
    indices=[[[generated[(model,s,k,a)] for a in ARTISTS] for k in range(2)] for s in range(14)]
    x=vectors[np.asarray(indices)]
    score_arrays={r:np.empty((14,2,4,4)) for r in RULES}; norm_arrays={r:np.empty((14,2,4)) for r in RULES}
    for scene in range(14):
     train_scenes=[s for s in range(14) if s!=scene]
     train_indices=[generated[(model,s,k,a)] for s in train_scenes for k in range(2) for a in ARTISTS]
     test_indices=[generated[(model,scene,k,a)] for k in range(2) for a in ARTISTS]
     assert len(train_indices)==104 and len(test_indices)==8 and not set(train_indices)&set(test_indices)
     train_mean=sum(vectors[i] for i in train_indices)/104
     translation=target_mean-train_mean
     means=np.stack([sum(vectors[generated[(model,s,k,a)]] for s in train_scenes for k in range(2))/26 for a in ARTISTS])
     gen_units=means/np.linalg.norm(means,axis=1)[:,None]
     fold=recorded['folds'][scene]
     assert fold['held_out_scene']==scene and fold['train_scenes']==train_scenes and fold['training_image_count']==104
     close(fold['training_mean'],train_mean); close(fold['reference_mean'],target_mean)
     close(fold['translation'],translation); close(fold['translation_norm'],np.linalg.norm(translation))
     close(fold['reference_prototype_norms'],np.linalg.norm(prototype,axis=1))
     close(fold['generated_prototypes'],means); close(fold['generated_prototype_norms'],np.linalg.norm(means,axis=1))
     for repeat in range(2):
      for artist in range(4):
       q=x[scene,repeat,artist]
       for rule,qv,pv in [('reference_baseline',q,units),('common_translation',q+translation,units),('generated_prototype',q,gen_units)]:
        score_arrays[rule][scene,repeat,artist]=np.array([np.dot(qv,u) for u in pv])
        norm_arrays[rule][scene,repeat,artist]=np.linalg.norm(qv)
     # Same translation must act as a class intercept, preserving within-fold centered geometry.
     close(score_arrays['common_translation'][scene],score_arrays['reference_baseline'][scene]+units@translation)
     close((x[scene]+translation)-(x[scene]+translation).mean(axis=1,keepdims=True),x[scene]-x[scene].mean(axis=1,keepdims=True))
    corrects={}; accuracies=[]
    for rule in RULES:
     rs=recorded['rules'][rule]; scores=score_arrays[rule]; norms=norm_arrays[rule]
     max_score_error=max(max_score_error,float(np.max(abs(scores-rs['scores'])))); close(rs['scores'],scores)
     prediction=scores.argmax(axis=3); correct=prediction==truth; corrects[rule]=correct
     confusion=np.zeros((4,4),dtype=int)
     for t,p in zip(truth.ravel(),prediction.ravel()): confusion[t,p]+=1
     count=confusion.sum(axis=1); recalls=np.diag(confusion)/count
     margin=np.empty((14,2,4))
     for a in range(4): margin[:,:,a]=scores[:,:,a,a]-scores[:,:,a,[b for b in range(4) if b!=a]].max(axis=-1)
     ties=(scores==scores.max(axis=-1,keepdims=True)).sum(axis=-1)>1; zeros=norms==0
     equal(rs['predictions'],prediction); equal(rs['correct'],correct); equal(rs['confusion_counts'],confusion)
     equal(count,[28]*4); equal(rs['counts'],count); assert confusion.sum()==112
     close(rs['per_painter_recall'],recalls); close(rs['macro_accuracy'],recalls.mean()); close(rs['micro_accuracy'],correct.mean())
     close(rs['scene_accuracy'],correct.mean(axis=(1,2))); close(rs['margins'],margin); close(rs['mean_margin'],margin.mean()); close(rs['query_norms'],norms)
     equal(rs['top_ties'],ties); equal(rs['zero_queries'],zeros)
     assert rs['tie_counts']==dict(total=int(ties.sum()),per_scene=ties.sum(axis=(1,2)).tolist())
     assert rs['zero_query_counts']==dict(total=int(zeros.sum()),per_scene=zeros.sum(axis=(1,2)).tolist())
     all_ties+=int(ties.sum()); all_zeros+=int(zeros.sum()); accuracies.append(int(correct.sum()))
     if rule=='common_translation':
      translated_min_norm=min(translated_min_norm,float(norms.min())); translated_max_norm=max(translated_max_norm,float(norms.max()))
      nonzero=norms>0
      equal((scores[nonzero]/norms[nonzero,None]).argmax(axis=-1),prediction[nonzero])
    legacy=next(v for v in retained[rep][view]['targets'][target]['models'] if v['model']==model)['recognition']
    for field in ['counts','confusion_counts','macro_accuracy','micro_accuracy']:
     equal(recorded['rules']['reference_baseline'][field],legacy[field])
    equal(recorded['rules']['reference_baseline']['per_painter_recall'],legacy['per_painter_accuracy'])
    for rule,key in [('common_translation','paired_translation_vs_baseline'),('generated_prototype','paired_generated_prototype_vs_baseline')]:
     before,after=corrects['reference_baseline'],corrects[rule]
     pair=recorded[key]; change=after.astype(float)-before.astype(float)
     close(pair['accuracy_difference'],change.mean()); close(pair['scene_accuracy_difference'],change.mean(axis=(1,2)))
     assert pair['corrected_count']==int((after&~before).sum())
     assert pair['newly_incorrect_count']==int((~after&before).sum())
     assert pair['unchanged_correct_count']==int((after&before).sum())
     assert pair['unchanged_incorrect_count']==int((~after&~before).sum())
     assert sum(pair[k] for k in ['corrected_count','newly_incorrect_count','unchanged_correct_count','unchanged_incorrect_count'])==112
     (deltas if rule=='common_translation' else g_deltas).append(float(change.mean()))
    if view=='original' and target=='primary':
     paired=recorded['paired_translation_vs_baseline']; scene_delta=np.array(paired['scene_accuracy_difference'])
     tables.append(dict(rep=rep,model=model,correct=accuracies,delta=paired['accuracy_difference'],corrected=paired['corrected_count'],harmed=paired['newly_incorrect_count'],scene_win_tie_loss=[int((scene_delta>0).sum()),int((scene_delta==0).sum()),int((scene_delta<0).sum())]))
   close(target_result['equal_configuration_mean_accuracy_difference']['paired_translation_vs_baseline'],np.mean(deltas))
   close(target_result['equal_configuration_mean_accuracy_difference']['paired_generated_prototype_vs_baseline'],np.mean(g_deltas))
   sensitivity.append(dict(rep=rep,view=view,target=target,translation=float(np.mean(deltas)),generated=float(np.mean(g_deltas)),negative_configs=int((np.array(deltas)<0).sum()),positive_configs=int((np.array(deltas)>0).sum())))
# Check inputs did not change during the audit.
for rel,digest in binding['bindings'].items(): assert sha(ROOT/rel)==digest
receipt=dict(status='PASS',finished_utc=datetime.now(timezone.utc).isoformat(),checks=checks,max_numeric_error=max_numeric_error,max_score_error=max_score_error,input_sha256=sha(OUT/'inputs.json'),analysis_sha256=sha(OUT/'analysis.json'),report_sha256=sha(OUT/'REPORT.md'),audit_script_sha256=sha(Path(__file__)),bindings_checked=len(binding['bindings']),configurations=48,folds=672,predictions=16128,scores=64512,primary_predictions=4032,ties=all_ties,zero_queries=all_zeros,translated_query_norm_range=[translated_min_norm,translated_max_norm],primary=tables,sensitivity=sensitivity)
print(json.dumps(receipt,indent=2))
