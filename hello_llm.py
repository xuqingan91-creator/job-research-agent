"""Day 1: 验证 DeepSeek 连通 + JSON 结构化输出 + token 用量日志。"""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

PROMPT = """请针对"AI Agent 方向实习岗位调研"输出 JSON，格式如下：
{
  "topic": "调研主题",
  "keywords": ["关键词1", "关键词2", "关键词3"],
  "outline": ["章节1", "章节2", "章节3"]
}
只输出 JSON，不要输出任何其他内容。"""

resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": PROMPT}],
    response_format={"type": "json_object"},
    temperature=0.3,
)

content = resp.choices[0].message.content
usage = resp.usage

print("返回内容:")
print(content)
print("---")
print(
    f"prompt_tokens={usage.prompt_tokens}, "
    f"completion_tokens={usage.completion_tokens}, "
    f"total_tokens={usage.total_tokens}"
)
