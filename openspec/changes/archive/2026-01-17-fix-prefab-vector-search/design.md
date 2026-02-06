# Technical Design: Fix Prefab Vector Search API Mismatch

## Context

The prefab recommendation feature relies on a FAISS vector service for semantic search. The service has a specific API contract that differs from GTPlanner's original assumptions, causing search failures.

### Current Architecture

```
User Query → NodePrefabRecommend → Vector Service API → Search Results
                                      ↓
                               Response Format Mismatch
                                      ↓
                                    No Results
```

### Vector Service API Contract

**Search Request (`/search`)**:
```json
{
  "question": "user query text",  // Note: "question" not "query"
  "vector_field": "combined_text",
  "index": "document_gtplanner_prefabs",
  "top_k": 10
}
```

**Search Response**:
```json
{
  "total_found": 42,
  "detailed_results": [
    {
      "text": "{\"id\": \"prefab-001\", \"name\": \"Hello World\", ...}",  // JSON string
      "score": 0.892,
      "faiss_id": 123,
      "text_relevance": 0.892,
      "search_method": "vector"
    }
  ]
}
```

**Add Document Request (`/add`)**:
```json
{
  "content": "document content here",  // JSON strings separated by newlines
  "businesstype": "gtplanner_prefabs",
  "chunk_size": 1000,
  "chunk_overlap": 100
}
```

## Goals / Non-Goals

### Goals
- Fix API parameter mismatch in search requests
- Adapt response parsing to handle vector service format
- Improve error handling for malformed results
- Simplify index building script

### Non-Goals
- Changing the vector service API (it's external)
- Implementing alternative search algorithms
- Modifying the local search fallback mode
- Changing the LLM filtering logic

## Decisions

### Decision 1: Adapt Request Parameter Name
**What**: Change `"query"` to `"question"` in search requests

**Why**: The vector service API expects the parameter name to be `"question"`, not `"query"`. This is a hard requirement of the external service.

**Alternatives Considered**:
1. Modify vector service to accept both names ❌ (Not our service to modify)
2. Use a proxy/adapter layer ❌ (Adds unnecessary complexity)
3. Adapt to use `"question"` ✅ (Simplest solution)

**Implementation**: Single line change in `node_prefab_recommend.py:343`

### Decision 2: Adapt Response Format in Node
**What**: Add response adaptation logic in `_search_prefabs_vector()`

**Why**: The vector service returns `{total_found, detailed_results}` but GTPlanner expects `{total, results}`. Additionally, the prefab data is embedded as a JSON string in the `text` field.

**Alternatives Considered**:
1. Change vector service response format ❌ (Not our service)
2. Create a separate adapter layer ❌ (Over-engineering for one usage)
3. Adapt in the search method ✅ (Keeps change localized)

**Implementation**:
```python
# Extract total count
total_results = result.get('total_found', result.get('total', 0))

# Parse and convert detailed_results
detailed_results = result.get('detailed_results', [])
adapted_results = []
for item in detailed_results:
    prefab_info = json.loads(item.get('text', '{}'))
    adapted_item = {
        'score': item.get('score', 0.0),
        'document': prefab_info,
        'faiss_id': item.get('faiss_id'),
        'text_relevance': item.get('text_relevance'),
        'search_method': item.get('search_method')
    }
    adapted_results.append(adapted_item)

# Replace with adapted format
result['total'] = total_results
result['results'] = adapted_results
```

### Decision 3: Update Index Building Script
**What**: Replace deprecated index management endpoints with `/add` endpoint

**Why**: The vector service deprecated the manual index creation and document addition endpoints in favor of a simpler `/add` endpoint that handles everything automatically.

**Alternatives Considered**:
1. Keep using deprecated endpoints ❌ (Will break eventually)
2. Use `/add` endpoint ✅ (Recommended by vector service)
3. Switch to different indexing strategy ❌ (Outside scope)

**Implementation**:
- Remove: `/index/{name}` (PUT) and `/documents` (POST)
- Use: `/add` (POST) with `businesstype` parameter
- Simplify document format: JSON strings instead of structured objects

## Risks / Trade-offs

### Risk 1: JSON Parsing Failures
**Risk**: Malformed JSON in `text` field could cause crashes

**Mitigation**: Added try-catch around `json.loads()`, skip malformed results with warning

### Risk 2: Vector Service API Changes
**Risk**: Future changes to vector service API could break again

**Mitigation**: Add clear comments about API contract, consider versioning in future

### Trade-off: Code Complexity vs. Correctness
**Choice**: Added response adaptation logic (~30 lines) to ensure correct behavior

**Rationale**: The complexity is justified because it's isolated to one method and makes the system work correctly with the actual vector service API.

## Migration Plan

### Steps
1. Update `node_prefab_recommend.py` with search request fix
2. Add response format adaptation logic
3. Update `build_index.py` to use `/add` endpoint
4. Run tests to verify compatibility
5. Deploy with monitoring for search failures

### Rollback
If issues arise:
1. Revert code changes (simple git revert)
2. Vector service will return errors (graceful degradation to local search)
3. No data loss or corruption risk

## Open Questions

1. **Should we add API version checking?**
   - **Status**: Not needed for current fix
   - **Future consideration**: Could add version endpoint check for robustness

2. **Should we implement retry logic for transient failures?**
   - **Status**: Already exists in `NodePrefabRecommend` parent class
   - **Current**: `max_retries=3, wait=2.0`

3. **Should we add metrics for search success/failure rates?**
   - **Status**: Out of scope for this fix
   - **Future consideration**: Add to tracing/monitoring system
