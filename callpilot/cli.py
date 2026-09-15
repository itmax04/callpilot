import argparse, hashlib, json
from pathlib import Path
from .config import get_settings
from .ingest import ingest
from .providers import DemoProvider, OpenAIProvider, ProviderError, RequestBudget, input_hash, prompt_hash
from .db import make_db, upsert_inputs, store_run, cached_results
from .reporting import compare, write_report, write_detailed_csv
ROOT=Path(__file__).resolve().parents[1]

def run_pipeline(settings, split='all'):
    out=ROOT/'outputs'; out.mkdir(exist_ok=True)
    transcripts,crm,manifest=ingest(ROOT/'data/transcripts',ROOT/'data/crm.csv',out/'manifest.json')
    splits=json.loads((ROOT/'data/splits.json').read_text())
    if split!='all': transcripts=[t for t in transcripts if splits.get(t.call_id)==split]
    engine=make_db(settings.database_url); upsert_inputs(engine,transcripts,crm,manifest)
    if settings.mode=='demo': provider=DemoProvider(ROOT/'data'); model='demo-fixture'
    else:
        # Budget counts both prompt versions and every retry. A live run is never silently converted to demo.
        provider=None; model=settings.openai_model
    allres={}; run_ids=[]
    for version in ('v1','v2'):
        dataset_key=hashlib.sha256((''.join(input_hash(t) for t in transcripts)+settings.mode+model+prompt_hash(version)+split).encode()).hexdigest()[:16]
        rid=f'{settings.mode}-{split}-{version}-{dataset_key}'
        ids=[t.call_id for t in transcripts]; cached=cached_results(engine,rid,ids)
        byid={r.call_id:r for r in cached}; missing=[t for t in transcripts if t.call_id not in byid]
        if settings.mode=='live':
            remaining=settings.max_requests
            if len(missing)* (settings.max_retries+1) > remaining:
                # still run until the budget is exhausted; failures remain visible
                pass
            budget=RequestBudget(settings.max_requests)
            try: provider=OpenAIProvider(settings,budget=budget)
            except ProviderError as e: raise SystemExit(str(e))
        for t in missing:
            try: byid[t.call_id]=provider.analyze(t,version)
            except ProviderError as e:
                if settings.mode=='demo': raise
                from .models import AnalysisResult
                byid[t.call_id]=AnalysisResult(call_id=t.call_id,prompt_version=version,criteria=[],provider_status='failed',error_message=str(e)[:120],model=model,prompt_hash=prompt_hash(version),input_hash=input_hash(t))
        results=[byid[t.call_id] for t in transcripts]
        used=getattr(getattr(provider,'budget',None),'used',0)
        store_run(engine,rid,version,settings.mode,model,results,used,settings.max_requests if settings.mode=='live' else 0)
        allres[version]=results; run_ids.append(rid)
    # Gold is read only here; it is never passed to either provider.
    gold_path=ROOT/'data/gold_labels.json'
    summary=compare(allres,gold_path,out)
    write_detailed_csv(allres,out)
    write_report(summary,manifest,run_ids,out)
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    return summary

def main():
    p=argparse.ArgumentParser(description='CallPilot reproducible pipeline')
    p.add_argument('command',choices=['all','ingest','analyze','compare','report'])
    p.add_argument('--split',choices=['all','development','holdout'],default='all')
    args=p.parse_args(); settings=get_settings()
    if args.command=='ingest':
        ingest(ROOT/'data/transcripts',ROOT/'data/crm.csv',ROOT/'outputs/manifest.json')
    elif args.command in ('all','analyze','compare','report'):
        run_pipeline(settings,args.split)
    print('CallPilot завершён. Режим:',settings.mode,'split:',args.split)
if __name__=='__main__': main()
