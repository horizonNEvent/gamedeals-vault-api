from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from app.database import Base


class GameItem(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    deal_id = Column(String(255), nullable=True)
    store_id = Column(String(50), nullable=True)
    store_name = Column(String(100), nullable=True, default="Desconhecida")
    normal_price = Column(Float, nullable=False, default=0.0)
    sale_price = Column(Float, nullable=False, default=0.0)
    savings = Column(Float, nullable=False, default=0.0)
    metacritic_score = Column(Integer, nullable=True)
    thumb = Column(String(500), nullable=True)
    
    # Status no backlog do jogador: wishlist, backlog, playing, completed
    status = Column(String(50), nullable=False, default="wishlist")
    
    # Avaliação de 1 a 5 estrelas (0 se não avaliado)
    user_rating = Column(Integer, nullable=False, default=0)
    
    # Anotações e impressões do jogador
    notes = Column(Text, nullable=True, default="")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
