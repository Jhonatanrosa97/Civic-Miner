"from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt
import asyncio
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
pwd_context = CryptContext(schemes=[\"bcrypt\"], deprecated=\"auto\")
security = HTTPBearer()
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = \"HS256\"

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix=\"/api\")

# Models
class User(BaseModel):
    model_config = ConfigDict(extra=\"ignore\")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class CitySearch(BaseModel):
    city_name: str

class ScraperProgress(BaseModel):
    city_name: str
    progress: int
    status: str
    message: str

class DownloadedFile(BaseModel):
    model_config = ConfigDict(extra=\"ignore\")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    city_name: str
    file_name: str
    file_path: str
    user_id: str
    download_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    file_size: Optional[int] = None

class FileFilter(BaseModel):
    city_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode.update({\"exp\": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get(\"sub\")
        if email is None:
            raise HTTPException(status_code=401, detail=\"Token inválido\")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail=\"Token expirado\")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail=\"Token inválido\")
    
    user = await db.users.find_one({\"email\": email}, {\"_id\": 0})
    if user is None:
        raise HTTPException(status_code=401, detail=\"Usuário não encontrado\")
    
    if isinstance(user['created_at'], str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    return User(**user)

# Simular processo de scraper
async def simulate_scraper(city_name: str, user_id: str):
    \"\"\"Simula o processo de scraping com atualizações de progresso\"\"\"
    stages = [
        (10, \"Iniciando scraper...\"),
        (25, \"Conectando ao portal da cidade...\"),
        (40, \"Autenticando no sistema...\"),
        (60, \"Localizando contratos...\"),
        (75, \"Baixando PDF...\"),
        (90, \"Processando arquivo...\"),
        (100, \"Download concluído!\")
    ]
    
    for progress, message in stages:
        progress_data = {
            \"city_name\": city_name,
            \"progress\": progress,
            \"status\": \"em_andamento\" if progress < 100 else \"concluido\",
            \"message\": message,
            \"user_id\": user_id,
            \"timestamp\": datetime.now(timezone.utc).isoformat()
        }
        
        await db.scraper_progress.update_one(
            {\"city_name\": city_name, \"user_id\": user_id},
            {\"$set\": progress_data},
            upsert=True
        )
        
        await asyncio.sleep(random.uniform(0.5, 1.5))
    
    # Criar arquivo após conclusão
    file_name = f\"contrato_{city_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf\"
    file_data = DownloadedFile(
        city_name=city_name,
        file_name=file_name,
        file_path=f\"/downloads/{file_name}\",
        user_id=user_id,
        file_size=random.randint(500000, 2000000)
    )
    
    doc = file_data.model_dump()
    doc['download_date'] = doc['download_date'].isoformat()
    await db.downloaded_files.insert_one(doc)

# Auth routes
@api_router.post(\"/auth/register\", response_model=Token)
async def register(user_data: UserCreate):
    existing_user = await db.users.find_one({\"email\": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail=\"Email já cadastrado\")
    
    hashed_password = get_password_hash(user_data.password)
    user = User(email=user_data.email, name=user_data.name)
    
    user_doc = user.model_dump()
    user_doc['hashed_password'] = hashed_password
    user_doc['created_at'] = user_doc['created_at'].isoformat()
    
    await db.users.insert_one(user_doc)
    
    access_token = create_access_token(data={\"sub\": user.email})
    return Token(access_token=access_token, token_type=\"bearer\", user=user)

@api_router.post(\"/auth/login\", response_model=Token)
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({\"email\": credentials.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail=\"Email ou senha incorretos\")
    
    if not verify_password(credentials.password, user_doc['hashed_password']):
        raise HTTPException(status_code=401, detail=\"Email ou senha incorretos\")
    
    if isinstance(user_doc['created_at'], str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    user = User(**user_doc)
    access_token = create_access_token(data={\"sub\": user.email})
    return Token(access_token=access_token, token_type=\"bearer\", user=user)

@api_router.get(\"/auth/me\", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Scraper routes
@api_router.post(\"/scraper/start\")
async def start_scraper(
    search: CitySearch,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    # Limpar progresso anterior
    await db.scraper_progress.delete_many({
        \"city_name\": search.city_name,
        \"user_id\": current_user.id
    })
    
    # Iniciar scraper em background
    background_tasks.add_task(simulate_scraper, search.city_name, current_user.id)
    
    return {\"message\": \"Scraper iniciado\", \"city_name\": search.city_name}

@api_router.get(\"/scraper/progress/{city_name}\", response_model=ScraperProgress)
async def get_scraper_progress(
    city_name: str,
    current_user: User = Depends(get_current_user)
):
    progress_doc = await db.scraper_progress.find_one(
        {\"city_name\": city_name, \"user_id\": current_user.id},
        {\"_id\": 0}
    )
    
    if not progress_doc:
        return ScraperProgress(
            city_name=city_name,
            progress=0,
            status=\"nao_iniciado\",
            message=\"Scraper não iniciado\"
        )
    
    return ScraperProgress(**progress_doc)

@api_router.get(\"/cities/search\")
async def search_cities(
    q: str,
    current_user: User = Depends(get_current_user)
):
    \"\"\"Retorna sugestões de cidades para autocomplete\"\"\"
    cities = [
        \"São Paulo\", \"Rio de Janeiro\", \"Belo Horizonte\", \"Brasília\",
        \"Salvador\", \"Fortaleza\", \"Curitiba\", \"Manaus\", \"Recife\",
        \"Porto Alegre\", \"Belém\", \"Goiânia\", \"Guarulhos\", \"Campinas\",
        \"São Luís\", \"São Gonçalo\", \"Maceió\", \"Duque de Caxias\", \"Natal\",
        \"Teresina\", \"São Bernardo do Campo\", \"Nova Iguaçu\", \"João Pessoa\",
        \"São José dos Campos\", \"Santo André\", \"Ribeirão Preto\", \"Jaboatão dos Guararapes\",
        \"Osasco\", \"Uberlândia\", \"Sorocaba\", \"Contagem\", \"Aracaju\", \"Feira de Santana\",
        \"Cuiabá\", \"Joinville\", \"Londrina\", \"Aparecida de Goiânia\", \"Niterói\", \"Belford Roxo\",
        \"Campo Grande\", \"São José\", \"Santos\", \"Mauá\", \"Betim\", \"Diadema\", \"Jundiaí\"
    ]
    
    if not q:
        return cities[:10]
    
    filtered = [city for city in cities if q.lower() in city.lower()]
    return filtered[:10]

# Files routes
@api_router.get(\"/files\", response_model=List[DownloadedFile])
async def get_files(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    files = await db.downloaded_files.find(
        {\"user_id\": current_user.id},
        {\"_id\": 0}
    ).sort(\"download_date\", -1).limit(limit).to_list(limit)
    
    for file in files:
        if isinstance(file['download_date'], str):
            file['download_date'] = datetime.fromisoformat(file['download_date'])
    
    return files

@api_router.post(\"/files/filter\", response_model=List[DownloadedFile])
async def filter_files(
    filter_data: FileFilter,
    current_user: User = Depends(get_current_user)
):
    query = {\"user_id\": current_user.id}
    
    if filter_data.city_name:
        query[\"city_name\"] = {\"$regex\": filter_data.city_name, \"$options\": \"i\"}
    
    if filter_data.start_date:
        query[\"download_date\"] = {\"$gte\": filter_data.start_date.isoformat()}
    
    if filter_data.end_date:
        if \"download_date\" in query:
            query[\"download_date\"][\"$lte\"] = filter_data.end_date.isoformat()
        else:
            query[\"download_date\"] = {\"$lte\": filter_data.end_date.isoformat()}
    
    files = await db.downloaded_files.find(query, {\"_id\": 0}).sort(\"download_date\", -1).to_list(100)
    
    for file in files:
        if isinstance(file['download_date'], str):
            file['download_date'] = datetime.fromisoformat(file['download_date'])
    
    return files

@api_router.delete(\"/files/clear\")
async def clear_all_files(current_user: User = Depends(get_current_user)):
    result = await db.downloaded_files.delete_many({\"user_id\": current_user.id})
    return {\"message\": f\"{result.deleted_count} arquivos removidos\"}

@api_router.delete(\"/files/{file_id}\")
async def delete_file(file_id: str, current_user: User = Depends(get_current_user)):
    result = await db.downloaded_files.delete_one({
        \"id\": file_id,
        \"user_id\": current_user.id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=\"Arquivo não encontrado\")
    
    return {\"message\": \"Arquivo removido com sucesso\"}

@api_router.get(\"/stats\")
async def get_stats(current_user: User = Depends(get_current_user)):
    \"\"\"Retorna estatísticas do usuário\"\"\"
    total_files = await db.downloaded_files.count_documents({\"user_id\": current_user.id})
    
    cities = await db.downloaded_files.distinct(\"city_name\", {\"user_id\": current_user.id})
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    files_today = await db.downloaded_files.count_documents({
        \"user_id\": current_user.id,
        \"download_date\": {\"$gte\": today.isoformat()}
    })
    
    return {
        \"total_files\": total_files,
        \"total_cities\": len(cities),
        \"files_today\": files_today
    }

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=[\"*\"],
    allow_headers=[\"*\"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event(\"shutdown\")
async def shutdown_db_client():
    client.close()
"