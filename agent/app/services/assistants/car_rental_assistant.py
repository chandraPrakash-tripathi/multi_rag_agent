# defines a specialized AI assistant dedicated to car rental tasks.
# It creates a detailed system prompt that instructs the LLM to handle only car rental-related requests, search persistently for suitable rentals,
#  confirm booking details before completing a reservation, and hand control back to the primary assistant using CompleteOrEscalate whenever the request
# is outside its scope or the conversation needs to be redirected.
#  The file also categorizes tools into safe tools (read-only search operations) and
#  sensitive tools (book, update, and cancel operations that modify the database), binds these tools to the shared LLM using llm.bind_tools(),
# and combines the prompt and tool-enabled LLM into a runnable pipeline.
# Finally, this runnable is wrapped by the base Assistant class,
#  creating a reusable car_rental_assistant that the LangGraph workflow can invoke whenever the primary assistant delegates a car rental-related task.
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from agent.app.services.tools import (
    search_car_rentals,
    book_car_rental,
    update_car_rental,
    cancel_car_rental,
)
from agent.app.services.assistants.assistant_base import (
    Assistant,
    CompleteOrEscalate,
    llm,
)

# Car rental assistant prompt
car_rental_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a specialized assistant for handling car rental bookings. "
            "The primary assistant delegates work to you whenever the user needs help booking a car rental. "
            "Search for available car rentals based on the user's preferences and confirm the booking details with the customer. "
            "When searching, be persistent. Expand your query bounds if the first search returns no results. "
            "If you need more information or the customer changes their mind, escalate the task back to the main assistant. "
            "Remember that a booking isn't completed until after the relevant tool has successfully been used."
            "\nCurrent time: {time}."
            "\n\nIf the user needs help, and none of your tools are appropriate for it, then "
            '"CompleteOrEscalate" the dialog to the host assistant. Do not waste the user\'s time. Do not make up invalid tools or functions.'
            "\n\nSome examples for which you should CompleteOrEscalate:\n"
            " - 'what's the weather like this time of year?'\n"
            " - 'What flights are available?'\n"
            " - 'nevermind I think I'll book separately'\n"
            " - 'Oh wait I haven't booked my flight yet I'll do that first'\n"
            " - 'Car rental booking confirmed'",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

# Car rental tools
book_car_rental_safe_tools = [search_car_rentals]
book_car_rental_sensitive_tools = [
    book_car_rental,
    update_car_rental,
    cancel_car_rental,
]
book_car_rental_tools = book_car_rental_safe_tools + book_car_rental_sensitive_tools

# Create the car rental assistant runnable
book_car_rental_runnable = car_rental_prompt | llm.bind_tools(
    book_car_rental_tools + [CompleteOrEscalate]
)

# Instantiate the car rental assistant
car_rental_assistant = Assistant(book_car_rental_runnable)
