export type StudyMethod = "reading" | "practice" | "flashcards" | "review";

export interface Topic {
  name: string;
  description: string;
}

export interface StudySession {
  date: string;
  topic: Topic;
  information: string;
  duration_minutes: number;
  methods: StudyMethod[];
}

export interface StudyPlan {
  overview: string;
  sessions: StudySession[];
  total_duration_hours: number;
}
