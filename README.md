# GTPlanner: AI-Powered PRD Generator

<p align="center">
  <img src="./assets/banner.png" width="800" alt="GTPlanner Banner"/>
</p>

<p align="center">
  <strong>An intelligent Agent PRD generation tool that transforms natural language descriptions into structured technical documentation optimized for Vibe coding.</strong>
</p>

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#web-ui-recommended">Web UI</a> •
  <a href="#mcp-integration">MCP Integration</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#project-structure">Project Structure</a> •
  <a href="#prefab-ecosystem">Prefab Ecosystem</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

<p align="center">
  <strong>Languages:</strong>
  <a href="README.md">English</a> •
  <a href="docs/zh/README.md">简体中文</a> •
  <a href="docs/ja/README.md">日本語</a>
</p>

---

## Overview—How to Make Agents Work for You?

- First, define the task: What are the inputs? What are the specific steps? What are the outputs? How do you define success? These are typically called SOPs. **Work that can be SOPed can be automated by AI.**
- Second, provide the right tools for your agent. Humans use Office suites, browse the web, manage files and data, etc. If you want agents to work, they need these tools too.
- Finally, specify how the agent should organize its outputs.

In the Agent context, there's a more appropriate term for this: **context engineering**. Specifically, before starting Code Agents (Claude Code/Cursor/Augment/Devin/...), we want to clearly define through documentation:
- design.md: Define what the work is.
- prefab.md: Define available tools and how to use them. We call these **Prefabs**.
- starter-kit: Define development frameworks and available environments (this part is mostly consistent across projects).

This is what GTPlanner does—simplifying the process of building Agents.

## Why Choose GTPlanner

GTPlanner helps you easily generate an Agent PRD—a standard operating procedure (SOP) that AI can understand—to quickly automate your tasks. GTPlanner's design philosophy:
- **Determinism**: Eliminate AI ambiguity through clear SOPs (Agent PRDs), ensuring highly controllable and predictable execution paths and results.
- **Composability**: Break SOPs into reusable "Prefabs" and task modules, combining them like building blocks to create more complex workflows.
- **Freedom**: We don't lock you into execution platforms (like n8n), but instead use minimal AI frameworks and native Python code for maximum flexibility and freedom.

---

## Web UI (Recommended)

For the best experience, we strongly recommend using the Web UI. It provides a streamlined AI planning workflow tailored for modern developers.

![GTPlanner Web UI](./assets/web.gif)

**Key Advantages:**
- **Intelligent Planning Assistant**: AI-assisted rapid generation of system architecture and project plans
- **Instant Documentation**: Automatically create comprehensive technical documentation
- **Perfectly Suited for Vibe Coding**: Optimized output for Cursor, Windsurf, GitHub Copilot
- **Team Collaboration**: Multi-format export for easy sharing

[Try the Live Demo](https://the-agent-builder.com/)

---

## MCP Integration

<details>
<summary>Click to expand MCP integration instructions</summary>

GTPlanner supports the Model Context Protocol (MCP) for direct use in AI programming tools.

<table>
<tr>
<td width="50%">

**Using in Cherry Studio**
![MCP in Cherry Studio](./assets/Cherry_Studio_2025-06-24_01-05-49.png)

</td>
<td width="50%">

**Using in Cursor**
![MCP in Cursor](./assets/Cursor_2025-06-24_01-12-05.png)

</td>
</tr>
</table>

Detailed configuration guide → [MCP Documentation](./mcp/README.md)

</details>

---

## Quick Start

### Online Quick Experience (No Installation)

[Try Web UI](https://the-agent-builder.com/) - WYSIWYG planning and documentation generation

### Local Setup

#### Prerequisites

- **Python ≥ 3.10** (3.11+ recommended)
- **Package Manager**: [uv](https://github.com/astral-sh/uv) (recommended)
- **LLM API Key**: OpenAI / Anthropic / Azure OpenAI / Self-hosted compatible endpoint

#### Installation

```bash
git clone https://github.com/OpenSQZ/GTPlanner.git
cd GTPlanner

# Install dependencies with uv
uv sync
```

#### Configuration

Copy the configuration template and set your API Key:

```bash
cp .env.example .env
# Edit .env file and set required environment variables
```

**Required Configuration:**
```bash
LLM_API_KEY="your-api-key-here"
LLM_BASE_URL="https://api.openai.com/v1"
LLM_MODEL="gpt-5"
```

Detailed configuration guide (including common providers, Langfuse, etc.) → [Configuration Documentation](./docs/configuration.md)

### CLI Usage

#### Interactive Mode

```bash
python gtplanner.py
```

After starting, simply input your requirements, for example:
```
Create a video analysis assistant that can automatically extract video subtitles, generate summaries and key points.
```

#### Direct Execution

```bash
python gtplanner.py "Design a document analysis assistant that supports PDF, Word document parsing and intelligent Q&A"
```

CLI detailed documentation (session management, parameter explanations, etc.) → [CLI Documentation](./gtplanner/agent/cli/README.md)

### API Usage

Start the FastAPI service:

```bash
uv run fastapi_main.py
# Runs on http://0.0.0.0:11211 by default
```

Visit `http://0.0.0.0:11211/docs` to view API documentation

API detailed documentation (endpoint descriptions, usage examples, etc.) → [API Documentation](./gtplanner/agent/api/README.md)

### MCP Integration

```bash
cd mcp
uv sync
uv run python mcp_service.py
```

MCP detailed documentation (client configuration, available tools, etc.) → [MCP Documentation](./mcp/README.md)

---

## Configuration

GTPlanner supports multiple configuration methods:

- **Environment Variables** (.env file): API Key, Base URL, Model, etc.
- **Configuration File** (settings.toml): Language, tracing, vector services, etc.
- **Langfuse Tracing** (optional): Execution process tracing and performance analysis

Complete configuration guide → [Configuration Documentation](./docs/configuration.md)

---

## Project Structure

```
GTPlanner/
├── README.md                  # Main documentation
├── gtplanner.py              # CLI entry point
├── fastapi_main.py           # API service entry
├── settings.toml             # Configuration file
│
├── gtplanner/                # Core code
│   ├── agent/               # Agent system
│   │   ├── cli/            # → [CLI Documentation](./gtplanner/agent/cli/README.md)
│   │   ├── api/            # → [API Documentation](./gtplanner/agent/api/README.md)
│   │   ├── flows/          # Control flows
│   │   ├── subflows/       # Specialized subflows
│   │   └── ...
│   └── utils/              # Utilities
│
├── prefabs/                 # Prefab ecosystem
│   ├── README.md           # → [Prefab Documentation](./prefabs/README.md)
│   └── releases/           # Release management
│       ├── community-prefabs.json  # Prefab registry
│       └── CONTRIBUTING.md # → [Prefab Contributing Guide](./prefabs/releases/CONTRIBUTING.md)
│
├── mcp/                    # MCP service
│   └── README.md          # → [MCP Documentation](./mcp/README.md)
│
├── docs/                   # Documentation
│   ├── zh/                # Chinese documentation
│   ├── ja/                # Japanese documentation
│   ├── configuration.md   # Configuration guide
│   └── architecture/      # Architecture documentation
│
├── workspace/             # Runtime directory
│   ├── logs/             # Logs
│   └── output/           # Output documents
│
└── tests/                # Tests
```

System architecture documentation → [Architecture Documentation](./docs/architecture/README.md)

---

## Prefab Ecosystem

GTPlanner extends capabilities through the Prefab ecosystem. Each Prefab is a standardized, reusable AI functional component.

### What is a Prefab?

Prefabs are ready-to-use AI functional modules that can be:
- **Discovered**: GTPlanner automatically recognizes available Prefabs
- **Deployed**: Automatically deployed to the platform after PR merge
- **Integrated**: Called through standard APIs
- **Version Managed**: Semantic versioning

### How Do Prefabs Enhance GTPlanner?

When you contribute a Prefab to `community-prefabs.json`:

1. **Expand Planning Capabilities**: GTPlanner learns about a new solution
2. **Smart Recommendations**: GTPlanner recommends appropriate Prefabs when generating plans
3. **Automatic Integration**: Planning documents include Prefab usage instructions

**Example Prefabs:**
- **Media Processing**: [Video Processing Prefab](./Video-processing/) - Video to audio, subtitle extraction
- **Data Services**: [Amap Weather Prefab](./Amap-Weather/) - Weather queries
- **Document Processing**: PDF parsing, Excel processing
- **AI Services**: Speech recognition, image recognition

### Getting Started

**Using Prefabs:**

Call any published Prefab through the Prefab Gateway:

```bash
# 1. Create API Key on AgentBuilder platform
# 2. Call Prefab through gateway
curl -X POST "https://gateway.agentbuilder.com/v1/prefabs/{prefab-id}/execute" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"function": "function_name", "parameters": {...}}'
```

**Browse Available Prefabs:**
```bash
cat prefabs/releases/community-prefabs.json | jq '.'
```

**Create Your Own Prefab:**
```bash
git clone https://github.com/The-Agent-Builder/Prefab-Template.git my-prefab
cd my-prefab
uv sync --dev
# Develop, test, publish
```

Complete Prefab documentation → [Prefab Guide](./prefabs/README.md)  
Gateway calling details → [Prefab Usage Guide](./prefabs/README.md#for-users-using-prefabs)

---

## Contributing

We believe that an excellent tool requires community wisdom and collaboration. GTPlanner welcomes your participation!

### Contributing Prefabs (Easiest Way to Contribute)

**Why Contribute Prefabs?**

Each Prefab will:
- Extend GTPlanner's planning capabilities
- Help other developers solve problems
- Be automatically included in the recommendation system
- Gain community recognition

**How to Contribute?**

1. Create a Prefab using the template → [Prefab-Template](https://github.com/The-Agent-Builder/Prefab-Template)
2. Develop and test your functionality
3. Publish a GitHub Release and upload the `.whl` file
4. Submit a PR to `prefabs/releases/community-prefabs.json`

**Prefab Impact:**
- **Enter Recommendation System**: Prefabs in `community-prefabs.json` are recognized by GTPlanner
- **Smart Matching**: Automatically recommended for appropriate scenarios during planning
- **Auto Deployment**: Automatically deployed to Prefab platform after PR merge

Detailed contribution guide → [Prefab Contributing Documentation](./prefabs/releases/CONTRIBUTING.md)

### Contributing Core Code

Improve GTPlanner's planning quality and system performance through evaluation-driven development.

Core code contribution → [Contributing Guide](./docs/zh/CONTRIBUTING.md)

### Sharing Case Studies

Share your experience to help the community discover GTPlanner's full potential:

- **Use Cases**: Applications in real projects
- **GTPlanner-Generated PRDs**: Showcase planning quality
- **Tutorials and Best Practices**: Help new users get started

Submit cases → Create PR in `docs/examples/community-cases/`

---

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE.md) for details.

---

## Acknowledgments

- Built on [PocketFlow](https://github.com/The-Pocket/PocketFlow) async workflow engine
- Configuration management powered by [Dynaconf](https://www.dynaconf.com/)
- Designed for seamless integration with AI assistants through MCP protocol

---

<p align="center">
  <strong>GTPlanner</strong> - Transform your ideas into structured blueprints with the power of AI.
</p>
