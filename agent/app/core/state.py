# The state.py file defines the shared state (memory) that is passed between every node in the LangGraph workflow.
# Instead of passing multiple variables individually, LangGraph passes a single State object (implemented using TypedDict) containing all the information that agents need.
# The messages field stores the complete conversation history and uses the built-in add_messages reducer to automatically append new messages instead of overwriting old ones.
# The user_info field holds user-specific details that any agent can access.
# The dialog_state field maintains a stack of active assistants (such as "assistant", "book_hotel", or "update_flight"), and the custom update_dialog_stack reducer manages
# this stack by pushing a new agent when control is transferred, popping the current agent when it finishes ("pop"), or leaving it unchanged if None is returned.
#  This stack-based approach allows the graph to temporarily switch to a specialized agent and then seamlessly resume the previous conversation context,
#  making state.py the central source of truth for managing conversation history, user context, and workflow state throughout the entire LangGraph execution.

##dialog_state
# dialog_state = ["assistant"]
# Top
#  │
#  ▼
# +------------+
# | assistant  |
# +------------+
# User: "Book me a hotel"

# The router transfers control to the hotel agent.

# return {"dialog_state": "book_hotel"}

# The reducer executes:

# update_dialog_stack(
#     ["assistant"],
#     "book_hotel"
# )

# Result:

# dialog_state = ["assistant", "book_hotel"]
# Top
#  │
#  ▼
# +---------------+
# | book_hotel    |  ← Active agent
# +---------------+
# | assistant     |
# +---------------+

from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages


def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """Push or pop the dialog state stack."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str
    dialog_state: Annotated[
        list[
            Literal[
                "assistant",
                "update_flight",
                "book_car_rental",
                "book_hotel",
                "book_excursion",
            ]
        ],
        update_dialog_stack,
    ]
