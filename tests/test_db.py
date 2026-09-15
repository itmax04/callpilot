from callpilot.db import make_db,upsert_inputs
from callpilot.ingest import ingest
from sqlalchemy import text
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_crm_join_does_not_multiply_deal_amount(tmp_path):
 a,c,_=ingest(ROOT/'data/transcripts',ROOT/'data/crm.csv',tmp_path/'m.json'); e=make_db('sqlite:///'+str(tmp_path/'x.db')); upsert_inputs(e,a,c)
 rows=e.connect().execute(text('SELECT SUM(amount) FROM deals')).scalar(); assert rows==sum(float(x['amount']) for x in c.values())
