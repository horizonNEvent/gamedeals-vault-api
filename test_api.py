from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    print("[OK] Health check OK")


def test_currency_rate():
    response = client.get("/api/currency/rate")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "USD"
    assert data["codein"] == "BRL"
    assert data["rate"] > 0
    print(f"[OK] AwesomeAPI Cotacao OK: 1 USD = R$ {data['rate']}")


def test_external_deals():
    response = client.get("/api/external/deals?title=batman&limit=2")
    assert response.status_code == 200
    deals = response.json()
    assert len(deals) > 0
    assert "store_name" in deals[0]
    assert "sale_price" in deals[0]
    assert "sale_price_brl" in deals[0]
    print(f"[OK] CheapShark Deals OK: '{deals[0]['title']}' por ${deals[0]['sale_price']} (R$ {deals[0]['sale_price_brl']}) na {deals[0]['store_name']}")


def test_crud_lifecycle():
    # 1. POST: Cria novo item
    payload = {
        "title": "The Witcher 3: Wild Hunt - Complete Edition",
        "deal_id": "test-deal-123",
        "store_id": "1",
        "store_name": "Steam",
        "normal_price": 49.99,
        "sale_price": 12.49,
        "savings": 75.0,
        "metacritic_score": 93,
        "thumb": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/292030/capsule_231x87.jpg",
        "status": "wishlist",
        "user_rating": 0,
        "notes": "Comprar assim que entrar em promocao maior!"
    }
    post_res = client.post("/api/games", json=payload)
    assert post_res.status_code == 201
    created = post_res.json()
    game_id = created["id"]
    assert created["title"] == payload["title"]
    assert "sale_price_brl" in created
    print(f"[OK] POST /api/games OK: Jogo criado com ID {game_id} (R$ {created['sale_price_brl']})")

    # 2. GET: Lista jogos e estatisticas
    get_res = client.get("/api/games")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["stats"]["total_games"] >= 1
    assert data["stats"]["total_saved_usd"] >= 37.0
    assert data["stats"]["total_saved_brl"] > 0
    print(f"[OK] GET /api/games OK: Total = {data['stats']['total_games']}, Economia = ${data['stats']['total_saved_usd']} (R$ {data['stats']['total_saved_brl']})")

    # 3. PUT: Atualiza status e avaliacao
    update_payload = {
        "status": "completed",
        "user_rating": 5,
        "notes": "Obra de arte! Finalizado com 100 horas."
    }
    put_res = client.put(f"/api/games/{game_id}", json=update_payload)
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["status"] == "completed"
    assert updated["user_rating"] == 5
    print(f"[OK] PUT /api/games/{game_id} OK: Status '{updated['status']}', nota {updated['user_rating']} estrelas")

    # 4. DELETE: Exclui o item
    del_res = client.delete(f"/api/games/{game_id}")
    assert del_res.status_code == 204
    print(f"[OK] DELETE /api/games/{game_id} OK")

    # 5. Verifica se realmente foi removido
    verify_res = client.get(f"/api/games")
    remaining_ids = [item["id"] for item in verify_res.json()["items"]]
    assert game_id not in remaining_ids
    print("[OK] Confirmacao pos-exclusao OK")


if __name__ == "__main__":
    print("Iniciando bateria de testes do Back-End...")
    test_health_check()
    test_currency_rate()
    test_external_deals()
    test_crud_lifecycle()
    print(">>> TODOS OS TESTES PASSARAM COM SUCESSO! <<<")
