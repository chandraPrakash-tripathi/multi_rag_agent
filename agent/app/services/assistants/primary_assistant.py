# most important assistant in the project because it acts as the router, coordinator, and entry point for all user interactions.
# Unlike the specialized assistants, it doesn't perform bookings itself—it decides who should handle the request.
# defines the main customer support assistant that receives every user query first.
# Its responsibilities are to answer general questions, search flights and company policies using search_flights() and lookup_policy(),
#  perform web searches through DuckDuckGo if needed, and determine whether a request should be delegated to a specialized assistant.
# Instead of directly booking hotels, cars, flights, or excursions,
# it transfers control by invoking one of the delegation tools (ToFlightBookingAssistant, ToBookCarRental, ToHotelBookingAssistant, or ToBookExcursion),
#  which causes LangGraph to route execution to the appropriate specialized assistant.
# This makes the primary assistant the orchestrator of the entire multi-agent system—it understands user intent, decides the next step,
# and coordinates the workflow while leaving domain-specific operations to the specialized assistants.
#                     User
#                       │
#                       ▼
#             Primary Assistant
#          (Router / Orchestrator)
#                       │
#      ┌────────────────┼──────────────────┐
#      ▼                ▼                  ▼
#  Flight          Hotel Assistant    Car Assistant
#  Assistant
#      │                │                  │
#      ▼                ▼                  ▼
#  Flight Tools    Hotel Tools       Car Tools

#                 Excursion Assistant
#                         │
#                         ▼
#                  Excursion Tools

# DuckDuckGoSearchResults tool gives the Primary Assistant access to the public internet. Without it, the assistant can only answer using:

# The LLM's knowledge
# Your Qdrant vector database
# The SQLite database

# With DuckDuckGo, it can search for live information that isn't stored locally.
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from agent.app.services.tools import (
    search_flights,
    lookup_policy,
)
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchResults
from agent.app.services.assistants.assistant_base import Assistant, llm
from agent.app.core.state import State
from pydantic import BaseModel, Field


# Define task delegation tools
class ToFlightBookingAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle flight updates and cancellations."""

    request: str = Field(
        description="Any necessary follow-up questions the update flight assistant should clarify before proceeding."
    )


class ToBookCarRental(BaseModel):
    """Transfers work to a specialized assistant to handle car rental bookings."""

    location: str = Field(
        description="The location where the user wants to rent a car."
    )
    start_date: str = Field(description="The start date of the car rental.")
    end_date: str = Field(description="The end date of the car rental.")
    request: str = Field(
        description="Any additional information or requests from the user regarding the car rental."
    )


class ToHotelBookingAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle hotel bookings."""

    location: str = Field(
        description="The location where the user wants to book a hotel."
    )
    checkin_date: str = Field(description="The check-in date for the hotel.")
    checkout_date: str = Field(description="The check-out date for the hotel.")
    request: str = Field(
        description="Any additional information or requests from the user regarding the hotel booking."
    )


class ToBookExcursion(BaseModel):
    """Transfers work to a specialized assistant to handle trip recommendation and other excursion bookings."""

    location: str = Field(
        description="The location where the user wants to book a recommended trip."
    )
    request: str = Field(
        description="Any additional information or requests from the user regarding the trip recommendation."
    )


# Primary assistant prompt
primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful customer support assistant for Swiss Airlines. "
            "Your primary role is to search for flight information and company policies to answer customer queries. "
            "If a customer requests to update or cancel a flight, book a car rental, book a hotel, or get trip recommendations, "
            "delegate the task to the appropriate specialized assistant by invoking the corresponding tool. You are not able to make these types of changes yourself. "
            "Only the specialized assistants are given permission to do this for the user. "
            "The user is not aware of the different specialized assistants, so do not mention them; just quietly delegate through function calls. "
            "Provide detailed information to the customer, and always double-check the database before concluding that information is unavailable. "
            "When searching, be persistent. Expand your query bounds if the first search returns no results. "
            "If a search comes up empty, expand your search before giving up."
            "\n\nFor any question outside flights, policies, and bookings - such as weather, current events, "
            "general facts, or anything requiring real-time information you don't already have - "
            "always call the DuckDuckGo search tool to find an answer rather than saying you don't have access "
            "to it or asking the user to check elsewhere. Only decline to answer if the search tool itself "
            "returns no useful results after you've tried."
            "\n\nCurrent user flight information:\n<Flights>\n{user_info}\n</Flights>"
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

# Primary assistant tools
primary_assistant_tools = [
    DuckDuckGoSearchResults(max_results=10),
    search_flights,
    lookup_policy,
    ToFlightBookingAssistant,
    ToBookCarRental,
    ToHotelBookingAssistant,
    ToBookExcursion,
]

# Create the primary assistant runnable
primary_assistant_runnable = primary_assistant_prompt | llm.bind_tools(
    primary_assistant_tools
)

# Instantiate the primary assistant
primary_assistant = Assistant(primary_assistant_runnable)
