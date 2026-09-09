"""Day 1: 验证 Tavily 搜索在当前网络下是否可用。"""
import os

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
resp = client.search("AI Agent 实习 面经", max_results=3)

for r in resp.get("results", []):
    print(r.get("title"))
    print(r.get("url"))
    print(r.get("content", "")[:120])
    print("---")
