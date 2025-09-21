"""
代码重复检测测试

验证代码重构后的重复率降低和功能兼容性。
"""

import pytest
import ast
import inspect
from typing import Dict, List, Set
from pathlib import Path

from agent.nodes.base_requirements_analysis_node import BaseRequirementsAnalysisNode
from agent.subflows.quick_design.nodes.quick_requirements_analysis_node import QuickRequirementsAnalysisNode
from agent.subflows.deep_design_docs.nodes.agent_requirements_analysis_node import AgentRequirementsAnalysisNode


class CodeDuplicationAnalyzer:
    """代码重复分析器"""
    
    def __init__(self):
        self.method_signatures: Dict[str, List[str]] = {}
        self.code_blocks: Dict[str, List[str]] = {}
    
    def analyze_class(self, cls, class_name: str):
        """分析类的方法签名和代码块"""
        self.method_signatures[class_name] = []
        self.code_blocks[class_name] = []
        
        for method_name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not method_name.startswith('_'):  # 只分析公共方法
                # 获取方法签名
                signature = str(inspect.signature(method))
                self.method_signatures[class_name].append(f"{method_name}{signature}")
                
                # 获取方法源码
                try:
                    source = inspect.getsource(method)
                    # 简化源码（移除注释和空行）
                    lines = [line.strip() for line in source.split('\n') 
                            if line.strip() and not line.strip().startswith('#')]
                    self.code_blocks[class_name].extend(lines)
                except:
                    pass
    
    def calculate_duplication_rate(self, class1: str, class2: str) -> float:
        """计算两个类之间的代码重复率"""
        if class1 not in self.code_blocks or class2 not in self.code_blocks:
            return 0.0
        
        blocks1 = set(self.code_blocks[class1])
        blocks2 = set(self.code_blocks[class2])
        
        if not blocks1 or not blocks2:
            return 0.0
        
        intersection = blocks1 & blocks2
        union = blocks1 | blocks2
        
        return len(intersection) / len(union) if union else 0.0
    
    def find_common_methods(self, class1: str, class2: str) -> Set[str]:
        """查找两个类的共同方法"""
        if class1 not in self.method_signatures or class2 not in self.method_signatures:
            return set()
        
        methods1 = set(self.method_signatures[class1])
        methods2 = set(self.method_signatures[class2])
        
        return methods1 & methods2


class TestCodeDuplication:
    """测试代码重复优化"""
    
    def setup_method(self):
        """设置测试"""
        self.analyzer = CodeDuplicationAnalyzer()
        
        # 分析相关类
        self.analyzer.analyze_class(BaseRequirementsAnalysisNode, "BaseRequirementsAnalysisNode")
        self.analyzer.analyze_class(QuickRequirementsAnalysisNode, "QuickRequirementsAnalysisNode")
        
        # 如果AgentRequirementsAnalysisNode存在，也分析它
        try:
            self.analyzer.analyze_class(AgentRequirementsAnalysisNode, "AgentRequirementsAnalysisNode")
        except:
            pass
    
    def test_base_class_extraction(self):
        """测试基类提取是否成功"""
        # 验证基类存在必要的抽象方法
        base_methods = self.analyzer.method_signatures.get("BaseRequirementsAnalysisNode", [])
        
        # 检查关键方法是否存在
        method_names = [method.split('(')[0] for method in base_methods]
        
        # 基类应该有这些核心方法
        expected_methods = [
            "_prep_impl", "_exec_impl", "_post_impl",
            "_extract_base_data", "_validate_required_fields",
            "_build_analysis_prompt"
        ]
        
        for expected_method in expected_methods:
            assert any(expected_method in method for method in method_names), \
                f"基类缺少方法: {expected_method}"
    
    def test_inheritance_structure(self):
        """测试继承结构是否正确"""
        # 验证QuickRequirementsAnalysisNode继承自BaseRequirementsAnalysisNode
        assert issubclass(QuickRequirementsAnalysisNode, BaseRequirementsAnalysisNode), \
            "QuickRequirementsAnalysisNode应该继承自BaseRequirementsAnalysisNode"
        
        # 验证子类实现了必要的抽象方法
        quick_node = QuickRequirementsAnalysisNode()
        
        # 检查抽象方法是否被实现
        assert hasattr(quick_node, '_prep_specific'), "缺少_prep_specific方法"
        assert hasattr(quick_node, '_process_analysis_result'), "缺少_process_analysis_result方法"
        assert hasattr(quick_node, '_post_specific'), "缺少_post_specific方法"
    
    def test_reduced_duplication(self):
        """测试代码重复率是否降低"""
        # 如果有多个需求分析节点类，检查它们之间的重复率
        classes = list(self.analyzer.code_blocks.keys())
        
        if len(classes) >= 2:
            # 计算重复率
            for i in range(len(classes)):
                for j in range(i + 1, len(classes)):
                    class1, class2 = classes[i], classes[j]
                    duplication_rate = self.analyzer.calculate_duplication_rate(class1, class2)
                    
                    # 重复率应该相对较低（基类提取后）
                    assert duplication_rate < 0.5, \
                        f"{class1}和{class2}之间的重复率过高: {duplication_rate:.2%}"
    
    def test_common_functionality_extraction(self):
        """测试共同功能是否被提取到基类"""
        # 检查基类是否包含了共同的功能
        base_methods = self.analyzer.method_signatures.get("BaseRequirementsAnalysisNode", [])
        
        # 基类应该包含数据提取、验证、提示词构建等共同功能
        common_functionality = [
            "_extract_base_data",
            "_validate_required_fields", 
            "_format_additional_data",
            "_build_analysis_prompt",
            "_analyze_standard"
        ]
        
        base_method_names = [method.split('(')[0] for method in base_methods]
        
        for func in common_functionality:
            assert any(func in method for method in base_method_names), \
                f"基类应该包含共同功能: {func}"
    
    @pytest.mark.asyncio
    async def test_functional_compatibility(self):
        """测试重构后的功能兼容性"""
        # 创建测试节点实例
        quick_node = QuickRequirementsAnalysisNode()
        
        # 模拟共享数据
        shared_data = {
            "user_requirements": "创建一个Web应用",
            "short_planning": "使用Python和FastAPI",
            "research_findings": {},
            "recommended_tools": [],
            "language": "zh"
        }
        
        # 测试准备阶段
        prep_result = await quick_node._prep_impl(shared_data)
        
        # 验证准备结果
        assert isinstance(prep_result, dict), "准备结果应该是字典"
        assert "user_requirements" in prep_result, "应该包含用户需求"
        assert "language" in prep_result, "应该包含语言设置"
        
        # 如果没有错误，测试执行阶段
        if "error" not in prep_result:
            # 模拟执行结果（避免实际调用LLM）
            mock_exec_result = {
                "analysis_result": "模拟分析结果",
                "analysis_success": True
            }
            
            # 测试后处理阶段
            post_result = await quick_node._post_impl(shared_data, prep_result, mock_exec_result)
            
            # 验证后处理结果
            assert post_result in ["success", "error"], "后处理应该返回有效状态"
    
    def test_configuration_flexibility(self):
        """测试配置灵活性"""
        # 测试不同配置的节点创建
        from agent.nodes.base_requirements_analysis_node import AnalysisType, ProcessingMode
        
        # 创建不同配置的节点
        quick_node = QuickRequirementsAnalysisNode()
        
        # 验证配置
        assert quick_node.analysis_type == AnalysisType.QUICK, "分析类型应该是QUICK"
        assert quick_node.processing_mode == ProcessingMode.STANDARD, "处理模式应该是STANDARD"
        assert "user_requirements" in quick_node.required_fields, "应该包含必需字段"
    
    def test_error_handling_consistency(self):
        """测试错误处理一致性"""
        quick_node = QuickRequirementsAnalysisNode()
        
        # 测试缺少必需字段的情况
        shared_data = {
            "short_planning": "使用Python",
            "language": "zh"
            # 故意缺少user_requirements
        }
        
        # 准备阶段应该返回错误
        import asyncio
        prep_result = asyncio.run(quick_node._prep_impl(shared_data))
        
        assert "error" in prep_result, "缺少必需字段时应该返回错误"
        assert "user_requirements" in prep_result["error"], "错误信息应该指出缺少的字段"


class TestArchitectureImprovement:
    """测试架构改进"""
    
    def test_strategy_pattern_implementation(self):
        """测试策略模式实现"""
        from agent.nodes.base_requirements_analysis_node import AnalysisType, ProcessingMode
        
        # 验证枚举类型的存在
        assert AnalysisType.QUICK in AnalysisType, "应该支持QUICK分析类型"
        assert AnalysisType.DEEP in AnalysisType, "应该支持DEEP分析类型"
        assert AnalysisType.AGENT in AnalysisType, "应该支持AGENT分析类型"
        
        assert ProcessingMode.STANDARD in ProcessingMode, "应该支持STANDARD处理模式"
        assert ProcessingMode.STREAMING in ProcessingMode, "应该支持STREAMING处理模式"
    
    def test_template_method_pattern(self):
        """测试模板方法模式"""
        # 验证基类定义了算法骨架
        base_class = BaseRequirementsAnalysisNode
        
        # 检查模板方法
        assert hasattr(base_class, '_prep_impl'), "应该有准备阶段模板方法"
        assert hasattr(base_class, '_exec_impl'), "应该有执行阶段模板方法"
        assert hasattr(base_class, '_post_impl'), "应该有后处理阶段模板方法"
        
        # 检查抽象方法（子类必须实现）
        import inspect
        abstract_methods = [
            method for method, obj in inspect.getmembers(base_class)
            if getattr(obj, '__isabstractmethod__', False)
        ]
        
        expected_abstract_methods = ['_prep_specific', '_process_analysis_result']
        for method in expected_abstract_methods:
            assert method in abstract_methods, f"应该有抽象方法: {method}"
    
    def test_code_reuse_metrics(self):
        """测试代码复用指标"""
        # 计算代码复用率
        analyzer = CodeDuplicationAnalyzer()
        analyzer.analyze_class(BaseRequirementsAnalysisNode, "Base")
        analyzer.analyze_class(QuickRequirementsAnalysisNode, "Quick")
        
        # 基类应该包含大部分共同逻辑
        base_methods = len(analyzer.method_signatures.get("Base", []))
        quick_methods = len(analyzer.method_signatures.get("Quick", []))
        
        # 子类方法数应该明显少于基类（因为继承了大部分功能）
        assert quick_methods < base_methods, "子类应该比基类方法更少（通过继承复用）"
        
        # 验证代码行数减少
        base_lines = len(analyzer.code_blocks.get("Base", []))
        quick_lines = len(analyzer.code_blocks.get("Quick", []))
        
        # 子类代码行数应该明显少于基类
        assert quick_lines < base_lines * 0.5, "子类代码行数应该显著少于基类"
