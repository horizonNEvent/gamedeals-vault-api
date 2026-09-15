import httpx
from typing import List, Dict, Any, Optional
from app.services.currency import get_usd_to_brl_rate

CHEAPSHARK_BASE_URL = "https://www.cheapshark.com/api/1.0"
USER_AGENT = "GameDealsVault/1.0 (puc-mvp-estudante@pucminas.br)"

# Cache em memoria para os nomes das lojas (evita bater na API a cada busca)
_STORES_CACHE: Dict[str, str] = {}


async def get_store_names() -> Dict[str, str]:
    """Retorna dicionario mapeando storeID -> storeName da CheapShark."""
    global _STORES_CACHE
    if _STORES_CACHE:
        return _STORES_CACHE

    try:
        async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=10.0) as client:
            resp = await client.get(f"{CHEAPSHARK_BASE_URL}/stores")
            if resp.status_code == 200:
                data = resp.json()
                _STORES_CACHE = {
                    item["storeID"]: item["storeName"]
                    for item in data
                    if "storeID" in item and "storeName" in item
                }
    except Exception as e:
        print(f"Erro ao carregar lojas da CheapShark: {e}")
        # Fallback com lojas mais populares caso ocorra erro
        _STORES_CACHE = {
            "1": "Steam",
            "2": "GamersGate",
            "3": "GreenManGaming",
            "7": "GOG",
            "11": "Humble Store",
            "15": "Fanatical",
            "25": "Epic Games Store"
        }

    return _STORES_CACHE


def _treat_deal_item(item: Dict[str, Any], stores_map: Dict[str, str], rate: float) -> Dict[str, Any]:
    """Trata e normaliza o registro bruto da CheapShark API com conversao para BRL."""
    store_id = str(item.get("storeID", ""))
    normal_price = float(item.get("normalPrice", 0.0) or 0.0)
    sale_price = float(item.get("salePrice", 0.0) or 0.0)
    savings = float(item.get("savings", 0.0) or 0.0)

    # Converte metacriticScore para inteiro se existir
    raw_metacritic = item.get("metacriticScore")
    metacritic = int(raw_metacritic) if raw_metacritic and raw_metacritic != "0" else None

    # Normaliza a URL do thumbnail
    thumb = item.get("thumb")
    if thumb:
        thumb = thumb.replace("\\/", "/")

    # Converte precos para Real brasileiro (BRL) usando a cotacao da AwesomeAPI
    normal_price_brl = round(normal_price * rate, 2)
    sale_price_brl = round(sale_price * rate, 2)

    return {
        "title": item.get("title", "Sem titulo"),
        "deal_id": item.get("dealID", ""),
        "store_id": store_id,
        "store_name": stores_map.get(store_id, f"Loja {store_id}"),
        "normal_price": round(normal_price, 2),
        "sale_price": round(sale_price, 2),
        "normal_price_brl": normal_price_brl,
        "sale_price_brl": sale_price_brl,
        "savings": round(savings, 1),
        "metacritic_score": metacritic,
        "steam_rating_text": item.get("steamRatingText"),
        "thumb": thumb
    }


async def fetch_deals(title: Optional[str] = None, limit: int = 15) -> List[Dict[str, Any]]:
    """Consulta ofertas da CheapShark, tratando e mapeando os resultados e cotacao BRL."""
    stores_map = await get_store_names()
    rate = await get_usd_to_brl_rate()
    
    params = {
        "pageSize": min(limit, 30),
        "sortBy": "Savings"
    }
    if title and title.strip():
        params["title"] = title.strip()

    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=10.0) as client:
        resp = await client.get(f"{CHEAPSHARK_BASE_URL}/deals", params=params)
        resp.raise_for_status()
        raw_deals = resp.json()

    treated_deals = [_treat_deal_item(deal, stores_map, rate) for deal in raw_deals]
    return treated_deals
