# 🏥 Healthcare Concierge Multi-Agent System

A healthcare concierge system that routes user queries to specialized agents, each with access to different data sources and LLMs, then synthesizes their responses into unified answers.

## Project Overview

This is an **agentic AI system** that leverages multiple specialized language models (Claude and Gemini) working together to provide comprehensive healthcare information and assistance. Instead of a single monolithic AI, the system uses a **multi-agent architecture** where each agent specializes in a specific domain:

- **Insurance & Policy Agent** — Understands your healthcare plan details and coverage limitations
- **Healthcare Provider Agent** — Finds qualified doctors and specialists near you
- **Health Research Agent** — Provides medical information about conditions, treatments, and prevention
- **Concierge Orchestrator** — Routes your queries intelligently to the right specialists and synthesizes their answers

This multi-agent approach ensures **accuracy**, **expertise**, and **comprehensive answers** by allowing each agent to focus on what it does best, while the orchestrator ensures all your questions are fully answered.

### Key Features

- **Multi-source answers** — Get policy info + provider recommendations + medical research in one response
- **Real data** — Uses your actual insurance policy PDF and a local database of healthcare providers
- **Specialized expertise** — Each agent uses the best model for its domain (Claude for policy/providers, Gemini for research)
- **Observability** — Optional Phoenix tracing to see exactly how agents make decisions
- **Model Context Protocol** — Provider search uses MCP for clean tool integration

## What You Can Do

- **Get insurance coverage info** — Upload your policy PDF, ask about coverage details
- **Find healthcare providers** — Search for doctors by location and specialty from a local database
- **Research health conditions** — Get real-time health information with citations
- **Get complete answers** — Single query routes to multiple agents for comprehensive responses

## Quick Start

### How It Works (60-second overview)

1. You ask a question to the **Concierge Agent** (the orchestrator)
2. Concierge analyzes your question and routes it to 1-3 specialized agents:
   - Policy Agent (for insurance questions)
   - Provider Agent (for doctor/hospital searches)
   - Research Agent (for medical information)
3. Each specialist agent processes your request in parallel
4. Concierge collects all responses and synthesizes them into one comprehensive answer
5. You get a complete answer with sources cited for each piece of information

### Prerequisites
- Python 3.12+
- API keys: `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` (from `.env.local` or environment)
- Data files: `data/2026AnthemgHIPSBC.pdf` (insurance policy) and `data/doctors.json` (provider database)

### Setup Overview

The system requires **7 services running in parallel**:
1. **MCP Server** — Database of healthcare providers (provider data source)
2. **Policy Agent** — Analyzes insurance policies (Claude Haiku 4.5 on port 9999)
3. **Provider Agent** — Searches for doctors (Claude Haiku 4.5 on port 9997)
4. **Research Agent** — Finds health information (Gemini 3.1 Flash Lite on port 9996)
5. **Concierge Agent** — Routes queries to agents (Gemini 3.1 Flash Lite on port 9001)
6. **Phoenix Server** — Traces LLM calls (optional, port 6006)
7. **Test Client** — Sends example queries to verify everything works

### Manual Setup (run each in a separate terminal)

**Terminal 1 — MCP Server** (provider database)
```bash
python mcpserver.py
# Expected output: Server running, listening for connections
```

**Terminal 2 — Policy Agent** (insurance coverage)
```bash
python a2a_policy_agent.py
# Expected output: Running Healthcare Policy Agent on http://localhost:9999
```

**Terminal 3 — Provider Agent** (doctor search via MCP)
```bash
python a2a_provider_agent.py
# Expected output: Running Healthcare Provider Agent on http://localhost:9997
```

**Terminal 4 — Research Agent** (health information)
```bash
python a2a_research_agent.py
# Expected output: Running Healthcare Research Agent on http://localhost:9996
```

**Terminal 5 — Healthcare Concierge** (orchestrator)
```bash
python a2a_healthcare_agent.py
# Expected output: Running Healthcare Concierge Agent on http://localhost:9001
```

**Terminal 6 — Phoenix Observability Server** (optional, for tracing)
```bash
python -m phoenix.server.main serve
# Expected output: Server running on http://localhost:6006
# View traces at: http://localhost:6006 (or set PHOENIX_ENDPOINT in agents)
```

**Terminal 7 — Test the System** (integration test)
```bash
python test_client.py
# Should output the Healthcare Concierge response with:
# - Policy coverage info
# - Provider search results
# - Health research data
# If Phoenix is running, traces will appear at http://localhost:6006
```
---

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  User Query (e.g., "Are there cardiologists near Boston with coverage?")    │
│                                                                             │
│                                  ↓                                          │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                  Healthcare Concierge Agent                          │   │
│  │                       (Gemini 2.5)                                   │   │
│  │  Orchestrates queries to specialist agents using HandoffTool         │   │
│  │  Synthesizes responses and enforces constraints                      │   │
│  └─────────┬──────────────────────┬──────────────────────┬──────────────┘   │
│            │                      │                      │                  │
│  ┌─────────▼────────┐  ┌──────────▼────────┐   ┌─────────▼──────────┐       │
│  │  Policy Agent    │  │ Provider Agent    │   │ Research Agent     │       │
│  │  (Claude Haiku)  │  │ (Claude Haiku)    │   │ (Gemini 2.5)       │       │
│  │                  │  │                   │   │                    │       │
│  │ Coverage queries │  │ Doctor searches   │   │ Health information │       │
│  └────────┬─────────┘  └─────────┬────────┘    └────────┬───────────┘       │
│           │                      │                      │                   │
│           │ loads PDF            │ calls MCP            │ calls Google      │
│           ↓                      ↓                      ↓                   │
│  ┌─────────────────┐  ┌──────────────────┐    ┌──────────────────┐          │
│  │ 2026AnthemPDF   │  │  MCP Server      │    │  Google Search   │          │
│  │ (insurance plan)│  │  list_doctors()  │    │  (real-time data)│          │
│  │                 │  │                  │    │                  │          │
│  │ - Coverage info │  │ data/doctors.json│    │ - Medical facts  │          │
│  │ - Plans         │  │ (doctor profiles)│    │ - Conditions     │          │
│  │ - Waiting times │  │                  │    │ - Treatments     │          │
│  └─────────────────┘  └──────────────────┘    └──────────────────┘          │
│                                                                             │
│            ┌──────────────────────────────────────────────┐                 │
│            │  All responses flow back to Concierge        │                 │
│            │  Synthesized into unified answer             │                 │
│            └────────────────────┬─────────────────────────┘                 │
│                                 │                                           │
│                                 ↓                                           │
│                    ┌────────────────────────────┐                           │
│                    │   User receives complete   │                           │
│                    │   answer with sources      │                           │
│                    └────────────────────────────┘                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Example

**Query**: "Are there psychiatrists in Boston, MA and does my plan cover mental health?"

```
1. Concierge receives query
   ├─→ Policy Agent queries PDF for "mental health coverage"
   │   └─ Returns: "Plan covers 80% inpatient, 50% outpatient, $2000 deductible"
   │
   ├─→ Provider Agent searches MCP for "psychiatrists in Boston, MA"
   │   └─ Returns: Table of 5 psychiatrists with credentials and affiliations
   │
   └─→ Research Agent searches Google for "mental health treatment options"
       └─ Returns: Overview of available treatments with citations

2. Concierge synthesizes all three responses
   └─ Final answer: "Based on your plan and local providers..."
```

---

## How the System Works in Detail

### Agent Specialization & Data Sources

Each agent is optimized for a specific task:

**Policy Agent** (`a2a_policy_agent.py`)
- **Model**: Claude Haiku 4.5 (cost-effective, fast)
- **Data**: Insurance policy PDF (loaded as base64-encoded document)
- **Task**: Answer questions about coverage, deductibles, waiting periods, network status
- **Example**: "Does my plan cover mental health therapy?" → "Yes, 50% coverage after $2000 deductible"

**Provider Agent** (`a2a_provider_agent.py`)
- **Model**: Claude Haiku 4.5 + LangChain + MCP
- **Data**: `data/doctors.json` (local healthcare provider database via MCP server)
- **Task**: Search for doctors by location, specialty, credentials
- **Example**: "Find cardiologists in Boston" → Returns table of 10 cardiologists with ratings, affiliations, contact info

**Research Agent** (`a2a_research_agent.py`)
- **Model**: Gemini 3.1 Flash Lite (real-time search capability)
- **Data**: Google Search (live medical information)
- **Task**: Provide medical information about conditions, treatments, symptoms
- **Example**: "What is diabetes?" → Comprehensive overview with treatment options

**Concierge Agent** (`a2a_healthcare_agent.py`)
- **Model**: Gemini 3.1 Flash Lite with BeeAI RequirementAgent (orchestration framework)
- **Data**: Access to all three agents via HandoffTool
- **Task**: Route queries, enforce constraints, synthesize answers with source attribution
- **Example**: "Find cardiologists that my insurance covers" → Calls Policy + Provider agents, synthesizes results

### Technology Stack Explained

| Component | Technology | Why This Choice |
|-----------|-----------|-----------------|
| **Agent Framework** | Google A2A (Agentic AI for Access) | Built for multi-agent systems with HTTP-based service architecture |
| **Orchestration** | BeeAI Framework + RequirementAgent | Enforces constraints (e.g., must call Policy Agent), handles parallel tool calls |
| **LLM Communication** | Model Context Protocol (MCP) | Clean, standardized way for agents to access external tools (provider database) |
| **PDF Processing** | Claude's Document API | Base64-encoded PDFs passed directly to Claude for context (no external parsing needed) |
| **Observability** | Arize Phoenix + OpenInference | Traces all LLM calls and agent decisions for debugging and optimization |

---

## Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Healthcare Concierge** | Gemini 2.5 + BeeAI | Routes queries, orchestrates agents via HandoffTool |
| **Policy Agent** | Claude Haiku 4.5 + RAG | Insurance coverage from PDF documents |
| **Provider Agent** | Claude Haiku 4.5 + MCP | Healthcare provider search via Model Context Protocol |
| **Research Agent** | Gemini 2.5 + Google Search | Real-time health information with citations |
| **MCP Server** | Model Context Protocol | Exposes `list_doctors()` tool; queries `data/doctors.json` |

**Architecture**: Multi-agent hub-and-spoke with Concierge orchestrating specialized agents

---

## Services & Ports

When running `python start_healthcare_system.py`:

| Service | Port | Purpose |
|---------|------|---------|
| Policy Agent | 9999 | Insurance policy queries |
| Provider Agent | 9997 | Healthcare provider searches |
| Research Agent | 9996 | Health research and information |
| Healthcare Concierge | 9001 | Main orchestrator & API |
| MCP Server | stdio | Provider database (internal) |

---

## Example Queries

Try these in the prompt in test_client.py and run:

- **"What does my insurance cover?"** → Policy Agent
- **"Find cardiologists near Boston, MA"** → Provider Agent  
- **"What are the symptoms of diabetes?"** → Research Agent
- **"Are there specialists near me that cover [condition]?"** → All three agents

---
## Project Status

- ✅ Multi-agent orchestration working
- ✅ MCP integration for provider search
- ✅ Phoenix observability instrumentation (optional)

---

## Author

**Anurag Dogra**
anuragdogra2192@gmail.com

---
## Update
The updated version with 6 agents, openclaw compatibility and a special frontend is PRIVATE.
For the current demo, contact the author. 
## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

### Attribution & Usage

If you use this code in your project, please:

1. **Include a copy of the LICENSE file** in your project
2. **Add attribution** to your README or documentation:
   ```
   Based on the Healthcare Concierge Multi-Agent System 
   Licensed under MIT License - Copyright (c) 2026 Anurag Dogra
   ```
3. **Retain copyright notices** in any modified versions

The MIT License is permissive and allows commercial use, modification, and distribution — just include the license file and attribution.

---

## Quick Links

- **Anthropic Claude API**: https://console.anthropic.com/
- **Google Gemini API**: https://ai.google.dev/
- **Model Context Protocol**: https://modelcontextprotocol.io/
- **Google A2A Framework**: https://github.com/google-ai-dev-kit/agents-sdk
