import asyncio
from aiohttp import web
from sqlalchemy import select, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime, timedelta
import jwt
from passlib.hash import pbkdf2_sha256 as sha256

DATABASE_URL = 'sqlite+aiosqlite:///./ads.db'
JWT_SECRET = '123867'
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 3600

Base = declarative_base()


# Моделька юзера
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)


# Объявление
class Ad(Base):
    __tablename__ = 'ads'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner = relationship('User', back_populates='ads')


User.ads = relationship('Ad', order_by=Ad.id, back_populates='owner')

# Установите асинхронный движок и сессию
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


# Генераторы хэшей и прочего всякого + JWT токены
def generate_password_hash(password):
    return sha256.hash(password)


def check_password(hash, password):
    return sha256.verify(password, hash)


def create_access_token(identity):
    payload = {
        'sub': str(identity),  # Преобразуем identity в строку
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.DecodeError:
        return None


# Маршруты
async def register(request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return web.json_response({"message": "Email и пароль обязательны"}, status=400)

    async with async_session() as session:
        stmt = select(User).filter_by(email=email)
        result = await session.execute(stmt)
        if result.scalars().first():
            return web.json_response({"message": "Пользователь с таким email уже существует"}, status=400)

        user = User(email=email, password_hash=generate_password_hash(password))
        session.add(user)
        await session.commit()

    return web.json_response({"message": "Пользователь зарегистрирован"}, status=201)


async def login(request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return web.json_response({"message": "Email и пароль обязательны"}, status=400)

    async with async_session() as session:
        stmt = select(User).filter_by(email=email)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if user is None or not check_password(user.password_hash, password):
            return web.json_response({"message": "Неверные учётные данные"}, status=401)

        access_token = create_access_token(user.id)
        return web.json_response({"access_token": access_token}, status=200)


async def create_ad(request):
    auth_header = request.headers.get('Authorization', None)
    if not auth_header:
        return web.json_response({"message": "Необходима авторизация"}, status=401)

    token = auth_header.split(" ")[1]
    user_id = decode_access_token(token)

    if not user_id:
        return web.json_response({"message": "Недействительный или просроченный токен"}, status=401)

    data = await request.json()
    title = data.get("title")
    description = data.get("description")

    if not title or not description:
        return web.json_response({"message": "Недостаточно данных для создания объявления"}, status=400)

    async with async_session() as session:
        ad = Ad(title=title, description=description, owner_id=user_id)
        session.add(ad)
        await session.commit()

        return web.json_response({
            "message": "Объявление создано",
            "ad": {
                "id": ad.id,
                "title": ad.title,
                "description": ad.description,
                "created_at": ad.created_at.isoformat(),
                "owner_id": ad.owner_id
            }
        }, status=201)


async def get_ad(request):
    ad_id = request.match_info.get('ad_id')

    async with async_session() as session:
        stmt = select(Ad).filter_by(id=ad_id)
        result = await session.execute(stmt)
        ad = result.scalars().first()

        if not ad:
            return web.json_response({"message": "Объявление не найдено"}, status=404)

        return web.json_response({
            "id": ad.id,
            "title": ad.title,
            "description": ad.description,
            "created_at": ad.created_at.isoformat(),
            "owner_id": ad.owner_id
        }, status=200)


async def delete_ad(request):
    auth_header = request.headers.get('Authorization', None)
    if not auth_header:
        return web.json_response({"message": "Необходима авторизация"}, status=401)

    token = auth_header.split(" ")[1]
    user_id = decode_access_token(token)

    if not user_id:
        return web.json_response({"message": "Недействительный или просроченный токен"}, status=401)

    ad_id = request.match_info.get('ad_id')

    async with async_session() as session:
        stmt = select(Ad).filter_by(id=ad_id, owner_id=user_id)
        result = await session.execute(stmt)
        ad = result.scalars().first()

        if not ad:
            return web.json_response({"message": "Объявление не найдено или вы не являетесь владельцем"}, status=403)

        await session.delete(ad)
        await session.commit()
        return web.json_response({"message": "Объявление удалено"}, status=200)


# Роутинг
app = web.Application()
app.router.add_post('/register', register)
app.router.add_post('/login', login)
app.router.add_post('/ads', create_ad)
app.router.add_get(r'/ads/{ad_id:\d+}', get_ad)
app.router.add_delete(r'/ads/{ad_id:\d+}', delete_ad)


async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == '__main__':
    asyncio.run(setup_db())
    web.run_app(app, host='0.0.0.0', port=5000)
