"""
安心宝服务性能测试
使用Locust进行负载测试

运行方式:
  locust -f tests/performance/locustfile.py --host=http://localhost:8000
  然后访问 http://localhost:8089 启动测试
"""
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import json
import random
import logging

logger = logging.getLogger(__name__)


class AnxinbaoUser(HttpUser):
    """模拟安心宝用户行为"""

    # 请求间隔1-3秒
    wait_time = between(1, 3)

    # 测试数据
    test_messages = [
        "你好",
        "今天天气怎么样",
        "我有点头晕",
        "我睡眠不太好",
        "最近胃口不好",
        "帮我查一下明天的天气",
        "我想和你聊聊天",
        "孩子们都忙，我一个人在家",
        "我今天去公园散步了",
        "晚上睡不着觉怎么办",
    ]

    health_messages = [
        "我头痛",
        "最近血压有点高",
        "膝盖疼",
        "胸口有点闷",
        "眼睛干涩",
        "腰酸背痛",
    ]

    def on_start(self):
        """用户开始时执行 - 登录获取token"""
        self.token = None
        self.session_id = f"perf-test-{random.randint(10000, 99999)}"

        # 尝试登录
        response = self.client.post(
            "/api/auth/login",
            json={
                "username": "13800138000",
                "password": "Test123456"
            },
            catch_response=True
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            response.success()
        else:
            # 如果登录失败，继续测试但标记
            response.failure("Login failed")
            logger.warning("登录失败，部分测试可能受影响")

    @property
    def auth_headers(self):
        """获取认证头"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(10)
    def health_check(self):
        """健康检查 - 高频率"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(5)
    def api_info(self):
        """API信息查询"""
        self.client.get("/api/info")

    @task(20)
    def chat_message(self):
        """发送普通对话消息 - 主要测试场景"""
        message = random.choice(self.test_messages)

        with self.client.post(
            "/api/chat/message",
            json={
                "message": message,
                "session_id": self.session_id
            },
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code in [401, 403]:
                response.failure("Authentication required")
            else:
                response.failure(f"Chat failed: {response.status_code}")

    @task(8)
    def health_chat(self):
        """健康咨询对话"""
        message = random.choice(self.health_messages)

        with self.client.post(
            "/api/chat/message",
            json={
                "message": message,
                "session_id": f"health-{self.session_id}"
            },
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # 检查是否有风险评估
                response.success()
            elif response.status_code in [401, 403]:
                response.failure("Authentication required")
            else:
                response.failure(f"Health chat failed: {response.status_code}")

    @task(3)
    def get_chat_history(self):
        """获取对话历史"""
        self.client.get(
            f"/api/chat/history?session_id={self.session_id}",
            headers=self.auth_headers
        )

    @task(2)
    def get_notifications(self):
        """获取通知列表"""
        self.client.get(
            "/api/notify/list",
            headers=self.auth_headers
        )


class DeviceUser(HttpUser):
    """模拟设备端行为"""

    wait_time = between(2, 5)

    def on_start(self):
        """设备启动 - 设备登录"""
        self.token = None
        self.session_id = f"device-perf-{random.randint(10000, 99999)}"

        response = self.client.post(
            "/api/auth/device/login",
            json={
                "device_id": "speaker-test-001",
                "device_secret": "device-secret-123"
            },
            catch_response=True
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            response.success()
        else:
            response.failure("Device login failed")

    @property
    def auth_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(10)
    def voice_interaction(self):
        """模拟语音交互"""
        # 发送对话消息
        messages = [
            "今天吃什么",
            "我想出去走走",
            "帮我放首歌",
            "现在几点了",
        ]

        self.client.post(
            "/api/chat/message",
            json={
                "message": random.choice(messages),
                "session_id": self.session_id
            },
            headers=self.auth_headers
        )

    @task(2)
    def heartbeat(self):
        """设备心跳"""
        self.client.get("/health")


class FamilyUser(HttpUser):
    """模拟家属端行为"""

    wait_time = between(3, 8)

    def on_start(self):
        """家属登录"""
        self.token = None

        response = self.client.post(
            "/api/auth/login",
            json={
                "username": "13900139000",
                "password": "Test123456"
            },
            catch_response=True
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            response.success()
        else:
            response.failure("Family login failed")

    @property
    def auth_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(5)
    def check_notifications(self):
        """检查通知"""
        self.client.get(
            "/api/notify/list",
            headers=self.auth_headers
        )

    @task(3)
    def view_health_summary(self):
        """查看健康摘要"""
        self.client.get(
            "/api/health/summary?user_id=1",
            headers=self.auth_headers
        )

    @task(2)
    def view_chat_history(self):
        """查看老人对话历史"""
        self.client.get(
            "/api/chat/history?user_id=1",
            headers=self.auth_headers
        )


# ==================== 测试事件钩子 ====================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时"""
    logger.info("性能测试开始")
    if isinstance(environment.runner, MasterRunner):
        logger.info("运行在分布式模式（Master）")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时"""
    logger.info("性能测试结束")
    # 可以在这里生成报告


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """每个请求完成后"""
    if exception:
        logger.error(f"请求失败: {name} - {exception}")
    elif response_time > 2000:  # 超过2秒
        logger.warning(f"慢请求: {name} - {response_time}ms")


# ==================== 自定义测试场景 ====================

class StressTestUser(HttpUser):
    """压力测试用户 - 高并发场景"""

    wait_time = between(0.1, 0.5)  # 极短间隔

    @task
    def rapid_health_check(self):
        """快速健康检查"""
        self.client.get("/health")

    @task
    def rapid_chat(self):
        """快速对话"""
        self.client.post(
            "/api/chat/message",
            json={
                "message": "测试",
                "session_id": "stress-test"
            }
        )


class SoakTestUser(HttpUser):
    """浸泡测试用户 - 长时间稳定负载"""

    wait_time = between(5, 15)  # 较长间隔

    @task
    def normal_interaction(self):
        """正常交互"""
        self.client.get("/health")
        self.client.post(
            "/api/chat/message",
            json={
                "message": "浸泡测试消息",
                "session_id": "soak-test"
            }
        )
