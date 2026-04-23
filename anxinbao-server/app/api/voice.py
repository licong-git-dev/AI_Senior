"""
API路由 - 语音接口
支持语音识别（ASR）和语音合成（TTS）
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import io
import base64

from app.services.xfyun_service import asr_service, tts_service

router = APIRouter(prefix="/api/voice", tags=["语音"])


class TTSRequest(BaseModel):
    """语音合成请求"""
    text: str
    voice: str = 'xiaoyan'  # 发音人
    speed: int = 50  # 语速 0-100
    volume: int = 50  # 音量 0-100


class ASRResponse(BaseModel):
    """语音识别响应"""
    text: str
    dialect: str
    success: bool


@router.post("/asr", response_model=ASRResponse)
async def speech_to_text(
    audio: UploadFile = File(..., description="音频文件 (PCM, 16k, 16bit)"),
    dialect: str = Form(default="mandarin", description="方言类型: mandarin/wuhan/ezhou")
):
    """
    语音识别 - 将音频转换为文字

    支持的音频格式: PCM, 16000Hz采样率, 16bit
    支持的方言: mandarin(普通话), wuhan(武汉话), ezhou(鄂州话)
    """
    try:
        # 读取音频数据
        audio_data = await audio.read()

        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="音频文件为空")

        # 调用科大讯飞语音识别
        text = asr_service.recognize(audio_data, dialect=dialect)

        if not text:
            return ASRResponse(text="", dialect=dialect, success=False)

        return ASRResponse(text=text, dialect=dialect, success=True)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音识别失败: {str(e)}")


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    语音合成 - 将文字转换为音频

    发音人选项:
    - xiaoyan: 普通话女声（默认）
    - aisjiuxu: 湖北话
    - xiaoyu: 普通话男声

    返回: PCM音频流 (16000Hz, 16bit)
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="文本不能为空")

        if len(request.text) > 500:
            raise HTTPException(status_code=400, detail="文本长度不能超过500字")

        # 调用科大讯飞语音合成
        audio_data = tts_service.synthesize(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            volume=request.volume
        )

        if not audio_data:
            raise HTTPException(status_code=500, detail='语音合成失败')

        # 返回音频流
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/pcm",
            headers={
                "Content-Disposition": "attachment; filename=speech.pcm",
                "X-Audio-Format": "pcm;rate=16000;bits=16"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")


@router.post("/tts/base64")
async def text_to_speech_base64(request: TTSRequest):
    """
    语音合成 - 返回Base64编码的音频数据
    适合前端直接播放
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail='文本不能为空')

        # 调用语音合成
        audio_data = tts_service.synthesize(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            volume=request.volume
        )

        if not audio_data:
            raise HTTPException(status_code=500, detail='语音合成失败')

        # 给 PCM 数据添加标准 WAV 文件头，浏览器才能正常播放
        sample_rate = 16000
        num_channels = 1
        bits_per_sample = 16
        pcm_len = len(audio_data)
        import struct
        wav_header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF', 36 + pcm_len, b'WAVE',
            b'fmt ', 16, 1,  # PCM format
            num_channels, sample_rate,
            sample_rate * num_channels * bits_per_sample // 8,
            num_channels * bits_per_sample // 8,
            bits_per_sample,
            b'data', pcm_len
        )
        wav_data = wav_header + audio_data

        # 转换为Base64
        audio_base64 = base64.b64encode(wav_data).decode('utf-8')

        return {
            'audio': audio_base64,
            'format': "wav",
            "sample_rate": 16000,
            'bits': 16
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")


@router.get("/voices")
async def get_available_voices():
    """获取可用的发音人列表"""
    return {
        'voices': [
            {'id': 'xiaoyan', 'name': '小燕', 'language': '普通话', 'gender': '女'},
            {'id': 'aisjiuxu', 'name': '许久', 'language': '湖北话', 'gender': '男'},
            {'id': 'xiaoyu', 'name': '小宇', 'language': '普通话', 'gender': '男'},
            {'id': 'xiaomei', 'name': '小美', 'language': '普通话', 'gender': '女'},
        ],
        'dialects': [
            {'id': 'mandarin', 'name': '普通话'},
            {'id': 'wuhan', 'name': '武汉话'},
            {'id': 'ezhou', 'name': "鄂州话"},
        ]
    }
