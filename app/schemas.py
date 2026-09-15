from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CurrencyRateResponse(BaseModel):
    code: str = Field("USD", description="Moeda de origem")
    codein: str = Field("BRL", description="Moeda de destino")
    rate: float = Field(..., description="Taxa de cambio atual")
    source: str = Field("AwesomeAPI", description="Fonte da cotacao")
    timestamp: Optional[str] = Field(None, description="Data/hora da cotacao oficial")


class ExternalDealResponse(BaseModel):
    title: str = Field(..., description="Nome do jogo")
    deal_id: str = Field(..., description="ID unico da oferta na CheapShark")
    store_id: str = Field(..., description="ID da loja")
    store_name: str = Field(..., description="Nome amigavel da loja (ex: Steam, GOG)")
    normal_price: float = Field(..., description="Preco de tabela original em USD")
    sale_price: float = Field(..., description="Preco com desconto em USD")
    normal_price_brl: float = Field(..., description="Preco de tabela original convertido para BRL")
    sale_price_brl: float = Field(..., description="Preco com desconto convertido para BRL")
    savings: float = Field(..., description="Percentual de economia (ex: 75.0)")
    metacritic_score: Optional[int] = Field(None, description="Pontuacao do Metacritic (0-100)")
    steam_rating_text: Optional[str] = Field(None, description="Classificacao na Steam (ex: Very Positive)")
    thumb: Optional[str] = Field(None, description="URL da capa do jogo")


class GameCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Nome do jogo")
    deal_id: Optional[str] = Field(None, description="ID da oferta na CheapShark")
    store_id: Optional[str] = Field(None, description="ID da loja")
    store_name: Optional[str] = Field("Steam", description="Nome da loja onde foi encontrado")
    normal_price: float = Field(..., ge=0.0, description="Preco original em USD")
    sale_price: float = Field(..., ge=0.0, description="Preco promocional em USD")
    savings: Optional[float] = Field(0.0, ge=0.0, le=100.0, description="Percentual de economia")
    metacritic_score: Optional[int] = Field(None, ge=0, le=100, description="Nota Metacritic")
    thumb: Optional[str] = Field(None, description="URL da capa do jogo")
    status: Optional[str] = Field("wishlist", description="Status: wishlist, backlog, playing, completed")
    user_rating: Optional[int] = Field(0, ge=0, le=5, description="Avaliacao pessoal de 1 a 5 estrelas")
    notes: Optional[str] = Field("", description="Anotacoes pessoais do usuario")


class GameUpdate(BaseModel):
    status: Optional[str] = Field(None, description="Novo status: wishlist, backlog, playing, completed")
    user_rating: Optional[int] = Field(None, ge=0, le=5, description="Nova avaliacao pessoal (0-5 estrelas)")
    notes: Optional[str] = Field(None, description="Novas anotacoes do jogador")


class GameResponse(BaseModel):
    id: int
    title: str
    deal_id: Optional[str] = None
    store_id: Optional[str] = None
    store_name: Optional[str] = None
    normal_price: float
    sale_price: float
    normal_price_brl: Optional[float] = None
    sale_price_brl: Optional[float] = None
    savings_brl: Optional[float] = None
    savings: float
    metacritic_score: Optional[int] = None
    thumb: Optional[str] = None
    status: str
    user_rating: int
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CollectionStats(BaseModel):
    total_games: int = Field(..., description="Quantidade total de jogos cadastrados")
    total_saved_usd: float = Field(..., description="Economia acumulada total em dolares")
    total_saved_brl: float = Field(..., description="Economia acumulada total em reais (BRL)")
    usd_brl_rate: float = Field(..., description="Cotacao comercial atual do Dolar (AwesomeAPI)")
    average_savings_percent: float = Field(..., description="Media do percentual de desconto da colecao")
    completed_games: int = Field(..., description="Quantidade de jogos finalizados")
    wishlist_games: int = Field(..., description="Quantidade de jogos na lista de desejos")
    backlog_games: int = Field(..., description="Quantidade de jogos na fila do backlog")
    playing_games: int = Field(..., description="Quantidade de jogos atualmente jogando")


class CollectionListResponse(BaseModel):
    items: List[GameResponse]
    stats: CollectionStats
