"""
会员订阅 API 回归测试
重点验证 get_current_user 返回 UserInfo 后，订阅接口仍能正确读取 user_id。
"""
import pytest
from unittest.mock import patch, MagicMock

from app.services.subscription_service import MembershipTier, BillingCycle, PaymentMethod, SubscriptionStatus


class TestSubscriptionAPI:
    @pytest.mark.api
    def test_get_my_subscription_returns_free_state_when_no_subscription(
        self,
        client,
        auth_headers,
        sample_user_auth,
    ):
        with patch("app.api.subscription.subscription_service.get_user_subscription", return_value=None) as mock_get_subscription:
            response = client.get("/api/subscription/my", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["has_subscription"] is False
        assert data["tier"] == "free"
        mock_get_subscription.assert_called_once_with(sample_user_auth.id)

    @pytest.mark.api
    def test_get_my_tier_uses_authenticated_user_info_id(
        self,
        client,
        auth_headers,
        sample_user_auth,
    ):
        with patch("app.api.subscription.subscription_service.get_user_tier", return_value=MembershipTier.BASIC) as mock_get_tier:
            response = client.get("/api/subscription/my/tier", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "basic"
        assert data["name"] == "基础会员"
        mock_get_tier.assert_called_once_with(sample_user_auth.id)

    @pytest.mark.api
    def test_subscribe_passes_authenticated_user_info_id_to_service(
        self,
        client,
        auth_headers,
        sample_user_auth,
    ):
        mock_plan = MagicMock()
        mock_plan.plan_id = "basic_monthly"
        mock_plan.tier = MembershipTier.BASIC
        mock_plan.price = 29.9
        mock_plan.billing_cycle = BillingCycle.MONTHLY
        mock_plan.to_dict.return_value = {
            "plan_id": "basic_monthly",
            "tier": "basic",
            "price": 29.9,
        }

        mock_subscription = MagicMock()
        mock_subscription.subscription_id = "sub_test_001"
        mock_subscription.to_dict.return_value = {
            "subscription_id": "sub_test_001",
            "plan_id": "basic_monthly",
            "tier": "basic",
            "status": "active",
        }

        mock_payment = MagicMock()
        mock_payment.to_dict.return_value = {
            "payment_id": "pay_test_001",
            "amount": 29.9,
            "payment_method": "wechat",
            "status": "pending",
        }

        with patch("app.api.subscription.subscription_service.get_plan", return_value=mock_plan), \
             patch("app.api.subscription.subscription_service.get_user_subscription", return_value=None), \
             patch("app.api.subscription.subscription_service.create_subscription", return_value=mock_subscription) as mock_create_subscription, \
             patch("app.api.subscription.subscription_service.create_payment", return_value=mock_payment) as mock_create_payment:
            response = client.post(
                "/api/subscription/subscribe",
                headers=auth_headers,
                json={
                    "plan_id": "basic_monthly",
                    "payment_method": "wechat",
                    "is_trial": False,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["subscription"]["subscription_id"] == "sub_test_001"
        assert data["payment"]["payment_id"] == "pay_test_001"
        mock_create_subscription.assert_called_once_with(
            user_id=sample_user_auth.id,
            plan_id="basic_monthly",
            payment_method=PaymentMethod.WECHAT,
            is_trial=False,
        )
        mock_create_payment.assert_called_once_with(
            user_id=sample_user_auth.id,
            subscription_id="sub_test_001",
            amount=29.9,
            payment_method=PaymentMethod.WECHAT,
        )

    @pytest.mark.api
    def test_admin_cannot_access_subscription_endpoints_with_non_numeric_user_id(
        self,
        client,
        admin_auth_headers,
    ):
        response = client.get("/api/subscription/my", headers=admin_auth_headers)

        assert response.status_code == 403
        assert response.json()["detail"] == "当前角色不支持订阅操作"

    @pytest.mark.api
    def test_device_cannot_access_subscription_endpoints(
        self,
        client,
        device_auth_headers,
    ):
        response = client.get("/api/subscription/my", headers=device_auth_headers)

        assert response.status_code == 403
        assert response.json()["detail"] == "当前角色不支持订阅操作"

    @pytest.mark.api
    def test_subscribe_uses_explicit_tier_order_for_upgrade_check(
        self,
        client,
        auth_headers,
    ):
        mock_plan = MagicMock()
        mock_plan.plan_id = "family_monthly"
        mock_plan.tier = MembershipTier.FAMILY
        mock_plan.price = 69.9

        mock_existing = MagicMock()
        mock_existing.status = SubscriptionStatus.ACTIVE
        mock_existing.tier = MembershipTier.PREMIUM

        mock_subscription = MagicMock()
        mock_subscription.subscription_id = "sub_family_001"
        mock_subscription.to_dict.return_value = {
            "subscription_id": "sub_family_001",
            "plan_id": "family_monthly",
            "tier": "family",
            "status": "active",
        }

        mock_payment = MagicMock()
        mock_payment.to_dict.return_value = {
            "payment_id": "pay_family_001",
            "amount": 69.9,
            "payment_method": "wechat",
            "status": "pending",
        }

        with patch("app.api.subscription.subscription_service.get_plan", return_value=mock_plan), \
             patch("app.api.subscription.subscription_service.get_user_subscription", return_value=mock_existing), \
             patch("app.api.subscription.subscription_service.create_subscription", return_value=mock_subscription), \
             patch("app.api.subscription.subscription_service.create_payment", return_value=mock_payment):
            response = client.post(
                "/api/subscription/subscribe",
                headers=auth_headers,
                json={
                    "plan_id": "family_monthly",
                    "payment_method": "wechat",
                    "is_trial": False,
                },
            )

        assert response.status_code == 200
        assert response.json()["success"] is True
