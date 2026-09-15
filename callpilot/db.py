from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, String, Integer, Float, Text, DateTime, ForeignKey, select, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .models import Transcript, AnalysisResult

class Base(DeclarativeBase): pass
class DealRow(Base):
 __tablename__='deals'; deal_id: Mapped[str]=mapped_column(String,primary_key=True); manager_id: Mapped[str]=mapped_column(String); stage: Mapped[str]=mapped_column(String); amount: Mapped[float]=mapped_column(Float); currency: Mapped[str]=mapped_column(String)
class CallRow(Base):
 __tablename__='calls'; call_id: Mapped[str]=mapped_column(String,primary_key=True); deal_id: Mapped[str|None]=mapped_column(String,nullable=True); call_date: Mapped[str]=mapped_column(String); language: Mapped[str]=mapped_column(String); transcript_json: Mapped[str]=mapped_column(Text); synthetic: Mapped[int]=mapped_column(Integer,default=1)
class RunRow(Base):
 __tablename__='runs'; run_id: Mapped[str]=mapped_column(String,primary_key=True); prompt_version: Mapped[str]=mapped_column(String); mode: Mapped[str]=mapped_column(String); model: Mapped[str]=mapped_column(String); started_at: Mapped[datetime]=mapped_column(DateTime); status: Mapped[str]=mapped_column(String); requests_used: Mapped[int]=mapped_column(Integer,default=0); max_requests: Mapped[int]=mapped_column(Integer,default=0)
class EvaluationRow(Base):
 __tablename__='evaluations'; __table_args__=(UniqueConstraint('run_id','call_id',name='uq_run_call'),); id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True); run_id: Mapped[str]=mapped_column(String,ForeignKey('runs.run_id')); call_id: Mapped[str]=mapped_column(String,ForeignKey('calls.call_id')); result_json: Mapped[str]=mapped_column(Text); provider_status: Mapped[str]=mapped_column(String); latency_ms: Mapped[float|None]=mapped_column(Float); input_tokens: Mapped[int|None]=mapped_column(Integer); output_tokens: Mapped[int|None]=mapped_column(Integer)
class ManifestRow(Base):
 __tablename__='manifest'; record_id: Mapped[str]=mapped_column(String,primary_key=True); path: Mapped[str]=mapped_column(String); sha256: Mapped[str]=mapped_column(String); status: Mapped[str]=mapped_column(String); reason: Mapped[str|None]=mapped_column(Text)

def make_db(url):
 if url.startswith('sqlite:///'): Path(url[10:]).parent.mkdir(parents=True,exist_ok=True)
 engine=create_engine(url); Base.metadata.create_all(engine); return engine

def upsert_inputs(engine, transcripts, crm, manifest=None):
 S=sessionmaker(engine); s=S()
 for d in crm.values(): s.merge(DealRow(deal_id=d['deal_id'],manager_id=d['manager_id'],stage=d['stage'],amount=float(d['amount']),currency=d['currency']))
 import json
 for t in transcripts: s.merge(CallRow(call_id=t.call_id,deal_id=t.deal_id,call_date=str(t.date),language=t.language,transcript_json=t.model_dump_json(),synthetic=1))
 if manifest:
  for row in manifest: s.merge(ManifestRow(**row))
 s.commit(); s.close()

def cached_results(engine, run_id, call_ids):
 S=sessionmaker(engine); s=S(); rows=s.execute(select(EvaluationRow).where(EvaluationRow.run_id==run_id)).scalars().all(); s.close()
 found={r.call_id:AnalysisResult.model_validate_json(r.result_json) for r in rows}
 return [found[c] for c in call_ids if c in found]

def store_run(engine, run_id, prompt_version, mode, model, results, requests_used=0, max_requests=0):
 import json
 S=sessionmaker(engine); s=S(); s.merge(RunRow(run_id=run_id,prompt_version=prompt_version,mode=mode,model=model,started_at=datetime.utcnow(),status='completed',requests_used=requests_used,max_requests=max_requests))
 # idempotent by run/call; delete old rows for same run
 for r in results:
  old=s.execute(select(EvaluationRow).where(EvaluationRow.run_id==run_id,EvaluationRow.call_id==r.call_id)).scalar_one_or_none()
  if old: old.result_json=r.model_dump_json(); old.provider_status=r.provider_status; old.latency_ms=r.latency_ms; old.input_tokens=r.input_tokens; old.output_tokens=r.output_tokens
  else: s.add(EvaluationRow(run_id=run_id,call_id=r.call_id,result_json=r.model_dump_json(),provider_status=r.provider_status,latency_ms=r.latency_ms,input_tokens=r.input_tokens,output_tokens=r.output_tokens))
 s.commit(); s.close()
