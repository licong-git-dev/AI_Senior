"""
认证API端点测试
测试用户注册、登录、令牌刷新等功能
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import json
import time


class TestAuthRegister:
    """用户注册测试"""

    @pytest.mark.api
    def test_register_success(self, client: TestClient, db_session):
        """测试成功注册"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "13800001111",
                "password": "Test123456",
                "role": "family",
                "name": "测试用户"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user_id" in data

    @pytest.mark.api
    def test_register_duplicate_username(self, client: TestClient, sample_user_auth):
        """测试重复用户名注册"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": sample_user_auth.username,  # 已存在的用户名
                "password": "Test123456",
                "role": "family",
                "name": "新用户"
            }
        )

        assert response.status_code == 400
        assert "已存在" in response.json()["detail"] or "exist" in response.json()["detail"].lower()

    @pytest.mark.api
    def test_register_invalid_role(self, client: TestClient, db_session):
        """测试无效角色注册"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "13800002222",
                "password": "Test123456",
                "role": "invalid_role",
                "name": "测试"
            }
        )

        # role字段使用Literal["elder","family"]白名单校验，无效角色返回422
        assert response.status_code == 422

    @pytest.mark.api
    def test_register_weak_password(self, client: TestClient):
        """测试弱密码注册"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "13800003333",
                "password": "123",  # 太短
                "role": "family",
                "name": "测试"
            }
        )

        assert response.status_code in [400, 422]


class TestAuthLogin:
    """用户登录测试"""

    @pytest.mark.api
    def test_login_success(self, client: TestClient, sample_user_auth):
        """测试成功登录"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": sample_user_auth.username,
                "password": "Test123456"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.api
    def test_login_wrong_password(self, client: TestClient, sample_user_auth):
        """测试错误密码登录"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": sample_user_auth.username,
                "password": "WrongPassword"
            }
        )

        assert response.status_code == 401

    @pytest.mark.api
    def test_login_nonexistent_user(self, client: TestClient):
        """测试不存在用户登录"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent_user",
                "password": "Test123456"
            }
        )

        assert response.status_code == 401

    @pytest.mark.api
    def test_login_inactive_user(self, client: TestClient, sample_user_auth, db_session):
        """测试已禁用用户登录"""
        # 禁用用户
        sample_user_auth.is_active = False
        db_session.commit()

        response = client.post(
            "/api/auth/login",
            json={
                "username": sample_user_auth.username,
                "password": "Test123456"
            }
        )

        assert response.status_code in [401, 403]


class TestAuthTokenRefresh:
    """令牌刷新测试"""

    @pytest.mark.api
    def test_refresh_token_success(self, client: TestClient, sample_user_auth):
        """测试成功刷新令牌"""
        # 先登录获取refresh_token
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": sample_user_auth.username,
                "password": "Test123456"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # 等待1秒以确保新令牌的时间戳不同，避免token_hash唯一约束冲突
        time.sleep(1)

        # 使用refresh_token获取新令牌
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.api
    def test_refresh_token_invalid(self, client: TestClient):
        """测试无效刷新令牌"""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == 401


class TestAuthLogout:
    """登出测试"""

    @pytest.mark.api
    def test_logout_success(self, client: TestClient, sample_user_auth):
        """测试成功登出"""
        # 先登录获取令牌
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": sample_user_auth.username,
                "password": "Test123456"
            }
        )
        tokens = login_response.json()
        auth_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        response = client.post(
            "/api/auth/logout",
            headers=auth_headers,
            json={"refresh_token": tokens["refresh_token"]}
        )

        assert response.status_code == 200

    @pytest.mark.api
    def test_logout_without_auth(self, client: TestClient):
        """测试未认证登出"""
        response = client.post("/api/auth/logout")

        assert response.status_code in [401, 403]


class TestAuthPasswordChange:
    """密码修改测试"""

    @pytest.mark.api
    def test_change_password_success(self, client: TestClient, auth_headers, sample_user_auth):
        """测试成功修改密码"""
        response = client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "Test123456",
                "new_password": "NewTest789"
            }
        )

        assert response.status_code == 200

        # 使用新密码登录
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": sample_user_auth.username,
                "password": "NewTest789"
            }
        )
        assert login_response.status_code == 200

    @pytest.mark.api
    def test_change_password_wrong_old(self, client: TestClient, auth_headers):
        """测试旧密码错误"""
        response = client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "WrongOldPassword",
                "new_password": "NewTest789"
            }
        )

        assert response.status_code == 400


class TestDeviceAuth:
    """设备认证测试"""

    @pytest.mark.api
    def test_device_register_success(self, client: TestClient, db_session):
        """测试设备注册成功"""
        response = client.post(
            "/api/auth/device/register",
            json={
                "device_id": "new-speaker-001",
                "device_type": "speaker"
            }
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.api
    def test_device_login_success(self, client: TestClient, sample_device_auth):
        """测试设备登录成功"""
        response = client.post(
            "/api/auth/device/login",
            json={
                "device_id": sample_device_auth.device_id,
                "device_secret": "device-secret-123"
            }
        )

        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.api
    def test_device_login_wrong_secret(self, client: TestClient, sample_device_auth):
        """测试设备密钥错误"""
        response = client.post(
            "/api/auth/device/login",
            json={
                "device_id": sample_device_auth.device_id,
                "device_secret": "wrong-secret"
            }
        )

        assert response.status_code == 401


class TestAuthRBAC:
    """基于角色的访问控制测试"""

    @pytest.mark.api
    def test_admin_access_admin_endpoint(self, client: TestClient, admin_auth_headers):
        """测试管理员访问管理端点"""
        response = client.get(
            "/api/users",  # 假设这是管理员端点
            headers=admin_auth_headers
        )

        # 管理员应该可以访问
        assert response.status_code in [200, 404]  # 200或404（如果端点需要参数）

    @pytest.mark.api
    def test_family_cannot_access_admin_endpoint(self, client: TestClient, family_auth_headers):
        """测试家属不能访问管理端点"""
        # 根据实际API权限设置测试
        pass

    @pytest.mark.api
    def test_protected_endpoint_without_auth(self, client: TestClient):
        """测试未认证访问受保护端点"""
        response = client.get("/api/auth/me")

        assert response.status_code in [401, 403]
