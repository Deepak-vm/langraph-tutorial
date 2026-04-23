import operator
from pydantic.types import AnyItemType
import os 
from dotenv import load_dotenv
from typing import TypedDict , Annotated
import psycopg
from langgraph.graph import StateGraph , START , END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage
)

# pyrefly: ignore [missing-import]
from tavily import TavilyClient
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import tools, search_flights, tavily_search
load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash"
)

DB_URL = os.getenv("DB_URL")

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage] , operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int 

def flight_agent(state: TravelState):
    query = state["user_query"]
    flight_data = search_flights.invoke(query)
    return {
        "flight_results": flight_data, 
        "messages":[
            AIMessage(content=f"Flight data fetched")
        ], 
        "llm_calls": state.get("llm_calls" , 0)+1
    }

def hotel_agent(state: TravelState):
    query =f"Best hotels in {state['user_query']}"
    hotel_data = tavily_search.invoke(query)
    return {
        "hotel_results": hotel_data, 
        "messages":[
            AIMessage(content=f"Hotel data fetched")
        ], 
        "llm_calls": state.get("llm_calls" , 0)+1
    }


def itinerary_agent(state: TravelState):
    prompt = f"""
    Create a travel itinerary for the user.
    User_query:{state["user_query"]}
    Flight data:{state["flight_results"]}
    Hotel data:{state["hotel_results"]}
    """
    itinerary = llm.invoke([
        SystemMessage(content="Create the itinerary"),
        HumanMessage(content=prompt)
    ])
    return {
        "itinerary": itinerary.content, 
        "messages":[itinerary], 
        "llm_calls": state.get("llm_calls" , 0)+1
    }


def final_agent(state: TravelState):
    prompt = f"""
    Summarise the itineary for the user
    User_query:{state['user_query']}
    Flight data:{state['flight_results']}
    Hotel data:{state['hotel_results']}
    Itinerary:{state['itinerary']}
    """
    final = llm.invoke([
        HumanMessage(content=prompt)
    ])
    return {
        "messages":[final], 
        "llm_calls": state.get("llm_calls" , 0)+1
    }


graph = StateGraph(TravelState)
graph.add_node("flight_agent" , flight_agent)
graph.add_node("hotel_agent" , hotel_agent)
graph.add_node("itinerary_agent" , itinerary_agent)
graph.add_node("final_agent" , final_agent)

graph.add_edge(START , "flight_agent" )
graph.add_edge("flight_agent" , "hotel_agent" )
graph.add_edge("hotel_agent" , "itinerary_agent" )
graph.add_edge("itinerary_agent" , "final_agent" )
graph.add_edge("final_agent" , END )


#connecting memory to the graph
_conn = psycopg.connect(DB_URL)
checkpointer = PostgresSaver(_conn)
checkpointer.setup()
app=graph.compile(checkpointer=checkpointer)


if __name__ == "__main__":

    config = {
        "configurable": {
            "thread_id": "1"
        }
    }
    result = app.invoke({
        "user_query": "Looking for flights to goa from delhi",
        "messages":[
            HumanMessage(content="Looking for flights to goa from delhi")
        ],
        "llm_calls":0

    }, config=config)

    print("\n" + "="*60)
    print("✈️  FLIGHT RESULTS")
    print("="*60)
    print(result.get("flight_results", "No flight results"))

    print("\n" + "="*60)
    print("🏨  HOTEL RESULTS")
    print("="*60)
    print(result.get("hotel_results", "No hotel results"))

    print("\n" + "="*60)
    print("🗺️  ITINERARY")
    print("="*60)
    print(result.get("itinerary", "No itinerary"))

    print("\n" + "="*60)
    print("📋  FINAL SUMMARY")
    print("="*60)
    messages = result.get("messages", [])
    if messages:
        print(messages[-1].content)

    print(f"\n✅ Total LLM calls: {result.get('llm_calls', 0)}")
 
