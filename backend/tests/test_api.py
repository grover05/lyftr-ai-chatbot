import pytest
from unittest.mock import patch
from litellm.types.utils import ModelResponse, Choices, Message as LiteLLMMessage, Usage
import uuid


def make_mock_response(content: str = "Test response", prompt_tokens: int = 15, completion_tokens: int = 8, is_cache_hit: bool = False):
    resp = ModelResponse(
        id=f"chatcmpl-{uuid.uuid4()}",
        choices=[Choices(message=LiteLLMMessage(role="assistant", content=content))],
        model="gemini/gemini-2.0-flash",
        usage=Usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=prompt_tokens + completion_tokens)
    )
    resp._hidden_params = {"cache_hit": is_cache_hit}
    return resp


def test_health_endpoint(client):
    """GET /health returns 200, keys_configured, and cache_enabled."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["keys_configured"] >= 2
    assert data["cache_enabled"] is True


def test_chat_validation_missing_session_id(client):
    """Validation: missing session_id returns 422."""
    response = client.post("/chat", json={"message": "hello"})
    assert response.status_code == 422


def test_chat_validation_empty_session_id(client):
    """Validation: empty session_id returns 422."""
    response = client.post("/chat", json={"session_id": "   ", "message": "hello"})
    assert response.status_code == 422


def test_chat_validation_empty_message(client):
    """Validation: empty message returns 422."""
    response = client.post("/chat", json={"session_id": "s-test", "message": ""})
    assert response.status_code == 422


def test_chat_validation_whitespace_only_message(client):
    """Validation: whitespace-only message returns 422."""
    response = client.post("/chat", json={"session_id": "s-test", "message": "   \n\t   "})
    assert response.status_code == 422


def test_chat_validation_message_over_4000_chars(client):
    """Validation: message > 4000 characters returns 422."""
    long_message = "x" * 4001
    response = client.post("/chat", json={"session_id": "s-test", "message": long_message})
    assert response.status_code == 422


def test_chat_validation_message_4000_chars_allowed(client):
    """Validation: exactly 4000 characters message is accepted."""
    msg = "a" * 4000
    mock_resp = make_mock_response("Received 4000 chars")
    with patch("litellm.completion", return_value=mock_resp):
        response = client.post("/chat", json={"session_id": "s-4000", "message": msg})
        assert response.status_code == 200
        assert response.json()["reply"] == "Received 4000 chars"


def test_unknown_session_returns_404(client):
    """GET /sessions/{session_id}/messages returns 404 for unknown session."""
    response = client.get("/sessions/unknown-session-12345/messages")
    assert response.status_code == 404
    assert response.json()["detail"] == "session not found"


def test_successful_chat_and_history(client):
    """Successful chat turn persists history and retrieves correctly."""
    session_id = f"s-{uuid.uuid4().hex[:8]}"
    mock_resp = make_mock_response("The capital of France is Paris.", prompt_tokens=25, completion_tokens=7)

    with patch("litellm.completion", return_value=mock_resp):
        chat_res = client.post(
            "/chat",
            json={"session_id": session_id, "message": "What is the capital of France?"}
        )
        assert chat_res.status_code == 200
        data = chat_res.json()
        assert data["session_id"] == session_id
        assert data["reply"] == "The capital of France is Paris."
        assert data["metadata"]["resolution_source"] == "LIVE_INFERENCE"
        assert data["metadata"]["key_id"] == "key_1"
        assert data["metadata"]["fallback_attempts"] == 0
        assert data["metadata"]["input_tokens"] == 25
        assert data["metadata"]["output_tokens"] == 7
        assert isinstance(data["metadata"]["latency_ms"], int)

    # Check session history
    hist_res = client.get(f"/sessions/{session_id}/messages")
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert hist["session_id"] == session_id
    assert len(hist["messages"]) == 2

    # User message
    assert hist["messages"][0]["role"] == "user"
    assert hist["messages"][0]["content"] == "What is the capital of France?"
    # Assistant message
    assert hist["messages"][1]["role"] == "assistant"
    assert hist["messages"][1]["content"] == "The capital of France is Paris."
    assert hist["messages"][1]["metadata"]["resolution_source"] == "LIVE_INFERENCE"
    assert hist["messages"][1]["metadata"]["input_tokens"] == 25
    assert hist["messages"][1]["metadata"]["output_tokens"] == 7


def test_multi_turn_history_and_isolation(client):
    """Multi-turn conversation history is maintained and sessions are isolated."""
    s1 = f"s-turn-1-{uuid.uuid4().hex[:6]}"
    s2 = f"s-turn-2-{uuid.uuid4().hex[:6]}"

    # Turn 1 on s1
    with patch("litellm.completion", return_value=make_mock_response("Nice to meet you, Alice!")):
        r1 = client.post("/chat", json={"session_id": s1, "message": "My name is Alice."})
        assert r1.status_code == 200

    # Turn 2 on s1
    with patch("litellm.completion", return_value=make_mock_response("Your name is Alice.")):
        r2 = client.post("/chat", json={"session_id": s1, "message": "What is my name?"})
        assert r2.status_code == 200

    # Check s1 history has 4 messages
    hist1 = client.get(f"/sessions/{s1}/messages").json()
    assert len(hist1["messages"]) == 4
    assert [m["role"] for m in hist1["messages"]] == ["user", "assistant", "user", "assistant"]
    assert hist1["messages"][0]["content"] == "My name is Alice."
    assert hist1["messages"][2]["content"] == "What is my name?"

    # Check s2 has no history (isolated)
    assert client.get(f"/sessions/{s2}/messages").status_code == 404


def test_failover_key_1_429(client):
    """X-Simulate-Failure: key_1=429 causes key_1 to fail and key_2 to succeed."""
    session_id = f"s-fail-{uuid.uuid4().hex[:8]}"
    mock_resp = make_mock_response("Handled by key_2")

    with patch("litellm.completion", return_value=mock_resp):
        res = client.post(
            "/chat",
            json={"session_id": session_id, "message": "Test key_1=429 failover"},
            headers={"X-Simulate-Failure": "key_1=429"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["reply"] == "Handled by key_2"
        assert data["metadata"]["key_id"] == "key_2"
        assert data["metadata"]["fallback_attempts"] == 1
        assert data["metadata"]["resolution_source"] == "LIVE_INFERENCE"


def test_failover_key_1_500(client):
    """X-Simulate-Failure: key_1=500 causes key_1 to fail and key_2 to succeed."""
    session_id = f"s-fail500-{uuid.uuid4().hex[:8]}"
    mock_resp = make_mock_response("Handled by key_2 after 500")

    with patch("litellm.completion", return_value=mock_resp):
        res = client.post(
            "/chat",
            json={"session_id": session_id, "message": "Test key_1=500 failover"},
            headers={"X-Simulate-Failure": "key_1=500"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["metadata"]["key_id"] == "key_2"
        assert data["metadata"]["fallback_attempts"] == 1


def test_failover_all_keys_failed_503(client):
    """X-Simulate-Failure: *=429 causes 503 and nothing is persisted."""
    session_id = f"s-allfail-{uuid.uuid4().hex[:8]}"

    res = client.post(
        "/chat",
        json={"session_id": session_id, "message": "This request must fail entirely"},
        headers={"X-Simulate-Failure": "*=429"}
    )
    assert res.status_code == 503
    assert res.json() == {"detail": "all providers unavailable"}

    # Verify failed request was NOT persisted
    hist_res = client.get(f"/sessions/{session_id}/messages")
    assert hist_res.status_code == 404
    assert hist_res.json()["detail"] == "session not found"


def test_response_caching_behavior(client):
    """
    Test LiteLLM caching behavior:
    1st request -> LIVE_INFERENCE
    2nd identical request -> LLM_CACHE with key_id=null and fallback_attempts=0.
    """
    s_a = f"s-cache-a-{uuid.uuid4().hex[:6]}"
    s_b = f"s-cache-b-{uuid.uuid4().hex[:6]}"
    prompt = "Explain machine learning in simple terms"

    live_resp = make_mock_response("Machine learning is training algorithms on data.", is_cache_hit=False)
    cache_resp = make_mock_response("Machine learning is training algorithms on data.", is_cache_hit=True)

    # First call in session A -> LIVE_INFERENCE
    with patch("litellm.completion", return_value=live_resp):
        res_a = client.post("/chat", json={"session_id": s_a, "message": prompt})
        assert res_a.status_code == 200
        data_a = res_a.json()
        assert data_a["metadata"]["resolution_source"] == "LIVE_INFERENCE"
        assert data_a["metadata"]["key_id"] == "key_1"
        assert data_a["metadata"]["fallback_attempts"] == 0

    # Second call in session B with identical prompt -> LLM_CACHE
    with patch("litellm.completion", return_value=cache_resp):
        res_b = client.post("/chat", json={"session_id": s_b, "message": prompt})
        assert res_b.status_code == 200
        data_b = res_b.json()
        assert data_b["reply"] == data_a["reply"]
        assert data_b["metadata"]["resolution_source"] == "LLM_CACHE"
        assert data_b["metadata"]["key_id"] is None
        assert data_b["metadata"]["fallback_attempts"] == 0
        assert data_b["metadata"]["input_tokens"] == data_a["metadata"]["input_tokens"]
        assert data_b["metadata"]["output_tokens"] == data_a["metadata"]["output_tokens"]


def test_real_litellm_cache_integration():
    """
    Direct integration test with LiteLLM's internal caching engine.
    Verifies that calling LiteLLM with identical messages populates the cache
    and sets _hidden_params['cache_hit'] = True on the subsequent call.
    """
    import litellm
    from litellm.caching import Cache

    litellm.cache = Cache(type="local")
    litellm.enable_cache()

    unique_text = f"Cache test prompt {uuid.uuid4().hex}"
    msgs = [{"role": "user", "content": unique_text}]

    # Call 1: Uncached
    r1 = litellm.completion(
        model="gpt-3.5-turbo",
        messages=msgs,
        mock_response="Mock answer from LiteLLM",
        caching=True
    )
    is_hit_1 = getattr(r1, "_hidden_params", {}).get("cache_hit") is True
    assert is_hit_1 is False

    # Call 2: Identical prompt should be a cache hit
    r2 = litellm.completion(
        model="gpt-3.5-turbo",
        messages=msgs,
        mock_response="Mock answer from LiteLLM",
        caching=True
    )
    is_hit_2 = getattr(r2, "_hidden_params", {}).get("cache_hit") is True
    assert is_hit_2 is True
    assert r2.choices[0].message.content == r1.choices[0].message.content

