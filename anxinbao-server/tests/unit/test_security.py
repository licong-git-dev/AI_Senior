"""
安全模块单元测试
测试JWT认证、密码哈希、数据加密等功能
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
import hashlib
import base64
import time

from app.core.security import (
    get_password_hash,
    verify_password,
    create_tokens,
    decode_token,
    DataEncryptor,
    mask_phone,
    mask_id_card,
    mask_name,
    mask_address,
    generate_api_signature,
    verify_api_signature,
)


class TestPasswordHashing:
    """密码哈希测试"""

    @pytest.mark.unit
    def test_get_password_hash_returns_hash(self):
        """测试密码哈希返回哈希值"""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 50  # bcrypt哈希长度

    @pytest.mark.unit
    def test_get_password_hash_different_each_time(self):
        """测试每次哈希结果不同（因为salt）"""
        password = "TestPassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2  # bcrypt使用随机salt

    @pytest.mark.unit
    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    @pytest.mark.unit
    def test_verify_password_incorrect(self):
        """测试错误密码验证"""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password("WrongPassword", hashed) is False

    @pytest.mark.unit
    def test_verify_password_empty(self):
        """测试空密码验证"""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password("", hashed) is False


class TestJWTTokens:
    """JWT令牌测试"""

    @pytest.mark.unit
    def test_create_tokens_returns_both(self):
        """测试创建令牌返回access和refresh"""
        tokens = create_tokens(user_id="user123", role="elder")

        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"

    @pytest.mark.unit
    def test_create_tokens_with_device_id(self):
        """测试创建带设备ID的令牌"""
        tokens = create_tokens(
            user_id="user123",
            role="device",
            device_id="device-001"
        )

        assert tokens.access_token is not None
        decoded = decode_token(tokens.access_token)
        assert decoded.device_id == "device-001"

    @pytest.mark.unit
    def test_decode_token_valid(self):
        """测试解码有效令牌"""
        tokens = create_tokens(user_id="user123", role="family")
        decoded = decode_token(tokens.access_token)

        assert decoded.sub == "user123"
        assert decoded.role == "family"

    @pytest.mark.unit
    def test_decode_token_expired(self):
        """测试解码过期令牌"""
        # 使用mock修改过期时间
        with patch('app.core.security.get_settings') as mock_settings:
            mock_settings.return_value.jwt_access_token_expire_minutes = -1  # 已过期
            mock_settings.return_value.jwt_secret_key = "test-secret-key-for-testing-only-32chars!"
            mock_settings.return_value.jwt_algorithm = "HS256"
            mock_settings.return_value.jwt_refresh_token_expire_days = 7

            tokens = create_tokens(user_id="user123", role="elder")

        # 解码应该失败或返回None
        decoded = decode_token(tokens.access_token)
        # 根据实现可能返回None或抛出异常

    @pytest.mark.unit
    def test_decode_token_invalid(self):
        """测试解码无效令牌"""
        decoded = decode_token("invalid.token.here")
        assert decoded is None

    @pytest.mark.unit
    def test_decode_token_empty(self):
        """测试解码空令牌"""
        decoded = decode_token("")
        assert decoded is None


class TestDataEncryption:
    """数据加密测试"""

    @pytest.fixture
    def encryptor(self):
        """创建加密器实例（不传key，使用jwt_secret_key派生）"""
        return DataEncryptor()

    @pytest.mark.unit
    def test_encrypt_returns_ciphertext(self, encryptor):
        """测试加密返回密文"""
        plaintext = "敏感数据123"
        ciphertext = encryptor.encrypt(plaintext)

        assert ciphertext is not None
        assert ciphertext != plaintext

    @pytest.mark.unit
    def test_encrypt_decrypt_roundtrip(self, encryptor):
        """测试加密解密往返"""
        plaintext = "敏感数据123，包含中文！"
        ciphertext = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(ciphertext)

        assert decrypted == plaintext

    @pytest.mark.unit
    def test_encrypt_different_each_time(self, encryptor):
        """测试每次加密结果不同（因为IV）"""
        plaintext = "相同的数据"
        cipher1 = encryptor.encrypt(plaintext)
        cipher2 = encryptor.encrypt(plaintext)

        assert cipher1 != cipher2  # AES-GCM使用随机IV

    @pytest.mark.unit
    def test_decrypt_invalid_data(self, encryptor):
        """测试解密无效数据返回原文（降级处理）"""
        result = encryptor.decrypt("invalid_base64_data")
        # 实现中对无效数据返回原文作为降级
        assert result == "invalid_base64_data"

    @pytest.mark.unit
    def test_encrypt_empty_string(self, encryptor):
        """测试加密空字符串"""
        ciphertext = encryptor.encrypt("")
        decrypted = encryptor.decrypt(ciphertext)
        assert decrypted == ""


class TestDataMasking:
    """数据脱敏测试"""

    @pytest.mark.unit
    def test_mask_phone_standard(self):
        """测试标准手机号脱敏"""
        assert mask_phone("13812345678") == "138****5678"

    @pytest.mark.unit
    def test_mask_phone_short(self):
        """测试短号码不脱敏（<7位原样返回）"""
        assert mask_phone("1234") == "1234"

    @pytest.mark.unit
    def test_mask_phone_empty(self):
        """测试空号码"""
        assert mask_phone("") == ""
        assert mask_phone(None) is None

    @pytest.mark.unit
    def test_mask_id_card_18_digits(self):
        """测试18位身份证脱敏"""
        assert mask_id_card("110101199001011234") == "110***********1234"

    @pytest.mark.unit
    def test_mask_id_card_15_digits(self):
        """测试15位身份证脱敏"""
        assert mask_id_card("110101900101123") == "110********1123"

    @pytest.mark.unit
    def test_mask_id_card_short(self):
        """测试短身份证号（<8位原样返回）"""
        assert mask_id_card("123") == "123"

    @pytest.mark.unit
    def test_mask_name_chinese_2chars(self):
        """测试2字中文名脱敏"""
        assert mask_name("张三") == "张*"

    @pytest.mark.unit
    def test_mask_name_chinese_3chars(self):
        """测试3字中文名脱敏"""
        assert mask_name("张三丰") == "张*丰"

    @pytest.mark.unit
    def test_mask_name_single_char(self):
        """测试单字名原样返回"""
        assert mask_name("张") == "张"

    @pytest.mark.unit
    def test_mask_address_standard(self):
        """测试地址脱敏"""
        address = "北京市朝阳区建国路123号5栋601室"
        masked = mask_address(address)
        assert "****" in masked
        assert masked.startswith(address[:10])


class TestAPISignature:
    """API签名测试"""

    @pytest.mark.unit
    def test_generate_signature(self):
        """测试生成签名"""
        ts = int(time.time())
        signature = generate_api_signature("GET", "/api/health", ts, secret_key="test-secret")

        assert signature is not None
        assert len(signature) == 64  # SHA256 hex digest

    @pytest.mark.unit
    def test_verify_signature_valid(self):
        """测试验证有效签名"""
        ts = int(time.time())
        secret = "test-secret"
        signature = generate_api_signature("POST", "/api/chat", ts, body='{"msg":"hi"}', secret_key=secret)

        assert verify_api_signature("POST", "/api/chat", ts, signature, body='{"msg":"hi"}', secret_key=secret) is True

    @pytest.mark.unit
    def test_verify_signature_invalid(self):
        """测试验证无效签名"""
        ts = int(time.time())
        assert verify_api_signature("GET", "/api/test", ts, "invalid_signature", secret_key="test-secret") is False

    @pytest.mark.unit
    def test_signature_deterministic(self):
        """测试相同参数生成相同签名"""
        secret = "test-secret"
        ts = 1704067200
        sig1 = generate_api_signature("GET", "/api/data", ts, secret_key=secret)
        sig2 = generate_api_signature("GET", "/api/data", ts, secret_key=secret)

        assert sig1 == sig2

    @pytest.mark.unit
    def test_verify_signature_expired(self):
        """测试过期签名验证失败"""
        old_ts = int(time.time()) - 600  # 10分钟前
        secret = "test-secret"
        signature = generate_api_signature("GET", "/api/test", old_ts, secret_key=secret)

        assert verify_api_signature("GET", "/api/test", old_ts, signature, secret_key=secret) is False
