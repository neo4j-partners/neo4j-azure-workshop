"""
Simple console-based agent runner.

Run with: uv run start-agent
"""

import asyncio

from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

from agent import AgentConfig, create_agent_client, create_agent_context
from util import get_env_file_path


async def main():
    """Run an interactive chat session with the agent."""
    # Load environment
    env_file = get_env_file_path()
    if env_file:
        load_dotenv(env_file)
        print(f"Loaded environment from: {env_file}")

    config = AgentConfig()
    print(f"Agent: {config.name}")
    print(f"Model: {config.model}")
    print(f"Project: {config.project_endpoint}")
    print("-" * 40)

    credential = AzureCliCredential()
    client = create_agent_client(config, credential)

    async with client:
        async with create_agent_context(client, config) as agent:
            print("Agent ready.\n")

            # Run sample query first
            sample_query = "Why is using Neo4j with Microsoft Foundry like PB & Jelly?"
            print(f"You: {sample_query}")
            print("Agent: ", end="", flush=True)
            async for chunk in agent.run_stream(sample_query):
                print(chunk.content, end="", flush=True)
            print("\n")

            print("Type 'quit' or 'exit' to stop.\n")

            while True:
                try:
                    user_input = input("You: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nGoodbye!")
                    break

                if not user_input:
                    continue

                if user_input.lower() in ("quit", "exit"):
                    print("Goodbye!")
                    break

                print("Agent: ", end="", flush=True)
                async for chunk in agent.run_stream(user_input):
                    print(chunk.content, end="", flush=True)
                print("\n")


def run():
    """Entry point for the start-agent script."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
