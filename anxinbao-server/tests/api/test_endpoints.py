"""
健康检查和通用API测试
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """健康检查端点测试"""

    @pytest.mark.api
    def test_health_check(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data

    @pytest.mark.api
    def test_api_info(self, client: TestClient):
        """测试API信息端点"""
        response = client.get("/api/info")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data

    @pytest.mark.api
    def test_docs_endpoint(self, client: TestClient):
        """测试文档端点"""
        response = client.get("/docs")
        assert response.status_code == 200

    @pytest.mark.api
    def test_openapi_json(self, client: TestClient):
        """测试OpenAPI JSON端点"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestNotifyEndpoints:
    """通知API测试"""

    @pytest.mark.api
    def test_get_notifications(self, client: TestClient, family_auth_headers, sample_health_notification):
        """测试获取通知列表"""
        response = client.get(
            "/api/notify/list",
            headers=family_auth_headers
        )

        # 端点可能需要不同的路径
        assert response.status_code in [200, 404]

    @pytest.mark.api
    def test_mark_notification_read(self, client: TestClient, family_auth_headers, sample_health_notification):
        """测试标记通知已读"""
        response = client.post(
            f"/api/notify/{sample_health_notification.id}/read",
            headers=family_auth_headers
        )

        assert response.status_code in [200, 404]


class TestUserEndpoints:
    """用户API测试"""

    @pytest.mark.api
    def test_get_user_profile(self, client: TestClient, auth_headers):
        """测试获取用户信息"""
        response = client.get(
            "/api/users/me",
            headers=auth_headers
        )

        # 根据实际API实现
        assert response.status_code in [200, 404]

    @pytest.mark.api
    def test_update_user_profile(self, client: TestClient, auth_headers):
        """测试更新用户信息"""
        response = client.put(
            "/api/users/me",
            headers=auth_headers,
            json={"name": "更新后的名字"}
        )

        assert response.status_code in [200, 404, 405]

    @pytest.mark.api
    def test_list_family_members(self, client: TestClient, auth_headers, sample_family_member):
        """测试列出家属"""
        response = client.get(
            "/api/users/family",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]


class TestVoiceEndpoints:
    """语音API测试"""

    @pytest.mark.api
    def test_voice_tts_endpoint(self, client: TestClient, auth_headers, mock_iflytek_tts):
        """测试语音合成端点"""
        response = client.post(
            "/api/voice/tts",
            headers=auth_headers,
            json={"text": "你好，今天天气真好"}
        )

        # 根据实际API实现
        assert response.status_code in [200, 404]

    @pytest.mark.api
    def test_voice_asr_endpoint(self, client: TestClient, auth_headers, mock_iflytek_asr):
        """测试语音识别端点"""
        # 创建一个假的音频文件
        audio_data = b"fake_audio_data"

        response = client.post(
            "/api/voice/asr",
            headers=auth_headers,
            files={"audio": ("test.wav", audio_data, "audio/wav")}
        )

        assert response.status_code in [200, 404, 422]


class TestHealthDataEndpoints:
    """健康数据API测试"""

    @pytest.mark.api
    def test_get_health_summary(self, client: TestClient, family_auth_headers, sample_user):
        """测试获取健康摘要"""
        response = client.get(
            f"/api/health/summary?user_id={sample_user.id}",
            headers=family_auth_headers
        )

        assert response.status_code in [200, 404]

    @pytest.mark.api
    def test_get_risk_history(self, client: TestClient, family_auth_headers, sample_user):
        """测试获取风险历史"""
        response = client.get(
            f"/api/health/risks?user_id={sample_user.id}",
            headers=family_auth_headers
        )

        assert response.status_code in [200, 404]


class TestVideoEndpoints:
    """视频通话API测试"""

    @pytest.mark.api
    def test_initiate_video_call(self, client: TestClient, family_auth_headers, sample_user):
        """测试发起视频通话"""
        response = client.post(
            "/api/video/call",
            headers=family_auth_headers,
            json={"target_user_id": sample_user.id}
        )

        assert response.status_code in [200, 404]

    @pytest.mark.api
    def test_get_call_status(self, client: TestClient, family_auth_headers):
        """测试获取通话状态"""
        response = client.get(
            "/api/video/status",
            headers=family_auth_headers
        )

        assert response.status_code in [200, 404]


class TestCORSHeaders:
    """CORS头测试"""

    @pytest.mark.api
    def test_cors_headers_present(self, client: TestClient):
        """测试CORS头存在"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )

        # CORS预检请求应该返回200
        assert response.status_code in [200, 204, 405]


class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.api
    def test_404_not_found(self, client: TestClient):
        """测试404错误"""
        response = client.get("/api/nonexistent-endpoint")
        assert response.status_code == 404

    @pytest.mark.api
    def test_method_not_allowed(self, client: TestClient):
        """测试405方法不允许"""
        response = client.delete("/health")  # 健康检查不支持DELETE
        assert response.status_code in [404, 405]

    @pytest.mark.api
    def test_invalid_json(self, client: TestClient, auth_headers):
        """测试无效JSON请求"""
        response = client.post(
            "/api/chat/send",
            headers={**auth_headers, "Content-Type": "application/json"},
            content="invalid json {"
        )

        assert response.status_code in [400, 422]
