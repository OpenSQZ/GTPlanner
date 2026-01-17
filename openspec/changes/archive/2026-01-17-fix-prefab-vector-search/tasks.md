# Implementation Tasks

## 1. Code Changes

- [x] 1.1 Fix search request parameter in `node_prefab_recommend.py`
  - Change `"query": query` to `"question": query` at line 343
  - Add comment explaining the parameter name requirement

- [x] 1.2 Adapt vector service response format in `node_prefab_recommend.py`
  - Extract `total_found` from response (fallback to `total`)
  - Parse `detailed_results` array and convert to `results` format
  - Extract and parse JSON string from `text` field
  - Handle JSON parsing errors gracefully (skip malformed results)

- [x] 1.3 Update `build_index.py` script
  - Remove deprecated index management endpoints (`/index/{name}`, `/documents`)
  - Use `/add` endpoint with `businesstype` parameter
  - Simplify document conversion to JSON string format
  - Update `DEFAULT_BUSINESS_TYPE` to `"gtplanner_prefabs"`

## 2. Testing

- [x] 2.1 Verify existing tests still pass
  - Run `pytest tests/test_prefab_recommend.py -v`
  - Confirm `test_prefab_recommend_tool()` works with vector service
  - Verify fallback mode works when vector service unavailable

- [x] 2.2 Manual testing with real queries
  - Test query: "hello world example prefab"
  - Verify search returns relevant prefabs with scores
  - Confirm LLM filtering works when enabled

## 3. Documentation

- [x] 3.1 Update code comments
  - Add explanation for `question` parameter name
  - Document response format adaptation logic
  - Add error handling documentation

- [x] 3.2 Verify proposal completeness
  - All changes documented in proposal.md
  - Spec deltas accurately reflect behavior changes
  - Validation passes without errors

## 4. Validation

- [x] 4.1 OpenSpec validation
  - Run `openspec validate fix-prefab-vector-search --strict --no-interactive`
  - Confirm all validation checks pass
  - Verify spec delta format is correct

- [x] 4.2 Code quality checks
  - Verify code follows project conventions
  - Check type hints are correct
  - Ensure error handling is comprehensive
