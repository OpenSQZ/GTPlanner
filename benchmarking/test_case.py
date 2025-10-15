from datetime import datetime
from typing import List, Dict


class TestCase:
    """评测用例类（仅定义用例结构和序列化逻辑）"""

    def __init__(self, case_id: str, requirements: str, expected_features: List[str]):
        self.case_id = case_id          # 用例唯一ID
        self.requirements = requirements# 用户需求描述
        self.expected_features = expected_features  # 预期包含的功能点
        self.created_at = datetime.now()# 用例创建时间

    def to_dict(self) -> Dict:
        """序列化为字典（用于保存到JSON）"""
        return {
            "case_id": self.case_id,
            "requirements": self.requirements,
            "expected_features": self.expected_features,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'TestCase':
        """从字典反序列化为TestCase对象（用于加载JSON）"""
        case = cls(
            case_id=data["case_id"],
            requirements=data["requirements"],
            expected_features=data["expected_features"]
        )
        case.created_at = datetime.fromisoformat(data["created_at"])
        return case