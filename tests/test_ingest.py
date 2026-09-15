from pathlib import Path
from callpilot.ingest import ingest
ROOT=Path(__file__).resolve().parents[1]
def test_ingest_manifest_quality(tmp_path):
 acc,crm,m=ingest(ROOT/'data/transcripts',ROOT/'data/crm.csv',tmp_path/'manifest.json'); statuses=[x['status'] for x in m]; assert len(acc)==27; assert 'duplicate' in statuses and 'rejected' in statuses and 'warning' in statuses
