# Spec Delta: Prefab Search

## MODIFIED Requirements

### Requirement: Vector Service Search API Integration
The prefab recommendation system SHALL correctly integrate with the FAISS vector service search API using the expected request and response format.

#### Scenario: Successful search with correct API parameters
- **WHEN** user provides a query for prefab recommendation
- **THEN** the system SHALL send a search request with `"question"` parameter (not `"query"`)
- **AND** the system SHALL include `"vector_field"`, `"index"`, and `"top_k"` parameters
- **AND** the system SHALL receive results in the vector service's response format

#### Scenario: Response format adaptation
- **WHEN** the vector service returns search results in format `{total_found, detailed_results}`
- **THEN** the system SHALL adapt the response to GTPlanner's expected format `{total, results}`
- **AND** the system SHALL parse the JSON string from each result's `text` field
- **AND** the system SHALL handle JSON parsing errors gracefully by skipping malformed results

#### Scenario: Search returns relevant prefabs with scores
- **WHEN** the vector service returns valid search results
- **THEN** the system SHALL extract prefab information from the parsed JSON
- **AND** the system SHALL preserve the similarity score for ranking
- **AND** the system SHALL return results sorted by relevance score in descending order

### Requirement: Prefab Index Building
The prefab index building script SHALL use the vector service's `/add` endpoint to index prefab documents.

#### Scenario: Index building with correct endpoint
- **WHEN** the `build_index.py` script is executed with vector service URL
- **THEN** the system SHALL convert prefabs to JSON string format
- **AND** the system SHALL send documents to the `/add` endpoint (not deprecated `/documents` endpoint)
- **AND** the system SHALL include `businesstype` parameter set to `"gtplanner_prefabs"`
- **AND** the system SHALL specify `chunk_size` and `chunk_overlap` parameters

#### Scenario: Simplified document format
- **WHEN** converting prefabs to document content
- **THEN** the system SHALL create JSON strings for each prefab containing: `id`, `name`, `description`, `tags`, `version`, `author`, `repo_url`
- **AND** the system SHALL separate prefab JSON strings with newlines
- **AND** the system SHALL send the combined content as a single `content` parameter

## ADDED Requirements

### Requirement: Search Request Parameter Mapping
The system SHALL correctly map query parameters to match the vector service API expectations.

#### Scenario: Query parameter uses correct field name
- **WHEN** constructing a search request for the vector service
- **THEN** the system SHALL use `"question"` as the parameter name for the user query
- **AND** the system SHALL NOT use `"query"` or `"q"` as parameter names
- **AND** the parameter value SHALL contain the user's search text

#### Scenario: Error handling for parameter mismatch
- **WHEN** the vector service returns a 400 error due to parameter mismatch
- **THEN** the system SHALL log a descriptive error message
- **AND** the system SHALL suggest checking the vector service API documentation
- **AND** the system SHALL fall back to local search if configured

### Requirement: Response Parsing Robustness
The system SHALL handle vector service response parsing failures without crashing the search operation.

#### Scenario: Graceful handling of malformed JSON
- **WHEN** a search result contains invalid JSON in the `text` field
- **THEN** the system SHALL catch the JSON parsing exception
- **AND** the system SHALL skip the malformed result and continue processing
- **AND** the system SHALL log a warning about the skipped result

#### Scenario: Empty results handling
- **WHEN** the vector service returns zero results or all results are filtered out
- **THEN** the system SHALL return an empty prefab list
- **AND** the system SHALL indicate total_found as 0
- **AND** the system SHALL not raise an exception for empty results

#### Scenario: Missing fields in response
- **WHEN** the vector service response is missing expected fields
- **THEN** the system SHALL use sensible defaults (e.g., `total_found` defaults to 0, `score` defaults to 0.0)
- **AND** the system SHALL continue processing with available data
- **AND** the system SHALL log warnings about missing fields
