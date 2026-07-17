import os
import logging
from typing import List, Optional, Callable

from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.tools import BaseTool

from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

VALID_ENVIRONMENTS = {"local", "prod"}

# Groq deprecated llama-3.3-70b-versatile and llama-3.1-8b-instant (announced
# 2026-06-17). gpt-oss-120b is the closest tool-calling replacement; swap to
# gpt-oss-20b if you need to stay strictly free-tier / lower latency.
DEFAULT_PROD_MODEL = "openai/gpt-oss-120b"
DEFAULT_LOCAL_MODEL = "qwen2.5:7b"


class AssistantBase:
    """
    A unified LLM wrapper for LangGraph Agents.
    Handles environment switching, system prompt injection, tool binding,
    and failure isolation so a single node's LLM error doesn't crash the graph.
    """

    def __init__(
        self,
        system_prompt: str,
        tools: Optional[List[BaseTool]] = None,
        temperature: float = 0.1,
        context_builder: Optional[Callable[[dict], str]] = None,
    ):
        """
        Args:
            system_prompt: Static instructions for this agent.
            tools: BaseTool instances (from @tool-decorated functions) to bind.
            temperature: Sampling temperature. Keep low (~0.1) for tool-calling
                agents; raise it for prose-generation agents like synthesis/report.
            context_builder: Optional function that takes the full GraphState
                and returns a string to inject into the prompt after the system
                message. Use this to pull domain-layer data (Layer 3), retrieved
                documents (Layer 4), or analytics (Layer 5) into context for
                agents that need more than raw message history.
        """
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.temperature = temperature
        self.context_builder = context_builder

        self.environment = os.getenv("ENVIRONMENT", "local").lower()
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError(
                f"Invalid ENVIRONMENT={self.environment!r}. "
                f"Expected one of {VALID_ENVIRONMENTS}."
            )

        self.llm = self._initialize_llm()

        if self.tools:
            self.llm = self.llm.bind_tools(self.tools)
            logger.info(
                "Bound %d tool(s) to assistant: %s",
                len(self.tools),
                [t.name for t in self.tools],
            )
        else:
            logger.info("Assistant initialized with no tools (prompt-only agent).")

    def _initialize_llm(self):
        """Dynamically switch between Local (Ollama) and Production (Groq)."""
        if self.environment == "prod":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise RuntimeError("ENVIRONMENT=prod but GROQ_API_KEY is not set.")
            model_name = os.getenv("PROD_MODEL", DEFAULT_PROD_MODEL)
            return ChatGroq(
                temperature=self.temperature,
                model_name=model_name,
                api_key=api_key,
            )
        else:
            model_name = os.getenv("LOCAL_MODEL", DEFAULT_LOCAL_MODEL)
            return ChatOllama(model=model_name, temperature=self.temperature)

    def __call__(self, state: dict) -> dict:
        """
        The executable method LangGraph calls when it routes to this agent node.
        Never raises: LLM/provider failures are caught and surfaced through
        GraphState's `errors` layer instead of crashing the graph run.
        """
        messages = state.get("messages", [])

        prompt = [SystemMessage(content=self.system_prompt)]

        if self.context_builder is not None:
            try:
                extra_context = self.context_builder(state)
                if extra_context:
                    prompt.append(SystemMessage(content=extra_context))
            except Exception as exc:
                logger.warning("context_builder failed, continuing without it: %s", exc)

        prompt += messages

        try:
            response = self.llm.invoke(prompt)
        except Exception as exc:
            logger.error(
                "LLM invocation failed in %s: %s", self.__class__.__name__, exc
            )
            error_message = AIMessage(
                content=(
                    "I hit an error while processing this request and couldn't "
                    "complete it. The issue has been logged."
                )
            )
            return {
                "messages": [error_message],
                "errors": [
                    {
                        "node": self.__class__.__name__,
                        "error": str(exc),
                        "environment": self.environment,
                    }
                ],
            }

        return {"messages": [response]}
