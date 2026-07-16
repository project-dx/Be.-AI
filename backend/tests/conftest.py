from collections.abc import Generator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models import Profile, User, UserDailyReport

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    Base.metadata.create_all(engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_user(db: Session, email: str, role: str, display_name: str,
              assigned_staff_id: int | None = None, password: str = "Password1!") -> User:
    user = User(email=email, password_hash=hash_password(password), role=role)
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id, display_name=display_name, assigned_staff_id=assigned_staff_id))
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def admin(db: Session) -> User:
    return make_user(db, "admin@test.com", "admin", "管理者")


@pytest.fixture()
def staff(db: Session) -> User:
    return make_user(db, "staff@test.com", "staff", "スタッフA")


@pytest.fixture()
def other_staff(db: Session) -> User:
    return make_user(db, "staff2@test.com", "staff", "スタッフB")


@pytest.fixture()
def member(db: Session, staff: User) -> User:
    """スタッフAが担当する利用者"""
    return make_user(db, "member@test.com", "user", "利用者1", assigned_staff_id=staff.id)


@pytest.fixture()
def other_member(db: Session, other_staff: User) -> User:
    """スタッフBが担当する別の利用者"""
    return make_user(db, "member2@test.com", "user", "利用者2", assigned_staff_id=other_staff.id)


def login_headers(client: TestClient, email: str, password: str = "Password1!") -> dict[str, str]:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def add_report(db: Session, user_id: int, d: date, *, mood: int = 3, sleep: float = 7.0,
               bedtime: str = "23:00", wake: str = "06:30", quality: int = 3,
               stress: int = 3, fatigue: int = 3, social: int = 3,
               success: str | None = None, difficulty: str | None = None,
               tomorrow_goal: str | None = "目標", is_draft: bool = False) -> UserDailyReport:
    report = UserDailyReport(
        user_id=user_id, report_date=d, mood=mood, sleep_hours=sleep,
        bedtime=bedtime, wake_time=wake, sleep_quality=quality,
        breakfast_status="eaten", lunch_status="eaten", dinner_status="eaten",
        exercise_minutes=30, work_study_minutes=240,
        stress_level=stress, fatigue_level=fatigue, social_level=social,
        achievement="できた", success_experience=success, difficulty=difficulty,
        tomorrow_goal=tomorrow_goal, is_draft=is_draft,
    )
    db.add(report)
    db.commit()
    return report


def add_week_reports(db: Session, user_id: int, end: date, days: int = 7, **kwargs) -> None:
    for i in range(days):
        add_report(db, user_id, end - timedelta(days=i), **kwargs)
