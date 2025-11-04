from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage
from typing import Annotated, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import requests
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

load_dotenv()
THREAD = '1'

llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash')

# ***************************** TOOLS ********************************8
search_tool = DuckDuckGoSearchRun()

@tool
def caculator_tool(first_num: float, second_num: float, operation: str) -> float:
    """Perform a math operation between two numbers."""
    if operation in ['addition', '+']:
        return first_num + second_num
    elif operation in ['subtraction', '-']:
        return first_num - second_num
    elif operation in ['multiplication', '*']:
        return first_num * second_num
    elif operation in ['division', '/']:
        if second_num == 0:
            return "Error: Cannot divide by zero"
        return first_num / second_num
    else:
        return first_num % second_num


@tool
def get_stock_price(company_code: str) -> dict:
    """Fetch latest stock price of a company."""
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={company_code}&apikey=4STEE86DNR9S3882"
    return requests.get(url).json()


@tool
def get_weather(city: str) -> dict:
    """Get current weather details for a city."""
    url = f"https://wttr.in/{city}?format=j1"
    data = requests.get(url, timeout=10).json()
    current = data.get("current_condition", [{}])[0]
    return {
        "city": city,
        "temperature_C": current.get("temp_C"),
        "condition": current.get("weatherDesc", [{}])[0].get("value")
    }


@tool
def get_current_time(timezone: str = "UTC") -> dict:
    """Get the current time in a chosen timezone."""
    import pytz
    from datetime import datetime
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    return {"timezone": timezone, "time": now.strftime("%Y-%m-%d %H:%M:%S")}


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert currency based on the latest exchange rate."""
    url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
    data = requests.get(url).json()
    rate = data["rates"].get(to_currency.upper())
    return {"converted_amount": round(amount * rate, 2), "rate": rate}


@tool
def get_random_fact() -> str:
    """Return a random interesting fact."""
    return requests.get("https://uselessfacts.jsph.pl/random.json?language=en").json().get("text")


@tool
def get_joke() -> dict:
    """Return a random joke."""
    return requests.get("https://official-joke-api.appspot.com/random_joke").json()


tools = [
    search_tool,
    caculator_tool,
    get_stock_price,
    get_weather,
    get_current_time,
    convert_currency,
    get_random_fact,
    get_joke
]

llm_with_tools = llm.bind_tools(tools)

# ****************************** STATE ************************8
class ChatState(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages]


# ******************************* NODES ************************
def chat_node(state: ChatState):
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {'messages' : [response]}

tool_node = ToolNode(tools)

# ************************* DB CONN *******************
conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)

checkpointer = SqliteSaver(conn=conn)


# **************************** INIT GRAPH *********************
graph = StateGraph(ChatState)
graph.add_node('chat_node', chat_node)
graph.add_node('tools', tool_node)

graph.add_edge(START, 'chat_node')
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools', 'chat_node')
chatbot = graph.compile(checkpointer=checkpointer)

# ******************************** HELPER **************************8
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    return list(all_threads)