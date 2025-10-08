import asyncio
from dotenv import load_dotenv
from enum import Enum
from pydantic import BaseModel
import json
from typing import List, Optional

from google.adk import Agent
from google.adk.tools import google_search
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


load_dotenv(".env")

class Category(str, Enum):
    GROCERIES = "Groceries"
    EATING_OUT = "Eating out"
    TRAVEL = "Travel"
    CAR = "Car"
    RENT_BILLS = "Rent and bills"
    FITNESS_HEALTH = "Fitness or health"

class TransactionInput(BaseModel):
    account_id: Optional[str]
    transaction_id: Optional[str]
    amount: Optional[int]
    source: Optional[str]
    time: Optional[int]
    vendor: Optional[str]
    location: Optional[str]
    description: Optional[str]

class TransactionListInput(BaseModel):
    transactions: list[TransactionInput]

PROMPT = f"""
You are a personal banking assistant that categorizes financial transactions.
The user will provide data as a list of transaction objects.
Your only job is to categorize each transaction based on the fields, especially description, vendor and location.
If the data is inadequate to make a decision, use the google_search tool to find out more. For example, you could search for the vendor to verify that the transaction took place at a restaurant.
You must assign each transaction a category from this list: {", ".join([cat.value for cat in Category])}.
Your final output must only be a single JSON object with the schema defined below. Do not include any conversational or introductory text outside the JSON object, otherwise the JSON parser will throw an error.
{{
    "categorized_transactions": [
        {{
            "transaction_id": "...",
            "category": "...",
            "reason": "..."
        }}
    ]
}}
"""

# Couldn't get agent to use both google_search and output_schema 💀
agent = Agent(
    name="categorization_agent",
    description="Categorizes personal banking transactions, using Google search when necessary.",
    model="gemini-2.0-flash",
    instruction=PROMPT,
    tools=[google_search],
    input_schema=TransactionListInput,
    # output_schema=CategorizedTransactionList
)

def extract_json_from_md(text: str) -> str:
    l_brace, r_brace = text.find("{"), text.rfind("}")
    return text[l_brace : r_brace + 1] if r_brace > l_brace > -1 else text

async def run_categorization_agent(input: TransactionListInput) -> list[dict]:
    app_name, user_id, session_id = "categorization_service", "user", "session"
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )
    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service
    )
    
    # Send user message as JSON to the agent
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=input.model_dump_json())]
    )
    print(f"Sending message to agent: {user_message}")

    # Run agent
    agent_response = None
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=user_message
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                agent_response = event.content.parts[0].text
            break

    if agent_response:
        try:
            parsed_output = json.loads(extract_json_from_md(agent_response))
            return parsed_output["categorized_transactions"]
        except json.JSONDecodeError:
            print("Failed to parse JSON output")
    else:
        print("No response from agent")
    return []

def categorize_transactions(transactions: list[TransactionInput]):
    print("Starting categorization service...")
    result = asyncio.run(
        run_categorization_agent(TransactionListInput(transactions=transactions))
    )
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    dummy_data = [
        {
            "account_id": "acc-001", "transaction_id": "txn-001", "amount": 1500,
            "source": "visa-4567", "time": 1698778800, "vendor": "Woolworths",
            "category": "", "location": "Sydney", "description": "Woolworths Metro"
        },
        {
            "account_id": "acc-002", "transaction_id": "txn-002", "amount": 7500,
            "source": "mastercard-1234", "time": 1698779000, "vendor": "Qantas",
            "category": "", "location": "Sydney Airport", "description": "Flight to Melbourne"
        },
        {
            "account_id": "acc-003", "transaction_id": "txn-003", "amount": 4500,
            "source": "debit-9876", "time": 1698780000, "vendor": "Little India",
            "category": "", "location": "Ryde, Sydney", "description": "Supermarket"
        }
    ]
    
    load_dotenv()
    categorize_transactions([TransactionInput(**t) for t in dummy_data])
