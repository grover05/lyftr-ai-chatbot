import time
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException
import litellm
from litellm.caching import Cache
from litellm.exceptions import (
    RateLimitError,
    BudgetExceededError,
    InternalServerError,
    ServiceUnavailableError,
    APIConnectionError,
    Timeout,
    APIError,
)
from app.config import settings

logger = logging.getLogger("lyftr.llm_service")

# Initialize LiteLLM Built-in Cache
try:
    if settings.LITELLM_CACHE_TYPE == "disk":
        cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", ".litellm_cache")
        os.makedirs(cache_dir, exist_ok=True)
        litellm.cache = Cache(type="disk", disk_cache_dir=cache_dir)
    else:
        litellm.cache = Cache(type="local")
except Exception as e:
    logger.warning(f"Failed to initialize disk cache: {e}. Falling back to local cache.")
    litellm.cache = Cache(type="local")

litellm.enable_cache()

# Supported simulation statuses
SUPPORTED_SIMULATED_STATUSES = {429, 500, 502, 503}


def parse_simulation_header(header_value: Optional[str]) -> Dict[str, int]:
    """
    Parses X-Simulate-Failure header.
    Format: comma-separated <key_id>=<status> pairs; * means every key.
    e.g. 'key_1=429,key_2=500' or '*=429'
    """
    if not header_value:
        return {}

    rules: Dict[str, int] = {}
    parts = [p.strip() for p in header_value.split(",") if p.strip()]
    for part in parts:
        if "=" in part:
            key_id, status_str = part.split("=", 1)
            key_id = key_id.strip()
            status_str = status_str.strip()
            try:
                status_code = int(status_str)
                if status_code in SUPPORTED_SIMULATED_STATUSES:
                    rules[key_id] = status_code
                else:
                    logger.warning(f"Unsupported simulated status: {status_code}")
            except ValueError:
                logger.warning(f"Invalid simulated status in pair: {part}")
    return rules


def is_eligible_provider_error(exc: Exception) -> bool:
    """
    Determines if an exception is an eligible provider failure
    (429, quota failure, or supported 5xx provider failure).
    """
    if isinstance(exc, (RateLimitError, BudgetExceededError, InternalServerError, ServiceUnavailableError, Timeout, APIConnectionError)):
        return True

    status_code = getattr(exc, "status_code", None)
    if status_code in {429, 500, 502, 503, 504}:
        return True

    err_msg = str(exc).lower()
    if any(q in err_msg for q in ["quota", "rate limit", "ratelimit", "exceeded", "capacity", "503", "502", "500", "429"]):
        return True

    return False


class LLMService:
    def __init__(self):
        self.model = settings.MODEL_NAME

    def execute_completion(
        self,
        messages: List[Dict[str, str]],
        simulation_header: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes LiteLLM completion with key pool failover, built-in caching,
        and failure simulation.
        """
        start_time = time.perf_counter()
        key_pool = settings.key_pool

        if not key_pool:
            logger.error("No API keys configured in key pool.")
            raise HTTPException(status_code=503, detail="all providers unavailable")

        sim_rules: Dict[str, int] = {}
        if settings.ENABLE_FAILURE_SIMULATION and simulation_header:
            sim_rules = parse_simulation_header(simulation_header)

        fallback_attempts = 0
        last_error = None

        for key_id, raw_key in key_pool:
            # 1. Check if this key should be simulated as failed
            sim_status = sim_rules.get(key_id) or sim_rules.get("*")
            if sim_status:
                logger.info(f"Simulating provider failure: key={key_id}, status={sim_status}")
                fallback_attempts += 1
                last_error = f"Simulated failure {sim_status} for {key_id}"
                continue

            # 2. Attempt real completion through LiteLLM
            try:
                response = litellm.completion(
                    model=self.model,
                    messages=messages,
                    api_key=raw_key,
                    caching=True
                )

                elapsed_ms = int((time.perf_counter() - start_time) * 1000)

                # Check LiteLLM cache hit
                hidden_params = getattr(response, "_hidden_params", {}) or {}
                is_cache_hit = (
                    hidden_params.get("cache_hit") is True
                    or hidden_params.get("is_cache_hit") is True
                    or getattr(response, "is_cache_hit", False) is True
                )

                # Extract reply text
                reply = ""
                if response.choices and len(response.choices) > 0:
                    reply = response.choices[0].message.content or ""

                # Extract token usage
                usage = getattr(response, "usage", None)
                if usage:
                    input_tokens = getattr(usage, "prompt_tokens", 0) or 0
                    output_tokens = getattr(usage, "completion_tokens", 0) or 0
                else:
                    # Fallback token estimate if usage is missing
                    input_tokens = sum(len(m.get("content", "")) for m in messages) // 4
                    output_tokens = len(reply) // 4

                if is_cache_hit:
                    return {
                        "reply": reply,
                        "metadata": {
                            "resolution_source": "LLM_CACHE",
                            "model": response.model or self.model,
                            "latency_ms": elapsed_ms,
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "key_id": None,
                            "fallback_attempts": 0
                        }
                    }
                else:
                    return {
                        "reply": reply,
                        "metadata": {
                            "resolution_source": "LIVE_INFERENCE",
                            "model": response.model or self.model,
                            "latency_ms": elapsed_ms,
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "key_id": key_id,
                            "fallback_attempts": fallback_attempts
                        }
                    }

            except Exception as e:
                if is_eligible_provider_error(e):
                    logger.warning(f"Key {key_id} encountered provider error: {e}. Falling over to next key.")
                    fallback_attempts += 1
                    last_error = e
                    continue
                else:
                    # Non-eligible error (e.g. malformed input, 400), don't fail over
                    logger.error(f"Non-provider error on key {key_id}: {e}")
                    raise

        # If we exited loop, all keys failed
        logger.error(f"All keys in pool failed. Total attempts: {fallback_attempts}. Last error: {last_error}")
        raise HTTPException(status_code=503, detail="all providers unavailable")


llm_service = LLMService()
