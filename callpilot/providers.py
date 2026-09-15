"""One real provider and one strictly offline provider. No gold labels imported."""
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from pydantic import ValidationError
from .models import ModelPayload, AnalysisResult, Transcript
from .rubric import rubric_text

ROOT = Path(__file__).resolve().parents[1]

class ProviderError(RuntimeError):
    pass

class RequestBudget:
    """Counts every outbound attempt, including retries; optional persistent ledger."""
    def __init__(self, maximum, used=0, on_consume=None):
        self.maximum, self.used, self.on_consume = maximum, used, on_consume

    def consume(self):
        if self.used >= self.maximum:
            raise ProviderError('budget_exhausted')
        self.used += 1
        if self.on_consume:
            self.on_consume(self.used)  # commit before sending


def input_hash(transcript):
    return hashlib.sha256(transcript.model_dump_json().encode()).hexdigest()


def prompt_text(version):
    if version not in ('v1','v2'):
        raise ValueError('Unknown prompt version')
    return (ROOT/f'prompts_{version}.txt').read_text() + '\n' + rubric_text(version)


def prompt_hash(version):
    return hashlib.sha256(prompt_text(version).encode()).hexdigest()


def messages(transcript, version):
    # No CRM stage/amount, no reference labels. Roles separate policy from untrusted text.
    return [
        {'role':'developer','content':prompt_text(version)},
        {'role':'user','content':json.dumps({'untrusted_transcript': transcript.model_dump(mode='json')}, ensure_ascii=False)},
    ]


def verify_evidence(transcript, criteria):
    turns={u.id:u.text for u in transcript.utterances}; checks=[]
    for c in criteria:
        # Validate EACH quote, plus unmatched ids/quotes. Exact full utterance match.
        for index in range(max(len(c.utterance_ids),len(c.quotes))):
            uid=c.utterance_ids[index] if index<len(c.utterance_ids) else None
            quote=c.quotes[index] if index<len(c.quotes) else None
            valid=uid in turns and quote is not None and turns[uid]==quote
            checks.append({'criterion_id':c.criterion_id,'utterance_id':uid,'quote':quote,'valid':valid,'kind':'quote' if quote is not None else 'missing_quote'})
        if c.status.value=='met' and not c.quotes:
            checks.append({'criterion_id':c.criterion_id,'utterance_id':None,'quote':None,'valid':False,'kind':'missing_evidence'})
    return checks


class DemoProvider:
    model='demo-fixture'
    def __init__(self, fixture_dir=ROOT/'data'):
        self.fixture_dir=Path(fixture_dir)

    def analyze(self, transcript, prompt_version):
        data=json.loads((self.fixture_dir/f'demo_answers_{prompt_version}.json').read_text())
        entry=data.get(transcript.call_id)
        if not entry or entry['input_hash']!=input_hash(transcript):
            raise ProviderError(f'Demo: неизвестный или изменённый вход {transcript.call_id}; фикстуры нет')
        payload=ModelPayload.model_validate({'criteria':entry['criteria']})
        checks=verify_evidence(transcript,payload.criteria)
        return AnalysisResult(call_id=transcript.call_id,prompt_version=prompt_version,criteria=payload.criteria,provider_status='demo',model=self.model,model_version='fixture-2',prompt_hash=prompt_hash(prompt_version),input_hash=input_hash(transcript),evidence_checks=checks,review_required=any(not x['valid'] for x in checks))


class OpenAIProvider:
    def __init__(self, settings, budget=None, client=None, sleeper=time.sleep):
        if not settings.allow_paid_live:
            raise ProviderError('Live заблокирован: нужно явное разрешение расходов (--allow-paid-live)')
        if not settings.openai_api_key:
            raise ProviderError('Для live отсутствует OPENAI_API_KEY')
        from openai import OpenAI
        self.settings=settings; self.model=settings.openai_model
        self.budget=budget or RequestBudget(settings.max_requests)
        self.client=client or OpenAI(api_key=settings.openai_api_key.get_secret_value(),timeout=settings.timeout_seconds,max_retries=0)
        self.sleeper=sleeper

    def analyze(self, transcript, prompt_version):
        import openai
        started=time.perf_counter(); attempts=0; raw_response=None
        base=dict(call_id=transcript.call_id,prompt_version=prompt_version,model=self.model,prompt_hash=prompt_hash(prompt_version),input_hash=input_hash(transcript))
        def failed(status,code):
            usage=getattr(raw_response,'usage',None)
            return AnalysisResult(**base,provider_status=status,error_message=code,attempts=attempts,latency_ms=(time.perf_counter()-started)*1000,input_tokens=getattr(usage,'input_tokens',None),output_tokens=getattr(usage,'output_tokens',None))
        for retry in range(self.settings.max_retries+1):
            try:
                self.budget.consume(); attempts+=1
                raw_response=self.client.responses.parse(
                    model=self.model,input=messages(transcript,prompt_version),
                    text_format=ModelPayload,
                    max_output_tokens=self.settings.max_output_tokens, store=False,
                )
                break
            except ProviderError:
                return failed('budget_exhausted','request_budget_exhausted')
            except (openai.APITimeoutError,openai.APIConnectionError) as e:
                code=type(e).__name__
                if retry>=self.settings.max_retries: return failed('failed',code)
            except openai.APIStatusError as e:
                code=f'http_{e.status_code}'
                if e.status_code not in (408,409,429) and e.status_code<500 or retry>=self.settings.max_retries:
                    return failed('failed',code)
            except Exception as e:
                return failed('failed',type(e).__name__)  # no raw API error/secrets in logs
            self.sleeper(min(2**retry,4))
        if getattr(raw_response,'status','completed')!='completed':
            return failed('invalid_response','incomplete_or_refused')
        try:
            payload=raw_response.output_parsed
            if payload is None: raise ValueError('missing parsed output')
        except (ValidationError,ValueError):
            return failed('invalid_response','schema_or_json_error')
        usage=getattr(raw_response,'usage',None)
        it=getattr(usage,'input_tokens',None); ot=getattr(usage,'output_tokens',None)
        cost=None
        if self.settings.pricing_source_date and it is not None and ot is not None and self.settings.price_input_per_1m is not None and self.settings.price_output_per_1m is not None:
            cost=(it*self.settings.price_input_per_1m+ot*self.settings.price_output_per_1m)/1_000_000
        checks=verify_evidence(transcript,payload.criteria)
        return AnalysisResult(**base,criteria=payload.criteria,provider_status='success',model_version=getattr(raw_response,'model',None),attempts=attempts,latency_ms=(time.perf_counter()-started)*1000,input_tokens=it,output_tokens=ot,cost_usd=cost,evidence_checks=checks,review_required=any(not c['valid'] for c in checks))
