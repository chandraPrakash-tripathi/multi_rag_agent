from typing import Literal
from langgraph.types import Command
from agent.app.core.graph.graph_state import GraphState

MAX_AUDIT_RETRIES = 2  # hard ceiling, independent of what the errors say — same
# safety pattern as supervisor.MAX_CYCLES, so a persistent
# error can never bounce the graph forever


def auditor_node(state: GraphState) -> Command[Literal["supervisor", "report_agent"]]:
    """
    Hard gate between the supervisor declaring DONE and report_agent running.
    If real errors were recorded during data gathering, send control back to
    the supervisor for a retry instead of letting report_agent silently
    synthesize a report on incomplete/broken data. Bounded by MAX_AUDIT_RETRIES
    so a genuinely unfixable error (e.g. a dead API) can't loop forever —
    it eventually proceeds to report_agent anyway, with the errors intact so
    the report can be honest about them.
    """

    if not state.errors:
        return Command(
            goto="report_agent",
            update={
                "execution_logs": [
                    "Auditor: no errors recorded, proceeding to synthesis."
                ]
            },
        )

    if state.audit_cycle_count >= MAX_AUDIT_RETRIES:
        return Command(
            goto="report_agent",
            update={
                "execution_logs": [
                    f"Auditor: {len(state.errors)} error(s) present but max retries "
                    f"({MAX_AUDIT_RETRIES}) reached — proceeding to synthesis with errors noted."
                ]
            },
        )

    return Command(
        goto="supervisor",
        update={
            "audit_cycle_count": state.audit_cycle_count + 1,
            "execution_logs": [
                f"Auditor: {len(state.errors)} error(s) found — cycle {state.audit_cycle_count}, "
                f"sending back to supervisor for retry."
            ],
        },
    )
