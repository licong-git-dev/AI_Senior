"""
科大讯飞语音识别服务
支持普通话和湖北方言（武汉话、鄂州话）
"""
import websocket
import hashlib
import base64
import hmac
import json
import time
import ssl
from datetime import datetime
from urllib.parse import urlencode
from typing import Optional, Callable
import threading

from app.core.config import get_settings


class XfyunASR:
    """科大讯飞语音识别服务"""

    def __init__(self):
        settings = get_settings()
        self.appid = settings.xfyun_appid
        self.api_key = settings.xfyun_api_key
        self.api_secret = settings.xfyun_api_secret

        # 语音识别WebSocket地址
        self.asr_url = "wss://iat-api.xfyun.cn/v2/iat"

    def _create_url(self) -> str:
        """生成鉴权URL"""
        # 生成RFC1123格式的时间戳
        now = datetime.utcnow()
        date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")

        # 拼接签名原文
        signature_origin = f'host: iat-api.xfyun.cn\ndate: {date}\nGET /v2/iat HTTP/1.1'

        # 使用hmac-sha256进行加密
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            hashlib.sha256
        ).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')

        # 构建authorization
        authorization_origin = (
            f'api_key="{self.api_key}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature_sha_base64}"'
        )
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')

        # 构建请求参数
        params = {
            "authorization": authorization,
            'date': date,
            'host': "iat-api.xfyun.cn"
        }

        return f'{self.asr_url}?{urlencode(params)}'

    def recognize(
        self,
        audio_data: bytes,
        dialect: str = 'mandarin',
        on_result: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        识别音频数据

        Args:
            audio_data: 音频二进制数据 (PCM格式, 16k采样率, 16bit)
            dialect: 方言类型 mandarin/wuhan/ezhou
            on_result: 实时结果回调

        Returns:
            识别结果文本
        """
        result_text = []
        is_finished = threading.Event()

        def on_message(ws, message):
            try:
                data = json.loads(message)
                code = data.get('code', -1)

                if code != 0:
                    print(f'识别错误: {data.get('message', '未知错误')}')
                    is_finished.set()
                    return

                # 解析识别结果
                result = data.get('data', {}).get('result', {})
                ws_data = result.get('ws', [])

                text = ""
                for item in ws_data:
                    for cw in item.get('cw', []):
                        text += cw.get('w', '')

                if text:
                    result_text.append(text)
                    if on_result:
                        on_result(text)

                # 检查是否结束
                if data.get('data', {}).get('status') == 2:
                    is_finished.set()

            except Exception as e:
                print(f'解析消息错误: {e}')
                is_finished.set()

        def on_error(ws, error):
            print(f'WebSocket错误: {error}')
            is_finished.set()

        def on_close(ws, close_status_code, close_msg):
            is_finished.set()

        def on_open(ws):
            def send_audio():
                # 根据方言设置语言参数
                language_map = {
                    'mandarin': 'zh_cn',
                    'wuhan': 'zh_cn',  # 武汉话使用中文+方言参数
                    'ezhou': 'zh_cn'   # 鄂州话使用中文+方言参数
                }

                # 方言引擎参数
                accent_map = {
                    'mandarin': 'mandarin',
                    'wuhan': 'lmz',  # 武汉话方言代码
                    'ezhou': 'lmz'   # 鄂州话暂用武汉话近似
                }

                # 发送开始参数帧
                common_args = {'app_id': self.appid}
                business_args = {
                    'language': language_map.get(dialect, 'zh_cn'),
                    'domain': 'iat',
                    'accent': accent_map.get(dialect, 'mandarin'),
                    'vad_eos': 3000,  # 静音检测时间
                    'dwa': 'wpgs',    # 开启动态修正
                    'ptt': 0          # 不添加标点
                }
                data_args = {
                    'status': 0,
                    'format': 'audio/L16;rate=16000',
                    'encoding': 'raw'
                }

                first_frame = {
                    'common': common_args,
                    'business': business_args,
                    'data': data_args
                }
                ws.send(json.dumps(first_frame))

                # 分帧发送音频数据
                frame_size = 8000  # 每帧大小
                offset = 0

                while offset < len(audio_data):
                    chunk = audio_data[offset:offset + frame_size]
                    offset += frame_size

                    status = 2 if offset >= len(audio_data) else 1

                    audio_frame = {
                        'data': {
                            'status': status,
                            'format': 'audio/L16;rate=16000',
                            'encoding': 'raw',
                            'audio': base64.b64encode(chunk).decode('utf-8')
                        }
                    }
                    ws.send(json.dumps(audio_frame))

                    if status != 2:
                        time.sleep(0.04)  # 模拟实时发送

            threading.Thread(target=send_audio).start()

        # 创建WebSocket连接
        ws_url = self._create_url()
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        # 启动连接
        ws_thread = threading.Thread(
            target=ws.run_forever,
            kwargs={'sslopt': {'cert_reqs': ssl.CERT_NONE}}
        )
        ws_thread.start()

        # 等待识别完成
        is_finished.wait(timeout=30)
        ws.close()

        return "".join(result_text)


class XfyunTTS:
    """科大讯飞语音合成服务"""

    def __init__(self):
        settings = get_settings()
        self.appid = settings.xfyun_appid
        self.api_key = settings.xfyun_api_key
        self.api_secret = settings.xfyun_api_secret

        # 语音合成WebSocket地址
        self.tts_url = "wss://tts-api.xfyun.cn/v2/tts"

    def _create_url(self) -> str:
        """生成鉴权URL"""
        now = datetime.utcnow()
        date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')

        signature_origin = f'host: tts-api.xfyun.cn\ndate: {date}\nGET /v2/tts HTTP/1.1'

        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            hashlib.sha256
        ).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')

        authorization_origin = (
            f'api_key="{self.api_key}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature_sha_base64}"'
        )
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')

        params = {
            "authorization": authorization,
            'date': date,
            'host': "tts-api.xfyun.cn"
        }

        return f'{self.tts_url}?{urlencode(params)}'

    def synthesize(
        self,
        text: str,
        voice: str = 'xiaoyan',
        speed: int = 50,
        volume: int = 50
    ) -> bytes:
        """
        合成语音

        Args:
            text: 要合成的文本
            voice: 发音人 (xiaoyan=普通话女声, aisjiuxu=湖北话)
            speed: 语速 0-100
            volume: 音量 0-100

        Returns:
            音频二进制数据 (PCM格式)
        """
        audio_data = []
        is_finished = threading.Event()

        def on_message(ws, message):
            try:
                data = json.loads(message)
                code = data.get('code', -1)

                if code != 0:
                    print(f'合成错误: {data.get('message', '未知错误')}')
                    is_finished.set()
                    return

                # 获取音频数据
                audio = data.get('data', {}).get('audio')
                if audio:
                    audio_data.append(base64.b64decode(audio))

                # 检查是否结束
                if data.get('data', {}).get('status') == 2:
                    is_finished.set()

            except Exception as e:
                print(f'解析消息错误: {e}')
                is_finished.set()

        def on_error(ws, error):
            print(f'WebSocket错误: {error}')
            is_finished.set()

        def on_close(ws, close_status_code, close_msg):
            is_finished.set()

        def on_open(ws):
            # 发送合成请求
            common_args = {'app_id': self.appid}
            business_args = {
                'aue': 'raw',
                'auf': 'audio/L16;rate=16000',
                'vcn': voice,
                'speed': speed,
                'volume': volume,
                'tte': 'utf8'
            }
            data_args = {
                'status': 2,
                'text': base64.b64encode(text.encode('utf-8')).decode('utf-8')
            }

            request = {
                'common': common_args,
                'business': business_args,
                'data': data_args
            }
            ws.send(json.dumps(request))

        # 创建WebSocket连接
        ws_url = self._create_url()
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        # 启动连接
        ws_thread = threading.Thread(
            target=ws.run_forever,
            kwargs={'sslopt': {'cert_reqs': ssl.CERT_NONE}}
        )
        ws_thread.start()

        # 等待合成完成
        is_finished.wait(timeout=30)
        ws.close()

        return b''.join(audio_data)


# 全局实例
asr_service = XfyunASR()
tts_service = XfyunTTS()
