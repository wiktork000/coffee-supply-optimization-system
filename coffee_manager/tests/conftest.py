from __future__ import annotations

import os
import uuid as _uuid

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("JWT_SECRET", "test-secret-for-pytest")
os.environ.setdefault("OPTIMIZER_URL", "http://optimizer.test")

import sqlalchemy.dialects.postgresql as _pg
from sqlalchemy import CHAR, JSON
from sqlalchemy.types import TypeDecorator


class _UUIDType(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def __init__(self, as_uuid: bool = False, **kw):
        self.as_uuid = as_uuid
        super().__init__(length=36)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, _uuid.UUID):
            return str(value)
        return str(_uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if self.as_uuid and not isinstance(value, _uuid.UUID):
            return _uuid.UUID(value)
        return value


class _JSONBType(TypeDecorator):
    impl = JSON
    cache_ok = True


_pg.UUID = _UUIDType  # type: ignore[assignment]
_pg.JSONB = _JSONBType  # type: ignore[assignment]

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from passlib.context import CryptContext  # noqa: E402

from coffee_manager import auth as auth_module  # noqa: E402

_test_ctx = CryptContext(schemes=["pbkdf2_sha256"], pbkdf2_sha256__rounds=1000)
auth_module.pwd_context = _test_ctx

from coffee_manager.database import Base, get_db  # noqa: E402
from coffee_manager.main import app  # noqa: E402
from coffee_manager.models import Distributor, User  # noqa: E402


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture()
def db(session_factory) -> Session:
    s = session_factory()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture()
def client(engine, session_factory, monkeypatch):
    import coffee_manager.main as main_module

    monkeypatch.setattr(main_module, "engine", engine)

    def _override_get_db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def user_factory(db):
    """Create a User and return it. Uses a deliberately weak hash override
    elsewhere for speed where applicable, but here uses real bcrypt."""

    def _make(
        username: str = "alice", password: str = "pw12345", role: str = "coordinator"
    ) -> User:
        u = User(
            name=username,
            password_hash=auth_module.hash_password(password),
            role=role,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        return u

    return _make


@pytest.fixture()
def auth_headers(user_factory):
    user = user_factory()
    token = auth_module.create_access_token(str(user.id), user.role)
    return {"Authorization": f"Bearer {token}"}, user


@pytest.fixture()
def distributor_factory(db):
    def _make(username: str = "Acme") -> Distributor:
        d = Distributor(
            username=username,
            contact_email=f"{username.lower()}@example.com",
            contact_phone=f"+48-{abs(hash(username)) % 1_000_000_000:09d}",
        )
        db.add(d)
        db.commit()
        db.refresh(d)
        return d

    return _make
