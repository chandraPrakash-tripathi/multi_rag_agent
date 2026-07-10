                                      USER
                                        │
                                        ▼
                          LangGraph Entry Point
                                        │
                                        ▼
                             Shared Graph State
         ┌──────────────────────────────────────────────────────┐
         │ State                                                │
         │ • messages                                            │
         │ • user_info                                            │
         │ • dialog_state (stack)                                 │
         └──────────────────────────────────────────────────────┘
                                        │
                                        ▼
                    fetch_user_flight_information()
                  (Loads logged-in user's bookings)
                                        │
                                        ▼
                     PRIMARY ASSISTANT (Router + Planner)
                                        │
      ┌─────────────────────────────────┼──────────────────────────────────────┐
      │                                 │                                      │
      ▼                                 ▼                                      ▼
General Question                 Company Policy                     Flight Search
      │                                 │                                      │
      ▼                                 ▼                                      ▼
DuckDuckGo Search                lookup_policy()                   search_flights()
(Live Web Search)                 (Qdrant FAQ)                     (Qdrant Flights)
      │                                 │                                      │
      └─────────────────────────────────┼──────────────────────────────────────┘
                                        │
                                        ▼
                     Does this require a specialized task?
                                        │
                    ┌───────────────────┴───────────────────┐
                    │                                       │
                   No                                      Yes
                    │                                       │
                    ▼                                       ▼
            Respond to User                    Delegation Tool Invoked
                                                        │
      ┌──────────────────────────────┬───────────────────────────────┬──────────────────────────────┐
      ▼                              ▼                               ▼                              ▼
ToFlightBookingAssistant     ToHotelBookingAssistant        ToBookCarRental             ToBookExcursion
      │                              │                               │                              │
      ▼                              ▼                               ▼                              ▼
Flight Assistant             Hotel Assistant               Car Assistant            Excursion Assistant
      │                              │                               │                              │
      ▼                              ▼                               ▼                              ▼
Flight Tools                 Hotel Tools                  Car Tools                 Excursion Tools
      │                              │                               │                              │
      │                              │                               │                              │
search_flights()             search_hotels()             search_car_rentals()      search_trip_recommendations()
update_ticket()              book_hotel()                book_car_rental()          book_excursion()
cancel_ticket()              update_hotel()              update_car_rental()        update_excursion()
                              cancel_hotel()             cancel_car_rental()        cancel_excursion()

                                        │
                                        ▼
                           CompleteOrEscalate Tool
                                        │
                                        ▼
                          Pop dialog_state stack
                                        │
                                        ▼
                          Return to Primary Assistant
                                        │
                                        ▼
                           Generate Final Response
                                        │
                                        ▼
                                      USER


primary_assistant.py acts as the central orchestrator and router of the multi-agent system. It is the first assistant that receives every user query, understands the user's intent, and decides the next action. If the request is a general query, it answers directly using tools like search_flights, lookup_policy, or DuckDuckGo for live web information. If the request involves a specialized task such as booking or modifying a flight, hotel, car rental, or excursion, it does not perform the operation itself. Instead, it delegates the request to the appropriate specialized assistant using routing tools (ToFlightBookingAssistant, ToHotelBookingAssistant, etc.), which then execute the required tools. Once the specialized assistant completes its task, control returns to the primary assistant, which generates the final response for the user. In essence, the Primary Assistant decides what needs to be done and who should do it, while the specialized assistants actually perform the work.                                     