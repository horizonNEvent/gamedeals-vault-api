from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from app.database import get_db
from app.models import GameItem
from app.schemas import (
    GameCreate,
    GameUpdate,
    GameResponse,
    CollectionListResponse,
    CollectionStats,
    ExternalDealResponse,
    CurrencyRateResponse
)
from app.services.cheapshark import fetch_deals
from app.services.currency import get_usd_to_brl_rate, get_cached_rate_info

router = APIRouter(tags=["Games & Deals"])


@router.get(
    "/currency/rate",
    response_model=CurrencyRateResponse,
    summary="Consultar cotacao atual USD para BRL (AwesomeAPI)",
    description="Retorna a cotacao comercial oficial do Dolar em tempo real consumida da AwesomeAPI com informacoes de cache."
)
async def get_currency_rate():
    rate = await get_usd_to_brl_rate()
    info = get_cached_rate_info()
    return CurrencyRateResponse(
        code="USD",
        codein="BRL",
        rate=rate,
        source="AwesomeAPI",
        timestamp=info.get("timestamp")
    )


@router.get(
    "/external/deals",
    response_model=List[ExternalDealResponse],
    summary="Consultar ofertas na CheapShark API (Externa)",
    description="Consulta promocoes diretamente da API publica externa CheapShark, tratando lojas e convertendo precos para BRL."
)
async def search_external_deals(
    title: Optional[str] = Query(None, description="Nome do jogo a pesquisar (deixe vazio para melhores ofertas gerais)"),
    limit: int = Query(12, ge=1, le=30, description="Quantidade maxima de ofertas a retornar")
):
    try:
        deals = await fetch_deals(title=title, limit=limit)
        return deals
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao comunicar com a API CheapShark: {str(e)}"
        )


@router.get(
    "/games",
    response_model=CollectionListResponse,
    summary="Listar jogos da colecao e metricas consolidadas (USD e BRL)",
    description="Retorna os jogos salvos no banco local com suporte a filtros por status, pesquisa por titulo, cotacao atual da AwesomeAPI e metricas convertidas em BRL."
)
async def list_collection(
    status_filter: Optional[str] = Query(None, description="Filtrar por status: wishlist, backlog, playing, completed"),
    search: Optional[str] = Query(None, description="Filtrar pelo titulo do jogo"),
    sort_by: Optional[str] = Query("latest", description="Ordenacao: latest, savings, rating, price"),
    db: Session = Depends(get_db)
):
    rate = await get_usd_to_brl_rate()
    query = db.query(GameItem)

    if status_filter and status_filter.strip():
        query = query.filter(GameItem.status == status_filter.strip().lower())

    if search and search.strip():
        query = query.filter(GameItem.title.ilike(f"%{search.strip()}%"))

    # Ordenacao
    if sort_by == "savings":
        query = query.order_by(desc(GameItem.savings))
    elif sort_by == "rating":
        query = query.order_by(desc(GameItem.user_rating))
    elif sort_by == "price":
        query = query.order_by(asc(GameItem.sale_price))
    else:
        query = query.order_by(desc(GameItem.id))

    db_items = query.all()

    # Formata cada item adicionando os precos convertidos em BRL
    response_items = []
    for item in db_items:
        normal_brl = round(item.normal_price * rate, 2)
        sale_brl = round(item.sale_price * rate, 2)
        savings_brl = round(max(0.0, normal_brl - sale_brl), 2)
        
        resp_item = GameResponse(
            id=item.id,
            title=item.title,
            deal_id=item.deal_id,
            store_id=item.store_id,
            store_name=item.store_name,
            normal_price=item.normal_price,
            sale_price=item.sale_price,
            normal_price_brl=normal_brl,
            sale_price_brl=sale_brl,
            savings_brl=savings_brl,
            savings=item.savings,
            metacritic_score=item.metacritic_score,
            thumb=item.thumb,
            status=item.status,
            user_rating=item.user_rating,
            notes=item.notes,
            created_at=item.created_at,
            updated_at=item.updated_at
        )
        response_items.append(resp_item)

    # Calculo de metricas da colecao
    all_items = db.query(GameItem).all()
    total_games = len(all_items)
    
    total_saved_usd = sum(max(0.0, item.normal_price - item.sale_price) for item in all_items)
    total_saved_brl = round(total_saved_usd * rate, 2)
    avg_savings = (sum(item.savings for item in all_items) / total_games) if total_games > 0 else 0.0

    stats = CollectionStats(
        total_games=total_games,
        total_saved_usd=round(total_saved_usd, 2),
        total_saved_brl=total_saved_brl,
        usd_brl_rate=rate,
        average_savings_percent=round(avg_savings, 1),
        completed_games=sum(1 for item in all_items if item.status == "completed"),
        wishlist_games=sum(1 for item in all_items if item.status == "wishlist"),
        backlog_games=sum(1 for item in all_items if item.status == "backlog"),
        playing_games=sum(1 for item in all_items if item.status == "playing"),
    )

    return CollectionListResponse(items=response_items, stats=stats)


@router.post(
    "/games",
    response_model=GameResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar jogo a colecao / lista de desejos",
    description="Persiste um jogo no banco de dados SQLite com dados da oferta e status inicial."
)
async def add_game_to_collection(payload: GameCreate, db: Session = Depends(get_db)):
    # Verifica se a oferta ou titulo identico ja foi adicionado
    existing = db.query(GameItem).filter(
        (GameItem.title.ilike(payload.title)) & 
        (GameItem.status == payload.status)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este jogo ja esta registrado com o mesmo status na sua colecao."
        )

    # Calcula percentual de economia se nao informado
    savings = payload.savings
    if savings == 0.0 and payload.normal_price > 0:
        savings = round(((payload.normal_price - payload.sale_price) / payload.normal_price) * 100.0, 1)

    new_item = GameItem(
        title=payload.title,
        deal_id=payload.deal_id,
        store_id=payload.store_id,
        store_name=payload.store_name,
        normal_price=payload.normal_price,
        sale_price=payload.sale_price,
        savings=savings,
        metacritic_score=payload.metacritic_score,
        thumb=payload.thumb,
        status=payload.status or "wishlist",
        user_rating=payload.user_rating or 0,
        notes=payload.notes or ""
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    rate = await get_usd_to_brl_rate()
    normal_brl = round(new_item.normal_price * rate, 2)
    sale_brl = round(new_item.sale_price * rate, 2)
    savings_brl = round(max(0.0, normal_brl - sale_brl), 2)

    return GameResponse(
        id=new_item.id,
        title=new_item.title,
        deal_id=new_item.deal_id,
        store_id=new_item.store_id,
        store_name=new_item.store_name,
        normal_price=new_item.normal_price,
        sale_price=new_item.sale_price,
        normal_price_brl=normal_brl,
        sale_price_brl=sale_brl,
        savings_brl=savings_brl,
        savings=new_item.savings,
        metacritic_score=new_item.metacritic_score,
        thumb=new_item.thumb,
        status=new_item.status,
        user_rating=new_item.user_rating,
        notes=new_item.notes,
        created_at=new_item.created_at,
        updated_at=new_item.updated_at
    )


@router.put(
    "/games/{game_id}",
    response_model=GameResponse,
    summary="Atualizar status, avaliacao ou anotacoes de um jogo",
    description="Permite ao usuario atualizar o status do jogo (ex: de wishlist para backlog ou completed), sua nota (1-5) e impressoes."
)
async def update_game_in_collection(
    game_id: int,
    payload: GameUpdate,
    db: Session = Depends(get_db)
):
    item = db.query(GameItem).filter(GameItem.id == game_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jogo com ID {game_id} nao encontrado na colecao."
        )

    if payload.status is not None:
        item.status = payload.status
    if payload.user_rating is not None:
        item.user_rating = payload.user_rating
    if payload.notes is not None:
        item.notes = payload.notes

    db.commit()
    db.refresh(item)

    rate = await get_usd_to_brl_rate()
    normal_brl = round(item.normal_price * rate, 2)
    sale_brl = round(item.sale_price * rate, 2)
    savings_brl = round(max(0.0, normal_brl - sale_brl), 2)

    return GameResponse(
        id=item.id,
        title=item.title,
        deal_id=item.deal_id,
        store_id=item.store_id,
        store_name=item.store_name,
        normal_price=item.normal_price,
        sale_price=item.sale_price,
        normal_price_brl=normal_brl,
        sale_price_brl=sale_brl,
        savings_brl=savings_brl,
        savings=item.savings,
        metacritic_score=item.metacritic_score,
        thumb=item.thumb,
        status=item.status,
        user_rating=item.user_rating,
        notes=item.notes,
        created_at=item.created_at,
        updated_at=item.updated_at
    )


@router.delete(
    "/games/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover jogo da colecao",
    description="Exclui definitivamente o jogo do banco de dados SQLite."
)
def delete_game_from_collection(game_id: int, db: Session = Depends(get_db)):
    item = db.query(GameItem).filter(GameItem.id == game_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jogo com ID {game_id} nao encontrado na colecao."
        )

    db.delete(item)
    db.commit()
    return None
