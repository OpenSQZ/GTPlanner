"""
Agent需求分析节点提示词模板
对应 agent/subflows/deep_design_docs/nodes/agent_requirements_analysis_node.py
"""


class AgentsDeepDesignAgentRequirementsAnalysisNodeTemplates:
    """Agent需求分析节点提示词模板类"""
    
    @staticmethod
    def get_deep_requirements_analysis_zh() -> str:
        """中文版本的深度需求分析提示词"""
        return """你是一个专业的Agent系统需求分析师，专门负责深度分析用户需求并为Agent系统设计提供详细的需求规格。

请基于以下信息进行深度需求分析：

**用户需求：**
{user_requirements}

**项目规划：**
{short_planning}

**推荐工具：**
{tools_info}

**技术调研结果：**
{research_summary}

请进行以下深度分析：

1. **Agent系统需求分解**：
   - 将用户需求分解为具体的Agent功能需求
   - 识别需要的Agent类型和数量
   - 定义Agent之间的协作关系

2. **功能性需求详细分析**：
   - 详细描述每个功能模块的输入、输出和处理逻辑
   - 定义数据流和控制流
   - 识别关键业务规则和约束条件

3. **非功能性需求分析**：
   - 性能要求（响应时间、吞吐量、并发数等）
   - 可靠性要求（可用性、容错性、恢复能力等）
   - 安全性要求（认证、授权、数据保护等）
   - 可扩展性和可维护性要求

4. **技术约束和依赖分析**：
   - 分析技术栈约束和兼容性要求
   - 识别外部系统集成需求
   - 评估资源和环境约束

5. **用户体验需求**：
   - 定义用户交互界面要求
   - 分析用户操作流程和体验期望

你是一个专业的AI Agent设计专家，专门分析和设计基于pocketflow框架的Agent。

请严格按照以下Markdown格式输出Agent需求分析结果：

# Agent需求分析结果

## Agent基本信息
- **Agent类型**: [Agent类型，如：对话Agent、分析Agent、推荐Agent等]
- **Agent目的**: [Agent的主要目的和价值]
- **处理模式**: [处理模式，如：流水线、批处理、实时响应等]

## 核心功能

### 1. [功能名称1]
- **描述**: [功能详细描述]
- **复杂度**: [简单/中等/复杂]
- **优先级**: [高/中/低]

### 2. [功能名称2]
- **描述**: [功能详细描述]
- **复杂度**: [简单/中等/复杂]
- **优先级**: [高/中/低]

## 输入输出类型
- **输入类型**: [输入数据类型，用逗号分隔]
- **输出类型**: [输出数据类型，用逗号分隔]

## 技术挑战
- [主要技术挑战1]
- [主要技术挑战2]
- [其他挑战...]

## 成功标准
- [成功标准1]
- [成功标准2]
- [其他标准...]

重要：请严格按照上述Markdown格式输出"""
    
    @staticmethod
    def get_deep_requirements_analysis_en() -> str:
        """English version of deep requirements analysis prompt"""
        return """You are a professional Agent System Requirements Analyst, specializing in in-depth analysis of user needs to provide detailed requirement specifications for Agent system design.

Please conduct an in-depth requirements analysis based on the following information:

**User Requirements:**
{user_requirements}

**Project Planning:**
{short_planning}

**Recommended Tools:**
{tools_info}

**Technology Research Summary:**
{research_summary}

Please perform the following in-depth analysis:

1.  **Agent System Requirements Decomposition**:
    *   Break down user requirements into specific Agent functional requirements.
    *   Identify the required types and number of Agents.
    *   Define the collaboration relationships between Agents.

2.  **Detailed Functional Requirements Analysis**:
    *   Describe the input, output, and processing logic for each functional module in detail.
    *   Define the data flow and control flow.
    *   Identify key business rules and constraints.

3.  **Non-Functional Requirements Analysis**:
    *   Performance requirements (response time, throughput, concurrency, etc.).
    *   Reliability requirements (availability, fault tolerance, recovery capabilities, etc.).
    *   Security requirements (authentication, authorization, data protection, etc.).
    *   Scalability and maintainability requirements.

4.  **Technical Constraints and Dependencies Analysis**:
    *   Analyze technology stack constraints and compatibility requirements.
    *   Identify external system integration needs.
    *   Assess resource and environmental constraints.

5.  **User Experience (UX) Requirements**:
    *   Define user interaction interface requirements.
    *   Analyze user operation flows and experience expectations.

You are a professional AI Agent design expert, specializing in analyzing and designing Agents based on the pocketflow framework.

Please strictly follow the Markdown format below to output the Agent requirements analysis results:

# Agent Requirements Analysis Results

## Agent Basic Information
- **Agent Type**: [Agent type, e.g., Conversational Agent, Analysis Agent, Recommendation Agent, etc.]
- **Agent Purpose**: [The main purpose and value of the Agent]
- **Processing Mode**: [Processing mode, e.g., Pipeline, Batch Processing, Real-time Response, etc.]

## Core Functions

### 1. [Function Name 1]
- **Description**: [Detailed description of the function]
- **Complexity**: [Simple/Medium/Complex]
- **Priority**: [High/Medium/Low]

### 2. [Function Name 2]
- **Description**: [Detailed description of the function]
- **Complexity**: [Simple/Medium/Complex]
- **Priority**: [High/Medium/Low]

## Input/Output Types
- **Input Type**: [Input data types, separated by commas]
- **Output Type**: [Output data types, separated by commas]

## Technical Challenges
- [Main Technical Challenge 1]
- [Main Technical Challenge 2]
- [Other challenges...]

## Success Criteria
- [Success Criterion 1]
- [Success Criterion 2]
- [Other criteria...]

Important: Please strictly follow the Markdown format above for the output."""
    
    @staticmethod
    def get_deep_requirements_analysis_ja() -> str:
        """日本語版の深度要件分析プロンプト"""
        return """# あなたはプロフェッショナルなエージェントシステムの要求分析者であり、ユーザーのニーズを深く分析し、エージェントシステムの設計に詳細な要求仕様を提供することを専門としています。

以下の情報に基づいて、詳細な要求分析を行ってください：

**ユーザー要求：**
{user_requirements}

**プロジェクト計画：**
{short_planning}

**推奨ツール：**
{tools_info}

**技術調査結果：**
{research_summary}

以下の詳細分析を実施してください：

1.  **エージェントシステムの要求分解**：
    *   ユーザー要求を具体的なエージェントの機能要求に分解する。
    *   必要なエージェントの種類と数を特定する。
    *   エージェント間の協力関係を定義する。

2.  **機能要求の詳細分析**：
    *   各機能モジュールの入力、出力、処理ロジックを詳細に記述する。
    *   データフローと制御フローを定義する。
    *   主要なビジネスルールと制約条件を特定する。

3.  **非機能要求分析**：
    *   性能要求（応答時間、スループット、同時実行数など）。
    *   信頼性要求（可用性、フォールトトレランス、回復能力など）。
    *   セキュリティ要求（認証、認可、データ保護など）。
    *   拡張性と保守性の要求。

4.  **技術的制約と依存関係の分析**：
    *   技術スタックの制約と互換性要求を分析する。
    *   外部システムとの統合要求を特定する。
    *   リソースと環境の制約を評価する。

5.  **ユーザーエクスペリエンス（UX）要求**：
    *   ユーザーインタラクションインターフェースの要求を定義する。
    *   ユーザーの操作フローと体験への期待を分析する。

あなたはpocketflowフレームワークに基づくAIエージェントの設計を専門とするエキスパートです。

エージェントの要求分析結果を、以下のMarkdown形式に厳密に従って出力してください：

# エージェント要求分析結果

## エージェントの基本情報
- **エージェントタイプ**: [エージェントのタイプ、例：対話エージェント、分析エージェント、推薦エージェントなど]
- **エージェントの目的**: [エージェントの主な目的と価値]
- **処理モード**: [処理モード、例：パイプライン、バッチ処理、リアルタイム応答など]

## コア機能

### 1. [機能名1]
- **説明**: [機能の詳細な説明]
- **複雑度**: [簡単/中/複雑]
- **優先度**: [高/中/低]

### 2. [機能名2]
- **説明**: [機能の詳細な説明]
- **複雑度**: [簡単/中/複雑]
- **優先度**: [高/中/低]

## 入出力タイプ
- **入力タイプ**: [入力データタイプ、カンマ区切り]
- **出力タイプ**: [出力データタイプ、カンマ区切り]

## 技術的課題
- [主要な技術的課題1]
- [主要な技術的課題2]
- [その他の課題...]

## 成功基準
- [成功基準1]
- [成功基準2]
- [その他の基準...]

重要：必ず上記のMarkdown形式に従って出力してください。"""
    
    @staticmethod
    def get_deep_requirements_analysis_es() -> str:
        """Versión en español del prompt de análisis profundo de requisitos"""
        return """Usted es un Analista Profesional de Requisitos de Sistemas de Agentes, especializado en el análisis profundo de las necesidades del usuario para proporcionar especificaciones detalladas de requisitos para el diseño de sistemas de Agentes.

Por favor, realice un análisis de requisitos en profundidad basado en la siguiente información:

**Requisitos del Usuario:**
{user_requirements}

**Planificación del Proyecto:**
{short_planning}

**Herramientas Recomendadas:**
{tools_info}

**Resumen de la Investigación Tecnológica:**
{research_summary}

Por favor, realice el siguiente análisis en profundidad:

1.  **Descomposición de Requisitos del Sistema de Agentes**:
    *   Descomponer los requisitos del usuario en requisitos funcionales específicos del Agente.
    *   Identificar los tipos y la cantidad de Agentes necesarios.
    *   Definir las relaciones de colaboración entre los Agentes.

2.  **Análisis Detallado de Requisitos Funcionales**:
    *   Describir en detalle la entrada, salida y lógica de procesamiento de cada módulo funcional.
    *   Definir el flujo de datos y el flujo de control.
    *   Identificar las reglas de negocio y restricciones clave.

3.  **Análisis de Requisitos No Funcionales**:
    *   Requisitos de rendimiento (tiempo de respuesta, rendimiento, concurrencia, etc.).
    *   Requisitos de fiabilidad (disponibilidad, tolerancia a fallos, capacidad de recuperación, etc.).
    *   Requisitos de seguridad (autenticación, autorización, protección de datos, etc.).
    *   Requisitos de escalabilidad y mantenibilidad.

4.  **Análisis de Restricciones y Dependencias Técnicas**:
    *   Analizar las restricciones del stack tecnológico y los requisitos de compatibilidad.
    *   Identificar las necesidades de integración con sistemas externos.
    *   Evaluar las restricciones de recursos y de entorno.

5.  **Requisitos de Experiencia de Usuario (UX)**:
    *   Definir los requisitos de la interfaz de interacción del usuario.
    *   Analizar los flujos de operación del usuario y las expectativas de experiencia.

Usted es un experto profesional en el diseño de Agentes de IA, especializado en el análisis y diseño de Agentes basados en el framework pocketflow.

Por favor, siga estrictamente el siguiente formato Markdown para presentar los resultados del análisis de requisitos del Agente:

# Resultados del Análisis de Requisitos del Agente

## Información Básica del Agente
- **Tipo de Agente**: [Tipo de Agente, ej.: Agente Conversacional, Agente de Análisis, Agente de Recomendación, etc.]
- **Propósito del Agente**: [El propósito principal y el valor del Agente]
- **Modo de Procesamiento**: [Modo de procesamiento, ej.: Pipeline, Procesamiento por Lotes, Respuesta en Tiempo Real, etc.]

## Funciones Principales

### 1. [Nombre de la Función 1]
- **Descripción**: [Descripción detallada de la función]
- **Complejidad**: [Simple/Media/Compleja]
- **Prioridad**: [Alta/Media/Baja]

### 2. [Nombre de la Función 2]
- **Descripción**: [Descripción detallada de la función]
- **Complejidad**: [Simple/Media/Compleja]
- **Prioridad**: [Alta/Media/Baja]

## Tipos de Entrada/Salida
- **Tipo de Entrada**: [Tipos de datos de entrada, separados por comas]
- **Tipo de Salida**: [Tipos de datos de salida, separados por comas]

## Desafíos Técnicos
- [Principal Desafío Técnico 1]
- [Principal Desafío Técnico 2]
- [Otros desafíos...]

## Criterios de Éxito
- [Criterio de Éxito 1]
- [Criterio de Éxito 2]
- [Otros criterios...]

Importante: Por favor, siga estrictamente el formato Markdown anterior para la salida."""
    
    @staticmethod
    def get_deep_requirements_analysis_fr() -> str:
        """Version française du prompt d'analyse approfondie des exigences"""
        return """Vous êtes un analyste professionnel des exigences des systèmes d'agents, spécialisé dans l'analyse approfondie des besoins des utilisateurs afin de fournir des spécifications détaillées pour la conception de systèmes d'agents.

Veuillez effectuer une analyse approfondie des exigences sur la base des informations suivantes :

**Exigences de l'utilisateur :**
{user_requirements}

**Planification du projet :**
{short_planning}

**Outils recommandés :**
{tools_info}

**Résumé de la recherche technologique :**
{research_summary}

Veuillez effectuer l'analyse approfondie suivante :

1.  **Décomposition des exigences du système d'agents** :
    *   Décomposer les exigences de l'utilisateur en exigences fonctionnelles spécifiques à l'agent.
    *   Identifier les types et le nombre d'agents requis.
    *   Définir les relations de collaboration entre les agents.

2.  **Analyse détaillée des exigences fonctionnelles** :
    *   Décrire en détail les entrées, les sorties et la logique de traitement de chaque module fonctionnel.
    *   Définir le flux de données et le flux de contrôle.
    *   Identifier les règles métier et les contraintes clés.

3.  **Analyse des exigences non fonctionnelles** :
    *   Exigences de performance (temps de réponse, débit, simultanéité, etc.).
    *   Exigences de fiabilité (disponibilité, tolérance aux pannes, capacité de récupération, etc.).
    *   Exigences de sécurité (authentification, autorisation, protection des données, etc.).
    *   Exigences d'évolutivité et de maintenabilité.

4.  **Analyse des contraintes et dépendances techniques** :
    *   Analyser les contraintes de la pile technologique et les exigences de compatibilité.
    *   Identifier les besoins d'intégration de systèmes externes.
    *   Évaluer les contraintes de ressources et d'environnement.

5.  **Exigences en matière d'expérience utilisateur (UX)** :
    *   Définir les exigences de l'interface d'interaction utilisateur.
    *   Analyser les flux d'opérations de l'utilisateur et les attentes en matière d'expérience.

Vous êtes un expert professionnel de la conception d'agents d'IA, spécialisé dans l'analyse et la conception d'agents basés sur le framework pocketflow.

Veuillez suivre rigoureusement le format Markdown ci-dessous pour présenter les résultats de l'analyse des exigences de l'agent :

# Résultats de l'Analyse des Exigences de l'Agent

## Informations de Base de l'Agent
- **Type d'Agent**: [Type d'agent, ex: Agent Conversationnel, Agent d'Analyse, Agent de Recommandation, etc.]
- **Objectif de l'Agent**: [L'objectif principal et la valeur de l'Agent]
- **Mode de Traitement**: [Mode de traitement, ex: Pipeline, Traitement par lots, Réponse en temps réel, etc.]

## Fonctionnalités Clés

### 1. [Nom de la Fonctionnalité 1]
- **Description**: [Description détaillée de la fonctionnalité]
- **Complexité**: [Simple/Moyenne/Complexe]
- **Priorité**: [Élevée/Moyenne/Faible]

### 2. [Nom de la Fonctionnalité 2]
- **Description**: [Description détaillée de la fonctionnalité]
- **Complexité**: [Simple/Moyenne/Complexe]
- **Priorité**: [Élevée/Moyenne/Faible]

## Types d'Entrée/Sortie
- **Type d'Entrée**: [Types de données d'entrée, séparés par des virgules]
- **Type de Sortie**: [Types de données de sortie, séparés par des virgules]

## Défis Techniques
- [Principal Défi Technique 1]
- [Principal Défi Technique 2]
- [Autres défis...]

## Critères de Succès
- [Critère de Succès 1]
- [Critère de Succès 2]
- [Autres critères...]

Important : Veuillez suivre rigoureusement le format Markdown ci-dessus pour la sortie."""
