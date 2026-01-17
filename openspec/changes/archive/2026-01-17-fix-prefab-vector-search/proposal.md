# Change: Fix Prefab Vector Search API Mismatch

## Why

The prefab vector search feature was failing due to API contract mismatches between GTPlanner and the FAISS vector service. The search request used incorrect parameter names and the response parsing logic didn't handle the vector service's actual response format, causing all prefab searches to return no results.

## What Changes

- **FIX**: Update search request parameter from `query` to `question` to match vector service API
- **FIX**: Adapt response parsing to handle vector service format (`{total_found, detailed_results}` → `{total, results}`)
- **FIX**: Parse JSON string from `text` field in search results
- **FIX**: Update `build_index.py` to use correct `/add` endpoint instead of deprecated index management endpoints
- **FIX**: Improve error handling for JSON parsing failures in search results

## Impact

- **Affected specs**: `prefab-search`
- **Affected code**:
  - `gtplanner/agent/nodes/node_prefab_recommend.py:343` (search request parameter)
  - `gtplanner/agent/nodes/node_prefab_recommend.py:360-395` (response format adaptation)
  - `prefabs/releases/scripts/build_index.py` (endpoint changes)
  - `tests/test_prefab_recommend.py` (existing tests remain compatible)

## Testing

Existing tests in `tests/test_prefab_recommend.py` validate the fix:
- `test_prefab_recommend_tool()` - Tests vector search with actual vector service
- `test_local_search()` - Tests fallback local search mode
- `test_search_prefabs_tool()` - Tests agent tool integration

## Benefits

- ✅ Prefab vector search now works correctly with FAISS vector service
- ✅ Automatic keyword extraction from user queries improves search relevance
- ✅ Better error handling prevents crashes on malformed search results
- ✅ Simplified index building script using vector service's `/add` endpoint
