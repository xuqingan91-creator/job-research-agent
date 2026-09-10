"""全项目共用的 Pydantic 数据模板。"""

from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field, model_validator


def _normalize_keyword_group(value: Any) -> Any:
    """部分模型会把关键词组返回成 {"section": ..., "keywords": [...]}。"""
    if isinstance(value, dict):
        keywords = value.get("keywords")
        if isinstance(keywords, list):
            return keywords
        section = value.get("section")
        if isinstance(section, str) and section:
            return [section]
    return value


KeywordGroup = Annotated[list[str], BeforeValidator(_normalize_keyword_group)]


class JobResearchInput(BaseModel):
    company: str = Field(..., min_length=1, description="公司/岗位名称")
    jd_text: str = Field(..., min_length=1, description="JD 全文")
    profile_text: str = Field(default="", description="个人背景简述")


class ResearchPlan(BaseModel):
    topic: str = Field(..., description="调研主题")
    outline: list[str] = Field(..., description="报告章节")
    keyword_groups: list[KeywordGroup] = Field(..., description="分组搜索关键词")


class ReflectionDecision(BaseModel):
    enough: bool = Field(..., description="资料是否足够")
    gaps: list[str] = Field(default_factory=list, description="缺口描述")
    new_keywords: list[str] = Field(default_factory=list, description="补充关键词")

    @model_validator(mode="before")
    @classmethod
    def normalize_enough_synonyms(cls, data: Any) -> Any:
        if isinstance(data, dict) and "enough" not in data and "sufficient" in data:
            data["enough"] = data.pop("sufficient")
        return data


class SourceItem(BaseModel):
    url: str = Field(..., min_length=1, description="来源网址")
    title: str = Field(default="", description="标题")
    snippet: str = Field(default="", description="摘要")


class ReportJudgeScore(BaseModel):
    quality_score: int = Field(..., ge=1, le=5, description="报告质量分 1-5")
    summary: str = Field(default="", description="一句话评语")


class JobPosting(BaseModel):
    title: str = Field(..., min_length=1, description="岗位标题")
    url: str = Field(..., min_length=1, description="岗位链接")
    company: str = Field(default="", description="公司")
    location: str = Field(default="", description="地点")
    direction: str = Field(default="", description="岗位方向（多主体分类之一）")
    tech_tags: list[str] = Field(default_factory=list, description="技术栈标签")
    description: str = Field(default="", description="岗位描述/摘要")
    source: str = Field(default="", description="来源")


class JobSearchTheme(BaseModel):
    name: str = Field(..., min_length=1, description="主题名")
    keywords: list[str] = Field(..., description="搜索关键词")
    directions: list[str] = Field(default_factory=list, description="限定岗位方向")
    tech_tags: list[str] = Field(default_factory=list, description="限定技术标签")
    locations: list[str] = Field(default_factory=list, description="限定地点")
