# Design: Fix Prefab Search Functionality

## Context

**Problem**: GTPlanner's `search_prefabs` tool fails to find prefabs when LLM passes complete sentences instead of concise keywords.

**Current Behavior**:
- `LocalPrefabSearcher.search(query="视频处理、格式转换、视频编辑")` → 0 results
- `LocalPrefabSearcher.search(query="视频处理")` → 1 result ✅

**Root Cause**:
1. LLM interprets user's natural language query literally
2. LLM passes complete sentence to `search_prefabs`
3. `LocalPrefabSearcher` uses simple `in` operator for substring matching
4. Complete sentence doesn't match any prefab description substring

## Goals / Non-Goals

**Goals**:
- Enable prefab search with natural language queries
- Improve search success rate without breaking existing functionality
- Minimal code changes, maximal compatibility

**Non-Goals**:
- Full NLP/semantic search (that's what `prefab_recommend` with vector service does)
- Complex query language or advanced filters
- Changes to prefab data structure or indexing

## Decisions

### Decision 1: Keyword Extraction Approach

**Chosen**: Simple keyword extraction + multi-keyword fallback search

**Alternatives Considered**:
1. **Full NLP keyword extraction** (using jieba, spaCy)
   - Pros: More accurate segmentation
   - Cons: Heavy dependency, complex, overkill for simple use case

2. **Regex-based punctuation removal**
   - Pros: Lightweight, no dependencies
   - Cons: May not handle all edge cases

3. **Simple split + multi-keyword search** ✅ **CHOSEN**
   - Pros: Simple, effective, no dependencies, backward compatible
   - Cons: May not be perfect for all languages

**Implementation**:
```python
def extract_keywords(query: str) -> List[str]:
    """Extract keywords from query string"""
    # Remove common punctuation
    import re
    cleaned = re.sub(r'[、。，,.\s]+', ' ', query)
    # Split by spaces
    keywords = [k.strip() for k in cleaned.split(' ') if k.strip()]
    return keywords

# Try full query first, then fallback to individual keywords
results = searcher.search(query=query)
if not results and keywords:
    # Try each keyword and aggregate results
    for kw in keywords:
        results.extend(searcher.search(query=kw))
```

### Decision 2: Tool Description Update

**Chosen**: Add explicit examples to guide LLM behavior

**Rationale**: LLM follows patterns in tool descriptions. Providing examples will encourage passing concise keywords.

**Updated Description**:
```python
"description": "在本地预制件库中搜索。这是一个降级工具，当向量服务不可用时使用。提供基于关键词、标签、作者的模糊搜索功能。**建议优先使用 prefab_recommend（如果向量服务可用），该工具提供更精准的语义匹配。**\n\n**使用提示**：传递简洁的关键词效果最佳，例如：\n- 查询视频处理：query='视频处理' 或 query='视频'\n- 查询天气：query='天气' 或 query='weather'\n- 避免传递完整句子，如 '视频处理、格式转换、视频编辑'"
```

## Risks / Trade-offs

**Risk**: Keyword extraction may create false positives
- **Mitigation**: Maintain relevance scoring, return most relevant results first

**Risk**: Increased search time with multiple keyword searches
- **Mitigation**: Add caching, limit number of fallback keywords (max 3)

**Trade-off**: Simplicity vs. accuracy
- **Decision**: Favor simplicity for now, can enhance later if needed

## Migration Plan

**Steps**:
1. Add keyword extraction logic to `_execute_search_prefabs`
2. Update tool description in agent tools registration
3. Test with various query patterns
4. Monitor search success rate

**Rollback**: If issues arise, keyword extraction can be disabled by commenting out the fallback logic. The original search behavior remains intact.

## Open Questions

- [ ] Should we add logging for keyword extraction to help diagnose search issues?
- [ ] Should we limit the number of keywords to try in fallback mode? (Current proposal: max 3)
- [ ] Should we deduplicate results from multiple keyword searches?
