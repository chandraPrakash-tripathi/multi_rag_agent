# scripts/generate_graph_viz.py
from langgraph.checkpoint.sqlite import SqliteSaver
from agent.app.core.graph.graph_builder import build_graph

with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    graph = build_graph(checkpointer)

    png_bytes = graph.get_graph().draw_mermaid_png()

    with open("graph.png", "wb") as f:
        f.write(png_bytes)

print("Saved graph.png")
