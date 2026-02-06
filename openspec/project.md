# Project Context

## Purpose

GTPlanner is an AI-powered PRD (Product Requirements Document) generator that transforms natural language descriptions into structured technical documentation optimized for "vibe coding" with AI programming assistants like Claude Code, Cursor, and GitHub Copilot.

**Core Philosophy:**
- **Determinism**: Eliminate AI ambiguity through clear SOPs, ensuring highly controllable execution paths
- **Composability**: Break SOPs into reusable "Prefabs" and task modules for flexible workflows
- **Freedom**: Use minimal AI frameworks and native Python code without platform lock-in

**Key Goals:**
1. Help users quickly generate Agent PRDs (standard operating procedures that AI can understand)
2. Enable task automation through clear documentation (design.md, prefab.md, starter-kit)
3. Provide multiple interfaces: Web UI, CLI, API, and MCP integration
4. Support extensible capabilities through the Prefab ecosystem

## Tech Stack

### Core Languages & Frameworks
- **Python ≥3.11** (3.12+ recommended)
- **FastAPI 0.115.9** - Web API framework
- **Pydantic ≥2.5.0** - Data validation and settings
- **PocketFlow 0.0.3** - Async workflow engine for agent orchestration
- **pocketflow-agui 0.1.0** - Async GUI components
- **pocketflow-tracing ≥0.1.5** - Execution tracing

### LLM Integration
- **OpenAI SDK ≥1.0.0** - Primary LLM interface
- **Anthropic API** - Alternative LLM provider
- **Azure OpenAI** - Enterprise LLM option
- **Self-hosted endpoints** - Compatible with custom LLM deployments

### Key Dependencies
- **FastMCP** - Model Context Protocol server implementation
- **aiohttp ≥3.8.0** - Async HTTP client
- **Dynaconf ≥3.1.12** - Configuration management
- **python-dotenv ≥1.0.0** - Environment variable loading
- **PyYAML ≥6.0** - YAML parsing
- **json-repair ≥0.45.0** - JSON repair and parsing
- **Rich ≥13.0.0** - Terminal formatting (CLI)

### Development Tools
- **uv** - Fast Python package manager
- **pytest ≥8.4.1** - Testing framework
- **pytest-asyncio ≥1.1.0** - Async test support

## Project Conventions

### Code Style

**General Principles:**
- Use Python type hints consistently
- Follow PEP 8 style guide with 4-space indentation
- Maximum line length: 120 characters (flexible for long strings)
- Use descriptive variable and function names

**Naming Conventions:**
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`
- File/module names: `snake_case.py`

**Documentation:**
- Docstrings follow Google style
- Use Markdown for README files
- Separate documentation for multiple languages (en, zh, ja)

**Import Organization:**
1. Standard library imports
2. Third-party imports
3. Local application imports
4. Each section separated by blank line

### Architecture Patterns

**Multi-Interface Architecture:**
- **CLI Mode** (`gtplanner/agent/cli/`) - Interactive command-line interface
- **API Mode** (`gtplanner/agent/api/`) - FastAPI REST service
- **MCP Mode** (`mcp/`) - Model Context Protocol integration
- **Web UI** - Browser-based interface (separate deployment)

**Agent System:**
- **Flows** (`gtplanner/agent/flows/`) - Control flow orchestration
- **Subflows** (`gtplanner/agent/subflows/`) - Specialized workflows (research, etc.)
- **Utils** (`gtplanner/utils/`) - Shared utilities and helpers

**Prefab Ecosystem:**
- Prefabs are standardized, reusable AI functional components
- Managed through `prefabs/releases/community-prefabs.json`
- Semantic versioning for compatibility
- Automatic deployment after PR merge

**Configuration Management:**
- **Environment variables** (.env) - Sensitive data (API keys, endpoints)
- **settings.toml** - Application settings (language, tracing, vector services)
- **Dynaconf** for layered configuration

### Testing Strategy

**Test Organization:**
- Unit tests in `tests/` directory
- Async tests using `pytest-asyncio`
- Test files named: `test_*.py` or `*_test.py`

**Testing Principles:**
- Focus on agent workflow testing
- Test LLM integration with mock responses where appropriate
- Validate Prefab loading and execution
- Test configuration loading and validation

**Coverage Goals:**
- Critical paths: ≥80% coverage
- Main agent flows: Comprehensive testing
- Utils and helpers: High coverage priority

### Git Workflow

**Branching Strategy:**
- `main` - Production-ready code
- `feature/*` - New features and enhancements
- `fix/*` - Bug fixes
- `refactor/*` - Code refactoring
- `docs/*` - Documentation updates

**Commit Message Format:**
- Conventional Commits recommended
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Example: `feat: add support for Anthropic Claude API`

**PR Guidelines:**
- All changes require PR review
- Prefabs must include semantic version in PR title
- Update documentation for user-facing changes
- Include tests for new functionality
- Prefab contributions auto-deploy after merge

## Domain Context

**Key Concepts:**

1. **PRD (Product Requirements Document)**
   - Structured technical documentation
   - Optimized for AI code generation assistants
   - Includes: design.md (what), prefab.md (tools), starter-kit (environment)

2. **SOP (Standard Operating Procedure)**
   - Clear definition of inputs, steps, outputs, and success criteria
   - Work that can be "SOPed" can be automated by AI
   - Central to GTPlanner's determinism philosophy

3. **Context Engineering**
   - Process of defining work before AI execution
   - Ensures predictable and controllable AI behavior
   - Reduces ambiguity in AI-generated code

4. **Vibe Coding**
   - Modern development workflow using AI assistants
   - Tools: Claude Code, Cursor, Windsurf, GitHub Copilot
   - Requires well-structured documentation for optimal results

5. **Prefab**
   - Reusable AI functional component
   - Standardized interface and metadata
   - Discoverable, deployable, and version-managed

**User Workflows:**

1. **Interactive Planning**: User provides description → GTPlanner generates PRD → User edits → Export
2. **Prefab Integration**: Identify relevant Prefabs → Include in PRD → Auto-deploy to platform
3. **Code Generation**: Import PRD to AI assistant → Generate implementation code

## Important Constraints

**Technical Constraints:**
- Python ≥3.11 required (uses modern type hints and async features)
- LLM API key required (OpenAI/Anthropic/Azure/self-hosted)
- MCP integration requires compatible client (Cherry Studio, Cursor, etc.)

**Design Constraints:**
- Must maintain platform independence (no lock-in to n8n, etc.)
- Prefabs must follow standardized interface specification
- Documentation must support multiple languages (en, zh, ja)

**Performance Constraints:**
- API response time: Target <5 seconds for basic PRD generation
- Memory usage: Optimize for environments with <2GB RAM
- LLM cost awareness: Cache where possible, minimize token usage

**Security Constraints:**
- Never commit API keys or sensitive data to repository
- .env file must be in .gitignore
- Validate user inputs in API mode
- Sanitize LLM outputs before execution

**Quality Constraints:**
- All changes must pass tests
- Prefabs must be tested before submission
- Documentation updates required for user-facing changes
- Follow semantic versioning for breaking changes

## External Dependencies

**LLM Providers:**
- **OpenAI API** - Primary LLM provider
- **Anthropic API** - Alternative LLM provider
- **Azure OpenAI** - Enterprise LLM option
- **Self-hosted endpoints** - Custom LLM deployments

**Integration Platforms:**
- **Prefab Gateway** (https://gateway.agentbuilder.com) - Prefab execution platform
- **Langfuse** (optional) - Execution tracing and performance analysis
- **OpenSpec** - Spec-driven development workflow (currently integrated)

**Package Repositories:**
- **PyPI** - Python package distribution
- **Tsinghua Mirror** - Primary package mirror for Chinese users
- **GitHub Releases** - Prefab distribution (.whl files)

**Development Tools:**
- **uv** - Fast Python package manager
- **pytest** - Testing framework
- **GitHub Actions** - CI/CD (implied by .github directory)

**Documentation:**
- Multi-language README files (en, zh, ja)
- Web UI deployment (the-agent-builder.com)
- Architecture documentation in `docs/architecture/`
