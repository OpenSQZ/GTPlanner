## ADDED Requirements

### Requirement: Intelligent Prefab Search
The system SHALL provide intelligent prefab search functionality that can handle natural language queries and extract relevant keywords automatically.

#### Scenario: Natural language query with multiple keywords
- **WHEN** user provides a query with multiple keywords separated by punctuation (e.g., "视频处理、格式转换、视频编辑")
- **THEN** the system SHALL extract individual keywords and search for each
- **AND** the system SHALL return aggregated results matching any of the keywords
- **AND** the system SHALL deduplicate results

#### Scenario: Full sentence query
- **WHEN** user provides a full sentence as search query
- **THEN** the system SHALL remove punctuation and common stopwords
- **AND** the system SHALL extract meaningful keywords from the sentence
- **AND** the system SHALL perform search using extracted keywords

#### Scenario: Fallback to individual keyword search
- **WHEN** search with full query returns no results
- **THEN** the system SHALL automatically split query into keywords
- **AND** the system SHALL search using each keyword (up to 3 keywords)
- **AND** the system SHALL return combined results from all keyword searches

#### Scenario: Simple keyword query (backward compatibility)
- **WHEN** user provides a simple keyword query (e.g., "视频" or "video")
- **THEN** the system SHALL perform substring matching as before
- **AND** the system SHALL return matching prefabs

## MODIFIED Requirements

### Requirement: search_prefabs Tool Description
The `search_prefabs` tool SHALL include clear usage examples and guidance to encourage LLM to pass concise keywords.

#### Scenario: Tool description includes examples
- **WHEN** LLM examines the `search_prefabs` tool description
- **THEN** it SHALL see examples showing effective keyword usage
- **AND** examples SHALL demonstrate Chinese queries (e.g., "视频处理", "天气")
- **AND** examples SHALL demonstrate English queries (e.g., "video", "weather")
- **AND** description SHALL advise against passing complete sentences

#### Scenario: LLM follows tool description guidance
- **WHEN** LLM calls `search_prefabs` based on tool description
- **THEN** it SHALL prefer passing concise keywords over full sentences
- **AND** the system SHALL receive queries like "视频处理" instead of "视频处理、格式转换、视频编辑"
