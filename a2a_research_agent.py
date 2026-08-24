from dotenv import load_dotenv
import os
import uvicorn
import logging
import warnings

# Phoenix Observability Instrumentation
try:
    from phoenix.otel import register

    # Initialize Phoenix using the correct module
    register(project_name="health-research-agent")
    
    # Instrument modern Google GenAI SDK
    try:
        from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
        GoogleGenAIInstrumentor().instrument()
        print("✓ Phoenix + Google GenAI instrumentation enabled")
    except ImportError:
        print("⚠ Google GenAI instrumentation not available")

except ImportError:
    print("⚠ Phoenix not installed - observability disabled")
except Exception as e:
    print(f"⚠ Phoenix setup error: {e}")
    
logging.disable(level=logging.WARNING)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# Load from .env.local with override
load_dotenv(".env.local", override=True)

from google import genai #Really important
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from a2a.utils import new_agent_text_message


class ResearchAgentExecutor(AgentExecutor):
    """Health research agent using Gemini 3.1 Flash Lite for medical information"""

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        # Initialize modern GenAI client
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-3.1-flash-lite"

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        prompt = context.get_user_input()

        system_prompt = """You are a healthcare research expert with knowledge of:
- Medical conditions, symptoms, and diagnoses
- Treatments, medications, and procedures
- Preventive care and wellness
- Medical terminology and health concepts

Provide accurate, well-researched information. Cite sources when available.
Encourage users to consult healthcare professionals for serious concerns."""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=f"{system_prompt}\n\nUser Query: {prompt}"
            )
            result = response.text
        except Exception as e:
            result = f"Error: {str(e)}"

        await event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass


def main() -> None:
    print("Running Health Research Agent (Gemini 3.1 Flash Lite)")
    load_dotenv(".env.local", override=True)

    HOST = os.environ.get("AGENT_HOST", "localhost")
    PORT = int(os.environ.get("RESEARCH_AGENT_PORT", "9996"))

    skill = AgentSkill(
        id="health_research",
        name="Health Research",
        description="Provides detailed healthcare information about conditions, treatments, and procedures.",
        tags=["health", "research", "medical", "conditions", "treatment"],
        examples=[
            "What are the symptoms of diabetes?",
            "How is hypertension treated?",
            "Tell me about heart disease prevention",
        ],
    )

    agent_card = AgentCard(
        name="HealthResearchAgent",
        description="Provides healthcare information about symptoms, conditions, treatments, and procedures using Gemini 3.1 Flash Lite.",
        url=f"http://{HOST}:{PORT}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=ResearchAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host=HOST, port=PORT)


if __name__ == "__main__":
    main()