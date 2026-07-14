import os
from typing import List, Callable
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool

# Provider integrations
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq


class AssistantBase:
    """
    A unified LLM wrapper for LangGraph Agents.
    Handles environment switching, system prompt injection, and tool binding.
    """

    def __init__(self, system_prompt: str, tools: List[Callable] = None):
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.llm = self._initialize_llm()

        # If tools are provided, bind them to the LLM so it knows they exist
        if self.tools:
            self.llm = self.llm.bind_tools(self.tools)

    def _initialize_llm(self):
        """Dynamically switch between Local (Ollama) and Production (Groq)."""
        environment = os.getenv("ENVIRONMENT", "local").lower()

        if environment == "prod":
            # PRODUCTION: Groq running Llama 3.3 70B (Fast, Open Weights, Great for tools)
            # Requires GROQ_API_KEY in your .env file
            return ChatGroq(
                temperature=0.1,  # Low temperature is critical for reliable tool calling
                model_name="llama-3.3-70b-versatile",
                api_key=os.getenv("GROQ_API_KEY"),
            )
        else:
            # LOCAL: Ollama running Qwen 2.5 (100% Free, runs on your machine)
            # Make sure Ollama is running and you have pulled the model
            return ChatOllama(
                model=os.getenv("LOCAL_MODEL", "qwen2.5:7b"), temperature=0.1
            )

    def __call__(self, state: dict) -> dict:
        """
        The executable method that LangGraph will call when it routes to an agent node.
        """
        # 1. Grab the existing conversation history from the GraphState (Layer 1)
        messages = state.get("messages", [])

        # 2. Prepend the agent-specific system prompt to guide behavior
        prompt = [SystemMessage(content=self.system_prompt)] + messages

        # 3. Invoke the tool-bound LLM
        # The LLM will either return a standard AI message OR a ToolCall request
        response = self.llm.invoke(prompt)

        # 4. Return the new message to append to the GraphState
        return {"messages": [response]}
