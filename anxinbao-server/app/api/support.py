"""
客户支持API
提供智能客服、工单系统、FAQ知识库、用户反馈等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.services.support_service import (
    support_service,
    IntentType,
    TicketPriority,
    TicketStatus,
    TicketCategory,
    FeedbackType
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/support", tags=["客户支持"])


# ==================== 请求模型 ====================

class SendMessageRequest(BaseModel):
    """发送消息请求"""
    session_id: str = Field(..., description='会话ID')
    content: str = Field(..., max_length=500, description="消息内容")


class CreateTicketRequest(BaseModel):
    """创建工单请求"""
    category: str = Field(..., description="分类: account/payment/device/function/complaint/other")
    priority: str = Field("medium", description="优先级: low/medium/high/urgent")
    subject: str = Field(..., max_length=100, description='主题')
    description: str = Field(..., max_length=2000, description='详细描述')
    attachments: Optional[List[str]] = Field(None, description="附件列表")


class AddCommentRequest(BaseModel):
    """添加评论请求"""
    content: str = Field(..., max_length=1000, description='评论内容')
    attachments: Optional[List[str]] = Field(None, description="附件列表")


class SubmitFeedbackRequest(BaseModel):
    """提交反馈请求"""
    feedback_type: str = Field(..., description="类型: bug/feature/experience/praise/other")
    title: str = Field(..., max_length=100, description='标题')
    content: str = Field(..., max_length=2000, description='详细内容')
    rating: Optional[int] = Field(None, ge=1, le=5, description='评分1-5')
    app_version: Optional[str] = Field(None, description='APP版本')
    device_info: Optional[str] = Field(None, description='设备信息')
    screenshots: Optional[List[str]] = Field(None, description="截图")


class SubmitRatingRequest(BaseModel):
    """提交评分请求"""
    rating: int = Field(..., ge=1, le=5, description='评分1-5')
    review: Optional[str] = Field(None, max_length=500, description="评价内容")


# ==================== 智能客服API ====================

@router.post("/chat/sessions")
async def create_chat_session(current_user: dict = Depends(get_current_user)):
    """
    创建客服会话

    开始与智能客服对话
    """
    user_id = int(current_user['sub'])

    session = support_service.chatbot.create_session(user_id)

    return {
        'session': session.to_dict(),
        'messages': [m.to_dict() for m in session.messages],
        'message': '会话已创建，欢迎您！'
    }


@router.post("/chat/send")
async def send_chat_message(
    request: SendMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    发送消息

    向智能客服发送消息并获取回复
    """
    user_id = int(current_user['sub'])

    reply = support_service.chatbot.send_message(
        request.session_id,
        user_id,
        request.content
    )

    if not reply:
        raise HTTPException(status_code=404, detail='会话不存在或已关闭')

    session = support_service.chatbot.get_session(request.session_id)

    return {
        "reply": reply.to_dict(),
        "session_status": session.status if session else 'unknown'
    }


@router.get("/chat/sessions")
async def get_my_chat_sessions(current_user: dict = Depends(get_current_user)):
    """
    获取我的会话列表
    """
    user_id = int(current_user['sub'])

    sessions = support_service.chatbot.get_user_sessions(user_id)

    return {
        'sessions': [s.to_dict() for s in sessions],
        'count': len(sessions)
    }


@router.get("/chat/sessions/{session_id}")
async def get_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取会话详情

    包含所有历史消息
    """
    user_id = int(current_user['sub'])

    session = support_service.chatbot.get_session(session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404, detail='会话不存在')

    return {
        'session': session.to_dict(),
        "messages": [m.to_dict() for m in session.messages]
    }


@router.post("/chat/sessions/{session_id}/transfer")
async def request_transfer_to_agent(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    请求转接人工客服
    """
    user_id = int(current_user['sub'])

    session = support_service.chatbot.get_session(session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404, detail='会话不存在')

    # 模拟分配一个客服
    agent_id = 1001
    success = support_service.chatbot.transfer_to_agent(session_id, agent_id)

    if not success:
        raise HTTPException(status_code=400, detail='转接失败')

    return {
        'success': True,
        'agent_id': agent_id,
        "message": "正在为您转接人工客服，请稍候..."
    }


@router.post("/chat/sessions/{session_id}/close")
async def close_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    关闭会话
    """
    user_id = int(current_user['sub'])

    session = support_service.chatbot.get_session(session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404, detail='会话不存在')

    support_service.chatbot.close_session(session_id)

    return {
        'success': True,
        "message": "会话已关闭，感谢您的咨询！"
    }


# ==================== 工单API ====================

@router.post("/tickets")
async def create_ticket(
    request: CreateTicketRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    创建工单

    用于提交需要人工处理的问题
    """
    user_id = int(current_user['sub'])

    try:
        category = TicketCategory(request.category)
    except ValueError:
        valid_categories = [c.value for c in TicketCategory]
        raise HTTPException(
            status_code=400,
            detail=f"无效的分类，可选: {valid_categories}"
        )

    try:
        priority = TicketPriority(request.priority)
    except ValueError:
        priority = TicketPriority.MEDIUM

    ticket = support_service.ticket.create_ticket(
        user_id,
        category,
        priority,
        request.subject,
        request.description,
        request.attachments
    )

    return {
        'success': True,
        'ticket': ticket.to_dict(),
        "message": f"工单已创建，编号: {ticket.ticket_id}"
    }


@router.get("/tickets")
async def get_my_tickets(
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取我的工单列表
    """
    user_id = int(current_user['sub'])

    status_filter = None
    if status:
        try:
            status_filter = TicketStatus(status)
        except ValueError:
            pass

    tickets = support_service.ticket.get_user_tickets(user_id, status_filter)

    return {
        'tickets': [t.to_dict() for t in tickets],
        'count': len(tickets)
    }


@router.get("/tickets/{ticket_id}")
async def get_ticket_detail(
    ticket_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取工单详情
    """
    user_id = int(current_user['sub'])

    ticket = support_service.ticket.get_ticket(ticket_id)
    if not ticket or ticket.user_id != user_id:
        raise HTTPException(status_code=404, detail='工单不存在')

    return {
        'ticket': ticket.to_dict(),
        "comments": [c.to_dict() for c in ticket.comments]
    }


@router.post("/tickets/{ticket_id}/comments")
async def add_ticket_comment(
    ticket_id: str,
    request: AddCommentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    添加工单评论
    """
    user_id = int(current_user['sub'])

    ticket = support_service.ticket.get_ticket(ticket_id)
    if not ticket or ticket.user_id != user_id:
        raise HTTPException(status_code=404, detail='工单不存在')

    comment = support_service.ticket.add_comment(
        ticket_id,
        user_id,
        'user',
        request.content,
        request.attachments
    )

    if not comment:
        raise HTTPException(status_code=400, detail='添加评论失败')

    return {
        'success': True,
        "comment": comment.to_dict()
    }


# ==================== FAQ API ====================

@router.get("/faq/categories")
async def get_faq_categories():
    """
    获取FAQ分类列表
    """
    categories = support_service.faq.get_categories()
    return {'categories': categories}


@router.get("/faq/search")
async def search_faqs(
    q: str = Query(..., min_length=1, description='搜索关键词'),
    category: Optional[str] = Query(None, description="分类筛选"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    搜索FAQ
    """
    results = support_service.faq.search_faqs(q, category, limit)

    return {
        'results': [f.to_dict() for f in results],
        'count': len(results),
        'query': q
    }


@router.get("/faq/popular")
async def get_popular_faqs(limit: int = Query(10, ge=1, le=20)):
    """
    获取热门FAQ
    """
    faqs = support_service.faq.get_popular_faqs(limit)
    return {
        'faqs': [f.to_dict() for f in faqs],
        'count': len(faqs)
    }


@router.get("/faq/category/{category}")
async def get_faqs_by_category(category: str):
    """
    获取分类下的FAQ列表
    """
    faqs = support_service.faq.get_faqs_by_category(category)
    return {
        'category': category,
        'faqs': [f.to_dict() for f in faqs],
        'count': len(faqs)
    }


@router.get("/faq/{faq_id}")
async def get_faq_detail(faq_id: str):
    """
    获取FAQ详情
    """
    faq = support_service.faq.get_faq(faq_id)
    if not faq:
        raise HTTPException(status_code=404, detail='FAQ不存在')

    return {"faq": faq.to_dict()}


@router.post("/faq/{faq_id}/rate")
async def rate_faq(
    faq_id: str,
    helpful: bool = Query(..., description="是否有帮助")
):
    """
    评价FAQ是否有帮助
    """
    success = support_service.faq.rate_faq(faq_id, helpful)
    if not success:
        raise HTTPException(status_code=404, detail='FAQ不存在')

    return {
        'success': True,
        'faq_id': faq_id,
        'helpful': helpful,
        'message': '感谢您的反馈！'
    }


# ==================== 反馈API ====================

@router.post("/feedback")
async def submit_feedback(
    request: SubmitFeedbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    提交反馈

    用于提交问题报告、功能建议等
    """
    user_id = int(current_user['sub'])

    try:
        feedback_type = FeedbackType(request.feedback_type)
    except ValueError:
        valid_types = [t.value for t in FeedbackType]
        raise HTTPException(
            status_code=400,
            detail=f"无效的反馈类型，可选: {valid_types}"
        )

    feedback = support_service.feedback.submit_feedback(
        user_id,
        feedback_type,
        request.title,
        request.content,
        request.rating,
        request.app_version,
        request.device_info,
        request.screenshots
    )

    return {
        'success': True,
        'feedback': feedback.to_dict(),
        "message": "感谢您的反馈，我们会认真处理！"
    }


@router.get("/feedback")
async def get_my_feedbacks(current_user: dict = Depends(get_current_user)):
    """
    获取我的反馈列表
    """
    user_id = int(current_user['sub'])

    feedbacks = support_service.feedback.get_user_feedbacks(user_id)

    return {
        'feedbacks': [f.to_dict() for f in feedbacks],
        'count': len(feedbacks)
    }


@router.get("/feedback/{feedback_id}")
async def get_feedback_detail(
    feedback_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取反馈详情
    """
    user_id = int(current_user['sub'])

    feedback = support_service.feedback.get_feedback(feedback_id)
    if not feedback or feedback.user_id != user_id:
        raise HTTPException(status_code=404, detail='反馈不存在')

    return {'feedback': feedback.to_dict()}


@router.post("/rating")
async def submit_app_rating(
    request: SubmitRatingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    提交应用评分
    """
    user_id = int(current_user['sub'])

    rating = support_service.feedback.submit_rating(
        user_id,
        request.rating,
        request.review
    )

    return {
        'success': True,
        'rating': rating.to_dict(),
        'message': "感谢您的评价！"
    }


@router.get("/rating/stats")
async def get_rating_statistics():
    """
    获取应用评分统计
    """
    stats = support_service.feedback.get_rating_stats()
    return stats


# ==================== 帮助中心首页 ====================

@router.get("/help")
async def get_help_center():
    """
    获取帮助中心首页数据
    """
    categories = support_service.faq.get_categories()
    popular_faqs = support_service.faq.get_popular_faqs(5)

    return {
        'categories': categories,
        "popular_faqs": [f.to_dict() for f in popular_faqs],
        'contact': {
            'phone': "400-888-8888",
            'email': "support@anxinbao.com",
            'working_hours': "周一至周日 8:00-22:00"
        },
        "quick_actions": [
            {'name': '在线客服', 'action': 'chat'},
            {'name': '提交工单', 'action': 'ticket'},
            {'name': '常见问题', 'action': 'faq'},
            {'name': '反馈建议', 'action': "feedback"}
        ]
    }
