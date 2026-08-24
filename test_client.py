import asyncio
from beeai_framework.adapters.a2a.agents import A2AAgent
from beeai_framework.memory import UnconstrainedMemory

async def main():
    # Point the A2A client to your running orchestrator server
    orchestrator_url = "http://localhost:9001"
    
    print(f"Connecting to Healthcare Orchestrator at {orchestrator_url}...")
    client_agent = A2AAgent(url=orchestrator_url, memory=UnconstrainedMemory())
    
    # Verify connection and fetch AgentCard
    await client_agent.check_agent_exists()
    print(f"✓ Connected successfully to: {client_agent.name}\n")

    # Define a test prompt that requires coordination across your sub-agents
    prompt = "I live in Boston, MA. What are the standard treatment options for managing generalized anxiety disorder, does my policy cover mental health counseling services, and can you find any psychiatrists near me?"
    print(f"User Prompt: {prompt}\n")
    print("Waiting for multi-agent response (checking policy, research, and provider agents)...")

    # Run the agent pipeline
    response = await client_agent.run(prompt)
    
    print("\n--- Orchestrator Response ---")
    print(response.last_message.text)

if __name__ == "__main__":
    asyncio.run(main())