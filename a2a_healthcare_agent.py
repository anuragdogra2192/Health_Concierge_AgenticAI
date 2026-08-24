# --- Compatibility Patch for beeai_framework with Modern Starlette ---
from starlette.applications import Starlette
from contextlib import asynccontextmanager

if not hasattr(Starlette, "add_event_handler"):
    def _add_event_handler(self, event_type: str, func):
        original_lifespan = self.router.lifespan_context
        
        if event_type == "startup":
            @asynccontextmanager
            async def new_lifespan(app):
                await func()
                async with original_lifespan(app):
                    yield
            self.router.lifespan_context = new_lifespan
        elif event_type == "shutdown":
            @asynccontextmanager
            async def new_lifespan(app):
                async with original_lifespan(app):
                    yield
                await func()
            self.router.lifespan_context = new_lifespan
            
    Starlette.add_event_handler = _add_event_handler
# -------------------------------------------------------------------

from dotenv import load_dotenv
import asyncio
import os

# Phoenix Observability Instrumentation
try:
    from phoenix.otel import register
    from openinference.instrumentation.beeai import BeeAIInstrumentor
    from openinference.instrumentation.langchain import LangChainInstrumentor

    # Initialize Phoenix using the correct module
    register(project_name="health-concierge-agent")

    # Instrument BeeAI natively for agentic traces, inputs, and outputs
    BeeAIInstrumentor().instrument()
    print("✓ Phoenix + BeeAI instrumentation enabled")

    # Instrument LangChain
    LangChainInstrumentor().instrument()

    # Instrument Google GenAI if available
    try:
        from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
        GoogleGenAIInstrumentor().instrument()
        print("✓ Phoenix + Google GenAI instrumentation enabled")
    except ImportError:
        print("✓ Phoenix instrumentation enabled (Google GenAI not available)")

except ImportError:
    print("⚠ Phoenix not installed - observability disabled")
except Exception as e:
    print(f"⚠ Phoenix setup error: {e}")

# Load from .env.local with override
load_dotenv(".env.local", override=True)

from beeai_framework.adapters.a2a.serve.server import A2AServer, A2AServerConfig
from beeai_framework.adapters.a2a.agents import A2AAgent
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.backend.chat import ChatModel
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.serve.utils import LRUMemoryManager
from beeai_framework.tools import Tool
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.tools.think import ThinkTool

def main():
    print(f"Running A2A Orchestrator Agent")
    load_dotenv(".env.local", override=True)

    # Ensure Gemini API key is present
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    host = os.environ.get("AGENT_HOST", "localhost")
    policy_agent_port = os.environ.get("POLICY_AGENT_PORT", "9999")
    research_agent_port = os.environ.get("RESEARCH_AGENT_PORT", "9996")
    provider_agent_port = os.environ.get("PROVIDER_AGENT_PORT", "9997")
    healthcare_agent_port = int(os.environ.get("HEALTHCARE_AGENT_PORT", "9001"))

    policy_agent = A2AAgent(
        url=f"http://{host}:{policy_agent_port}", memory=UnconstrainedMemory()
    )
    asyncio.run(policy_agent.check_agent_exists())
    print("\tℹ️", f"{policy_agent.name} initialized")

    research_agent = A2AAgent(
        url=f"http://{host}:{research_agent_port}", memory=UnconstrainedMemory()
    )
    asyncio.run(research_agent.check_agent_exists())
    print("\tℹ️", f"{research_agent.name} initialized")

    provider_agent = A2AAgent(
        url=f"http://{host}:{provider_agent_port}", memory=UnconstrainedMemory()
    )
    asyncio.run(provider_agent.check_agent_exists())
    print("\tℹ️", f"{provider_agent.name} initialized")

    # Set Gemini 3.1 Flash Lite using BeeAI's unified backend loader and enable parallel tool calls
    llm = ChatModel.from_name("gemini:gemini-3.1-flash-lite")
    llm.allow_parallel_tool_calls = True

    healthcare_agent = RequirementAgent(
        name="Healthcare Agent",
        description="A personal concierge for Healthcare Information, customized to your policy.",
        llm=llm,
        tools=[
            thinktool := ThinkTool(),
            policy_tool := HandoffTool(
                target=policy_agent,
                name=policy_agent.name,
                description=policy_agent.agent_card.description,
            ),
            research_tool := HandoffTool(
                target=research_agent,
                name=research_agent.name,
                description=research_agent.agent_card.description,
            ),
            provider_tool := HandoffTool(
                target=provider_agent,
                name=provider_agent.name,
                description=provider_agent.agent_card.description,
            ),
        ],
        requirements=[
            ConditionalRequirement(policy_tool, consecutive_allowed=False),
            ConditionalRequirement(thinktool, force_at_step=1, force_after=Tool, consecutive_allowed=False),
        ],
        role="Healthcare Concierge",
        instructions=(
            f"""You are a concierge for healthcare services. Your task is to handoff to one or more agents to answer questions and provide a detailed summary of their answers. Be sure that all of their questions are answered before responding.
            Use `{policy_agent.name}` to answer insurance-related questions.
            Use `{research_agent.name}` to research health conditions, symptoms, and treatments.
            Use `{provider_agent.name}` to find healthcare providers.

            IMPORTANT: When returning answers about providers, only output providers from `{provider_agent.name}` and only provide insurance information based on the results from `{policy_agent.name}`.

            In your output, put which agent gave you the information!"""
        ),
    )

    print("\tℹ️", f"{healthcare_agent.meta.name} initialized")

    # Register the agent with the A2A server and run the HTTP server
    A2AServer(
        config=A2AServerConfig(port=healthcare_agent_port, protocol="jsonrpc", host=host),
        memory_manager=LRUMemoryManager(maxsize=100),
    ).register(healthcare_agent, send_trajectory=True).serve()

if __name__ == "__main__":
    main()