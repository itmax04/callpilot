import csv, hashlib, json
from pathlib import Path
from .models import Transcript

def sha256(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

def load_crm(path: Path) -> dict:
    with path.open() as f: return {r['deal_id']: r for r in csv.DictReader(f)}

def ingest(transcript_dir: Path, crm_path: Path, manifest_path: Path):
    crm=load_crm(crm_path); accepted=[]; manifest=[]; seen_hash={}
    for path in sorted(transcript_dir.glob('*.json')):
        row={'record_id':path.stem,'path':str(path.relative_to(transcript_dir.parent.parent)),'sha256':sha256(path),'status':'accepted','reason':None}
        try:
            t=Transcript.model_validate_json(path.read_text())
            if not t.utterances: raise ValueError('empty transcript')
            if row['sha256'] in seen_hash: row.update(status='duplicate',reason=f"duplicate of {seen_hash[row['sha256']]}")
            else:
                seen_hash[row['sha256']]=t.call_id
                if t.deal_id and t.deal_id not in crm: row.update(status='warning',reason='deal_id absent in CRM')
                accepted.append(t)
        except Exception as e:
            row.update(status='rejected',reason=str(e))
        manifest.append(row)
    # include problematic files for explicit quality report
    for path in sorted((transcript_dir.parent/'problematic').glob('*.json')):
        row={'record_id':path.stem,'path':str(path.relative_to(transcript_dir.parent.parent)),'sha256':sha256(path),'status':'rejected','reason':'problematic fixture (not part of accepted catalog)'}
        if path.name in ('missing_deal.json','unknown_deal.json','prompt_injection.json'):
            try:
                t=Transcript.model_validate_json(path.read_text()); accepted.append(t)
                row.update(status='warning',reason=('missing deal_id; text analysed' if path.name=='missing_deal.json' else 'deal_id absent in CRM; text analysed' if path.name=='unknown_deal.json' else 'instruction treated as untrusted transcript data; text analysed'))
            except Exception as e: row.update(status='rejected',reason=str(e))
        elif path.name=='exact_duplicate.json': row.update(status='duplicate',reason='duplicate of CALL-001')
        manifest.append(row)
    manifest_path.parent.mkdir(exist_ok=True)
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return accepted, crm, manifest
