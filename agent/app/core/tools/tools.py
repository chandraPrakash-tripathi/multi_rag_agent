import json
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from core.repository import DataRepository

repo = DataRepository()


# 1. Near-Earth Object Tools (NASA NeoWs)
@tool
def get_hazardous_asteroids(
    start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 5
) -> str:
    events = repo.get_events(
        dataset_id="neows",
        start_date=start_date,
        end_date=end_date,
        keyword="hazardous",
        limit=limit,
    )
    if not events:
        return "No hazardous asteroid data found for the specified timeframe."
    return "\n".join(
        [
            f"[{e['timestamp']}] {e['title']}\nDESCRIPTION: {e['description']}\n"
            for e in events
        ]
    )


@tool
def get_asteroid_closest_approaches(limit: int = 5) -> str:
    events = repo.get_events(dataset_id="neows", limit=limit)
    if not events:
        return "No asteroid approach data currently available."
    return "\n".join([f"[{e['timestamp']}] {e['title']}" for e in events])


# 2. Space Weather Tools (NASA DONKI)
@tool
def get_space_weather_events(event_type: Optional[str] = None, limit: int = 5) -> str:
    events = repo.get_events(dataset_id="donki", keyword=event_type, limit=limit)
    if not events:
        return f"No space weather events found matching '{event_type}'."
    return "\n".join(
        [
            f"[{e['timestamp']}] {e['title']}\nDETAILS: {e['description']}\n"
            for e in events
        ]
    )


# 3. Earth Natural Events Tools (NASA EONET)
@tool
def get_active_earth_events(category: Optional[str] = None, limit: int = 5) -> str:
    events = repo.get_events(dataset_id="eonet", keyword=category, limit=limit)
    if not events:
        return f"No Earth events found for category: '{category}'."
    return "\n".join([f"[{e['timestamp']}] {e['title']}\n" for e in events])


# 4. Astronomy Media Tools (NASA APOD)
@tool
def get_apod_by_date(date: Optional[str] = None) -> str:
    # If a specific date is requested, restrict both start and end to that single day
    events = repo.get_events(dataset_id="apod", start_date=date, end_date=date, limit=1)
    if not events:
        return "No Astronomy Picture of the Day available for that date."
    e = events[0]
    return f"[{e['timestamp']}] TITLE: {e['title']}\nEXPLANATION: {e['description']}"


# 5. Space Knowledge Tools (RAG / Qdrant)
@tool
def search_scientific_knowledge(query: str, limit: int = 3) -> str:
    results = repo.search_knowledge(query_text=query, limit=limit)
    if not results:
        return "No matching scientific documents found in the vector database."

    formatted = ["--- RETRIEVED SCIENTIFIC KNOWLEDGE ---"]
    for r in results:
        formatted.append(
            f"TITLE: {r['title']} (Source: {r['dataset']} | Relevance: {r['score']:.3f})"
        )
        formatted.append(f"CONTENT:\n{r['content']}")
        formatted.append("-" * 40)

    return "\n".join(formatted)


# 6. Space News Tools (Spaceflight News API)
@tool
def get_latest_space_news(limit: int = 5) -> str:
    events = repo.get_events(dataset_id="spaceflight_news", limit=limit)
    if not events:
        return "No recent space news found."
    return "\n".join([f"[{e['timestamp']}] {e['title']}" for e in events])


@tool
def search_news_archives(query: str, limit: int = 3) -> str:
    # Hybrid search: semantic query but strictly locked to the 'spaceflight_news' dataset
    results = repo.search_knowledge(
        query_text=query, dataset_filter="spaceflight_news", limit=limit
    )
    if not results:
        return "No matching news articles found."

    formatted = ["--- ARCHIVED NEWS ---"]
    for r in results:
        formatted.append(f"TITLE: {r['title']}")
        formatted.append(f"CONTENT:\n{r['content']}")
        formatted.append("-" * 40)
    return "\n".join(formatted)


# 7. Analytics Tools (Pure Python Math & Vis)
@tool
def calculate_trend_statistics(data_array: List[float]) -> str:
    if not data_array:
        return "Error: Empty data array provided."

    avg_val = sum(data_array) / len(data_array)
    max_val = max(data_array)
    min_val = min(data_array)

    return f"Count: {len(data_array)} | Average: {avg_val:.2f} | Max: {max_val:.2f} | Min: {min_val:.2f}"


@tool
def generate_chart_config(title: str, labels: List[str], values: List[float]) -> str:
    config = {
        "type": "bar",  # Defaulting to bar chart for simplicity
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "label": title,
                    "data": values,
                    "backgroundColor": "rgba(54, 162, 235, 0.5)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 1,
                }
            ],
        },
        "options": {
            "responsive": True,
            "plugins": {"title": {"display": True, "text": title}},
        },
    }
    return json.dumps(config, indent=2)


# Master Tool Registries
NEO_TOOLS = [get_hazardous_asteroids, get_asteroid_closest_approaches]
WEATHER_TOOLS = [get_space_weather_events]
EARTH_TOOLS = [get_active_earth_events]
MEDIA_TOOLS = [get_apod_by_date]
KNOWLEDGE_TOOLS = [search_scientific_knowledge]
NEWS_TOOLS = [get_latest_space_news, search_news_archives]
ANALYTICS_TOOLS = [calculate_trend_statistics, generate_chart_config]

# Note: The Report Generation Agent receives NO tools, as it only synthesizes GraphState.
