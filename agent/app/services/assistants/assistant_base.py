# defines the foundation shared by all specialized assistants in the system.
#  It initializes a single shared ChatOpenAI LLM instance that every assistant reuses, avoiding repeated model creation.
#  The Assistant class acts as a wrapper around a LangChain Runnable, making it callable by LangGraph.
# When invoked, it receives the current State and optional RunnableConfig,
# executes the underlying runnable (self.runnable.invoke()), and checks whether the LLM produced a meaningful response or tool call.
# If the model returns an empty or invalid output, it appends the message "Respond with a real output." to the conversation history
#  and retries until a valid response is generated, making the assistant more robust against empty LLM responses.
#  Finally, it returns the result in the format expected by LangGraph ({"messages": result}).
# The file also defines the CompleteOrEscalate Pydantic model,
# which serves as a structured tool allowing a specialized assistant to indicate that its task is complete or that control should be escalated back to the primary assistant,
# along with a reason for the handoff.
# it is not the application's entry point, it is the base execution layer that all assistants rely on to run consistently and communicate with the graph.
from typing import Optional

from langchain_core.runnables import Runnable, RunnableConfig
from agent.app.core.state import State
from pydantic import BaseModel
from agent.app.core.settings import get_settings
from langchain_ollama import ChatOllama

settings = get_settings()

# Initialize the language model (shared among assistants)
# Switched from cloud providers (OpenAI, Groq, Gemini) to a local Ollama model.
# Groq's llama-3.3-70b-versatile had a reproducible bug wrapping tool calls in
# malformed "<function=name{...}></function>" tags for certain tool schemas,
# which Groq's own API then rejected — not fixable via retries or temperature.
# qwen2.5:7b via Ollama has solid native tool-calling support and runs fully
# offline with no API key or rate limits.
llm = ChatOllama(
    model="qwen2.5:3b",
    temperature=0,
    num_ctx=4096,
)


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: Optional[RunnableConfig] = None):
        while True:
            result = self.runnable.invoke(state, config)

            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}


# Define the CompleteOrEscalate tool
class CompleteOrEscalate(BaseModel):
    """A tool to mark the current task as completed or to escalate control to the main assistant."""

    cancel: bool = True
    reason: str
