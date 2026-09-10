"""岗位发现：多主体分类 + 条件筛选 + 主题推荐。"""

from __future__ import annotations

import re

from job_research_agent.schemas import JobPosting, JobSearchTheme, SourceItem

DIRECTION_RULES: list[tuple[str, list[str]]] = [
    ("AI Agent 应用", ["ai agent", "agent 开发", "智能体", "langgraph", "agent"]),
    ("RAG/检索", ["rag", "检索增强", "向量检索", "知识库"]),
    ("大模型应用", ["大模型应用", "llm", "提示词", "prompt"]),
    ("智能硬件/AIoT", ["aiot", "物联网", "iot", "嵌入式", "端侧"]),
    ("算法/模型", ["pytorch", "微调", "算法", "模型训练", "nlp"]),
    ("后端/平台", ["后端", "java", "微服务", "backend", "fastapi"]),
]

TECH_RULES: dict[str, list[str]] = {
    "langgraph": ["langgraph"],
    "langchain": ["langchain"],
    "rag": ["rag", "检索增强", "向量检索"],
    "agent": ["agent", "智能体"],
    "mcp": ["mcp"],
    "llm": ["大模型", "llm"],
    "prompt": ["prompt", "提示词"],
    "python": ["python"],
    "fastapi": ["fastapi"],
    "pytorch": ["pytorch", "torch"],
    "embedding": ["embedding", "向量"],
    "aiot": ["aiot", "物联网", "iot"],
}

DEFAULT_THEMES: list[JobSearchTheme] = [
    JobSearchTheme(
        name="AI Agent 应用",
        keywords=[
            "AI Agent 实习",
            "LangGraph 实习",
            "Agent 开发 实习",
            "大模型 Agent 实习",
            "智能体 开发 实习",
        ],
        directions=["AI Agent 应用"],
        tech_tags=["langgraph", "agent", "mcp"],
    ),
    JobSearchTheme(
        name="RAG/检索",
        keywords=[
            "RAG 实习",
            "检索增强 实习",
            "知识库 问答 实习",
            "向量检索 实习",
            "RAG 工程师 实习",
        ],
        directions=["RAG/检索"],
        tech_tags=["rag", "embedding"],
    ),
    JobSearchTheme(
        name="大模型应用",
        keywords=[
            "大模型应用 实习",
            "LLM 应用开发 实习",
            "提示词工程 实习",
            "大模型产品 实习",
            "AIGC 应用 实习",
        ],
        directions=["大模型应用"],
        tech_tags=["llm", "prompt", "python"],
    ),
    JobSearchTheme(
        name="智能硬件/AIoT",
        keywords=[
            "AIoT Agent 实习",
            "智能硬件 大模型 实习",
            "端侧 AI 实习",
            "嵌入式 AI 实习",
            "边缘计算 大模型 实习",
        ],
        directions=["智能硬件/AIoT"],
        tech_tags=["aiot", "embedding"],
    ),
    JobSearchTheme(
        name="算法/模型",
        keywords=[
            "大模型算法 实习",
            "NLP 算法 实习",
            "模型微调 实习",
            "多模态算法 实习",
            "机器学习 实习",
        ],
        directions=["算法/模型"],
        tech_tags=["pytorch", "llm"],
    ),
]

BLOCKED_DOMAINS = ["career.nankai.edu.cn"]

JOB_PLATFORM_DOMAINS = [
    "zhipin.com",
    "zhaopin.com",
    "liepin.com",
    "51job.com",
    "lagou.com",
    "shixiseng.com",
    "yingjiesheng.com",
    "nowcoder.com",
    "maimai.cn",
    "linkedin.com",
    "chinahr.com",
    "dajie.com",
    "ganji.com",
    "indeed.com",
    "glassdoor.com",
]

INTERNET_BIG = [
    "腾讯",
    "阿里巴巴",
    "阿里",
    "字节跳动",
    "字节",
    "百度",
    "美团",
    "京东",
    "拼多多",
    "网易",
    "快手",
    "滴滴",
    "小米",
    "华为",
    "蚂蚁",
    "哔哩哔哩",
    "bilibili",
    "小红书",
    "携程",
    "360",
    "vivo",
    "oppo",
    "荣耀",
    "联想",
    "大疆",
    "科大讯飞",
    "商汤",
    "地平线",
    "寒武纪",
    "中芯国际",
    "京东方",
    "比亚迪",
    "宁德时代",
]

FOREIGN_BIG = [
    "微软",
    "microsoft",
    "谷歌",
    "google",
    "亚马逊",
    "amazon",
    "苹果",
    "apple",
    "特斯拉",
    "tesla",
    "英伟达",
    "nvidia",
    "英特尔",
    "intel",
    "amd",
    "arm",
    "asml",
    "高通",
    "qualcomm",
    "ti",
    "德州仪器",
    "英飞凌",
    "infineon",
    "恩智浦",
    "nxp",
    "意法半导体",
    "三星",
    "samsung",
    "索尼",
    "sony",
    "西门子",
    "siemens",
    "博世",
    "bosch",
    "sap",
    "oracle",
    "ibm",
    "思科",
    "cisco",
    "爱立信",
    "ericsson",
    "诺基亚",
]

MID_COMPANIES = [
    "中兴",
    "海康威视",
    "大华",
    "浪潮",
    "紫光",
    "展锐",
    "烽火",
    "兆易创新",
    "韦尔",
    "汇顶",
    "云从",
    "旷视",
    "依图",
    "第四范式",
    "用友",
    "金蝶",
    "金山",
    "唯品会",
    "去哪儿",
    "汽车之家",
    "58同城",
    "斗鱼",
    "虎牙",
    "货拉拉",
    "贝壳",
    "猿辅导",
    "作业帮",
    "好未来",
    "新东方",
    "迅雷",
    "猎豹",
    "立讯精密",
    "歌尔",
    "舜宇",
    "闻泰",
    "澜起科技",
    "恒玄科技",
    "乐鑫",
    "瑞芯微",
    "全志",
]

COMPANY_TIER_WEIGHTS = {"大厂": 5.0, "中厂": 3.0, "其他": 1.0}
COMPANY_TYPE_BONUS = {"互联网": 2.0, "外企": 2.0, "硬件/电子": 2.0, "其他": 0.0}


def _matches(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    for pattern in patterns:
        lowered_pattern = pattern.lower()
        if lowered_pattern.isascii() and len(lowered_pattern) <= 3:
            if re.search(rf"\b{re.escape(lowered_pattern)}\b", lowered):
                return True
        elif lowered_pattern in lowered:
            return True
    return False


def classify_company_tier(text: str) -> str:
    if _matches(text, INTERNET_BIG) or _matches(text, FOREIGN_BIG):
        return "大厂"
    if _matches(text, MID_COMPANIES):
        return "中厂"
    return "其他"


def classify_company_type(text: str) -> str:
    if _matches(text, FOREIGN_BIG):
        return "外企"
    if _matches(text, INTERNET_BIG):
        return "互联网"
    if _matches(text, MID_COMPANIES):
        return "硬件/电子"
    return "其他"

OFFICIAL_PATTERNS = ["careers.", "jobs.", "/careers", "/jobs", "recruit", "campus.", "hr."]
CAMPUS_DOMAINS = [".edu.cn", "ncss.cn"]
BLOG_PATTERNS = [
    "blog",
    "csdn.net",
    "juejin.cn",
    "zhihu.com",
    "medium.com",
    "jianshu.com",
    "cnblogs.com",
    "个人博客",
]
ARTICLE_URL_PATTERNS = ["/feed/", "/blog/", "/article/", "/post/", "/discuss/"]
ARTICLE_TITLE_PATTERNS = [
    "面试题",
    "面经",
    "攻略",
    "教程",
    "博客",
    "笔记",
    "汇总",
    "分享",
    "指南",
    "怎么",
    "入门",
    "避坑",
]

SOURCE_WEIGHTS = {
    "official": 1.2,
    "job_platform": 1.15,
    "campus": 1.0,
    "other": 0.9,
    "blog": 0.3,
    "blocked": 0.0,
}

CITY_TO_PROVINCE = {
    "北京": "北京市",
    "上海": "上海市",
    "广州": "广东省",
    "深圳": "广东省",
    "东莞": "广东省",
    "佛山": "广东省",
    "珠海": "广东省",
    "杭州": "浙江省",
    "宁波": "浙江省",
    "南京": "江苏省",
    "苏州": "江苏省",
    "无锡": "江苏省",
    "成都": "四川省",
    "武汉": "湖北省",
    "西安": "陕西省",
    "天津": "天津市",
    "重庆": "重庆市",
    "合肥": "安徽省",
    "长沙": "湖南省",
    "青岛": "山东省",
    "济南": "山东省",
    "厦门": "福建省",
    "福州": "福建省",
    "大连": "辽宁省",
    "沈阳": "辽宁省",
}

REMOTE_PATTERNS = ["远程", "remote", "居家办公"]


def classify_source(url: str, title: str = "", description: str = "") -> str:
    lowered_url = url.lower()
    if any(blocked in lowered_url for blocked in BLOCKED_DOMAINS):
        return "blocked"
    if any(pattern in lowered_url for pattern in ARTICLE_URL_PATTERNS):
        return "blog"
    lowered_title = title.lower()
    if any(pattern in lowered_title for pattern in ARTICLE_TITLE_PATTERNS):
        return "blog"
    if any(domain in lowered_url for domain in JOB_PLATFORM_DOMAINS):
        return "job_platform"
    if any(pattern in lowered_url for pattern in OFFICIAL_PATTERNS):
        return "official"
    if any(domain in lowered_url for domain in CAMPUS_DOMAINS):
        return "campus"
    text = f"{url} {title} {description}".lower()
    if any(pattern in text for pattern in BLOG_PATTERNS):
        return "blog"
    return "other"


def extract_location(text: str) -> tuple[str, str, bool]:
    lowered = text.lower()
    remote = any(pattern in lowered for pattern in REMOTE_PATTERNS)
    for city, province in CITY_TO_PROVINCE.items():
        if city in text:
            return city, province, remote
    for province in set(CITY_TO_PROVINCE.values()):
        if province in text:
            return province, province, remote
    if remote:
        return "远程", "远程", True
    return "", "", remote


def theme_by_name(name: str) -> JobSearchTheme:
    for theme in DEFAULT_THEMES:
        if theme.name == name:
            return theme
    raise KeyError(f"unknown theme: {name}")


def _text(posting: JobPosting) -> str:
    return f"{posting.title} {posting.description}".lower()


def classify_posting(posting: JobPosting) -> JobPosting:
    text = _text(posting)
    direction = posting.direction
    if not direction:
        best_name = ""
        best_score = 0
        for name, patterns in DIRECTION_RULES:
            score = 0
            for pattern in patterns:
                if pattern in posting.title.lower():
                    score += 3
                elif pattern in text:
                    score += 1
            if score > best_score:
                best_name = name
                best_score = score
        direction = best_name or "其他"

    tags = list(posting.tech_tags)
    for tag, patterns in TECH_RULES.items():
        if tag in tags:
            continue
        if any(pattern in text for pattern in patterns):
            tags.append(tag)
    return posting.model_copy(update={"direction": direction, "tech_tags": tags})


def filter_postings(
    postings: list[JobPosting],
    theme: JobSearchTheme,
) -> list[JobPosting]:
    result: list[JobPosting] = []
    for posting in postings:
        if theme.directions and posting.direction not in theme.directions:
            if not (theme.tech_tags and set(theme.tech_tags) & set(posting.tech_tags)):
                continue
        if theme.locations and posting.location and posting.location not in theme.locations:
            continue
        result.append(posting)
    return result


def score_posting(posting: JobPosting, theme: JobSearchTheme) -> float:
    text = _text(posting)
    score = 0.0
    for keyword in theme.keywords:
        for token in keyword.lower().split():
            if token in text:
                score += 1.0
    for tag in theme.tech_tags:
        if tag in posting.tech_tags:
            score += 2.0
    if posting.direction in theme.directions:
        score += 3.0
    if theme.locations and posting.location in theme.locations:
        score += 2.0
    score += COMPANY_TIER_WEIGHTS.get(posting.company_tier, 1.0)
    score += COMPANY_TYPE_BONUS.get(posting.company_type, 0.0)
    return score * SOURCE_WEIGHTS.get(posting.source_type, 0.9)


def _search(
    provider,
    query: str,
    max_results: int,
    include_domains: list[str] | None = None,
):
    try:
        if include_domains:
            return provider.search(
                query,
                max_results=max_results,
                include_domains=include_domains,
            )
        return provider.search(query, max_results=max_results)
    except TypeError:
        return provider.search(query, max_results=max_results)


def _passes_filters(
    posting: JobPosting,
    *,
    include_blogs: bool,
    provinces: list[str] | None,
    cities: list[str] | None,
    allow_remote: bool,
    company_tiers: list[str] | None,
) -> bool:
    if posting.source_type == "blocked":
        return False
    if posting.source_type == "blog" and not include_blogs:
        return False
    if company_tiers and posting.company_tier not in company_tiers:
        return False
    if provinces or cities:
        if posting.remote and not allow_remote:
            return False
        matched = False
        if provinces and posting.province in provinces:
            matched = True
        if cities and posting.location in cities:
            matched = True
        if posting.remote and allow_remote:
            matched = True
        if not matched:
            return False
    return True


def recommend_jobs(
    theme_name: str,
    *,
    search_provider,
    max_results: int = 20,
    results_per_keyword: int = 5,
    include_blogs: bool = False,
    provinces: list[str] | None = None,
    cities: list[str] | None = None,
    allow_remote: bool = True,
    use_source_queries: bool = True,
    company_tiers: list[str] | None = None,
    max_searches: int = 12,
) -> list[JobPosting]:
    theme = theme_by_name(theme_name)
    seen: set[str] = set()
    candidates: list[JobPosting] = []
    queries: list[tuple[str, list[str] | None]] = []
    for keyword in theme.keywords:
        queries.append((keyword, None))
        if use_source_queries:
            queries.append((f"{keyword} 官网 招聘", None))
            queries.append((keyword, JOB_PLATFORM_DOMAINS))
    for query, domains in queries[:max_searches]:
        results = _search(
            search_provider,
            query,
            results_per_keyword,
            include_domains=domains,
        )
        for item in results:
            if not item.url or item.url in seen:
                continue
            seen.add(item.url)
            title = item.title or item.snippet[:40] or item.url
            description = item.snippet
            combined = f"{title} {description}"
            location, province, remote = extract_location(combined)
            candidates.append(
                JobPosting(
                    title=title,
                    url=item.url,
                    description=description,
                    location=location,
                    province=province,
                    remote=remote,
                    source="web",
                    source_type=classify_source(item.url, title, description),
                    company_tier=classify_company_tier(combined),
                    company_type=classify_company_type(combined),
                )
            )
    classified = [classify_posting(item) for item in candidates]
    allowed = [
        item
        for item in classified
        if _passes_filters(
            item,
            include_blogs=include_blogs,
            provinces=provinces,
            cities=cities,
            allow_remote=allow_remote,
            company_tiers=company_tiers,
        )
    ]
    filtered = filter_postings(allowed, theme)
    ranked = sorted(filtered, key=lambda item: score_posting(item, theme), reverse=True)
    return ranked[:max_results]
