from collections import Counter
from .models import Status, AnalysisResult

def score(criteria):
 usable=[c for c in criteria if c.status not in (Status.not_applicable,Status.insufficient_data)]
 return (sum(c.status==Status.met for c in usable)/len(usable),len(usable)) if usable else (None,0)
def classification_metrics(gold, pred):
 labels=[s.value for s in Status]; tp=Counter(); fp=Counter(); fn=Counter(); total=0; correct=0
 for g,p in zip(gold,pred):
  total+=1; correct+=g==p
  if g==p: tp[g]+=1
  else: fp[p]+=1; fn[g]+=1
 f1=[]
 for l in labels:
  precision=tp[l]/(tp[l]+fp[l]) if tp[l]+fp[l] else 0
  recall=tp[l]/(tp[l]+fn[l]) if tp[l]+fn[l] else 0
  f1.append(2*precision*recall/(precision+recall) if precision+recall else 0)
 return {'accuracy':correct/total if total else None,'macro_f1':sum(f1)/len(labels) if labels else 0,'n':total,'class_counts':dict(Counter(gold))}

def evidence_stats(results):
    checked=[c for r in results for c in r.evidence_checks if c.get('kind') in ('quote','missing_quote')]
    bad=sum(not c.get('valid',False) for c in checked)
    return {'checked_quotes':len(checked),'invalid_quotes':bad,'invalid_rate':bad/len(checked) if checked else None}
