"""
验证器注册表

基于注册表模式的验证器管理，提供：
- 验证器类型注册
- 验证器实例管理
- 依赖关系管理
- 插件式验证器加载
- 验证器版本管理
- 热插拔支持
"""

import importlib
import inspect
from typing import Dict, Any, Optional, List, Type, Callable, Set
from threading import RLock
from .interfaces import IValidator, IValidationStrategy, IValidationRegistry
from .validation_result import ValidationError, ValidationSeverity


class ValidatorMetadata:
    """验证器元数据"""
    
    def __init__(
        self,
        validator_type: str,
        validator_class: Type,
        version: str = "1.0.0",
        description: str = "",
        dependencies: Optional[List[str]] = None,
        config_schema: Optional[Dict[str, Any]] = None
    ):
        self.validator_type = validator_type
        self.validator_class = validator_class
        self.version = version
        self.description = description
        self.dependencies = dependencies or []
        self.config_schema = config_schema or {}
        self.registration_time = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            元数据字典
        """
        return {
            "validator_type": self.validator_type,
            "validator_class": self.validator_class.__name__,
            "module": self.validator_class.__module__,
            "version": self.version,
            "description": self.description,
            "dependencies": self.dependencies,
            "config_schema": self.config_schema,
            "registration_time": self.registration_time
        }


class DependencyResolver:
    """依赖关系解析器"""
    
    def __init__(self):
        self.dependency_graph: Dict[str, Set[str]] = {}
    
    def add_dependency(self, validator_type: str, dependencies: List[str]) -> None:
        """添加依赖关系
        
        Args:
            validator_type: 验证器类型
            dependencies: 依赖的验证器类型列表
        """
        self.dependency_graph[validator_type] = set(dependencies)
    
    def resolve_order(self, validator_types: List[str]) -> List[str]:
        """解析验证器执行顺序
        
        Args:
            validator_types: 验证器类型列表
            
        Returns:
            按依赖关系排序的验证器类型列表
        """
        # 简单的拓扑排序实现
        resolved = []
        remaining = set(validator_types)
        
        while remaining:
            # 找到没有未解决依赖的验证器
            ready = []
            for validator_type in remaining:
                dependencies = self.dependency_graph.get(validator_type, set())
                unresolved_deps = dependencies - set(resolved)
                
                if not unresolved_deps:
                    ready.append(validator_type)
            
            if not ready:
                # 存在循环依赖，按原顺序返回剩余的
                resolved.extend(list(remaining))
                break
            
            # 添加就绪的验证器
            for validator_type in ready:
                resolved.append(validator_type)
                remaining.remove(validator_type)
        
        return resolved
    
    def check_circular_dependencies(self, validator_types: List[str]) -> List[str]:
        """检查循环依赖
        
        Args:
            validator_types: 验证器类型列表
            
        Returns:
            循环依赖的验证器类型列表
        """
        def has_cycle(start: str, visited: Set[str], path: Set[str]) -> bool:
            if start in path:
                return True
            if start in visited:
                return False
            
            visited.add(start)
            path.add(start)
            
            dependencies = self.dependency_graph.get(start, set())
            for dep in dependencies:
                if dep in validator_types and has_cycle(dep, visited, path):
                    return True
            
            path.remove(start)
            return False
        
        circular_deps = []
        visited = set()
        
        for validator_type in validator_types:
            if validator_type not in visited:
                if has_cycle(validator_type, visited, set()):
                    circular_deps.append(validator_type)
        
        return circular_deps


class ValidationRegistry(IValidationRegistry):
    """验证器注册表 - 统一的验证器管理和注册系统
    
    提供企业级的验证器管理功能：
    - 类型安全的验证器注册
    - 依赖关系管理和解析
    - 插件式验证器加载
    - 版本控制和兼容性检查
    - 热插拔支持
    """
    
    def __init__(self):
        self._validators: Dict[str, ValidatorMetadata] = {}
        self._instances: Dict[str, IValidator] = {}
        self._factory_functions: Dict[str, Callable[[Dict[str, Any]], IValidator]] = {}
        self.dependency_resolver = DependencyResolver()
        self._lock = RLock()
        
        # 注册统计
        self.registration_count = 0
        self.instance_creation_count = 0
        
        print("ValidationRegistry initialized")
    
    def register_validator(self, validator_type: str, validator_class: Type[IValidator], **metadata) -> None:
        """注册验证器类型
        
        Args:
            validator_type: 验证器类型标识
            validator_class: 验证器类
            **metadata: 额外的元数据
        """
        with self._lock:
            # 验证参数
            if not validator_type or not validator_class:
                raise ValueError("验证器类型和类不能为空")
            
            if not self._is_valid_validator_class(validator_class):
                raise ValueError(f"类 {validator_class.__name__} 不是有效的验证器类")
            
            # 创建元数据
            validator_metadata = ValidatorMetadata(
                validator_type=validator_type,
                validator_class=validator_class,
                version=metadata.get("version", "1.0.0"),
                description=metadata.get("description", ""),
                dependencies=metadata.get("dependencies", []),
                config_schema=metadata.get("config_schema", {})
            )
            
            # 注册验证器
            self._validators[validator_type] = validator_metadata
            
            # 注册依赖关系
            if validator_metadata.dependencies:
                self.dependency_resolver.add_dependency(validator_type, validator_metadata.dependencies)
            
            self.registration_count += 1
            print(f"✅ 验证器已注册: {validator_type} -> {validator_class.__name__}")
    
    def register_factory_function(self, validator_type: str, factory_func: Callable[[Dict[str, Any]], IValidator]) -> None:
        """注册验证器工厂函数
        
        Args:
            validator_type: 验证器类型标识
            factory_func: 工厂函数
        """
        with self._lock:
            self._factory_functions[validator_type] = factory_func
            print(f"✅ 验证器工厂函数已注册: {validator_type}")
    
    def get_validator(self, validator_type: str, config: Dict[str, Any]) -> Optional[IValidator]:
        """获取验证器实例
        
        Args:
            validator_type: 验证器类型标识
            config: 验证器配置
            
        Returns:
            验证器实例，如果类型不存在则返回None
        """
        with self._lock:
            # 检查是否已有缓存的实例（如果配置支持单例）
            if config.get("use_singleton", False):
                instance_key = f"{validator_type}:{hash(str(config))}"
                if instance_key in self._instances:
                    return self._instances[instance_key]
            
            # 尝试使用工厂函数创建
            if validator_type in self._factory_functions:
                try:
                    instance = self._factory_functions[validator_type](config)
                    if instance:
                        self.instance_creation_count += 1
                        
                        # 缓存单例实例
                        if config.get("use_singleton", False):
                            instance_key = f"{validator_type}:{hash(str(config))}"
                            self._instances[instance_key] = instance
                        
                        return instance
                except Exception as e:
                    print(f"Warning: Factory function failed for {validator_type}: {e}")
            
            # 尝试使用注册的类创建
            if validator_type in self._validators:
                try:
                    metadata = self._validators[validator_type]
                    instance = metadata.validator_class(config)
                    self.instance_creation_count += 1
                    
                    # 缓存单例实例
                    if config.get("use_singleton", False):
                        instance_key = f"{validator_type}:{hash(str(config))}"
                        self._instances[instance_key] = instance
                    
                    return instance
                except Exception as e:
                    print(f"Warning: Failed to create validator {validator_type}: {e}")
            
            return None
    
    def list_validators(self) -> List[str]:
        """列出所有已注册的验证器类型
        
        Returns:
            验证器类型列表
        """
        with self._lock:
            all_types = set(self._validators.keys())
            all_types.update(self._factory_functions.keys())
            return sorted(list(all_types))
    
    def unregister_validator(self, validator_type: str) -> bool:
        """注销验证器类型
        
        Args:
            validator_type: 验证器类型标识
            
        Returns:
            True表示注销成功，False表示类型不存在
        """
        with self._lock:
            removed = False
            
            if validator_type in self._validators:
                del self._validators[validator_type]
                removed = True
            
            if validator_type in self._factory_functions:
                del self._factory_functions[validator_type]
                removed = True
            
            # 清理相关的实例缓存
            keys_to_remove = [key for key in self._instances.keys() if key.startswith(f"{validator_type}:")]
            for key in keys_to_remove:
                del self._instances[key]
            
            return removed
    
    def get_validator_metadata(self, validator_type: str) -> Optional[ValidatorMetadata]:
        """获取验证器元数据
        
        Args:
            validator_type: 验证器类型
            
        Returns:
            验证器元数据，如果不存在则返回None
        """
        return self._validators.get(validator_type)
    
    def resolve_dependencies(self, validator_types: List[str]) -> List[str]:
        """解析验证器依赖关系
        
        Args:
            validator_types: 验证器类型列表
            
        Returns:
            按依赖关系排序的验证器类型列表
        """
        return self.dependency_resolver.resolve_order(validator_types)
    
    def validate_dependencies(self, validator_types: List[str]) -> List[str]:
        """验证依赖关系
        
        Args:
            validator_types: 验证器类型列表
            
        Returns:
            依赖问题列表
        """
        issues = []
        
        # 检查循环依赖
        circular_deps = self.dependency_resolver.check_circular_dependencies(validator_types)
        if circular_deps:
            issues.append(f"检测到循环依赖: {circular_deps}")
        
        # 检查缺失的依赖
        for validator_type in validator_types:
            if validator_type in self._validators:
                metadata = self._validators[validator_type]
                for dep in metadata.dependencies:
                    if dep not in validator_types and dep not in self._validators:
                        issues.append(f"验证器 {validator_type} 依赖的 {dep} 未注册")
        
        return issues
    
    def auto_register_from_module(self, module_name: str) -> int:
        """从模块自动注册验证器
        
        Args:
            module_name: 模块名称
            
        Returns:
            注册的验证器数量
        """
        try:
            module = importlib.import_module(module_name)
            registered_count = 0
            
            # 扫描模块中的验证器类
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if self._is_valid_validator_class(obj) and hasattr(obj, '__validator_type__'):
                    validator_type = obj.__validator_type__
                    self.register_validator(validator_type, obj)
                    registered_count += 1
            
            print(f"✅ 从模块 {module_name} 自动注册了 {registered_count} 个验证器")
            return registered_count
            
        except Exception as e:
            print(f"❌ 从模块 {module_name} 自动注册失败: {e}")
            return 0
    
    def _is_valid_validator_class(self, cls: Type) -> bool:
        """检查是否为有效的验证器类
        
        Args:
            cls: 待检查的类
            
        Returns:
            True表示有效，False表示无效
        """
        try:
            # 检查是否实现了IValidator接口
            return (
                inspect.isclass(cls) and
                issubclass(cls, IValidator) and
                hasattr(cls, 'validate') and
                hasattr(cls, 'get_validator_name')
            )
        except Exception:
            return False
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息
        
        Returns:
            统计信息字典
        """
        with self._lock:
            return {
                "total_registered_validators": len(self._validators),
                "total_factory_functions": len(self._factory_functions),
                "total_cached_instances": len(self._instances),
                "registration_count": self.registration_count,
                "instance_creation_count": self.instance_creation_count,
                "validator_types": list(self._validators.keys()),
                "factory_types": list(self._factory_functions.keys())
            }
    
    def export_registry_info(self) -> Dict[str, Any]:
        """导出注册表信息
        
        Returns:
            注册表详细信息
        """
        with self._lock:
            return {
                "validators": {
                    validator_type: metadata.to_dict()
                    for validator_type, metadata in self._validators.items()
                },
                "factory_functions": list(self._factory_functions.keys()),
                "dependency_graph": {
                    k: list(v) for k, v in self.dependency_resolver.dependency_graph.items()
                },
                "stats": self.get_registry_stats()
            }
    
    def clear_cache(self) -> int:
        """清空实例缓存
        
        Returns:
            清理的实例数量
        """
        with self._lock:
            cleared_count = len(self._instances)
            self._instances.clear()
            return cleared_count
    
    def validate_registry(self) -> List[str]:
        """验证注册表的完整性
        
        Returns:
            验证问题列表
        """
        issues = []
        
        with self._lock:
            # 检查所有注册的验证器
            for validator_type, metadata in self._validators.items():
                # 检查类是否仍然可用
                try:
                    if not self._is_valid_validator_class(metadata.validator_class):
                        issues.append(f"验证器类 {metadata.validator_class.__name__} 不再有效")
                except Exception:
                    issues.append(f"验证器类 {validator_type} 无法访问")
                
                # 检查依赖关系
                for dep in metadata.dependencies:
                    if dep not in self._validators and dep not in self._factory_functions:
                        issues.append(f"验证器 {validator_type} 的依赖 {dep} 未注册")
            
            # 检查循环依赖
            all_types = list(self._validators.keys())
            circular_deps = self.dependency_resolver.check_circular_dependencies(all_types)
            if circular_deps:
                issues.append(f"检测到循环依赖: {circular_deps}")
        
        return issues


def create_default_registry() -> ValidationRegistry:
    """创建默认的验证器注册表
    
    Returns:
        预注册了内置验证器的注册表实例
    """
    registry = ValidationRegistry()
    
    # 尝试注册内置验证策略
    try:
        from ..strategies.security_validator import SecurityValidationStrategy
        from ..factories.validator_factory import StrategyValidator
        
        def create_security_validator(config: Dict[str, Any]) -> IValidator:
            strategy = SecurityValidationStrategy(config)
            return StrategyValidator(strategy, "security")
        
        registry.register_factory_function("security", create_security_validator)
        
    except ImportError:
        pass
    
    try:
        from ..strategies.size_validator import SizeValidationStrategy
        from ..factories.validator_factory import StrategyValidator
        
        def create_size_validator(config: Dict[str, Any]) -> IValidator:
            strategy = SizeValidationStrategy(config)
            return StrategyValidator(strategy, "size")
        
        registry.register_factory_function("size", create_size_validator)
        
    except ImportError:
        pass
    
    try:
        from ..strategies.format_validator import FormatValidationStrategy
        from ..factories.validator_factory import StrategyValidator
        
        def create_format_validator(config: Dict[str, Any]) -> IValidator:
            strategy = FormatValidationStrategy(config)
            return StrategyValidator(strategy, "format")
        
        registry.register_factory_function("format", create_format_validator)
        
    except ImportError:
        pass
    
    # 注册其他验证器...
    # 这里可以继续注册其他验证器类型
    
    return registry


# 全局注册表实例
_global_registry: Optional[ValidationRegistry] = None
_registry_lock = RLock()


def get_global_registry() -> ValidationRegistry:
    """获取全局验证器注册表
    
    Returns:
        全局注册表实例
    """
    global _global_registry
    
    with _registry_lock:
        if _global_registry is None:
            _global_registry = create_default_registry()
        return _global_registry


def register_validator(validator_type: str, validator_class: Type[IValidator], **metadata) -> None:
    """注册验证器到全局注册表
    
    Args:
        validator_type: 验证器类型
        validator_class: 验证器类
        **metadata: 元数据
    """
    registry = get_global_registry()
    registry.register_validator(validator_type, validator_class, **metadata)


def get_validator(validator_type: str, config: Dict[str, Any]) -> Optional[IValidator]:
    """从全局注册表获取验证器
    
    Args:
        validator_type: 验证器类型
        config: 验证器配置
        
    Returns:
        验证器实例
    """
    registry = get_global_registry()
    return registry.get_validator(validator_type, config)


def list_available_validators() -> List[str]:
    """列出所有可用的验证器类型
    
    Returns:
        验证器类型列表
    """
    registry = get_global_registry()
    return registry.list_validators()


# 为了避免循环导入，添加time导入
import time
