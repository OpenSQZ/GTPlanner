"""
多模态消息辅助工具

提供便捷函数帮助前端构建符合 OpenAI API 标准的多模态消息格式。
"""

from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import base64


def create_text_content(text: str) -> Dict[str, Any]:
    """
    创建文本内容部分
    
    Args:
        text: 文本内容
    
    Returns:
        文本内容字典
    """
    return {
        "type": "text",
        "text": text
    }


def create_image_url_content(
    url: str,
    detail: str = "auto"
) -> Dict[str, Any]:
    """
    创建图片URL内容部分
    
    Args:
        url: 图片URL（可以是HTTP URL或Base64 Data URL）
        detail: 图片细节级别
            - "auto": 自动选择（默认）
            - "low": 低细节，更快更便宜
            - "high": 高细节，更慢更贵但更准确
    
    Returns:
        图片URL内容字典
    """
    return {
        "type": "image_url",
        "image_url": {
            "url": url,
            "detail": detail
        }
    }


def encode_image_to_data_url(
    image_data: bytes,
    image_format: str = "jpeg"
) -> str:
    """
    将图片字节数据编码为 Data URL 格式
    
    Args:
        image_data: 图片字节数据
        image_format: 图片格式（jpeg, png, gif, webp等）
    
    Returns:
        Base64 Data URL 字符串
    """
    base64_encoded = base64.b64encode(image_data).decode('utf-8')
    return f"data:image/{image_format};base64,{base64_encoded}"


def create_multimodal_content(
    text: Optional[str] = None,
    image_urls: Optional[List[str]] = None,
    image_data_list: Optional[List[Dict[str, Any]]] = None,
    image_detail: str = "auto"
) -> Union[str, List[Dict[str, Any]]]:
    """
    创建多模态内容（前端调用的主要函数）
    
    Args:
        text: 文本内容（可选）
        image_urls: 图片URL列表（HTTP URL或Base64 Data URL）
        image_data_list: 图片数据列表，格式：[
            {"data": bytes, "format": "jpeg"},
            ...
        ]
        image_detail: 图片细节级别（"auto", "low", "high"）
    
    Returns:
        - 如果只有文本：返回字符串
        - 如果包含图片：返回多模态内容列表
    
    Examples:
        >>> # 纯文本
        >>> content = create_multimodal_content(text="Hello")
        >>> # 返回: "Hello"
        
        >>> # 文本 + 图片URL
        >>> content = create_multimodal_content(
        ...     text="分析这张图片",
        ...     image_urls=["https://example.com/image.jpg"]
        ... )
        >>> # 返回: [
        ...   {"type": "text", "text": "分析这张图片"},
        ...   {"type": "image_url", "image_url": {"url": "https://...", "detail": "auto"}}
        ... ]
        
        >>> # 文本 + Base64图片
        >>> with open("image.jpg", "rb") as f:
        ...     image_bytes = f.read()
        >>> content = create_multimodal_content(
        ...     text="这是什么？",
        ...     image_data_list=[{"data": image_bytes, "format": "jpeg"}]
        ... )
    """
    content_parts = []
    
    # 添加文本内容
    if text:
        content_parts.append(create_text_content(text))
    
    # 添加图片URL
    if image_urls:
        for url in image_urls:
            content_parts.append(create_image_url_content(url, detail=image_detail))
    
    # 添加图片数据（需要先编码为Base64）
    if image_data_list:
        for image_info in image_data_list:
            image_data = image_info["data"]
            image_format = image_info.get("format", "jpeg")
            data_url = encode_image_to_data_url(image_data, image_format)
            content_parts.append(create_image_url_content(data_url, detail=image_detail))
    
    # 如果没有任何内容，返回空字符串
    if not content_parts:
        return ""
    
    # 如果只有文本，返回字符串（简化格式）
    if len(content_parts) == 1 and content_parts[0]["type"] == "text":
        return text
    
    # 返回多模态格式
    return content_parts


def build_multimodal_message(
    role: str,
    text: Optional[str] = None,
    image_urls: Optional[List[str]] = None,
    image_data_list: Optional[List[Dict[str, Any]]] = None,
    image_detail: str = "auto",
    timestamp: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    构建完整的多模态消息（包含 role 和 content）
    
    Args:
        role: 消息角色（"user", "assistant", "system"）
        text: 文本内容
        image_urls: 图片URL列表
        image_data_list: 图片数据列表
        image_detail: 图片细节级别
        timestamp: 时间戳（ISO格式字符串）
        metadata: 元数据
    
    Returns:
        完整的消息字典
    
    Examples:
        >>> # 构建用户消息（文本+图片）
        >>> message = build_multimodal_message(
        ...     role="user",
        ...     text="分析这个架构图",
        ...     image_urls=["data:image/jpeg;base64,/9j/4AAQ..."],
        ...     timestamp="2025-01-01T10:00:00Z"
        ... )
    """
    from datetime import datetime
    
    content = create_multimodal_content(
        text=text,
        image_urls=image_urls,
        image_data_list=image_data_list,
        image_detail=image_detail
    )
    
    message = {
        "role": role,
        "content": content,
        "timestamp": timestamp or datetime.now().isoformat()
    }
    
    if metadata:
        message["metadata"] = metadata
    
    return message


def validate_multimodal_content(content: Union[str, List[Dict[str, Any]]]) -> bool:
    """
    验证多模态内容格式是否正确
    
    Args:
        content: 待验证的内容
    
    Returns:
        是否有效
    """
    # 字符串格式有效
    if isinstance(content, str):
        return True
    
    # 列表格式验证
    if isinstance(content, list):
        for item in content:
            if not isinstance(item, dict):
                return False
            
            item_type = item.get("type")
            if item_type not in ["text", "image_url"]:
                return False
            
            if item_type == "text" and "text" not in item:
                return False
            
            if item_type == "image_url":
                if "image_url" not in item:
                    return False
                if "url" not in item["image_url"]:
                    return False
        
        return True
    
    return False


def extract_text_from_multimodal(content: Union[str, List[Dict[str, Any]]]) -> str:
    """
    从多模态内容中提取纯文本
    
    Args:
        content: 多模态内容
    
    Returns:
        提取的文本
    """
    if isinstance(content, str):
        return content
    
    if isinstance(content, list):
        text_parts = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        return " ".join(text_parts).strip()
    
    return ""


def count_images_in_content(content: Union[str, List[Dict[str, Any]]]) -> int:
    """
    统计多模态内容中的图片数量
    
    Args:
        content: 多模态内容
    
    Returns:
        图片数量
    """
    if isinstance(content, str):
        return 0
    
    if isinstance(content, list):
        return sum(
            1 for item in content
            if isinstance(item, dict) and item.get("type") == "image_url"
        )
    
    return 0


# ============================================================================
# 前端使用示例（供参考）
# ============================================================================

"""
前端使用示例（JavaScript/TypeScript）：

// 1. 纯文本消息
const textMessage = {
    role: "user",
    content: "设计一个用户管理系统",
    timestamp: new Date().toISOString()
};

// 2. 文本 + 图片URL（HTTP）
const messageWithHttpImage = {
    role: "user",
    content: [
        {
            type: "text",
            text: "分析这个架构图"
        },
        {
            type: "image_url",
            image_url: {
                url: "https://example.com/architecture.jpg",
                detail: "high"
            }
        }
    ],
    timestamp: new Date().toISOString()
};

// 3. 文本 + Base64图片（用户上传）
// 前端读取文件并转换为Base64
async function createMessageWithUploadedImage(file, text) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const base64Data = e.target.result; // 已经是 "data:image/...;base64,..." 格式
            
            const message = {
                role: "user",
                content: [
                    {
                        type: "text",
                        text: text
                    },
                    {
                        type: "image_url",
                        image_url: {
                            url: base64Data,
                            detail: "auto"
                        }
                    }
                ],
                timestamp: new Date().toISOString()
            };
            
            resolve(message);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file); // 读取为Base64
    });
}

// 使用示例
const fileInput = document.getElementById('imageUpload');
const file = fileInput.files[0];
const message = await createMessageWithUploadedImage(file, "这是什么架构？");

// 4. 多张图片
const messageWithMultipleImages = {
    role: "user",
    content: [
        {
            type: "text",
            text: "比较这两个设计方案"
        },
        {
            type: "image_url",
            image_url: {
                url: "data:image/jpeg;base64,/9j/4AAQ...",
                detail: "high"
            }
        },
        {
            type: "image_url",
            image_url: {
                url: "data:image/png;base64,iVBORw0KG...",
                detail: "high"
            }
        }
    ],
    timestamp: new Date().toISOString()
};

// 5. 构建对话历史（包含多模态消息）
const dialogueHistory = [
    {
        role: "user",
        content: [
            { type: "text", text: "这是我的系统架构图" },
            { type: "image_url", image_url: { url: "data:image/...", detail: "high" } }
        ],
        timestamp: "2025-01-01T10:00:00Z"
    },
    {
        role: "assistant",
        content: "我看到了一个基于微服务的架构图，包含API网关、用户服务、订单服务...",
        timestamp: "2025-01-01T10:00:05Z"
    },
    {
        role: "user",
        content: "请帮我生成设计文档",
        timestamp: "2025-01-01T10:00:10Z"
    }
];

// 6. 发送到后端
const response = await fetch('/api/chat/agent', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        session_id: "session_123",
        dialogue_history: dialogueHistory,
        tool_execution_results: {},
        session_metadata: {
            language: "zh"
        }
    })
});
"""

