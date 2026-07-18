from typing import Callable, Literal, Optional
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage
from agent.app.core.assistant.assistant import AssistantBase
from agent.app.core.graph.graph_state import GraphState
from datetime import date
import time
from langchain_core.messages import SystemMessage

# agent_node_factory.py — add these two lines at the very top, right after the imports
print(f"[DEBUG] agent_node_factory.py LOADED FROM: {__file__}")
MAX_TOOL_ITERATIONS = 4


def make_agent_node(
    name: str,
    assistant: AssistantBase,
    tool_map: dict,
    state_key: Optional[str] = None,
    merge: Optional[Callable[[list], object]] = None,
):
    """
    merge: combines artifacts collected across possibly multiple tool calls
    in this agent's loop into the final shape state_key expects. Defaults to
    flattening all artifact lists into one list — override for single-object
    state keys like astronomy_media.
    """

    def node(state: GraphState) -> Command[Literal["supervisor"]]:
        start_time = time.time()
        print(f"[TIMING {name}] started at {start_time:.3f}")
        today_str = date.today().isoformat()
        local_messages = [
            SystemMessage(
                content=f"Today's date is {today_str}. Use this as 'today' for any relative date calculations like 'this week' or 'next 7 days'."
            ),
            HumanMessage(content=state.user_query),
        ]
        collected_artifacts = []

        for _ in range(MAX_TOOL_ITERATIONS):
            result = assistant({"messages": local_messages})
            ai_message = result["messages"][0]
            local_messages.append(ai_message)

            tool_calls = getattr(ai_message, "tool_calls", None)
            print(f"[DEBUG {name}] ai_message.tool_calls: {tool_calls}")  # <-- add this
            if not tool_calls:
                break

            for call in tool_calls:
                tool_fn = tool_map.get(call["name"])
                if tool_fn is None:
                    continue  # unknown tool requested — skip rather than crash the node

                try:
                    # Passing the full call dict (not call["args"]) is what makes
                    # content_and_artifact tools return a proper ToolMessage with
                    # both .content and .artifact split out.
                    tool_message = tool_fn.invoke(call)
                except Exception as exc:
                    from langchain_core.messages import ToolMessage

                    tool_message = ToolMessage(
                        content=f"Tool '{call['name']}' failed: {exc}",
                        tool_call_id=call["id"],
                    )
                print(
                    f"[DEBUG {name}] tool_message.content: {tool_message.content[:200]}, artifact: {getattr(tool_message, 'artifact', 'NO ARTIFACT ATTR')}"
                )  # <-- add this  # <-- add this

                local_messages.append(tool_message)
                artifact = getattr(tool_message, "artifact", None)
                if artifact:
                    collected_artifacts.append(artifact)

        update = {"messages": [local_messages[-1]], "completed_agents": [name]}
        if state_key is not None:
            if merge:
                update[state_key] = merge(collected_artifacts)
            else:
                flat = [item for artifact in collected_artifacts for item in artifact]
                update[state_key] = flat

        print(
            f"[TIMING {name}] finished at {time.time():.3f} (took {time.time()-start_time:.2f}s)"
        )
        return Command(goto="supervisor", update=update)

    return node
