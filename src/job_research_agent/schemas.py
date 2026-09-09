"""全项目共用的 Pydantic 数据模板。"""

from pydantic import BaseModel, Field


class JobResearchInput(BaseModel):
    company: str = Field(..., min_length=1, description="公司/岗位名称")
    jd_text: str = Field(..., min_length=1, description="JD 全文")
    profile_text: str = Field(default="", description="个人背景简述")


class ResearchPlan(BaseModel):
    topic: str = Field(..., description="调研主题")
    outline: list[str] = Field(..., description="报告章节")
    keyword_groups: list[list[str]] = Field(..., description="分组搜索关键词")


class ReflectionDecision(BaseModel):
    enough: bool = Field(..., description="资料是否足够")
    gaps: list[str] = Field(default_factory=list, description="缺口描述")
    new_keywords: list[str] = Field(default_factory=list, description="补充关键词")


class SourceItem(BaseModel):
    url: str = Field(..., min_length=1, description="来源网址")
    title: str = Field(default="", description="标题")
    snippet: str = Field(default="", description="摘要")


class ReportJudgeScore(BaseModel):
    quality_score: int = Field(..., ge=1, le=5, description="报告质量分 1-5")
    summary: str = Field(default="", description="一句话评语")
