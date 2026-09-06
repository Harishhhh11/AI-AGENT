"""Analytics response schemas."""

from pydantic import BaseModel


class MetricSummary(BaseModel):
    total: int
    active: int
    completed: int
    average_per_conversation: float


class LeadMetrics(BaseModel):
    total: int
    new: int
    qualified: int
    converted: int


class RankedQuestion(BaseModel):
    question: str
    count: int


class AnalyticsOverview(BaseModel):
    conversations: MetricSummary
    messages: MetricSummary
    leads: LeadMetrics
    conversion_rate: float
    popular_questions: list[RankedQuestion]
    unanswered_questions: list[RankedQuestion]
