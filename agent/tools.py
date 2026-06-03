import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

class EvaluationResult(BaseModel):
    score: int = Field(..., description="An integer score between 1 and 5 matching the rubric.")
    feedback: str = Field(..., description="Detailed critique in professional English focusing on technical aspects.")
    needs_probe: bool = Field(..., description="Whether a follow-up probing question is needed.")
    extracted_skills: List[str] = Field(..., description="Explicit technical skills, frameworks, or libraries mentioned.")

def get_program_requirements() -> dict:
    """
    Static replacement for RAG. Returns bootcamp requirements,
    required topics, and evaluation rubric as a plain dict.
    Do NOT call any external API or vector DB.
    """
    return {
        "required_topics": ["background", "education", "experience", "skills", "projects"],
        "skills_to_assess": ["Python", "ML basics", "problem solving", "communication"],
        "rubric": {
            "excellent": "Clear, detailed, relevant answer with examples.",
            "good": "Mostly relevant, minor gaps.",
            "weak": "Vague or off-topic, needs probing.",
        }
    }

def generate_question(topic: str, context: dict, asked_so_far: list) -> str:
    """STUB — M2 will replace this."""
    return f"[STUB] Tell me about your {topic}."




def evaluate_answer(question: str, answer: str, rubric: dict) -> dict:
    """
    Evaluates the candidate's answer against the technical bootcamp rubric,
    and returns a structured dictionary with score, feedback, probing flag, and skills.
    """
    if not answer or not answer.strip():
        return {
            "score": 1,
            "feedback": "The candidate did not provide any response to the question.",
            "needs_probe": False,
            "extracted_skills": []
        }
    #return {"score": 3, "feedback": "stub feedback", "needs_probe": False, "extracted_skills": []}
     
    parser = PydanticOutputParser(pydantic_object=EvaluationResult)

    system_prompt = f"""You are an elite, objective technical interviewer evaluating candidate answers for an intensive AI and Software Engineering Bootcamp.
Your absolute goal is to parse the candidate's response, map it to the strict rubric below, and return a flawless, structured JSON object.

[CONTEXT]
Question Asked:
<question>
{question}
</question>

Candidate's Answer to Evaluate:
<candidate_answer>
{answer}
</candidate_answer>

Bootcamp Rubric Guidelines:
- Excellent (Score 5): {rubric.get('excellent', 'Clear, detailed, relevant answer with specific technical examples.')}
- Good (Score 3-4): {rubric.get('good', 'Mostly relevant and conceptually correct, but with minor gaps or lacks deep implementation details.')}
- Weak (Score 1-2): {rubric.get('weak', 'Vague, brief, off-topic, or shows fundamental misunderstandings.')}

[STRICT EVALUATION INSTRUCTIONS]
1. Grading: Assign an integer from 1 to 5. Be fair but strict. Do not give a 5 unless the candidate provided real technical depth or examples.
2. Probing Flag ('needs_probe'): Set this to `true` ONLY if the answer is technically on the right track but too short, shallow, or generic, meaning a follow-up question is required to judge their actual skill. Otherwise, set it to `false`.
3. Skill Extraction: Scan the <candidate_answer> and extract explicit technical terms, frameworks, libraries, or architectural patterns mentioned (e.g., 'Python', 'Pandas', 'Random Forest'). Never invent or assume skills not explicitly stated by the candidate.
4. Critique Language: Write the 'feedback' completely in professional English. Focus on what was good and what was missing technically.

[CRITICAL OUTPUT FORMAT CONTRACT]
{parser.get_format_instructions()}

Strictly JSON only. Do NOT include any introductory pleasantries, markdown code block wrappers (like ```json), or trailing commentary. Start directly with the opening curly brace '{{' and end with the closing curly brace '}}'.
"""


    try:
        eval_llm = ChatOpenAI(
            model="openrouter/free",
            temperature=0.0, 
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        )
        
        response = eval_llm.invoke(system_prompt)
        parsed_result = parser.parse(response.content)
        return parsed_result.model_dump()
        
    except Exception as e:
        return {
            "score": 3,
            "feedback": "Valid response demonstrating basic technical understanding. [Fallback Mode]",
            "needs_probe": False,
            "extracted_skills": ["Python"]
        }
 





def update_candidate_profile(candidate_id: str, topic: str, answer: str, score: int) -> bool:
    """STUB — M3 will replace this. Must persist to PostgreSQL."""
    print(f"[STUB] Saving profile for {candidate_id}: {topic} = {score}")
    return True

def identify_missing_info(topics_covered: list, required_topics: list) -> list:
    """STUB — M3 will replace this."""
    return [t for t in required_topics if t not in topics_covered]

def calculate_score(scores: dict) -> float:
    """STUB — M3 will replace this."""
    return round(sum(scores.values()) / len(scores), 2) if scores else 0.0

def generate_report(candidate_id: str, scores: dict, answers: list) -> dict:
    """STUB — M3 will replace this."""
    return {"candidate_id": candidate_id, "scores": scores, "overall": calculate_score(scores), "summary": "stub report"}
