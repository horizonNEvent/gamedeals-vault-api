from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routes.games import router as games_router

# Cria as tabelas do SQLite automaticamente na inicialização
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GameDeals Vault API",
    description="""
    API REST para rastreamento de ofertas de jogos em lojas digitais de PC (Steam, Epic, GOG, etc.) 
    e gerenciamento de backlog/coleção gamer.
    
    Integrada à API externa pública CheapShark.
    Desenvolvida para o MVP de Componentização e Sistemas Web (PUC Minas).
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Habilita CORS para permitir comunicação fluida com o Front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas do módulo de jogos
app.include_router(games_router, prefix="/api")


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "service": "GameDeals Vault API",
        "version": "1.0.0",
        "docs": "/docs"
    }
