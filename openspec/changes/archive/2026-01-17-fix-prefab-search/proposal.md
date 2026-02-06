# Change: Fix Prefab Search Functionality

## Why

Users reported that GTPlanner cannot retrieve prefabs when querying. The root cause is that LLM passes complete sentences (e.g., "视频处理、格式转换、视频编辑") to `search_prefabs`, but `LocalPrefabSearcher` uses simple substring matching which fails to match keywords in prefab descriptions.

**Impact**: This is a critical bug that prevents users from discovering and using available prefabs, breaking the core "Prefab Ecosystem" feature of GTPlanner.

## What Changes

- Improve `search_prefabs` to handle long queries by extracting keywords
- Add intelligent keyword extraction (remove common stopwords, punctuation)
- Update tool description to guide LLM to pass concise keywords
- Ensure backward compatibility with existing search behavior

**Breaking Changes**: None - this is a bug fix that improves existing functionality

## Impact

- Affected specs:
  - `prefab-system` (if exists) - prefab discovery and recommendation
- Affected code:
  - `gtplanner/agent/function_calling/agent_tools.py` - `_execute_search_prefabs` function
  - `gtplanner/agent/utils/local_prefab_searcher.py` - may need enhancements
- Benefits:
  - Users can successfully find prefabs using natural language queries
  - Improved user experience when searching for prefabs
  - Better alignment between LLM queries and search capabilities
