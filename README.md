# Autonomous Multi-Platform E-Commerce Product Finder

An advanced, AI-driven product discovery agent that uses the Model Context Protocol (MCP) to scrape and structure data across major retail platforms. 

Built with **LangGraph**, **LangChain**, and **Flask**, this application orchestrates an autonomous ReAct loop powered by **GPT-4o**. It securely utilizes **Bright Data's Web Unlocker** and proxy infrastructure via MCP to discover, scrape, and structure product results seamlessly into standard validation schemas.

## 🚀 Features

- **Autonomous Agentic Workflows:** Employs LangGraph's ReAct agent pattern to automatically transition from search engines to platform-specific data extraction.
- **Model Context Protocol (MCP):** Connects dynamically via an STDIO client connection to Bright Data's infrastructure, avoiding hardcoded scraping endpoints.
- **Strict Structural Schemas:** Enforces data integrity using robust Pydantic contracts (`Hit`, `PlatformBlock`, `ProductSearchResponse`) passed directly into the LLM as its final output format.
- **Multi-Platform Focus:** Designed to support target stores globally including Amazon, Best Buy, eBay, Walmart, Target, Costco, and Newegg.

## 📋 Architecture & Agent Strategy

The agent adheres to a strict hierarchical workflow defined by the `SYSTEM_PROMPT`:
1. **Discovery:** The agent first initializes product tracking using global search engines.
2. **Platform Extraction:** Once specific URLs or entities are located, it transitions to platform-specific extraction (`web_data` tools) or falls back to custom markdown scraping to aggregate reviews, titles, and paths.

## 🛠️ Prerequisites

Before running the application, ensure you have the following installed:
- Python 3.10+
- Node.js & npm (required to execute the `@brightdata/mcp` server package via `npx`)
