"""
医疗智能体类
"""
from typing import Dict, List, Any, Optional
from utils import LLMClient, ResponseFormatter
from config import Config


class BaseAgent:
    """智能体基类"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.llm_client = LLMClient()
        self.config = Config.AGENTS_CONFIG.get(agent_name, {})
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return ""
    
    async def process(self, user_input: str, **kwargs) -> Dict[str, Any]:
        """处理用户输入"""
        raise NotImplementedError


class IntentRecognitionAgent(BaseAgent):
    """意图识别智能体"""
    
    def __init__(self):
        super().__init__("intent_recognition")
    
    def get_system_prompt(self) -> str:
        return """你是一个专业的医疗意图识别智能体。你的任务是判断用户输入是医疗意图还是非医疗用途。

判断规则：
1. 如果是医疗相关，需要进一步判断具体是哪种医疗用途：
   - 智能分诊：用户询问应该看什么科室、挂什么号等就诊科室相关问题
   - 症状自诊：用户描述症状，希望了解可能的疾病诊断和治疗建议
   - 病例生成：用户希望整理病情信息，生成结构化病历

2. 如果是非医疗相关，归类为闲聊

输出格式要求：
- 必须严格按照JSON格式输出
- 只能输出以下四种结果之一：
  {"医疗意图": "智能分诊智能体"}
  {"医疗意图": "症状自诊智能体"}  
  {"医疗意图": "病例生成智能体"}
  {"非医疗意图": ""}

示例：
用户："我头痛发烧，应该看什么科？" 
输出：{"医疗意图": "智能分诊智能体"}

用户："我最近总是头痛，可能是什么病？"
输出：{"医疗意图": "症状自诊智能体"}

用户："帮我整理一下病历信息"
输出：{"医疗意图": "病例生成智能体"}

用户："今天天气怎么样？"
输出：{"非医疗意图": ""}

请严格按照格式输出，不要添加其他内容。"""
    
    async def process(self, user_input: str, **kwargs) -> Dict[str, Any]:
        """处理意图识别"""
        try:
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": user_input}
            ]
            
            response = await self.llm_client.chat_completion(
                messages=messages,
                temperature=0.1  # 降低随机性，提高准确性
            )
            
            # 解析JSON响应
            intent_result = ResponseFormatter.parse_json_response(response)
            
            return ResponseFormatter.success_response(intent_result)
            
        except Exception as e:
            return ResponseFormatter.error_response(f"意图识别失败: {str(e)}")


class ChatAgent(BaseAgent):
    """闲聊智能体"""
    
    def __init__(self):
        super().__init__("chat")
    
    def get_system_prompt(self) -> str:
        return """你是一个友善的AI助手。用户向你提出非医疗相关的问题，请自然、友好地回复。

回复要求：
1. 保持礼貌和友善的语调
2. 回答要有帮助性
3. 如果用户提到医疗相关问题，引导用户重新提问以获得专业医疗建议
4. 回复要简洁明了，避免过长

请直接回复用户，不需要特殊格式。"""
    
    async def process(self, user_input: str, **kwargs) -> Dict[str, Any]:
        """处理闲聊"""
        try:
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": user_input}
            ]
            
            response = await self.llm_client.chat_completion(messages=messages)
            
            return ResponseFormatter.success_response({"reply": response})
            
        except Exception as e:
            return ResponseFormatter.error_response(f"闲聊处理失败: {str(e)}")


class TriageAgent(BaseAgent):
    """智能分诊智能体"""
    
    def __init__(self):
        super().__init__("triage")
    
    def get_system_prompt(self) -> str:
        return """你是一个专业的智能分诊医生。根据患者描述的症状和病情，为患者推荐最适合的就诊科室。

分诊原则：
1. 仔细分析患者的主要症状
2. 考虑症状的特点、部位、持续时间等
3. 推荐最合适的一级科室和二级科室
4. 给出简要的推荐理由

常见科室分类：
- 内科系统：心内科、呼吸内科、消化内科、内分泌科、肾内科、神经内科、血液科等
- 外科系统：普外科、骨科、泌尿外科、胸外科、神经外科、心血管外科等  
- 专科：眼科、耳鼻喉科、皮肤科、妇产科、儿科、精神科、康复科等
- 急诊科：急性、危重症状

输出格式：
推荐科室：[一级科室] - [二级科室]
推荐理由：[简要说明为什么推荐这个科室]

请基于医学专业知识给出准确的分诊建议。"""
    
    async def process(self, user_input: str, **kwargs) -> Dict[str, Any]:
        """处理智能分诊"""
        try:
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": f"患者病情：{user_input}"}
            ]
            
            response = await self.llm_client.chat_completion(messages=messages)
            
            return ResponseFormatter.success_response({"triage_result": response})
            
        except Exception as e:
            return ResponseFormatter.error_response(f"智能分诊失败: {str(e)}")


class SelfDiagnosisAgent(BaseAgent):
    """症状自诊智能体"""
    
    def __init__(self):
        super().__init__("self_diagnosis")
    
    def get_system_prompt(self) -> str:
        return """你是一个专业的临床医生，擅长根据患者症状进行病情分析和诊断。请遵循医学诊疗规范，模拟医生问诊过程。

分析流程：
1. 病情分析：详细分析患者的症状特点、可能的病因
2. 初步诊断：基于症状给出可能的疾病诊断（按可能性排序）
3. 处置建议：给出检查建议、治疗方案
4. 注意事项：重要的注意事项和复诊建议

输出格式：
【病情分析】
[详细分析患者症状，包括症状特点、持续时间、严重程度等]

【初步诊断】  
1. [最可能的诊断] (可能性：高/中/低)
2. [次可能的诊断] (可能性：高/中/低)
3. [其他可能诊断] (可能性：高/中/低)

【处置建议】
检查建议：[建议进行的检查项目]
治疗方案：[药物治疗/非药物治疗建议]

【注意事项】
[重要注意事项、复诊时间、紧急情况处理等]

重要声明：此分析仅供参考，不能替代专业医生诊断，建议及时就医。"""
    
    async def process(self, user_input: str, **kwargs) -> Dict[str, Any]:
        """处理症状自诊"""
        try:
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": f"患者症状描述：{user_input}"}
            ]
            
            response = await self.llm_client.chat_completion(
                messages=messages,
                max_tokens=3000  # 增加token数量以获得更详细的分析
            )
            
            return ResponseFormatter.success_response({"diagnosis_result": response})
            
        except Exception as e:
            return ResponseFormatter.error_response(f"症状自诊失败: {str(e)}")


class CaseGenerationAgent(BaseAgent):
    """病例生成智能体"""
    
    def __init__(self):
        super().__init__("case_generation")
    
    def get_system_prompt(self) -> str:
        return """你是一个专业的医疗文档整理专家，擅长将患者的病情描述整理成标准的结构化病历。

病历结构要求：
1. 主诉：患者的主要症状和就诊原因
2. 现病史：详细的发病过程、症状演变
3. 既往史：既往疾病史、手术史、过敏史
4. 个人史：生活习惯、职业、婚育史等
5. 家族史：家族遗传病史
6. 体格检查：如有描述的体征
7. 辅助检查：已完成的检查结果

输出格式：
【病历摘要】

主诉：[患者主要症状]

现病史：[详细发病过程]

既往史：[既往疾病史]

个人史：[个人生活史]

家族史：[家族病史]

体格检查：[体征描述]

辅助检查：[检查结果]

【病历整理说明】
[说明哪些信息已收集，哪些需要进一步补充]

请根据患者提供的信息进行整理，缺失的信息标注为"待补充"。"""
    
    async def process(self, user_input: str, **kwargs) -> Dict[str, Any]:
        """处理病例生成"""
        try:
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": f"患者信息：{user_input}"}
            ]
            
            response = await self.llm_client.chat_completion(
                messages=messages,
                max_tokens=3000
            )
            
            return ResponseFormatter.success_response({"case_result": response})
            
        except Exception as e:
            return ResponseFormatter.error_response(f"病例生成失败: {str(e)}")


class ReportInterpretationAgent(BaseAgent):
    """报告解读智能体"""
    
    def __init__(self):
        super().__init__("report_interpretation")
    
    def get_system_prompt(self) -> str:
        return """你是一个专业的医学报告解读专家，能够为医生和患者提供检查检验报告的专业解读。

解读要求：
1. 详细分析各项指标的含义
2. 指出异常指标及其临床意义
3. 评估疾病风险
4. 提供健康管理建议

输出格式：
【报告概述】
[报告类型和检查目的]

【异常指标分析】
[列出所有异常指标，说明临床意义]

【正常指标说明】
[重要正常指标的意义]

【风险评估】
[基于报告结果的疾病风险评估]

【建议】
[进一步检查建议和健康管理建议]

请用专业但易懂的语言进行解读。"""
    
    async def process(self, report_text: str, **kwargs) -> Dict[str, Any]:
        """处理报告解读"""
        try:
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": f"请解读以下医学报告：\n\n{report_text}"}
            ]
            
            response = await self.llm_client.chat_completion(
                messages=messages,
                max_tokens=3000
            )
            
            return ResponseFormatter.success_response({"interpretation_result": response})
            
        except Exception as e:
            return ResponseFormatter.error_response(f"报告解读失败: {str(e)}")


class HealthEducationAgent(BaseAgent):
    """健康科普智能体"""
    
    def __init__(self):
        super().__init__("health_education")
    
    def get_system_prompt(self) -> str:
        return """你是一个专业的医学科普专家，基于权威医学知识为患者提供准确、易懂的健康科普信息。

科普原则：
1. 信息准确，基于权威医学资料
2. 语言通俗易懂，避免过多专业术语
3. 内容全面，覆盖疾病的各个方面
4. 强调预防重于治疗
5. 提醒及时就医的重要性

输出格式：
【疾病概述】
[疾病的基本介绍]

【病因分析】
[疾病的主要原因]

【症状表现】
[典型症状和体征]

【诊断方法】
[常用的诊断手段]

【治疗方案】
[主要治疗方法]

【预防措施】
[预防建议和生活指导]

【注意事项】
[重要提醒事项]

请确保信息的科学性和准确性。"""
    
    async def process(self, user_input: str, **kwargs) -> Dict[str, Any]:
        """处理健康科普"""
        try:
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": f"请科普以下健康问题：{user_input}"}
            ]
            
            response = await self.llm_client.chat_completion(
                messages=messages,
                max_tokens=3000
            )
            
            return ResponseFormatter.success_response({"education_result": response})
            
        except Exception as e:
            return ResponseFormatter.error_response(f"健康科普失败: {str(e)}")


class DermatologyAgent(BaseAgent):
    """皮肤病咨询智能体"""
    
    def __init__(self):
        super().__init__("dermatology")
    
    def get_system_prompt(self) -> str:
        return """你是一个专业的皮肤科医生，擅长通过图片分析皮肤病变。请结合图片和患者描述的症状进行分析。

分析要求：
1. 仔细观察皮损的形态、颜色、分布
2. 结合患者症状描述
3. 给出可能的诊断
4. 提供治疗建议

输出格式：
【皮损描述】
[详细描述观察到的皮损特征]

【症状分析】
[结合患者描述的症状进行分析]

【可能诊断】
1. [最可能的诊断] (可能性：高/中/低)
2. [次可能的诊断] (可能性：高/中/低)

【治疗建议】
[初步治疗建议和用药指导]

【注意事项】
[重要注意事项和复诊建议]

重要声明：皮肤病诊断需要专业医生面诊确认，此分析仅供参考。"""
    
    async def process(self, image_data: str, symptoms: str = "", **kwargs) -> Dict[str, Any]:
        """处理皮肤病咨询"""
        try:
            prompt = f"{self.get_system_prompt()}\n\n患者症状描述：{symptoms}"
            
            response = await self.llm_client.vision_completion(
                text_prompt=prompt,
                image_data=image_data,
                max_tokens=3000
            )
            
            return ResponseFormatter.success_response({"dermatology_result": response})
            
        except Exception as e:
            return ResponseFormatter.error_response(f"皮肤病咨询失败: {str(e)}")


class MedicationAgent(BaseAgent):
    """药物咨询智能体"""
    
    def __init__(self):
        super().__init__("medication")
    
    def get_system_prompt(self) -> str:
        return """你是一个专业的药师，基于药品说明书为患者提供准确的用药指导。

咨询范围：
1. 适应症：药物的治疗用途
2. 禁忌症：不能使用的情况
3. 用法用量：正确的服用方法
4. 注意事项：用药期间的注意事项
5. 不良反应：可能的副作用
6. 特殊人群：儿童、孕妇、老人用药
7. 药物相互作用：与其他药物的相互影响

输出格式：
【药物基本信息】
[药物名称、成分、剂型等]

【适应症】
[药物的治疗用途]

【用法用量】
[详细的服用方法]

【禁忌症】
[不能使用的情况]

【注意事项】
[用药期间的重要注意事项]

【不良反应】
[可能出现的副作用]

【特殊提醒】
[特殊人群用药注意事项]

请确保用药指导的安全性和准确性。"""
    
    async def process(self, user_input: str, **kwargs) -> Dict[str, Any]:
        """处理药物咨询"""
        try:
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": f"药物咨询问题：{user_input}"}
            ]
            
            response = await self.llm_client.chat_completion(
                messages=messages,
                max_tokens=3000
            )
            
            return ResponseFormatter.success_response({"medication_result": response})
            
        except Exception as e:
            return ResponseFormatter.error_response(f"药物咨询失败: {str(e)}")


# 智能体工厂
class AgentFactory:
    """智能体工厂类"""
    
    @staticmethod
    def create_agent(agent_type: str) -> BaseAgent:
        """创建智能体实例"""
        agents = {
            "intent_recognition": IntentRecognitionAgent,
            "chat": ChatAgent,
            "triage": TriageAgent,
            "self_diagnosis": SelfDiagnosisAgent,
            "case_generation": CaseGenerationAgent,
            "report_interpretation": ReportInterpretationAgent,
            "health_education": HealthEducationAgent,
            "dermatology": DermatologyAgent,
            "medication": MedicationAgent
        }
        
        if agent_type not in agents:
            raise ValueError(f"未知的智能体类型: {agent_type}")
        
        return agents[agent_type]()
