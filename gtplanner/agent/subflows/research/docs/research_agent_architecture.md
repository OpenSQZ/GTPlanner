# Research Agent 架构图

## 整体架构

```mermaid
graph TB
    subgraph "GTPlanner 主流程"
        A[用户输入] --> B[需求分析]
        B --> C[ProcessResearch节点]
        C --> D[架构设计]
        D --> E[文档生成]
    end
    
    subgraph "Research Agent"
        C --> F[ResearchFlow]
        F --> G[并发处理多个关键词]
        G --> H[关键词1子流程]
        G --> I[关键词2子流程]
        G --> J[关键词N子流程]
        H --> K[ResearchAggregator]
        I --> K
        J --> K
        K --> L[聚合结果]
    end
    
    subgraph "单个关键词子流程"
        H --> M[NodeSearch]
        M --> N[NodeURL]
        N --> O[LLMAnalysisNode]
        O --> P[ResultAssemblyNode]
    end
    
    style C fill:#e1f5fe
    style F fill:#f3e5f5
    style M fill:#e8f5e8
    style N fill:#fff3e0
    style O fill:#fce4ec
    style P fill:#f1f8e9
```

## 数据流架构

```mermaid
graph LR
    subgraph "输入数据"
        A1[用户意图]
        A2[结构化需求]
        A3[项目概览]
    end
    
    subgraph "关键词提取"
        B1[从用户意图提取]
        B2[从项目标题提取]
        B3[从核心功能提取]
    end
    
    subgraph "子流程处理"
        C1[搜索API调用]
        C2[URL解析API调用]
        C3[LLM分析API调用]
        C4[结果组装]
    end
    
    subgraph "输出数据"
        D1[关键词报告]
        D2[聚合总结]
        D3[研究元数据]
    end
    
    A1 --> B1
    A2 --> B2
    A3 --> B3
    
    B1 --> C1
    B2 --> C1
    B3 --> C1
    
    C1 --> C2
    C2 --> C3
    C3 --> C4
    
    C4 --> D1
    D1 --> D2
    D2 --> D3
```

## 节点详细架构

### NodeSearch (搜索节点)
```mermaid
graph TD
    A[prep: 提取搜索关键词] --> B[exec: 调用Jina搜索API]
    B --> C[post: 保存搜索结果]
    
    subgraph "数据流"
        D[search_keywords] --> A
        B --> E[search_results]
        C --> F[first_search_result]
        C --> G[all_search_results]
    end
```

### NodeURL (URL解析节点)
```mermaid
graph TD
    A[prep: 获取首条搜索结果URL] --> B[exec: 调用Jina Web API]
    B --> C[post: 保存网页内容]
    
    subgraph "数据流"
        D[first_search_result.url] --> A
        B --> E[parsed_content]
        C --> F[url_content]
        C --> G[url_title]
        C --> H[url_metadata]
    end
```

### LLMAnalysisNode (LLM分析节点)
```mermaid
graph TD
    A[prep: 准备分析数据] --> B[exec: 调用LLM API]
    B --> C[post: 保存分析结果]
    
    subgraph "数据流"
        D[url_content] --> A
        E[current_keyword] --> A
        F[analysis_requirements] --> A
        B --> G[analysis_result]
        C --> H[llm_analysis]
        C --> I[analyzed_keyword]
    end
```

### ResultAssemblyNode (结果组装节点)
```mermaid
graph TD
    A[prep: 收集所有数据] --> B[exec: 组装报告]
    B --> C[post: 保存最终报告]
    
    subgraph "数据流"
        D[current_keyword] --> A
        E[first_search_result] --> A
        F[url_content] --> A
        G[llm_analysis] --> A
        B --> H[assembled_report]
        C --> I[keyword_report]
    end
```

## 并发处理架构

```mermaid
graph TB
    A[ResearchFlow.process_research_keywords] --> B[ThreadPoolExecutor]
    
    subgraph "并发执行"
        B --> C[关键词1线程]
        B --> D[关键词2线程]
        B --> E[关键词3线程]
        B --> F[关键词N线程]
    end
    
    subgraph "独立子流程"
        C --> G[子流程实例1]
        D --> H[子流程实例2]
        E --> I[子流程实例3]
        F --> J[子流程实例N]
    end
    
    subgraph "结果收集"
        G --> K[keyword_report_1]
        H --> L[keyword_report_2]
        I --> M[keyword_report_3]
        J --> N[keyword_report_N]
    end
    
    K --> O[ResearchAggregator]
    L --> O
    M --> O
    N --> O
    
    O --> P[aggregated_summary]
```

## 错误处理架构

```mermaid
graph TD
    A[节点执行] --> B{是否成功?}
    B -->|成功| C[返回success]
    B -->|失败| D[返回error]
    
    C --> E[流程继续]
    D --> F[流程终止]
    
    subgraph "错误隔离"
        G[关键词1失败] --> H[不影响关键词2]
        I[关键词2成功] --> J[继续处理]
        K[关键词3成功] --> L[继续处理]
    end
    
    subgraph "降级处理"
        M[LLM API失败] --> N[使用模拟结果]
        O[搜索API失败] --> P[使用备用数据]
    end
```

## 配置架构

```mermaid
graph LR
    subgraph "配置源"
        A[.env文件]
        B[settings.toml]
        C[环境变量]
    end
    
    subgraph "配置管理器"
        D[MultilingualConfig]
        E[get_jina_api_key]
        F[get_llm_config]
    end
    
    subgraph "使用方"
        G[JinaSearchClient]
        H[JinaWebClient]
        I[LLMAnalysisNode]
    end
    
    A --> D
    B --> D
    C --> D
    
    D --> E
    D --> F
    
    E --> G
    E --> H
    F --> I
```

## 测试架构（已验证）

```mermaid
graph TB
    subgraph "测试层级"
        A[单元测试]
        B[集成测试]
        C[端到端测试]
    end

    subgraph "测试文件"
        D[test_complete_research_agent.py]
    end

    subgraph "测试内容 ✅"
        H[配置和导入测试]
        I[ProcessResearch prep方法测试]
        J[单个关键词子流程测试]
        K[并发研究流程测试]
        L[ProcessResearch完整流程测试]
    end

    subgraph "验证结果"
        M[5/5测试通过]
        N[真实API调用成功]
        O[pocketflow最佳实践验证]
        P[并发处理验证]
        Q[数据流完整性验证]
    end

    A --> D
    B --> D
    C --> D

    D --> H
    D --> I
    D --> J
    D --> K
    D --> L

    H --> M
    I --> N
    J --> O
    K --> P
    L --> Q
```

### 测试执行结果

**测试状态**: ✅ 全部通过 (5/5)
**测试时间**: 2024年12月1日
**成功率**: 100%
**关键词处理**: 5/5成功
**API调用**: 正常工作
**并发处理**: 稳定可靠

## 部署架构

```mermaid
graph TB
    subgraph "开发环境"
        A[本地开发]
        B[单元测试]
        C[集成测试]
    end
    
    subgraph "配置管理"
        D[环境变量]
        E[API密钥]
        F[模型配置]
    end
    
    subgraph "依赖服务"
        G[Jina搜索API]
        H[Jina Web API]
        I[LLM API]
    end
    
    subgraph "监控和日志"
        J[执行日志]
        K[错误追踪]
        L[性能监控]
    end
    
    A --> D
    D --> G
    D --> H
    D --> I
    
    G --> J
    H --> K
    I --> L
```

---

*本文档提供了 Research Agent 的完整架构视图，包括数据流、并发处理、错误处理、配置管理、测试和部署等各个方面。*
