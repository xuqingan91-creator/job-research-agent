"""集中读取 .env 与默认配置。本模块不包含业务逻辑。"""

import os
from pathlib import Path

from dotenv import load_dotenv

# src/job_research_agent/config.py -> 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 0.5
