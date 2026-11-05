import json
from types import SimpleNamespace

import httpx
import openai

from synapse_bench.engines.claude import ClaudeEngine
from synapse_bench.engines.openai_compat import OpenAICompatEngine
from synapse_bench.engines.two_stage import TwoStageEngine

LECTURE = {"lignes": [{"texte_brut": "Doliprane 1g 1cp x3/j 5j", "nom_lu": "Doliprane", "dosage_lu": "1g",
                       "forme_lue": None, "lisibilite": "claire",
                       "posologie": {"dose_par_prise": 1, "unite": "cp", "frequence": "3/j", "duree": "5 j", "voie": None}}],
           "age": None, "poids": None}


class FakeMessages:
    def __init__(self, text, stop="end_turn"):
        self.calls, self.text, self.stop = [], text, stop

    def create(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(stop_reason=self.stop, stop_details=SimpleNamespace(category="bio"),
                               content=[SimpleNamespace(type="text", text=self.text)],
                               usage=SimpleNamespace(input_tokens=10, output_tokens=5))


def claude(text, stop="end_turn"):
    m = FakeMessages(text, stop)
    return ClaudeEngine(client=SimpleNamespace(beta=SimpleNamespace(messages=m))), m


def test_claude_request_shape_and_parsing():
    e, m = claude(json.dumps(LECTURE))
    r = e.read(b"\x89PNG fake")
    assert r.lecture.lignes[0].nom_lu == "Doliprane" and r.erreur is None
    kw = m.calls[0]
    assert kw["model"] == "claude-opus-5-5" and kw["fallbacks"] == "default"
    assert kw["betas"] == ["server-side-fallback-2026-07-01"]
    assert kw["output_config"]["format"]["type"] == "json_schema" and kw["output_config"]["effort"] == "high"
    img = kw["messages"][0]["content"][0]
    assert img["type"] == "image" and img["source"]["media_type"] == "image/png"
    assert e.external is True


def test_claude_refusal_and_bad_json_are_errors_not_crashes():
    e, _ = claude("{}", stop="refusal")
    assert e.read(b"x").erreur.startswith("RuntimeError: refus")
    e, _ = claude('{"lignes": "pas une liste"}')
    assert e.read(b"x").lecture is None


def test_claude_choice():
    e, m = claude(json.dumps({"choix": "p2", "raison": "même dosage"}))
    c, _, err = e.choose("ligne", "p1 — A\np2 — B")
    assert c.choix == "p2" and err is None and m.calls[0]["output_config"]["effort"] == "medium"


def openai_engine(body, seen):
    def handler(request: httpx.Request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"id": "x", "object": "chat.completion", "created": 0, "model": "m",
                                         "choices": [{"index": 0, "finish_reason": "stop",
                                                      "message": {"role": "assistant", "content": body}}],
                                         "usage": {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7}})
    client = openai.OpenAI(base_url="http://gpu:8000/v1", api_key="local", http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    return OpenAICompatEngine("http://gpu:8000/v1", "Qwen/Qwen3-VL-32B-Instruct-FP8", client=client)


def test_openai_compat_structured_request():
    seen = []
    e = openai_engine("```json\n" + json.dumps(LECTURE) + "\n```", seen)
    r = e.read(b"png")
    assert r.lecture is not None and r.usage["output_tokens"] == 4
    req = seen[0]
    assert req["response_format"]["type"] == "json_schema" and req["temperature"] == 0
    assert req["messages"][0]["content"][0]["image_url"]["url"].startswith("data:image/png;base64,")
    assert e.external is False


def test_two_stage_sends_only_text_to_structurer():
    seen = []
    ocr = openai_engine("Doliprane 1g 1cp x3/j 5j", seen)
    structurer, m = claude(json.dumps(LECTURE))
    r = TwoStageEngine(ocr, structurer).read(b"png")
    assert r.lecture is not None and r.usage["ocr_texte"].startswith("Doliprane")
    sent = m.calls[0]["messages"][0]["content"]
    assert all(block["type"] == "text" for block in sent)  # aucune image vers le structurateur


def test_reasoning_disabled_by_default_sends_reasoning_effort_none():
    seen = []
    e = openai_engine(json.dumps(LECTURE), seen)
    assert e.read(b"png").lecture is not None
    assert seen[0]["reasoning_effort"] == "none"


def test_reasoning_can_be_enabled():
    seen = []
    e = openai_engine(json.dumps(LECTURE), seen)
    e.think = True
    e.read(b"png")
    assert "reasoning_effort" not in seen[0]


def test_think_block_in_content_is_stripped_before_json():
    seen = []
    e = openai_engine("<think>je réfléchis… {pas du json}</think>\n" + json.dumps(LECTURE), seen)
    r = e.read(b"png")
    assert r.lecture is not None and r.lecture.lignes[0].nom_lu == "Doliprane"


def test_diagnostic_reports_each_capability():
    import httpx as _h

    from synapse_bench.diagnostic import diagnostic

    def handler(request):
        body = json.loads(request.content)
        if "response_format" in body:
            return _h.Response(400, json={"error": {"message": "response_format not supported"}})
        return _h.Response(200, json={"id": "x", "object": "chat.completion", "created": 0, "model": "m",
                                      "choices": [{"index": 0, "finish_reason": "stop",
                                                   "message": {"role": "assistant", "content": "OK"}}]})
    client = openai.OpenAI(base_url="http://gpu/v1", api_key="k", max_retries=0,
                           http_client=_h.Client(transport=_h.MockTransport(handler)))
    e = OpenAICompatEngine("http://gpu/v1", "qwen3-vl:8b", client=client)
    d = diagnostic(e)
    assert list(d.ok) == [True, True, False, True]
    assert "response_format not supported" in d.loc[2, "réponse"]


def test_model_without_thinking_support_retries_without_reasoning_field():
    import httpx as _h
    calls = []

    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        if "reasoning_effort" in body:
            return _h.Response(400, json={"error": {"message": '"qwen3-vl:8b" does not support thinking'}})
        return _h.Response(200, json={"id": "x", "object": "chat.completion", "created": 0, "model": "m",
                                      "choices": [{"index": 0, "finish_reason": "stop",
                                                   "message": {"role": "assistant", "content": json.dumps(LECTURE)}}]})
    client = openai.OpenAI(base_url="http://gpu/v1", api_key="k", max_retries=0,
                           http_client=_h.Client(transport=_h.MockTransport(handler)))
    e = OpenAICompatEngine("http://gpu/v1", "qwen3-vl:8b", client=client)
    assert e.read(b"png").lecture is not None
    assert e.read(b"png").lecture is not None
    assert ["reasoning_effort" in c for c in calls] == [True, False, False]  # appris une fois, plus renvoyé
