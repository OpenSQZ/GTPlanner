"""
医疗智能体后端主程序
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn

from agents import AgentFactory
from utils import FileProcessor, ResponseFormatter, validate_file_type, validate_file_size
from config import Config
from payment import WeChatPay, PAYMENT_SERVICES

# 创建FastAPI应用
app = FastAPI(
    title="医疗智能体后端系统",
    description="基于大语言模型的医疗智能体后端服务",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str

class ReportRequest(BaseModel):
    """报告解读请求模型"""
    report_text: str

class HealthEducationRequest(BaseModel):
    """健康科普请求模型"""
    question: str

class MedicationRequest(BaseModel):
    """药物咨询请求模型"""
    question: str

class PaymentRequest(BaseModel):
    """支付请求模型"""
    service_type: str  # report, medication, education, dermatology
    openid: str

class PaymentNotifyRequest(BaseModel):
    """支付回调请求模型"""
    xml_data: str


@app.get("/")
async def root():
    """根路径"""
    return ResponseFormatter.success_response(
        {"service": "医疗智能体后端系统", "version": "1.0.0"}, 
        "服务运行正常"
    )


@app.post("/api/medical-chat")
async def medical_chat(request: ChatRequest):
    """
    主入口：医疗智能体聊天接口
    支持意图识别 -> 智能分诊/症状自诊/病例生成/闲聊
    """
    try:
        user_message = request.message.strip()
        if not user_message:
            return ResponseFormatter.error_response("请输入有效的消息内容")
        
        # 步骤1：意图识别
        intent_agent = AgentFactory.create_agent("intent_recognition")
        intent_result = await intent_agent.process(user_message)
        
        if not intent_result["success"]:
            return intent_result
        
        intent_data = intent_result["data"]
        
        # 步骤2：根据意图调用对应智能体
        if "非医疗意图" in intent_data:
            # 调用闲聊智能体
            chat_agent = AgentFactory.create_agent("chat")
            final_result = await chat_agent.process(user_message)
            agent_type = "闲聊智能体"
            
        elif "医疗意图" in intent_data:
            medical_type = intent_data["医疗意图"]
            
            if medical_type == "智能分诊智能体":
                triage_agent = AgentFactory.create_agent("triage")
                final_result = await triage_agent.process(user_message)
                agent_type = "智能分诊智能体"
                
            elif medical_type == "症状自诊智能体":
                diagnosis_agent = AgentFactory.create_agent("self_diagnosis")
                final_result = await diagnosis_agent.process(user_message)
                agent_type = "症状自诊智能体"
                
            elif medical_type == "病例生成智能体":
                case_agent = AgentFactory.create_agent("case_generation")
                final_result = await case_agent.process(user_message)
                agent_type = "病例生成智能体"
                
            else:
                return ResponseFormatter.error_response(f"未识别的医疗意图类型: {medical_type}")
        else:
            return ResponseFormatter.error_response("意图识别结果格式错误")
        
        # 返回最终结果
        return ResponseFormatter.success_response({
            "intent_recognition": intent_data,
            "agent_type": agent_type,
            "response": final_result["data"]
        })
        
    except Exception as e:
        return ResponseFormatter.error_response(f"处理失败: {str(e)}")


@app.post("/api/report-interpretation")
async def report_interpretation(file: UploadFile = File(...), payment_verified: bool = False):
    """
    独立接口：报告解读智能体
    上传office文件并解读医学报告
    """
    try:
        # 检查是否需要支付验证
        agent_config = Config.AGENTS_CONFIG.get("report_interpretation")
        if agent_config and agent_config.get('requires_payment', False) and not payment_verified:
            return ResponseFormatter.error_response("该服务需要支付，请先完成支付", code="PAYMENT_REQUIRED")
        
        # 验证文件类型
        if not validate_file_type(file.filename, "document"):
            return ResponseFormatter.error_response("不支持的文件类型，请上传Word或PDF文件")
        
        # 读取文件内容
        file_content = await file.read()
        
        # 验证文件大小
        if not validate_file_size(len(file_content)):
            return ResponseFormatter.error_response(f"文件大小超过限制 ({Config.MAX_FILE_SIZE / 1024 / 1024}MB)")
        
        # 提取文本
        file_ext = file.filename.split('.')[-1].lower()
        
        if file_ext == 'docx':
            report_text = FileProcessor.extract_text_from_docx(file_content)
        elif file_ext == 'pdf':
            report_text = FileProcessor.extract_text_from_pdf(file_content)
        elif file_ext == 'txt':
            report_text = file_content.decode('utf-8', errors='ignore')
        else:
            return ResponseFormatter.error_response("不支持的文件格式")
        
        if not report_text.strip():
            return ResponseFormatter.error_response("文件内容为空或无法解析")
        
        # 调用报告解读智能体
        report_agent = AgentFactory.create_agent("report_interpretation")
        result = await report_agent.process(report_text)
        
        return result
        
    except Exception as e:
        return ResponseFormatter.error_response(f"报告解读失败: {str(e)}")


@app.post("/api/health-education")
async def health_education(request: HealthEducationRequest, payment_verified: bool = False):
    """
    独立接口：健康科普智能体
    提供权威医学知识科普
    """
    try:
        # 检查是否需要支付验证
        agent_config = Config.AGENTS_CONFIG.get("health_education")
        if agent_config and agent_config.get('requires_payment', False) and not payment_verified:
            return ResponseFormatter.error_response("该服务需要支付，请先完成支付", code="PAYMENT_REQUIRED")
        
        question = request.question.strip()
        if not question:
            return ResponseFormatter.error_response("请输入有效的问题")
        
        # 调用健康科普智能体
        education_agent = AgentFactory.create_agent("health_education")
        result = await education_agent.process(question)
        
        return result
        
    except Exception as e:
        return ResponseFormatter.error_response(f"健康科普失败: {str(e)}")


@app.post("/api/dermatology-consultation")
async def dermatology_consultation(
    file: UploadFile = File(...),
    symptoms: str = Form(""),
    payment_verified: bool = False
):
    """
    独立接口：皮肤病咨询智能体
    上传皮肤图片并提供诊断建议
    """
    try:
        # 检查是否需要支付验证
        agent_config = Config.AGENTS_CONFIG.get("dermatology")
        if agent_config and agent_config.get('requires_payment', False) and not payment_verified:
            return ResponseFormatter.error_response("该服务需要支付，请先完成支付", code="PAYMENT_REQUIRED")
        
        # 验证文件类型
        if not validate_file_type(file.filename, "image"):
            return ResponseFormatter.error_response("不支持的图片格式，请上传JPG、PNG等图片文件")
        
        # 读取文件内容
        file_content = await file.read()
        
        # 验证文件大小
        if not validate_file_size(len(file_content)):
            return ResponseFormatter.error_response(f"文件大小超过限制 ({Config.MAX_FILE_SIZE / 1024 / 1024}MB)")
        
        # 处理图片
        image_base64 = FileProcessor.process_image_to_base64(file_content)
        
        # 调用皮肤病咨询智能体
        dermatology_agent = AgentFactory.create_agent("dermatology")
        result = await dermatology_agent.process(image_base64, symptoms)
        
        return result
        
    except Exception as e:
        return ResponseFormatter.error_response(f"皮肤病咨询失败: {str(e)}")


@app.post("/api/medication-consultation")
async def medication_consultation(request: MedicationRequest, payment_verified: bool = False):
    """
    独立接口：药物咨询智能体
    基于药品说明书提供用药指导
    """
    try:
        # 检查是否需要支付验证
        agent_config = Config.AGENTS_CONFIG.get("medication")
        if agent_config and agent_config.get('requires_payment', False) and not payment_verified:
            return ResponseFormatter.error_response("该服务需要支付，请先完成支付", code="PAYMENT_REQUIRED")
        
        question = request.question.strip()
        if not question:
            return ResponseFormatter.error_response("请输入有效的药物咨询问题")
        
        # 调用药物咨询智能体
        medication_agent = AgentFactory.create_agent("medication")
        result = await medication_agent.process(question)
        
        return result
        
    except Exception as e:
        return ResponseFormatter.error_response(f"药物咨询失败: {str(e)}")


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return ResponseFormatter.success_response({"status": "healthy"}, "服务健康")


@app.get("/api/config")
async def get_config():
    """获取配置信息（调试用）"""
    return ResponseFormatter.success_response({
        "agents": list(Config.AGENTS_CONFIG.keys()),
        "models": {
            "text_model": Config.TEXT_MODEL,
            "vision_model": Config.VISION_MODEL
        }
    })


# 支付相关接口
@app.post("/api/payment/create")
async def create_payment(request: PaymentRequest):
    """
    创建支付订单
    """
    try:
        service_type = request.service_type
        openid = request.openid
        
        # 验证服务类型
        if service_type not in PAYMENT_SERVICES:
            return ResponseFormatter.error_response("不支持的服务类型")
        
        # 检查服务是否需要支付
        agent_config = Config.AGENTS_CONFIG.get(service_type)
        if not agent_config or not agent_config.get('requires_payment', False):
            return ResponseFormatter.error_response("该服务不需要支付")
        
        # 创建支付订单
        wechat_pay = WeChatPay()
        service_info = PAYMENT_SERVICES[service_type]
        
        result = wechat_pay.create_order(
            openid=openid,
            service_type=service_type,
            description=service_info['description']
        )
        
        if result['success']:
            return ResponseFormatter.success_response(result['data'], "支付订单创建成功")
        else:
            return ResponseFormatter.error_response(result['message'])
            
    except Exception as e:
        return ResponseFormatter.error_response(f"创建支付订单失败: {str(e)}")


@app.post("/api/payment/query")
async def query_payment(out_trade_no: str):
    """
    查询支付状态
    """
    try:
        wechat_pay = WeChatPay()
        result = wechat_pay.query_order(out_trade_no)
        
        if result['success']:
            return ResponseFormatter.success_response(result['data'], "查询成功")
        else:
            return ResponseFormatter.error_response(result['message'])
            
    except Exception as e:
        return ResponseFormatter.error_response(f"查询支付状态失败: {str(e)}")


@app.post("/api/payment/notify")
async def payment_notify(request: PaymentNotifyRequest):
    """
    支付回调接口
    """
    try:
        wechat_pay = WeChatPay()
        result = wechat_pay.verify_notify(request.xml_data)
        
        if result['success']:
            # 这里可以添加支付成功后的业务逻辑
            # 比如更新用户权限、记录支付记录等
            return ResponseFormatter.success_response(None, "支付回调处理成功")
        else:
            return ResponseFormatter.error_response(result['message'])
            
    except Exception as e:
        return ResponseFormatter.error_response(f"支付回调处理失败: {str(e)}")


@app.get("/api/payment/services")
async def get_payment_services():
    """
    获取付费服务列表
    """
    try:
        paid_services = {}
        for service_type, config in Config.AGENTS_CONFIG.items():
            if config.get('requires_payment', False):
                paid_services[service_type] = {
                    'name': config['name'],
                    'description': config['description'],
                    'price': config['price']
                }
        
        return ResponseFormatter.success_response(paid_services, "获取付费服务列表成功")
        
    except Exception as e:
        return ResponseFormatter.error_response(f"获取付费服务列表失败: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG
    )
