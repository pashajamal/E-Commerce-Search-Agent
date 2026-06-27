import os
import json
import asyncio
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from flask import Flask, render_template, redirect, url_for, flash, request
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

# 1. INITIALIZATION & CONFIGURATION
load_dotenv()

# Initialize the OpenAI LLM (using GPT-4o for complex reasoning and schema adherence)
model = ChatOpenAI(model='gpt-4o')

# Configure the Model Context Protocol (MCP) parameters to run Bright Data's proxy server via npx
server_params = StdioServerParameters(
    command='npx',
    args=['@brightdata/mcp'],
    env={
        'API_TOKEN': os.getenv('API_TOKEN'),
        'BROWSER_AUTH': os.getenv('BROWSER_AUTH'),
        'WEB_UNLOCKER_ZONE': os.getenv('WEB_UNLOCKER_ZONE')
    }
)

# Prompt detailing how the agent should prioritize search engine tools vs platform-specific extraction tools
SYSTEM_PROMPT = (
    "To find products, first use the search_engine tool. When finding products, use the web_data tool for the platform. If none exists, scrape as markdown."
    "Example: Don't use web_data_bestbuy_products for search. Use it only for getting data on specific products you already found in search."
)

# Supported retail targets displayed on the frontend
PLATFORMS = ['Amazon', 'Best Buy', 'Ebay', 'Walmart', 'Target', 'Costco', 'Newegg']


class Hit(BaseModel):
    """Schema for an individual product discovery."""
    url: str = Field(..., description='The URL of the product that was found')
    title: str = Field(..., description='The title of the product that was found')
    rating: str = Field(..., description='The rating of the product (stars, number of ratings given etc.)')


class PlatformBlock(BaseModel):
    """Schema grouping product hits together by their specific store platform."""
    platform: str = Field(..., description='Name of the platform')
    results: list[Hit] = Field(..., description='List of results for this platform')


class ProductSearchResponse(BaseModel):
    """Final structural contract returned by the LLM containing all grouped data."""
    platforms: list[PlatformBlock] = Field(..., description='Aggregated list of all results grouped by platform')


app = Flask(__name__)
app.secret_key = 'mysecretkey-not-for-prod'


async def run_agent(query, platforms):
    """
    Spins up an isolated stdio client, connects to the MCP server, downloads 
    available tools, runs the LangGraph ReAct loop, and returns a validated dict object.
    """
    # Open the stdio channel with the subprocess running the MCP server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as sess:
            # Initialize connection handshake with MCP server
            await sess.initialize()

            # Dynamically pull accessible tools from the MCP context provider
            tools = await load_mcp_tools(sess)

            # Build an autonomous ReAct loop agent bound to our strict schema
            agent = create_react_agent(model, tools, response_format=ProductSearchResponse)

            # Construct user prompt injecting selected retail platforms
            prompt = f'{query}\n\nPlatforms: {",".join(platforms)}'

            # Run the agent asynchronously using a multi-turn chat history format
            result = await agent.ainvoke(
                {
                    'messages': [
                        {'role': 'system', 'content': SYSTEM_PROMPT},
                        {'role': 'user', 'content': prompt}
                    ]
                }
            )

            # Extract the raw data parsed by Pydantic directly out of the agent state
            structured = result

