import { get } from "./client";

export interface RankedQuestion {
  question: string;
  count: number;
}

export interface AnalyticsOverview {
  conversations: {
    total: number;
    active: number;
    completed: number;
    average_per_conversation: number;
  };
  messages: {
    total: number;
    active: number;
    completed: number;
    average_per_conversation: number;
  };
  leads: {
    total: number;
    new: number;
    qualified: number;
    converted: number;
  };
  conversion_rate: number;
  popular_questions: RankedQuestion[];
  unanswered_questions: RankedQuestion[];
}

export function getAnalyticsOverview(): Promise<AnalyticsOverview> {
  return get<AnalyticsOverview>("/analytics/overview");
}
