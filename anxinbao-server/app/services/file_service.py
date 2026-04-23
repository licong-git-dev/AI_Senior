"""
文件上传管理服务
提供图片、音视频、文档的上传、存储、管理功能
"""
import logging
import os
import uuid
import hashlib
import mimetypes
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import base64
import io

logger = logging.getLogger(__name__)


# ==================== 基础定义 ====================

class FileType(Enum):
    """文件类型"""
    IMAGE = 'image'  # 图片
    AUDIO = 'audio'  # 音频
    VIDEO = 'video'  # 视频
    DOCUMENT = 'document'  # 文档
    OTHER = "other"  # 其他


class FileStatus(Enum):
    """文件状态"""
    UPLOADING = 'uploading'  # 上传中
    COMPLETED = 'completed'  # 已完成
    FAILED = 'failed'  # 失败
    DELETED = "deleted"  # 已删除


class StorageType(Enum):
    """存储类型"""
    LOCAL = 'local'  # 本地存储
    OSS = 'oss'  # 阿里云OSS
    COS = 'cos'  # 腾讯云COS
    S3 = 's3'  # AWS S3


# 文件类型配置
FILE_TYPE_CONFIG = {
    FileType.IMAGE: {
        'extensions': [".jpg", '.jpeg', '.png', ".gif", '.webp', ".bmp"],
        'max_size': 10 * 1024 * 1024,  # 10MB
        'mime_types': ["image/jpeg", 'image/png', "image/gif", 'image/webp', "image/bmp"]
    },
    FileType.AUDIO: {
        'extensions': [".mp3", '.wav', '.m4a', '.aac', '.ogg', '.flac'],
        'max_size': 50 * 1024 * 1024,  # 50MB
        'mime_types': ['audio/mpeg', 'audio/wav', 'audio/m4a', 'audio/aac', 'audio/ogg']
    },
    FileType.VIDEO: {
        'extensions': ['.mp4', '.mov', '.avi', '.mkv', '.webm'],
        'max_size': 200 * 1024 * 1024,  # 200MB
        'mime_types': ['video/mp4', "video/quicktime", 'video/x-msvideo', "video/webm"]
    },
    FileType.DOCUMENT: {
        'extensions': [".pdf", '.doc', '.docx', '.txt', '.xls', ".xlsx"],
        'max_size': 20 * 1024 * 1024,  # 20MB
        'mime_types': ["application/pdf", 'application/msword', 'text/plain',
                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    }
}


# ==================== 数据模型 ====================

@dataclass
class FileInfo:
    """文件信息"""
    file_id: str
    user_id: int
    filename: str
    original_filename: str
    file_type: FileType
    mime_type: str
    size: int
    storage_type: StorageType
    storage_path: str
    url: str
    thumbnail_url: Optional[str] = None
    checksum: Optional[str] = None
    width: Optional[int] = None  # 图片/视频宽度
    height: Optional[int] = None  # 图片/视频高度
    duration: Optional[int] = None  # 音视频时长(秒)
    status: FileStatus = FileStatus.COMPLETED
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_id': self.file_id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            'file_type': self.file_type.value,
            'mime_type': self.mime_type,
            'size': self.size,
            "size_formatted": self._format_size(self.size),
            'url': self.url,
            "thumbnail_url": self.thumbnail_url,
            'width': self.width,
            'height': self.height,
            'duration': self.duration,
            'status': self.status.value,
            'tags': self.tags,
            'created_at': self.created_at.isoformat()
        }

    @staticmethod
    def _format_size(size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f'{size:.1f}{unit}'
            size /= 1024
        return f'{size:.1f}TB'


@dataclass
class UploadSession:
    """上传会话(分片上传)"""
    session_id: str
    user_id: int
    filename: str
    file_type: FileType
    total_size: int
    chunk_size: int
    total_chunks: int
    uploaded_chunks: List[int] = field(default_factory=list)
    storage_path: str = ""
    status: str = 'active'  # active/completed/expired
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'filename': self.filename,
            'total_size': self.total_size,
            'chunk_size': self.chunk_size,
            "total_chunks": self.total_chunks,
            "uploaded_chunks": len(self.uploaded_chunks),
            'progress': len(self.uploaded_chunks) / self.total_chunks * 100 if self.total_chunks > 0 else 0,
            'status': self.status,
            'expires_at': self.expires_at.isoformat()
        }


# ==================== 存储后端 ====================

class LocalStorage:
    """本地文件存储"""

    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self._ensure_directories()

    def _ensure_directories(self):
        """确保目录存在"""
        for file_type in FileType:
            (self.base_path / file_type.value).mkdir(parents=True, exist_ok=True)
        (self.base_path / "temp").mkdir(parents=True, exist_ok=True)
        (self.base_path / 'thumbnails').mkdir(parents=True, exist_ok=True)

    def save(self, data: bytes, file_type: FileType, filename: str) -> str:
        """保存文件"""
        # 按日期组织目录
        date_path = datetime.now().strftime("%Y/%m/%d")
        dir_path = self.base_path / file_type.value / date_path
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / filename
        with open(file_path, 'wb') as f:
            f.write(data)

        return str(file_path)

    def delete(self, file_path: str) -> bool:
        """删除文件"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
            return True
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False

    def get_url(self, file_path: str) -> str:
        """获取文件URL"""
        # 本地存储返回相对路径
        return f"/static/{file_path}"

    def save_thumbnail(self, data: bytes, filename: str) -> str:
        """保存缩略图"""
        thumb_path = self.base_path / 'thumbnails' / filename
        with open(thumb_path, "wb") as f:
            f.write(data)
        return str(thumb_path)


# ==================== 文件处理器 ====================

class ImageProcessor:
    """图片处理器"""

    @staticmethod
    def get_dimensions(data: bytes) -> Tuple[int, int]:
        """获取图片尺寸"""
        try:
            # 简单的图片头解析
            if data[:8] == b'\x89PNG\r\n\x1a\n':
                # PNG
                width = int.from_bytes(data[16:20], "big")
                height = int.from_bytes(data[20:24], 'big')
                return width, height
            elif data[:2] == b'\xff\xd8':
                # JPEG - 简化处理
                return 0, 0
            return 0, 0
        except Exception:
            return 0, 0

    @staticmethod
    def create_thumbnail(data: bytes, max_size: int = 200) -> Optional[bytes]:
        """创建缩略图(需要PIL库，这里返回None)"""
        # 实际使用时需要安装Pillow
        # from PIL import Image
        # img = Image.open(io.BytesIO(data))
        # img.thumbnail((max_size, max_size))
        # buffer = io.BytesIO()
        # img.save(buffer, format="JPEG")
        # return buffer.getvalue()
        return None


class FileValidator:
    """文件验证器"""

    @staticmethod
    def validate(
        data: bytes,
        filename: str,
        file_type: FileType = None
    ) -> Tuple[bool, str, FileType]:
        """验证文件"""
        # 获取扩展名
        ext = Path(filename).suffix.lower()

        # 确定文件类型
        detected_type = None
        for ftype, config in FILE_TYPE_CONFIG.items():
            if ext in config['extensions']:
                detected_type = ftype
                break

        if detected_type is None:
            detected_type = FileType.OTHER

        # 如果指定了类型，检查是否匹配
        if file_type and file_type != detected_type:
            return False, f'文件类型不匹配，期望 {file_type.value}', detected_type

        # 检查文件大小
        config = FILE_TYPE_CONFIG.get(detected_type)
        if config:
            if len(data) > config['max_size']:
                max_mb = config['max_size'] / 1024 / 1024
                return False, f'文件大小超过限制({max_mb:.0f}MB)', detected_type

        return True, "验证通过", detected_type

    @staticmethod
    def get_mime_type(filename: str) -> str:
        """获取MIME类型"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"


# ==================== 文件上传服务 ====================

class FileUploadService:
    """文件上传服务"""

    def __init__(self, storage_type: StorageType = StorageType.LOCAL):
        self.storage_type = storage_type
        self.storage = LocalStorage()
        self.files: Dict[str, FileInfo] = {}
        self.user_files: Dict[int, List[str]] = defaultdict(list)
        self.upload_sessions: Dict[str, UploadSession] = {}
        self.validator = FileValidator()

    def upload_file(
        self,
        user_id: int,
        data: bytes,
        filename: str,
        file_type: FileType = None,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Tuple[bool, str, Optional[FileInfo]]:
        """上传文件"""
        # 验证文件
        is_valid, message, detected_type = self.validator.validate(data, filename, file_type)
        if not is_valid:
            return False, message, None

        # 生成文件ID和新文件名
        file_id = f"file_{user_id}_{uuid.uuid4().hex[:8]}"
        ext = Path(filename).suffix.lower()
        new_filename = f'{file_id}{ext}'

        # 计算校验和
        checksum = hashlib.md5(data).hexdigest()

        # 保存文件
        try:
            storage_path = self.storage.save(data, detected_type, new_filename)
            url = self.storage.get_url(storage_path)
        except Exception as e:
            logger.error(f'保存文件失败: {e}')
            return False, "文件保存失败", None

        # 获取文件信息
        mime_type = self.validator.get_mime_type(filename)
        width, height = 0, 0
        thumbnail_url = None

        if detected_type == FileType.IMAGE:
            width, height = ImageProcessor.get_dimensions(data)
            # 创建缩略图
            thumb_data = ImageProcessor.create_thumbnail(data)
            if thumb_data:
                thumb_filename = f"thumb_{new_filename}"
                thumb_path = self.storage.save_thumbnail(thumb_data, thumb_filename)
                thumbnail_url = self.storage.get_url(thumb_path)

        # 创建文件信息
        file_info = FileInfo(
            file_id=file_id,
            user_id=user_id,
            filename=new_filename,
            original_filename=filename,
            file_type=detected_type,
            mime_type=mime_type,
            size=len(data),
            storage_type=self.storage_type,
            storage_path=storage_path,
            url=url,
            thumbnail_url=thumbnail_url,
            checksum=checksum,
            width=width if width > 0 else None,
            height=height if height > 0 else None,
            tags=tags or [],
            metadata=metadata or {}
        )

        self.files[file_id] = file_info
        self.user_files[user_id].append(file_id)

        logger.info(f'文件上传成功: {file_id} - {filename}')
        return True, "上传成功", file_info

    def upload_base64(
        self,
        user_id: int,
        base64_data: str,
        filename: str,
        file_type: FileType = None
    ) -> Tuple[bool, str, Optional[FileInfo]]:
        """上传Base64编码的文件"""
        try:
            # 处理data URL格式
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]

            data = base64.b64decode(base64_data)
            return self.upload_file(user_id, data, filename, file_type)
        except Exception as e:
            logger.error(f'Base64解码失败: {e}')
            return False, "文件数据格式错误", None

    def create_upload_session(
        self,
        user_id: int,
        filename: str,
        total_size: int,
        chunk_size: int = 5 * 1024 * 1024  # 5MB
    ) -> Tuple[bool, str, Optional[UploadSession]]:
        """创建分片上传会话"""
        # 验证文件类型
        ext = Path(filename).suffix.lower()
        detected_type = FileType.OTHER
        for ftype, config in FILE_TYPE_CONFIG.items():
            if ext in config['extensions']:
                detected_type = ftype
                if total_size > config['max_size']:
                    max_mb = config['max_size'] / 1024 / 1024
                    return False, f'文件大小超过限制({max_mb:.0f}MB)', None
                break

        session_id = f'upload_{user_id}_{uuid.uuid4().hex[:8]}'
        total_chunks = (total_size + chunk_size - 1) // chunk_size

        session = UploadSession(
            session_id=session_id,
            user_id=user_id,
            filename=filename,
            file_type=detected_type,
            total_size=total_size,
            chunk_size=chunk_size,
            total_chunks=total_chunks,
            storage_path=str(self.storage.base_path / 'temp' / session_id)
        )

        self.upload_sessions[session_id] = session
        return True, "会话创建成功", session

    def upload_chunk(
        self,
        session_id: str,
        chunk_index: int,
        data: bytes
    ) -> Tuple[bool, str, Optional[Dict]]:
        """上传文件分片"""
        session = self.upload_sessions.get(session_id)
        if not session:
            return False, '上传会话不存在', None

        if session.status != 'active':
            return False, '上传会话已失效', None

        if chunk_index in session.uploaded_chunks:
            return True, '分片已上传', session.to_dict()

        # 保存分片
        try:
            chunk_path = Path(session.storage_path)
            chunk_path.mkdir(parents=True, exist_ok=True)
            with open(chunk_path / f'chunk_{chunk_index}', 'wb') as f:
                f.write(data)

            session.uploaded_chunks.append(chunk_index)

            # 检查是否完成
            if len(session.uploaded_chunks) == session.total_chunks:
                return self._complete_upload_session(session)

            return True, '分片上传成功', session.to_dict()

        except Exception as e:
            logger.error(f'分片上传失败: {e}')
            return False, "分片上传失败", None

    def _complete_upload_session(
        self,
        session: UploadSession
    ) -> Tuple[bool, str, Optional[Dict]]:
        """完成分片上传"""
        try:
            # 合并分片
            chunk_path = Path(session.storage_path)
            merged_data = b""

            for i in range(session.total_chunks):
                with open(chunk_path / f"chunk_{i}", 'rb') as f:
                    merged_data += f.read()

            # 上传合并后的文件
            success, message, file_info = self.upload_file(
                session.user_id,
                merged_data,
                session.filename,
                session.file_type
            )

            if success:
                session.status = 'completed'
                # 清理临时文件
                import shutil
                shutil.rmtree(chunk_path, ignore_errors=True)
                return True, '上传完成', {
                    'session': session.to_dict(),
                    'file': file_info.to_dict()
                }
            else:
                return False, message, None

        except Exception as e:
            logger.error(f'合并分片失败: {e}')
            return False, "文件合并失败", None

    def get_file(self, file_id: str) -> Optional[FileInfo]:
        """获取文件信息"""
        return self.files.get(file_id)

    def get_user_files(
        self,
        user_id: int,
        file_type: FileType = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[FileInfo], int]:
        """获取用户文件列表"""
        file_ids = self.user_files.get(user_id, [])
        files = [self.files[fid] for fid in file_ids if fid in self.files]

        # 过滤已删除的文件
        files = [f for f in files if f.status != FileStatus.DELETED]

        if file_type:
            files = [f for f in files if f.file_type == file_type]

        # 按时间排序
        files = sorted(files, key=lambda x: x.created_at, reverse=True)

        total = len(files)
        files = files[offset:offset + limit]

        return files, total

    def delete_file(self, file_id: str, user_id: int) -> Tuple[bool, str]:
        """删除文件"""
        file_info = self.files.get(file_id)
        if not file_info:
            return False, '文件不存在'

        if file_info.user_id != user_id:
            return False, '无权限删除'

        # 标记为删除
        file_info.status = FileStatus.DELETED
        file_info.updated_at = datetime.now()

        # 实际删除文件(可选择延迟删除)
        # self.storage.delete(file_info.storage_path)

        return True, "文件已删除"

    def get_storage_usage(self, user_id: int) -> Dict[str, Any]:
        """获取存储使用情况"""
        file_ids = self.user_files.get(user_id, [])
        files = [self.files[fid] for fid in file_ids if fid in self.files]
        files = [f for f in files if f.status != FileStatus.DELETED]

        total_size = sum(f.size for f in files)
        by_type = defaultdict(lambda: {'count': 0, 'size': 0})

        for f in files:
            by_type[f.file_type.value]['count'] += 1
            by_type[f.file_type.value]['size'] += f.size

        return {
            "total_files": len(files),
            'total_size': total_size,
            "total_size_formatted": FileInfo._format_size(total_size),
            'by_type': dict(by_type)
        }


# ==================== 头像服务 ====================

class AvatarService:
    """头像服务"""

    DEFAULT_AVATARS = [
        "/static/avatars/default_1.png",
        '/static/avatars/default_2.png',
        '/static/avatars/default_3.png',
        '/static/avatars/default_4.png',
        "/static/avatars/default_5.png"
    ]

    def __init__(self, upload_service: FileUploadService):
        self.upload_service = upload_service
        self.user_avatars: Dict[int, str] = {}

    def upload_avatar(
        self,
        user_id: int,
        data: bytes,
        filename: str
    ) -> Tuple[bool, str, Optional[str]]:
        """上传头像"""
        # 验证是图片
        ext = Path(filename).suffix.lower()
        if ext not in [".jpg", '.jpeg', '.png', ".gif"]:
            return False, '仅支持JPG/PNG/GIF格式', None

        # 上传文件
        success, message, file_info = self.upload_service.upload_file(
            user_id, data, f'avatar_{user_id}{ext}', FileType.IMAGE
        )

        if success:
            self.user_avatars[user_id] = file_info.url
            return True, "头像上传成功", file_info.url

        return False, message, None

    def get_avatar(self, user_id: int) -> str:
        """获取用户头像"""
        return self.user_avatars.get(user_id, self.DEFAULT_AVATARS[user_id % len(self.DEFAULT_AVATARS)])

    def get_default_avatars(self) -> List[str]:
        """获取默认头像列表"""
        return self.DEFAULT_AVATARS


# ==================== 统一文件服务 ====================

class FileService:
    """统一文件服务"""

    def __init__(self):
        self.upload = FileUploadService()
        self.avatar = AvatarService(self.upload)


# 全局服务实例
file_service = FileService()
