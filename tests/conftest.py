import pytest
from core.settings import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models.base import Base
from fastapi.testclient import TestClient
from database.connection import get_db
from main import app
from models.user import User
from core.security import hash_password, return_token
from models.profile import Profile
from models.job import Job
from unittest.mock import MagicMock, patch
from fastapi import BackgroundTasks
from models.contract import Contract
from models.conversation import Conversation
import stripe

engine = create_engine(settings.tests_database_url)
LocalSessionTests = sessionmaker(bind=engine, autoflush=False, autocommit= False)


@pytest.fixture(scope="session", autouse=True)
def setup_base():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = LocalSessionTests(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture()
def client(db_session):
    def db_override():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = db_override

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def create_admin_professional_client(db_session: Session):
    hashed_passsword = hash_password("Test123*")
    admin = User(
        username = "test1",
        email = "test@test1.com",
        role = "ADMIN",
        hashed_password = hashed_passsword,)
    client = User(
        username = "test2",
        email = "test@test2.com",
        role = "CLIENT",
        hashed_password = hashed_passsword,)
    professional = User(
        username = "test3",
        email = "test@test3.com",
        role = "PROFESSIONAL",
        hashed_password = hashed_passsword, )
    client_2 = User(
        username = "test4",
        email = "test@test4.com",
        role = "CLIENT",
        hashed_password = hashed_passsword,)
    
    db_session.add_all([admin, client, professional, client_2])
    db_session.commit()

    return {
        "admin": admin,
        "client": client,
        "professional": professional,
        "client_2": client_2
    }
@pytest.fixture()
def client_2_token(create_admin_professional_client):
    user = create_admin_professional_client["client_2"]

    return return_token({"sub": user.user_id})
@pytest.fixture()
def admin_token(create_admin_professional_client):
    user = create_admin_professional_client["admin"]

    return return_token({"sub": user.user_id})
@pytest.fixture()
def client_token(create_admin_professional_client):
    user = create_admin_professional_client["client"]

    return return_token({"sub": user.user_id})

@pytest.fixture()
def professional_token(create_admin_professional_client):
    user = create_admin_professional_client["professional"]

    return return_token({"sub": user.user_id})

@pytest.fixture()
def admin_client(client, admin_token):
    client.headers.update({"Authorization": f"Bearer {admin_token}"})

    yield client

    client.headers.pop("Authorization", None)
@pytest.fixture()
def client_client(client, client_token):
    client.headers.update({"Authorization": f"Bearer {client_token}"})

    yield client

    client.headers.pop("Authorization", None)
@pytest.fixture()
def client_2_client(client_2_token, client):
    client.headers.update({"Authorization": f"Bearer {client_2_token}"})

    yield client

    client.headers.pop("Authorization", None)
@pytest.fixture()
def professional_client(client, professional_token):
    client.headers.update({"Authorization": f"Bearer {professional_token}"})

    yield client

    client.headers.pop("Authorization", None)

@pytest.fixture()
def create_job(create_admin_professional_client, db_session):
    db_session.flush()
    user = create_admin_professional_client["client"]
    new_job = Job(
        client_id = user.user_id,
        title = "TEST",
        description = "TEST",
        budget = 200        )
    
    db_session.add(new_job)

    db_session.commit()
    db_session.flush()

    return new_job.job_id

@pytest.fixture()
def professional_profile(create_admin_professional_client, db_session: Session):
    user = create_admin_professional_client["professional"]
    new_profile = Profile(user_id = user.user_id)
    db_session.add(new_profile)
    db_session.commit()

@pytest.fixture()
def mock_background():
   background =  MagicMock(spec= BackgroundTasks)
   return background

@pytest.fixture()
def create_contract(create_admin_professional_client, db_session, create_job):
    buyer = create_admin_professional_client["client"]
    seller = create_admin_professional_client["professional"]
    contract = Contract(
        job_id = create_job,
        buyer_id=buyer.user_id, 
        seller_id=seller.user_id, 
        status="PENDING_PAYMENT",
        amount = 200,
        detail = "TEST"
    )
    db_session.add(contract)
    db_session.commit()
    return contract

@pytest.fixture()
def create_conversation(create_admin_professional_client, db_session):
    user_a= create_admin_professional_client["client"]
    user_b= create_admin_professional_client["professional"]
    new_conversation = Conversation(
        conversation_id = "conv_123",
        user_id_a = user_a.user_id,
        user_id_b = user_b.user_id
    )
    db_session.add(new_conversation)
    db_session.commit()

