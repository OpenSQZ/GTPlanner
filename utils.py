"""
工具类 - 使用HTTP请求直接调用阿里云百炼API
"""
import json
import asyncio
import requests
from typing import Dict, List, Any, Optional, Union
import docx
import PyPDF2
import io
import base64
from PIL import Image
from config import Config

class LLMClient:
    """大语言模型客户端 - 直接调用阿里云百炼API"""
    
    def __init__(self):
        self.api_key = Config.DASHSCOPE_API_KEY
        self.base_url = Config.DASHSCOPE_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = Config.TEXT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """文本对话完成"""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # 在线程池中运行同步HTTP请求
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                raise Exception(f"API调用失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")
    
    async def vision_completion(
        self, 
        text_prompt: str, 
        image_data: str,
        model: str = Config.VISION_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """视觉理解完成"""
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        }
                    ]
                }
            ]
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # 在线程池中运行同步HTTP请求
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                raise Exception(f"API调用失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"视觉模型调用失败: {str(e)}")


class FileProcessor:
    """文件处理器"""
    
    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        """从Word文档提取文本"""
        try:
            doc = docx.Document(io.BytesIO(file_content))
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return "\n".join(text)
        except Exception as e:
            raise Exception(f"Word文档解析失败: {str(e)}")
    
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """从PDF文档提取文本"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = []
            for page in pdf_reader.pages:
                text.append(page.extract_text())
            return "\n".join(text)
        except Exception as e:
            raise Exception(f"PDF文档解析失败: {str(e)}")
    
    @staticmethod
    def process_image_to_base64(file_content: bytes) -> str:
        """将图片转换为base64编码"""
        try:
            # 打开图片并转换为RGB格式
            image = Image.open(io.BytesIO(file_content))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 压缩图片以减少大小
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            
            # 转换为base64
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return image_base64
        except Exception as e:
            raise Exception(f"图片处理失败: {str(e)}")


class ResponseFormatter:
    """响应格式化器"""
    
    @staticmethod
    def success_response(data: Any, message: str = "成功") -> Dict[str, Any]:
        """成功响应格式"""
        return {
            "code": 200,
            "message": message,
            "data": data,
            "success": True
        }
    
    @staticmethod
    def error_response(message: str, code: int = 400) -> Dict[str, Any]:
        """错误响应格式"""
        return {
            "code": code,
            "message": message,
            "data": None,
            "success": False
        }
    
    @staticmethod
    def parse_json_response(text: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
            # 查找JSON格式内容
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # 如果没有找到JSON格式，返回原文本
                return {"content": text.strip()}
        except json.JSONDecodeError:
            # 如果JSON解析失败，返回原文本
            return {"content": text.strip()}


def validate_file_type(filename: str, file_type: str) -> bool:
    """验证文件类型"""
    if file_type not in Config.ALLOWED_FILE_TYPES:
        return False
    
    file_ext = '.' + filename.split('.')[-1].lower()
    return file_ext in Config.ALLOWED_FILE_TYPES[file_type]


def validate_file_size(file_size: int) -> bool:
    """验证文件大小"""
    return file_size <= Config.MAX_FILE_SIZE
