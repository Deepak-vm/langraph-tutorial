from tavily import TavilyClient
import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def search_flights(query: str):
    """Use this to search for flight information."""
    url = "https://api.aviationstack.com/v1/flights"
    params = {
        "access_key": AVIATIONSTACK_API_KEY,
        "limit": 5
    }
    response = requests.get(url=url, params=params)
    data = response.json()

    flights = []
    if "data" in data:
        for flight in data["data"][:5]:
            airline = flight.get("airline", {}).get("name", "Unknown")
            arrival = flight.get("arrival", {}).get("airport", "Unknown")
            departure = flight.get("departure", {}).get("airport", "Unknown")
            status = flight.get("flight_status", "Unknown")
            flights.append(
                f"Airline: {airline} | From: {departure} → To: {arrival} | Status: {status}"
            )

    if not flights:
        return "No flight data found."

    return "\n".join(flights)


@tool
def tavily_search(query: str):
    """Use this to search for Hotel information."""
    response = client.search(query= query , max_results=5)

    results = []
    for i , r in enumerate(response["results"] , 1):
            title = r.get("title" , "unknown")
            url = r.get("url" , "")
            snippet = r.get("content" , "").strip()

            if len(snippet) > 300:
                snippet = snippet[:300] + "..."

            results.append(
                f"Title: {title}\nURL: {url}\nSnippet: {snippet}\n"
            )

    
    return "\n\n".join(results) 

tools = [tavily_search , search_flights]
