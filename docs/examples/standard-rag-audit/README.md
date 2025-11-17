# 标准研判 RAG 助手示例

本示例演示如何用 GTPlanner 规划一个“标准/法规条款研判”类 RAG 助手，包含完整的设计文档（design.md）和关键字段说明。

## 适用场景
- 行业/地方标准 PDF/Word 导入与解析
- 条款级检索与引用
- 合规性判定与风险提示

## 快速使用
```bash
# 使用内置 RAG 预设生成规划
python gtplanner.py --preset rag-doc-qa "设计一个标准研判RAG助手：支持PDF导入、条款检索、合规分析和引用结果输出"
```

生成的设计文档参考本目录下的 `design.md`，可直接交给后续 Agent/AI 编程工具或团队落地。 ***
