import json
from pathlib import Path
import pytest
from callpilot.models import Transcript, CriterionResult, Status
from callpilot.metrics import score, classification_metrics
from callpilot.providers import DemoProvider, ProviderError
ROOT=Path(__file__).resolve().parents[1]
def test_demo_fixture_and_quotes():
 t=Transcript.model_validate_json((ROOT/'data/transcripts/CALL-001.json').read_text()); r=DemoProvider(ROOT/'data').analyze(t,'v2'); assert len(r.criteria)==7; assert all(x['valid'] for x in r.evidence_checks)
def test_unknown_demo_fails_without_fallback():
 t=Transcript(call_id='UNKNOWN',date='2025-01-01',language='ru',utterances=[{'id':'u1','role':'client','text':'x'}],synthetic=True)
 with pytest.raises(ProviderError): DemoProvider(ROOT/'data').analyze(t,'v2')
def test_score_zero_denominator():
 cs=[CriterionResult(criterion_id=i,status=Status.insufficient_data,explanation='x',utterance_ids=[],quotes=[]) for i in range(1,8)]; assert score(cs)==(None,0)
def test_metrics_known_example():
 m=classification_metrics(['met','not_met','met'],['met','met','met']); assert m['accuracy']==pytest.approx(2/3); assert m['class_counts']['met']==2
def test_injection_is_data():
 raw=json.loads((ROOT/'data/problematic/prompt_injection.json').read_text()); assert 'Игнорируй критерии' in raw['utterances'][0]['text']

def test_live_is_explicitly_blocked_without_spend_permission():
    from callpilot.config import Settings
    from callpilot.providers import OpenAIProvider, ProviderError
    with pytest.raises(ProviderError, match='разрешение'):
        OpenAIProvider(Settings(openai_api_key='secret', allow_paid_live=False))

def test_timeout_is_recorded_and_retried_without_demo_fallback():
    import httpx, openai
    from callpilot.config import Settings
    from callpilot.providers import OpenAIProvider, RequestBudget
    class Responses:
        def parse(self, **kwargs): raise openai.APITimeoutError(request=httpx.Request('POST','https://example.com'))
    class Fake: responses=Responses()
    t=Transcript.model_validate_json((ROOT/'data/transcripts/CALL-001.json').read_text())
    settings=Settings(openai_api_key='secret',allow_paid_live=True,max_retries=1,max_requests=2)
    provider=OpenAIProvider(settings,budget=RequestBudget(2),client=Fake(),sleeper=lambda _:None)
    result=provider.analyze(t,'v2')
    assert result.provider_status=='failed' and result.error_message=='APITimeoutError' and result.attempts==2 and not result.criteria
