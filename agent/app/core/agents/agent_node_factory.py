from typing import Callable, Literal, Optional
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage
from assistant.assistant import AssistantBase
from graph.graph_state import GraphState

MAX_TOOL_ITERATIONS = (
    4  # bounded ReAct loop — prevents a runaway tool-call chain in one agent
)


def make_agent_node(
    name: str,
    assistant: AssistantBase,
    tool_map: dict,
    state_key: Optional[str] = None,
    extractor: Optional[Callable[[list], object]] = None,
):
    """
    Wraps an AssistantBase + its tools into a bounded ReAct-style LangGraph node.
    Always returns control to the supervisor when done — this is what makes
    mid-run replanning possible, since the supervisor re-evaluates after every
    single agent completes, not just once at the start.
    """

    def node(state: GraphState) -> Command[Literal["supervisor"]]:
        local_messages = [HumanMessage(content=state.user_query)]
        collected_outputs = []

        for _ in range(MAX_TOOL_ITERATIONS):
            result = assistant({"messages": local_messages})
            ai_message = result["messages"][0]
            local_messages.append(ai_message)

            tool_calls = getattr(ai_message, "tool_calls", None)
            if not tool_calls:
                break

            for call in tool_calls:
                tool_fn = tool_map.get(call["name"])
                if tool_fn is None:
                    output = f"Unknown tool requested: {call['name']}"
                else:
                    try:
                        output = tool_fn.invoke(call["args"])
                    except Exception as exc:
                        output = f"Tool '{call['name']}' failed: {exc}"

                collected_outputs.append(output)
                local_messages.append(
                    ToolMessage(content=str(output), tool_call_id=call["id"])
                )

        update = {"messages": [local_messages[-1]], "completed_agents": [name]}
        if state_key is not None:
            update[state_key] = (
                extractor(collected_outputs) if extractor else collected_outputs
            )

        return Command(goto="supervisor", update=update)

    return node
