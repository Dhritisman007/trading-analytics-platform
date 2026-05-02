import logging
import os
import json
from datetime import datetime, timezone
import openai
from core.config import settings
from core.cache import cache

logger = logging.getLogger(__name__)

async def generate_market_commentary(
    symbol: str,
    market_data: dict,
    indicators: dict,
    ml_prediction: dict,
    news_mood: dict,
    fii_dii: dict,
) -> dict:
    api_key = getattr(settings, "openai_api_key", "") or os.environ.get("OPENAI_API_KEY", "")

    if not api_key:
        return {
            "available":    False,
            "message":      "Set OPENAI_API_KEY in environment to enable GPT commentary",
            "commentary":   None,
        }

    cache_key = f"gpt_commentary:{symbol}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    client = openai.AsyncOpenAI(api_key=api_key)

    summary = market_data.get("summary", {}) if isinstance(market_data, dict) else {}
    latest = indicators.get("latest", {}) if isinstance(indicators, dict) else {}
    ml_signal = ml_prediction.get("signal", "N/A") if isinstance(ml_prediction, dict) else "N/A"
    
    prompt = f"""
    Write a brief, professional market commentary for {symbol}.
    Latest Data: {json.dumps(summary)}
    Indicators: {json.dumps(latest)}
    ML Signal: {ml_signal}
    
    Keep it to exactly 2-3 sentences. Professional tone. Focus on the most important indicators and signals. Do not use asterisks or bold text.
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        
        commentary = response.choices[0].message.content.strip()
        tokens = response.usage.total_tokens

        res = {
            "available": True,
            "commentary": commentary,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tokens_used": tokens
        }
        cache.set(cache_key, res, ttl_seconds=1800)
        return res
    except Exception as e:
        logger.error(f"GPT error: {e}")
        return {
            "available": False,
            "message": str(e),
            "commentary": None
        }