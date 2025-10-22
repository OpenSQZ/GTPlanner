"""
流程设计节点提示词模板
对应 agent/subflows/deep_design_docs/nodes/flow_design_node.py
"""


class AgentsDeepDesignFlowDesignNodeTemplates:
    """流程设计节点提示词模板类"""
    
    @staticmethod
    def get_flow_design_zh() -> str:
        """中文版本的流程设计提示词"""
        return """你是pocketflow流程设计师。设计Node之间的连接和执行流程。

**上下文：**
- Agent分析：{analysis_markdown}
- Node列表：{nodes_markdown}
- 用户需求：{user_requirements}
- 项目规划：{short_planning}
- 技术调研：{research_info}
- 推荐工具：{tools_info}

**关键要求：**
1. 只使用已识别的Node
2. 使用Action驱动逻辑
3. 避免使用保留字(end/subgraph/flowchart)作为节点名

**严格按照Markdown格式输出：**

# Flow设计

## Flow概述
- **名称**: [Flow名称]
- **起始节点**: [Node名称]

## Flow图表
```mermaid
flowchart TD
    [生成Mermaid代码]
```

## 编排代码
```python
node_1 = Node1()
node_2 = Node2()

node_1 - "action_1" >> node_2
node_2 >> node_3
```

## 连接说明
### [源Node] -> [目标Node]
- **Action**: [action名或default]
- **条件**: [简要说明，10字内]

重要：保持简洁，只描述关键连接逻辑"""
    
    @staticmethod
    def get_flow_design_en() -> str:
        """English version of flow design prompt"""
        return """You are a professional PocketFlow process designer, specializing in designing the connections and execution flows between Nodes.

Please design the complete Flow execution process based on the following information:

**Agent Analysis Results:**
{analysis_markdown}

**Node Identification Results:**
{nodes_markdown}

**User Requirements:**
{user_requirements}

**Project Planning:**
{short_planning}

**Technical Research Results:**
{research_info}

**Recommended Tools:**
{tools_info}

Please perform the following Flow design tasks:

1.  **Main Flow Design**:
    *   Design the main execution path from input to output.
    *   Define key execution stages and milestones.
    *   Ensure the logical integrity and consistency of the flow.

2.  **Node Connection Design**:
    *   Define the connection relationships and data transfer between Nodes.
    *   Design Action-driven state transition logic.
    *   Ensure the correctness and integrity of the data stream.

3.  **Branch and Conditional Handling**:
    *   Design conditional branches and exception handling processes.
    *   Define execution paths for different scenarios.
    *   Ensure all possible execution cases are handled.

4.  **Parallel and Serial Execution**:
    *   Identify combinations of Nodes that can be executed in parallel.
    *   Design dependencies for serial execution.
    *   Optimize overall execution efficiency and resource utilization.

5.  **Error Handling and Recovery**:
    *   Design error detection and handling mechanisms.
    *   Define failure retry and recovery strategies.
    *   Ensure the robustness and reliability of the system.

6.  **Performance Optimization Considerations**:
    *   Identify potential performance bottlenecks.
    *   Design caching and optimization strategies.
    *   Consider resource usage and response time.

Please strictly follow the Markdown format below to output the Flow design results:

# Flow Design Results

## Flow Overview
- **Flow Name**: [Flow Name]
- **Flow Description**: [Overall description of the Flow]
- **Start Node**: [Start Node Name, must be from the identified Node list]

## Flowchart

```mermaid
flowchart TD
  [Generate the complete Mermaid flowchart TD code here]
```

## Node Connection Relationships

### Connection 1
- **Source Node**: [Source Node Name]
- **Target Node**: [Target Node Name]
- **Trigger Action**: [default or specific action name]
- **Transition Condition**: [Description of the transition condition]
- **Data Transmitted**: [Description of the data being transmitted]

## Execution Process

### Step 1
- **Node**: [Node Name]
- **Description**: [The purpose of this step]
- **Input Data**: [Source of the input data]
- **Output Data**: [Destination of the output data]

## Orchestration Result
```python
node_1 = Node1()
node_2 = Node2()
node_3 = Node3()
node_4 = Node4() ## default 

node_1 - "action_1" >> node_2
node_2 - "action_2" >> node_3
node_3 >> node_4
```

## Design Rationale
[Rationale for the Flow orchestration design]

**Orchestration Requirements:**
1. Only use Nodes from the identified Node list.
2. Ensure the integrity and logic of the data flow.
3. Use Action-driven transition logic.
4. Consider error handling and branching logic.
5. The Mermaid diagram must clearly show all connections and data flows.
6. Ensure each Node has a clearly defined predecessor and successor relationship.

**Important**: Please strictly follow the Markdown format above. Do not output in JSON format! Directly output the complete Markdown document."""
    
    @staticmethod
    def get_flow_design_ja() -> str:
        """日本語版のフロー設計プロンプト"""
        return """あなたはプロのPocketFlowプロセスデザイナーであり、Node間の接続と実行フローの設計を専門としています。

以下の情報に基づいて、完全なFlow実行プロセスを設計してください：

**エージェント分析結果:**
{analysis_markdown}

**Node認識結果:**
{nodes_markdown}

**ユーザー要件:**
{user_requirements}

**プロジェクト計画:**
{short_planning}

**技術調査結果:**
{research_info}

**推奨ツール:**
{tools_info}

以下のFlow設計作業を行ってください：

1.  **メインフロー設計**:
    *   入力から出力までの主要な実行パスを設計する。
    *   主要な実行段階とマイルストーンを定義する。
    *   フローの論理的な完全性と一貫性を確保する。

2.  **Node接続設計**:
    *   Node間の接続関係とデータ転送を定義する。
    *   Action駆動の状態遷移ロジックを設計する。
    *   データストリームの正確性と完全性を確保する。

3.  **分岐と条件処理**:
    *   条件分岐と例外処理プロセスを設計する。
    *   異なるシナリオでの実行パスを定義する。
    *   考えられるすべての実行ケースに対応する処理を確保する。

4.  **並列および直列実行**:
    *   並列実行可能なNodeの組み合わせを特定する。
    *   直列実行の依存関係を設計する。
    *   全体的な実行効率とリソース利用を最適化する。

5.  **エラー処理と回復**:
    *   エラー検出および処理メカニズムを設計する。
    *   失敗時の再試行および回復戦略を定義する。
    *   システムの堅牢性と信頼性を確保する。

6.  **パフォーマンス最適化の考慮事項**:
    *   潜在的なパフォーマンスのボトルネックを特定する。
    *   キャッシングと最適化戦略を設計する。
    *   リソース使用量と応答時間を考慮する。

Flow設計結果は、以下のMarkdown形式に厳密に従って出力してください：

# Flow設計結果

## Flow概要
- **Flow名**: [フロー名]
- **Flowの説明**: [フローの全体的な説明]
- **開始ノード**: [開始ノード名、認識されたNodeリストから選択する必要があります]

## フローチャート

```mermaid
flowchart TD
  [ここに完全なMermaidフローチャートTDコードを生成してください]
```

## ノード接続関係

### 接続 1
- **ソースノード**: [ソースノード名]
- **ターゲットノード**: [ターゲットノード名]
- **トリガーアクション**: [defaultまたは特定のアクション名]
- **遷移条件**: [遷移条件の説明]
- **伝達データ**: [伝達されるデータの説明]

## 実行プロセス

### ステップ 1
- **ノード**: [ノード名]
- **説明**: [このステップの目的]
- **入力データ**: [入力データのソース]
- **出力データ**: [出力データの宛先]

## オーケストレーション結果
```python
node_1 = Node1()
node_2 = Node2()
node_3 = Node3()
node_4 = Node4() ## default 

node_1 - "action_1" >> node_2
node_2 - "action_2" >> node_3
node_3 >> node_4
```

## 設計理由
[Flowオーケストレーションの設計理由]

**オーケストレーション要件:**
1. 認識されたNodeリスト内のNodeのみを使用すること。
2. データフローの完全性と論理性を確保すること。
3. Action駆動の遷移ロジックを使用すること。
4. エラー処理と分岐ロジックを考慮すること。
5. Mermaid図は、すべての接続とデータフローを明確に表示すること。
6. 各Nodeには明確な先行および後続関係があることを確認すること。

**重要**: 上記のMarkdown形式に厳密に従って出力してください。JSON形式で出力しないでください！完全なMarkdownドキュメントを直接出力してください。"""
    
    @staticmethod
    def get_flow_design_es() -> str:
        """Versión en español del prompt de diseño de flujo"""
        return """# Eres un diseñador profesional de flujos de PocketFlow, especializado en diseñar las conexiones y los procesos de ejecución entre Nodos.

Por favor, diseña el proceso completo de ejecución del Flujo basándote en la siguiente información:

**Resultados del Análisis del Agente:**
{analysis_markdown}

**Resultados de Identificación de Nodos:**
{nodes_markdown}

**Requisitos del Usuario:**
{user_requirements}

**Planificación del Proyecto:**
{short_planning}

**Resultados de la Investigación Técnica:**
{research_info}

**Herramientas Recomendadas:**
{tools_info}

Por favor, realiza las siguientes tareas de diseño de Flujo:

1.  **Diseño del Flujo Principal**:
    *   Diseñar la ruta de ejecución principal desde la entrada hasta la salida.
    *   Definir las etapas clave de ejecución y los hitos.
    *   Asegurar la integridad lógica y la consistencia del flujo.

2.  **Diseño de Conexión de Nodos**:
    *   Definir las relaciones de conexión y la transferencia de datos entre Nodos.
    *   Diseñar la lógica de transición de estado impulsada por Acciones.
    *   Asegurar la corrección e integridad del flujo de datos.

3.  **Manejo de Ramificaciones y Condiciones**:
    *   Diseñar ramificaciones condicionales y procesos de manejo de excepciones.
    *   Definir rutas de ejecución para diferentes escenarios.
    *   Asegurar que todos los posibles casos de ejecución sean manejados.

4.  **Ejecución en Paralelo y en Serie**:
    *   Identificar combinaciones de Nodos que pueden ejecutarse en paralelo.
    *   Diseñar dependencias para la ejecución en serie.
    *   Optimizar la eficiencia general de la ejecución y la utilización de recursos.

5.  **Manejo de Errores y Recuperación**:
    *   Diseñar mecanismos de detección y manejo de errores.
    *   Definir estrategias de reintento y recuperación ante fallos.
    *   Asegurar la robustez y fiabilidad del sistema.

6.  **Consideraciones de Optimización del Rendimiento**:
    *   Identificar posibles cuellos de botella de rendimiento.
    *   Diseñar estrategias de almacenamiento en caché y optimización.
    *   Considerar el uso de recursos y el tiempo de respuesta.

Por favor, sigue estrictamente el siguiente formato Markdown para presentar los resultados del diseño del Flujo:

# Resultados del Diseño del Flujo

## Resumen del Flujo
- **Nombre del Flujo**: [Nombre del Flujo]
- **Descripción del Flujo**: [Descripción general del Flujo]
- **Nodo de Inicio**: [Nombre del Nodo de Inicio, debe pertenecer a la lista de Nodos identificados]

## Diagrama de Flujo

```mermaid
flowchart TD
  [Genera aquí el código completo del diagrama de flujo Mermaid TD]
```

## Relaciones de Conexión de Nodos

### Conexión 1
- **Nodo de Origen**: [Nombre del Nodo de Origen]
- **Nodo de Destino**: [Nombre del Nodo de Destino]
- **Acción de Disparo**: [default o nombre de acción específico]
- **Condición de Transición**: [Descripción de la condición de transición]
- **Datos Transmitidos**: [Descripción de los datos que se transmiten]

## Proceso de Ejecución

### Paso 1
- **Nodo**: [Nombre del Nodo]
- **Descripción**: [El propósito de este paso]
- **Datos de Entrada**: [Fuente de los datos de entrada]
- **Datos de Salida**: [Destino de los datos de salida]

## Resultado de la Orquestación
```python
nodo_1 = Nodo1()
nodo_2 = Nodo2()
nodo_3 = Nodo3()
nodo_4 = Nodo4() ## default 

nodo_1 - "accion_1" >> nodo_2
nodo_2 - "accion_2" >> nodo_3
nodo_3 >> nodo_4
```

## Justificación del Diseño
[Justificación del diseño de la orquestación del Flujo]

**Requisitos de Orquestación:**
1.  Utilizar únicamente Nodos de la lista de Nodos identificados.
2.  Asegurar la integridad y la lógica del flujo de datos.
3.  Utilizar una lógica de transición impulsada por Acciones.
4.  Considerar el manejo de errores y la lógica de ramificación.
5.  El diagrama de Mermaid debe mostrar claramente todas las conexiones y flujos de datos.
6.  Asegurarse de que cada Nodo tenga una relación predecesora y sucesora claramente definida.

**Importante**: ¡Por favor, sigue estrictamente el formato Markdown anterior. No generes la salida en formato JSON! Genera directamente el documento Markdown completo."""
    
    @staticmethod
    def get_flow_design_fr() -> str:
        """Version française du prompt de conception de flux"""
        return """# Vous êtes un concepteur de processus PocketFlow professionnel, spécialisé dans la conception des connexions et des flux d'exécution entre les Nœuds.

Veuillez concevoir le processus d'exécution complet du Flux en vous basant sur les informations suivantes :

**Résultats de l'Analyse de l'Agent :**
{analysis_markdown}

**Résultats de l'Identification des Nœuds :**
{nodes_markdown}

**Exigences de l'Utilisateur :**
{user_requirements}

**Planification du Projet :**
{short_planning}

**Résultats de la Recherche Technique :**
{research_info}

**Outils Recommandés :**
{tools_info}

Veuillez effectuer les tâches de conception de Flux suivantes :

1.  **Conception du Flux Principal** :
    *   Concevoir le chemin d'exécution principal de l'entrée à la sortie.
    *   Définir les étapes clés de l'exécution et les jalons.
    *   Assurer l'intégrité logique et la cohérence du flux.

2.  **Conception de la Connexion des Nœuds** :
    *   Définir les relations de connexion et le transfert de données entre les Nœuds.
    *   Concevoir une logique de transition d'état pilotée par des Actions.
    *   Assurer l'exactitude et l'intégrité du flux de données.

3.  **Gestion des Branches et des Conditions** :
    *   Concevoir des branches conditionnelles et des processus de gestion des exceptions.
    *   Définir des chemins d'exécution pour différents scénarios.
    *   S'assurer que tous les cas d'exécution possibles sont gérés.

4.  **Exécution Parallèle et Sérielle** :
    *   Identifier les combinaisons de Nœuds qui peuvent être exécutées en parallèle.
    *   Concevoir les dépendances pour une exécution en série.
    *   Optimiser l'efficacité globale de l'exécution et l'utilisation des ressources.

5.  **Gestion des Erreurs et Récupération** :
    *   Concevoir des mécanismes de détection et de gestion des erreurs.
    *   Définir des stratégies de nouvelle tentative et de récupération en cas d'échec.
    *   Assurer la robustesse et la fiabilité du système.

6.  **Considérations sur l'Optimisation des Performances** :
    *   Identifier les goulots d'étranglement potentiels en matière de performances.
    *   Concevoir des stratégies de mise en cache et d'optimisation.
    *   Prendre en compte l'utilisation des ressources et le temps de réponse.

Veuillez suivre strictement le format Markdown ci-dessous pour présenter les résultats de la conception du Flux :

# Résultats de la Conception du Flux

## Aperçu du Flux
- **Nom du Flux**: [Nom du Flux]
- **Description du Flux**: [Description globale du Flux]
- **Nœud de Départ**: [Nom du Nœud de Départ, doit provenir de la liste des Nœuds identifiés]

## Diagramme de Flux

```mermaid
flowchart TD
  [Générez ici le code complet du diagramme de flux Mermaid TD]
```

## Relations de Connexion des Nœuds

### Connexion 1
- **Nœud Source**: [Nom du Nœud Source]
- **Nœud Cible**: [Nom du Nœud Cible]
- **Action de Déclenchement**: [default ou nom d'action spécifique]
- **Condition de Transition**: [Description de la condition de transition]
- **Données Transmises**: [Description des données transmises]

## Processus d'Exécution

### Étape 1
- **Nœud**: [Nom du Nœud]
- **Description**: [Le but de cette étape]
- **Données d'Entrée**: [Source des données d'entrée]
- **Données de Sortie**: [Destination des données de sortie]

## Résultat de l'Orchestration
```python
noeud_1 = Noeud1()
noeud_2 = Noeud2()
noeud_3 = Noeud3()
noeud_4 = Noeud4() ## default 

noeud_1 - "action_1" >> noeud_2
noeud_2 - "action_2" >> noeud_3
noeud_3 >> noeud_4
```

## Justification de la Conception
[Justification de la conception de l'orchestration du Flux]

**Exigences d'Orchestration :**
1.  Utiliser uniquement les Nœuds de la liste des Nœuds identifiés.
2.  Assurer l'intégrité et la logique du flux de données.
3.  Utiliser une logique de transition pilotée par des Actions.
4.  Prendre en compte la gestion des erreurs et la logique de branchement.
5.  Le diagramme Mermaid doit montrer clairement toutes les connexions et les flux de données.
6.  S'assurer que chaque Nœud a une relation de prédécesseur et de successeur clairement définie.

**Important** : Veuillez suivre scrupuleusement le format Markdown ci-dessus. Ne pas générer de sortie au format JSON ! Générez directement le document Markdown complet."""
