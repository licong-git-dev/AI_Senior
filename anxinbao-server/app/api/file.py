"""
文件上传API
提供图片、音视频、文档的上传、管理接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.file_service import (
    file_service,
    FileType,
    FileStatus
)
from app.core.security import get_current_user, UserInfo
from app.core.limiter import limiter

router = APIRouter(prefix="/api/files", tags=["文件管理"])


# ==================== 请求模型 ====================

class UploadBase64Request(BaseModel):
    """Base64上传请求"""
    data: str = Field(..., description="Base64编码的文件数据")
    filename: str = Field(..., max_length=255, description='文件名')
    file_type: Optional[str] = Field(None, description='文件类型')
    tags: Optional[List[str]] = Field(None, description="标签")


class CreateUploadSessionRequest(BaseModel):
    """创建分片上传会话请求"""
    filename: str = Field(..., max_length=255, description='文件名')
    total_size: int = Field(..., gt=0, description='文件总大小(字节)')
    chunk_size: Optional[int] = Field(5 * 1024 * 1024, description="分片大小(字节)")


class UploadChunkRequest(BaseModel):
    """上传分片请求"""
    session_id: str = Field(..., description='上传会话ID')
    chunk_index: int = Field(..., ge=0, description="分片索引")
    data: str = Field(..., description="Base64编码的分片数据")


class UpdateFileRequest(BaseModel):
    """更新文件信息请求"""
    tags: Optional[List[str]] = Field(None, description='标签')
    metadata: Optional[Dict[str, Any]] = Field(None, description='元数据')


# ==================== 文件上传API ====================

@router.post("/upload")
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    file_type: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    上传文件

    支持图片、音频、视频、文档等文件类型
    """
    user_id = int(current_user.user_id)

    # 读取文件数据
    try:
        data = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'文件读取失败: {str(e)}')

    # 解析文件类型
    ftype = None
    if file_type:
        try:
            ftype = FileType(file_type)
        except ValueError:
            pass

    # 解析标签
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]

    success, message, file_info = file_service.upload.upload_file(
        user_id, data, file.filename, ftype, tag_list
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        'success': True,
        'file': file_info.to_dict(),
        "message": message
    }


@router.post("/upload/base64")
async def upload_base64(
    request: UploadBase64Request,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    上传Base64编码的文件

    适用于前端Canvas、相机拍照等场景
    """
    user_id = int(current_user.user_id)

    ftype = None
    if request.file_type:
        try:
            ftype = FileType(request.file_type)
        except ValueError:
            pass

    success, message, file_info = file_service.upload.upload_base64(
        user_id, request.data, request.filename, ftype
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        'success': True,
        'file': file_info.to_dict(),
        'message': message
    }


@router.post("/upload/multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    file_type: Optional[str] = Form(None),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    批量上传文件

    一次最多上传10个文件
    """
    user_id = int(current_user.user_id)

    if len(files) > 10:
        raise HTTPException(status_code=400, detail="一次最多上传10个文件")

    ftype = None
    if file_type:
        try:
            ftype = FileType(file_type)
        except ValueError:
            pass

    results = []
    for file in files:
        try:
            data = await file.read()
            success, message, file_info = file_service.upload.upload_file(
                user_id, data, file.filename, ftype
            )
            results.append({
                'filename': file.filename,
                'success': success,
                'message': message,
                'file': file_info.to_dict() if file_info else None
            })
        except Exception as e:
            results.append({
                'filename': file.filename,
                'success': False,
                'message': str(e),
                'file': None
            })

    success_count = sum(1 for r in results if r['success'])

    return {
        'success': success_count > 0,
        'results': results,
        "total": len(files),
        "success_count": success_count,
        "failed_count": len(files) - success_count
    }


# ==================== 分片上传API ====================

@router.post("/upload/session")
async def create_upload_session(
    request: CreateUploadSessionRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    创建分片上传会话

    用于大文件上传，支持断点续传
    """
    user_id = int(current_user.user_id)

    success, message, session = file_service.upload.create_upload_session(
        user_id,
        request.filename,
        request.total_size,
        request.chunk_size
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        'success': True,
        'session': session.to_dict(),
        'message': message
    }


@router.post("/upload/chunk")
async def upload_chunk(
    request: UploadChunkRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    上传文件分片

    分片上传后自动合并
    """
    import base64

    try:
        # 处理data URL格式
        data_str = request.data
        if ',' in data_str:
            data_str = data_str.split(",")[1]
        chunk_data = base64.b64decode(data_str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"分片数据格式错误: {str(e)}")

    success, message, result = file_service.upload.upload_chunk(
        request.session_id,
        request.chunk_index,
        chunk_data
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        'success': True,
        'result': result,
        "message": message
    }


@router.get("/upload/session/{session_id}")
async def get_upload_session(
    session_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取上传会话状态

    查看分片上传进度
    """
    session = file_service.upload.upload_sessions.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="上传会话不存在或已过期")

    return {
        'session': session.to_dict()
    }


# ==================== 文件管理API ====================

@router.get("/list")
async def get_file_list(
    file_type: Optional[str] = Query(None, description='文件类型筛选'),
    limit: int = Query(50, ge=1, le=200, description='返回数量'),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取文件列表

    获取当前用户上传的文件
    """
    user_id = int(current_user.user_id)

    ftype = None
    if file_type:
        try:
            ftype = FileType(file_type)
        except ValueError:
            pass

    files, total = file_service.upload.get_user_files(user_id, ftype, limit, offset)

    return {
        'files': [f.to_dict() for f in files],
        'total': total,
        'limit': limit,
        'offset': offset
    }


@router.get("/{file_id}")
async def get_file_info(
    file_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取文件详情
    """
    file_info = file_service.upload.get_file(file_id)

    if not file_info:
        raise HTTPException(status_code=404, detail='文件不存在')

    user_id = int(current_user.user_id)
    if file_info.user_id != user_id:
        raise HTTPException(status_code=403, detail='无权访问该文件')

    return {
        'file': file_info.to_dict()
    }


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    删除文件
    """
    user_id = int(current_user.user_id)

    success, message = file_service.upload.delete_file(file_id, user_id)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        'success': True,
        'message': message
    }


# ==================== 头像API ====================

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    上传头像

    仅支持JPG/PNG/GIF格式
    """
    user_id = int(current_user.user_id)

    try:
        data = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件读取失败: {str(e)}")

    success, message, avatar_url = file_service.avatar.upload_avatar(
        user_id, data, file.filename
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        'success': True,
        'avatar_url': avatar_url,
        'message': message
    }


@router.get("/avatar/me")
async def get_my_avatar(current_user: UserInfo = Depends(get_current_user)):
    """
    获取我的头像
    """
    user_id = int(current_user.user_id)

    avatar_url = file_service.avatar.get_avatar(user_id)

    return {
        'avatar_url': avatar_url
    }


@router.get("/avatar/defaults")
async def get_default_avatars(current_user: UserInfo = Depends(get_current_user)):
    """
    获取默认头像列表
    """
    avatars = file_service.avatar.get_default_avatars()

    return {
        'avatars': avatars
    }


# ==================== 存储统计API ====================

@router.get("/storage/usage")
async def get_storage_usage(current_user: UserInfo = Depends(get_current_user)):
    """
    获取存储使用情况

    查看已用存储空间
    """
    user_id = int(current_user.user_id)

    usage = file_service.upload.get_storage_usage(user_id)

    return usage


# ==================== 文件类型API ====================

@router.get("/types")
async def get_file_types(current_user: UserInfo = Depends(get_current_user)):
    """
    获取支持的文件类型
    """
    from app.services.file_service import FILE_TYPE_CONFIG

    types = []
    for ftype, config in FILE_TYPE_CONFIG.items():
        types.append({
            'type': ftype.value,
            'extensions': config['extensions'],
            'max_size': config['max_size'],
            'max_size_mb': config['max_size'] / 1024 / 1024
        })

    return {'types': types}
