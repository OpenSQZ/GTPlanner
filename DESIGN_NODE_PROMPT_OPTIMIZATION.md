# Design Node Prompt Optimization Summary

## Overview

Optimized the design node prompt template to properly display prefab function information in generated design documents. This ensures that when the orchestrator calls `list_prefab_functions` and passes the function list to the design tool, the generated document will include detailed function information.

## Changes Made

### File Modified
`gtplanner/agent/prompts/templates/agents/design/design_node.py`

### Optimization Content

#### 1. Chinese Version (lines 95-115)

**Before**:
```markdown
### 1. [预制件名称]
- **ID**: `[预制件ID]`
- **描述**: [预制件功能描述]
- **用途**: [在本系统中的具体使用场景和调用方式]
```

**After**:
```markdown
### 1. [预制件名称]
- **ID**: `[预制件ID]`
- **版本**: `[版本号，如 0.2.0]`
- **描述**: [预制件功能描述]
- **提供的函数**:
  - `[函数名1]`: [函数描述 - 从 functions 列表中获取]
  - `[函数名2]`: [函数描述]
  - ...
- **用途**: [在本系统中的具体使用场景，说明会调用哪些函数]
```

**Updated AI Instructions**:
- Point 3: **新增** "函数列表是关键信息：如果 `recommended_prefabs` 包含函数列表（`functions` 字段），**必须在"提供的函数"部分列出**"
- Point 4: **修改** 从"说明每个预制件在系统中的具体用途"改为"说明每个预制件在系统中的具体用途，**以及会使用哪些函数**"
- Point 5-6: 重新编号（原 4-5 改为 5-6）

#### 2. English Version (lines 310-328)

**Before**:
```markdown
### 1. [Prefab Name]
- **ID**: `[prefab-id]`
- **Description**: [Prefab functionality description]
- **Usage**: [Specific use case and how to call it in this system]
```

**After**:
```markdown
### 1. [Prefab Name]
- **ID**: `[prefab-id]`
- **Version**: `[version number, e.g., 0.2.0]`
- **Description**: [Prefab functionality description]
- **Provided Functions**:
  - `[function_name1]`: [function description - from functions list]
  - `[function_name2]`: [function description]
  - ...
- **Usage**: [Specific use case in this system, mentioning which functions will be called]
```

**Updated AI Instructions**:
- Point 3: **Added** "**Function list is critical information**: If `recommended_prefabs` includes a function list (`functions` field), **you MUST list them in the "Provided Functions" section**"
- Point 4: **Modified** from "Explain the specific use case for each prefab in this system" to "Explain the specific use case for each prefab in this system, **and which functions will be used**"
- Points 5-6: Renumbered (original 4-5 became 5-6)

## Key Improvements

### 1. Function List Display ✅
- **Added "Provided Functions" section** to show all functions available in each prefab
- **Requires function descriptions** to be extracted from the `functions` field in `recommended_prefabs`
- Ensures the design document contains actionable information about prefab capabilities

### 2. Version Information ✅
- **Added "Version" field** to track which version of the prefab is being recommended
- Helps with reproducibility and debugging

### 3. Enhanced Usage Description ✅
- **Updated usage field** to explicitly mention which functions will be called
- Provides clearer implementation guidance for downstream code generation

### 4. Stronger AI Instructions ✅
- **Elevated function list to "critical information"** status (matching prefab ID)
- **Made function listing mandatory** when `functions` field exists in `recommended_prefabs`
- **Required explicit function usage** in the usage description

## Integration with Workflow

### Upstream: Orchestrator
The orchestrator now **must** call `list_prefab_functions` after `prefab_recommend`:

```
1. prefab_recommend → Find suitable prefabs
2. list_prefab_functions → ⭐ Must immediately check function list (verify capability)
3. design → Generate document (with function list included)
```

### This Node: Design
The design node receives `recommended_prefabs` with function information:

```python
{
    "id": "prefab-id",
    "version": "0.2.0",
    "name": "Prefab Name",
    "description": "Prefab description",
    "functions": [
        {
            "name": "function_name",
            "description": "function description"
        }
    ]
}
```

And generates design documents that include:
- Prefab basic info (ID, version, description)
- **Function list with descriptions**
- **Specific usage scenarios mentioning which functions will be used**

### Downstream: Prefab Functions Detail Node
After the design document is generated, `PrefabFunctionsDetailNode` queries detailed function information:

```
Design Node (generates design.md)
    ↓
PrefabFunctionsDetailNode (queries function details)
    ↓
prefab_functions_details.md (detailed API documentation)
```

## Expected Output Format

When the orchestrator follows the new workflow, the generated design document will include:

```markdown
## Prefabs

### 1. Browser Automation Agent
- **ID**: `browser-automation-agent`
- **Version**: `0.2.0`
- **描述**: 提供浏览器自动化能力，支持网页操作、数据提取等功能
- **提供的函数**:
  - `navigate_and_extract`: 导航到指定URL并提取数据
  - `fill_form`: 自动填写网页表单
  - `click_element`: 点击页面元素
  - `wait_for_element`: 等待元素出现
- **用途**: 在本系统中用于自动化浏览器操作，主要使用 `navigate_and_extract` 提取页面数据，使用 `fill_form` 填写表单，使用 `wait_for_element` 等待页面加载完成
```

## Benefits

### 1. More Actionable Design Documents
Users can immediately see what functions are available in each recommended prefab, without needing to consult external documentation.

### 2. Verification of Recommendations
The orchestrator must verify that recommended prefabs have suitable functions before generating the design document, avoiding "blind recommendations".

### 3. Clear Implementation Guidance
The usage field now explicitly mentions which functions will be used, providing clear guidance for downstream code generation.

### 4. Consistent with Orchestrator Workflow
The design node template now aligns with the orchestrator's mandatory `list_prefab_functions` step, ensuring the function information is actually used.

## Testing

All tests pass successfully:
- ✅ Test 1: Normal flow with recommended prefabs and functions - **PASSED**
- ✅ Test 2: No recommended prefabs - **PASSED** (correctly skipped)
- ✅ Test 3: Recommended prefabs without function list - **PASSED** (correctly skipped)

## Related Changes

This optimization is part of a series of improvements:

1. **Orchestrator Prompt Optimization** ([ORCHESTRATOR_PROMPT_OPTIMIZATION.md](ORCHESTRATOR_PROMPT_OPTIMIZATION.md))
   - Elevated `list_prefab_functions` to core required tool
   - Made function list checking mandatory after prefab recommendation

2. **Prefab Functions Detail Node** ([PREFAB_FUNCTIONS_DETAIL_IMPLEMENTATION.md](PREFAB_FUNCTIONS_DETAIL_IMPLEMENTATION.md))
   - Created post-processing node to query detailed function information
   - Generates comprehensive API documentation

3. **Design Node Prompt Optimization** (this document)
   - Updated design template to display function lists
   - Ensures design documents include actionable function information

## Language Versions

- ✅ Chinese version (完整优化)
- ✅ English version (完整优化)
- ⏭️ Japanese version (待补充)
- ⏭️ Spanish version (待补充)
- ⏭️ French version (待补充)

## Next Steps

1. **Monitor Agent Behavior**
   - Verify that generated design documents include function lists
   - Check if function usage descriptions are specific and actionable

2. **Collect User Feedback**
   - Assess whether function lists improve design document usability
   - Determine if function descriptions need more detail

3. **Optimize Function Display**
   - Consider grouping functions by category
   - Add parameter hints in function descriptions

4. **Extend to Other Languages**
   - Apply same optimizations to Japanese, Spanish, and French versions
   - Ensure consistency across all language versions

## Summary

This optimization completes the workflow enhancement for prefab function information:

**Before**:
- Orchestrator recommends prefabs → Design generates document (without function info)

**After**:
- Orchestrator recommends prefabs → **Checks function list** → Design generates document **with function list** → Queries detailed function info → Generates API documentation

The design documents now provide:
- ✅ Clear visibility into prefab capabilities
- ✅ Verified function availability
- ✅ Specific usage guidance
- ✅ Actionable implementation details

This ensures users get comprehensive, accurate information about recommended prefabs in every design document.
