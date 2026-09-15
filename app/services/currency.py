import time
import httpx
from typing import Dict, Any

AWESOME_API_URL = "https://economia.awesomeapi.com.br/last/USD-BRL"

# Cache em memoria para a taxa de cambio (evita requisicoes excessivas)
_RATE_CACHE: Dict[str, Any] = {
    "rate": 5.14,
    "last_updated": 0,
    "source": "fallback"
}
CACHE_TTL_SECONDS = 600  # 10 minutos


async def get_usd_to_brl_rate() -> float:
    """Consulta a cotacao comercial atual do Dolar para Real via AwesomeAPI."""
    global _RATE_CACHE
    now = time.time()

    # Retorna do cache se ainda estiver valido
    if now - _RATE_CACHE["last_updated"] < CACHE_TTL_SECONDS and _RATE_CACHE["rate"] > 0:
        return _RATE_CACHE["rate"]

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(AWESOME_API_URL)
            if resp.status_code == 200:
                data = resp.json()
                usdBrl = data.get("USDBRL", {})
                bid = float(usdBrl.get("bid", 0.0))
                if bid > 0:
                    _RATE_CACHE = {
                        "rate": round(bid, 4),
                        "last_updated": now,
                        "source": "AwesomeAPI",
                        "timestamp": usdBrl.get("create_date", "")
                    }
                    return _RATE_CACHE["rate"]
    except Exception as e:
        print(f"Aviso: Nao foi possivel consultar a AwesomeAPI: {e}. Usando cotacao em cache.")

    return _RATE_CACHE["rate"]


def get_cached_rate_info() -> Dict[str, Any]:
    """Retorna detalhes sobre a taxa atual em cache."""
    return _RATE_CACHE
