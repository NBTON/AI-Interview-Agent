# Score Payload Contract

The interview agent writes the same nested JSON payload to `interview_sessions.scores`, `interview_reports.topic_scores`, and the LangGraph `InterviewState.scores` field.

```json
{
  "summary_metrics": {
    "overall_score": 4.25,
    "total_turns_taken": 6,
    "tier_assigned": "advanced_track"
  },
  "topic_scores": {
    "background": {
      "final_topic_score": 4.5,
      "turn_scores": [
        {
          "turn_number": 1,
          "score": 4,
          "feedback": "Clear background with relevant project evidence.",
          "extracted_skills": ["Python", "SQL"],
          "extracted_info": {
            "years_experience": 2,
            "current_role": "Backend Developer"
          }
        },
        {
          "turn_number": 2,
          "score": 5,
          "feedback": "Strong follow-up with concrete implementation details.",
          "extracted_skills": ["FastAPI", "PostgreSQL"],
          "extracted_info": {
            "project_domain": "APIs"
          }
        }
      ]
    },
    "education": {
      "final_topic_score": 3,
      "turn_scores": [
        {
          "turn_number": 6,
          "score": 3,
          "feedback": "Light coverage completed.",
          "extracted_skills": [],
          "extracted_info": {}
        }
      ]
    }
  }
}
```

Notes for UI mapping:

- `summary_metrics.overall_score` is a 1-5 score. Multiply by 20 for a percentage.
- `summary_metrics.total_turns_taken` is counted from all `turn_scores` arrays.
- `summary_metrics.tier_assigned` is one of `advanced_track`, `beginner_adaptive`, or an empty string before background is evaluated.
- `topic_scores.{topic}.final_topic_score` is the average of that topic's `turn_scores[].score`.
- `topic_scores.{topic}.turn_scores` preserves each evaluated answer, so charts can show per-turn progression without overwriting earlier attempts.
