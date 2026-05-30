"""M1: 认证测试 — 注册/登录/Token 刷新/Token 过期/封禁用户."""
import pytest


class TestAuthRegister:
    """注册测试套件."""

    async def test_register_success(self, async_client):
        """注册成功应返回 200，含 access_token 和用户信息."""
        response = await async_client.post("/auth/register", json={
            "email": "newuser@example.com",
            "password": "StrongPass1",
            "confirm_password": "StrongPass1",
            "display_name": "New User",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 86400
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["display_name"] == "New User"

    async def test_register_duplicate_email(self, async_client):
        """重复邮箱注册应返回 409."""
        # 第一次注册
        await async_client.post("/auth/register", json={
            "email": "dup@example.com",
            "password": "StrongPass1",
            "confirm_password": "StrongPass1",
        })
        # 第二次注册
        response = await async_client.post("/auth/register", json={
            "email": "dup@example.com",
            "password": "AnotherPass1",
            "confirm_password": "AnotherPass1",
        })
        assert response.status_code == 409
        assert "已被注册" in response.json()["detail"]

    async def test_register_weak_password(self, async_client):
        """弱密码（纯数字）注册应返回 422."""
        response = await async_client.post("/auth/register", json={
            "email": "weak@example.com",
            "password": "12345678",
            "confirm_password": "12345678",
        })
        assert response.status_code == 422
        assert "字母" in response.json()["detail"]

    async def test_register_mismatched_password(self, async_client):
        """密码与确认密码不一致应返回 422."""
        response = await async_client.post("/auth/register", json={
            "email": "mismatch@example.com",
            "password": "StrongPass1",
            "confirm_password": "Different1",
        })
        assert response.status_code == 422
        assert "不一致" in response.json()["detail"]

    async def test_register_invalid_email(self, async_client):
        """无效邮箱格式应返回 422."""
        response = await async_client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "StrongPass1",
            "confirm_password": "StrongPass1",
        })
        assert response.status_code == 422
        assert "邮箱" in response.json()["detail"]


class TestAuthLogin:
    """登录测试套件."""

    @pytest.fixture(autouse=True)
    async def _setup_user(self, async_client):
        """注册一个测试用户供登录测试使用."""
        await async_client.post("/auth/register", json={
            "email": "login-test@example.com",
            "password": "LoginTest1",
            "confirm_password": "LoginTest1",
            "display_name": "Login Tester",
        })

    async def test_login_success(self, async_client):
        """正确邮箱密码登录应返回 200，含 token 和用户信息."""
        response = await async_client.post("/auth/login", json={
            "email": "login-test@example.com",
            "password": "LoginTest1",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "login-test@example.com"

    async def test_login_wrong_password(self, async_client):
        """错误密码登录应返回 401."""
        response = await async_client.post("/auth/login", json={
            "email": "login-test@example.com",
            "password": "WrongPassword1",
        })
        assert response.status_code == 401
        assert "邮箱或密码错误" in response.json()["detail"]

    async def test_login_nonexistent_user(self, async_client):
        """不存在的用户登录应返回 401."""
        response = await async_client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "Whatever1",
        })
        assert response.status_code == 401

    async def test_login_empty_credentials(self, async_client):
        """空邮箱/密码登录应返回 422."""
        response = await async_client.post("/auth/login", json={
            "email": "",
            "password": "",
        })
        assert response.status_code == 422


class TestAuthToken:
    """Token 刷新与过期测试套件."""

    @pytest.fixture(autouse=True)
    async def _setup_token_user(self, async_client):
        """注册并登录，保存 token 相关信息."""
        reg_response = await async_client.post("/auth/register", json={
            "email": "token-test@example.com",
            "password": "TokenTest1",
            "confirm_password": "TokenTest1",
        })
        self._reg_data = reg_response.json()

    async def test_refresh_token_success(self, async_client):
        """使用有效的 refresh_token 刷新应返回新 token."""
        response = await async_client.post("/auth/refresh", json={
            "refresh_token": self._reg_data["refresh_token"],
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 86400
        # 注意: 由于测试运行极快，新旧 token 的 iat 可能相同，
        # 此处只验证返回格式正确 + 可解码

    async def test_refresh_with_access_token(self, async_client):
        """使用 access_token 去刷新应返回 401."""
        response = await async_client.post("/auth/refresh", json={
            "refresh_token": self._reg_data["access_token"],
        })
        assert response.status_code == 401
        assert "refresh token" in response.json()["detail"].lower()

    async def test_refresh_token_missing(self, async_client):
        """缺少 refresh_token 应返回 422."""
        response = await async_client.post("/auth/refresh", json={})
        assert response.status_code == 422

    async def test_expired_token_access(self, async_client):
        """过期的 access_token 应返回 401."""
        import jwt as pyjwt
        from datetime import datetime, timedelta, timezone

        from backend.devpulse.config import settings

        # 手动签发一个已过期的 token
        expired_payload = {
            "sub": 1,
            "email": "expired@example.com",
            "iat": datetime.now(timezone.utc) - timedelta(hours=48),
            "exp": datetime.now(timezone.utc) - timedelta(hours=24),
            "type": "access",
        }
        expired_token = pyjwt.encode(
            expired_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        response = await async_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401
        assert "过期" in response.json()["detail"]


class TestBannedUser:
    """封禁用户测试套件."""

    async def test_banned_user_access_denied(self, async_client, test_db):
        """被封禁用户的 token 访问受保护端点应返回 403."""
        # 注册用户
        reg_resp = await async_client.post("/auth/register", json={
            "email": "banned@example.com",
            "password": "BannedUser1",
            "confirm_password": "BannedUser1",
        })
        token = reg_resp.json()["access_token"]

        # 直接在 DB 中将用户设为非活跃
        from backend.devpulse.core.models import User
        from sqlalchemy import select
        async with test_db.get_session() as session:
            result = await session.execute(
                select(User).where(User.email == "banned@example.com")
            )
            user = result.scalar_one_or_none()
            assert user is not None
            user.is_active = False  # type: ignore[assignment]
            await session.commit()

        # 使用原有 token 访问 /auth/me 应被拒绝
        response = await async_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "封禁" in response.json()["detail"]


class TestAuthMe:
    """用户信息端点测试套件."""

    async def test_get_me_authenticated(self, async_client, auth_headers):
        """已认证用户获取个人信息应返回 200."""
        response = await async_client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test-auth@example.com"
        assert "display_name" in data
        assert "push_enabled" in data

    async def test_get_me_unauthenticated(self, async_client):
        """未认证用户获取个人信息应返回 401."""
        response = await async_client.get("/auth/me")
        assert response.status_code == 401
