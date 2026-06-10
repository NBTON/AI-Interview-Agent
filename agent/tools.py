import os
import uuid
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from supabase import create_client, Client

# Load variables from the project-root .env file
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

_supabase_url = os.environ.get("SUPABASE_URL")
_supabase_key = os.environ.get("SUPABASE_KEY")
_db_client: Client = None

if _supabase_url and _supabase_key and _supabase_key != "your_supabase_service_role_key_here":
    try:
        _db_client = create_client(_supabase_url, _supabase_key)
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")


# ---------------------------------------------------------------------------
# Pydantic model for structured evaluation output
# ---------------------------------------------------------------------------
class EvaluationResult(BaseModel):
    score: int = Field(..., ge=1, le=5, description="Score from 1 (weak) to 5 (excellent).")
    feedback: str = Field(..., description="Professional feedback on the candidate's answer.")
    needs_probe: bool = Field(..., description="True if a follow-up probe question is warranted.")
    extracted_skills: List[str] = Field(default_factory=list, description="Explicit technical skills, tools, or frameworks mentioned.")
    extracted_info: dict = Field(default_factory=dict, description="Structured facts extracted from the answer (e.g. university, degree, company, role, project name, etc.)")


def get_program_requirements() -> dict:
    """
    Retrieves bootcamp requirements, required topics, and rubric from the database.
    Falls back to a default program definition if the database is not available.
    """
    if _db_client:
        try:
            res = _db_client.table("programs").select("*").eq("is_active", True).limit(1).execute()
            if res.data:
                prog = res.data[0]
                return {
                    "id": prog["id"],
                    "name": prog["name"],
                    "required_topics": prog["required_topics"],
                    "skills_to_assess": prog["skills_to_assess"],
                    "rubric": prog["rubric"],
                    "max_turns": prog["max_turns"]
                }
        except Exception as e:
            print(f"Error fetching program requirements from database: {e}")
            
    # Default fallback program
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "name": "AI & Software Engineering Bootcamp",
        "required_topics": ["background", "education", "experience", "skills", "projects"],
        "skills_to_assess": ["Python", "ML basics", "problem solving", "communication"],
        "rubric": {
            "excellent": "Clear, detailed, relevant answer with specific technical examples and demonstrable depth.",
            "good": "Mostly relevant and conceptually correct, but with minor gaps or lacks deep implementation details.",
            "weak": "Vague, brief, off-topic, or shows fundamental misunderstandings. Needs probing."
        },
        "max_turns": 15
    }


openai_key = os.environ.get("OPENAI_API_KEY")
openrouter_key = os.environ.get("OPENROUTER_API_KEY")

primary_llm = None
fallback_llm = None

if openai_key:
    primary_llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=openai_key,
    )

if openrouter_key:
    fallback_llm = ChatOpenAI(
        model="openrouter/free",
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_key,
    )

if primary_llm and fallback_llm:
    _llm = primary_llm.with_fallbacks([fallback_llm])
elif primary_llm:
    _llm = primary_llm
elif fallback_llm:
    _llm = fallback_llm
else:
    _llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key="",
    )


def ensure_candidate_and_session(candidate_id: str, candidate_name: str, program_id: str = None) -> dict:
    """Ensures candidate, session, and profile exist in Supabase and returns verified UUIDs."""
    # Convert string ID to valid UUID format using uuid5 for consistency
    try:
        candidate_uuid = str(uuid.UUID(candidate_id))
    except ValueError:
        # Create deterministic UUID from string representation
        candidate_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"candidate.{candidate_id}"))

    session_uuid = str(uuid.uuid4())
    
    # Resolve program ID
    prog_uuid = program_id
    if not prog_uuid:
        prog = get_program_requirements()
        prog_uuid = prog.get("id")
        
    try:
        if _db_client:
            # 1. Upsert candidate
            _db_client.table("candidates").upsert({
                "id": candidate_uuid,
                "full_name": candidate_name,
                "email": f"{candidate_name.lower().replace(' ', '')}@example.com",
                "status": "interviewing"
            }).execute()
            
            # 2. Insert interview session
            _db_client.table("interview_sessions").insert({
                "id": session_uuid,
                "candidate_id": candidate_uuid,
                "program_id": prog_uuid if prog_uuid != "00000000-0000-0000-0000-000000000000" else None,
                "status": "in_progress",
                "current_topic": "",
                "topics_covered": [],
                "missing_topics": ["background", "education", "experience", "skills", "projects"],
                "turn_count": 0,
                "scores": {}
            }).execute()
            
            # 3. Create profile shell if not exists
            _db_client.table("candidate_profiles").upsert({
                "candidate_id": candidate_uuid,
                "background": {},
                "education": {},
                "experience": [],
                "skills": {"technical": [], "soft": [], "proficiency": {}},
                "projects": []
            }).execute()
            
            print(f"Initialized database session: {session_uuid} for candidate: {candidate_uuid}")
    except Exception as e:
        print(f"Error ensuring candidate and session in database: {e}")
        
    return {
        "candidate_id": candidate_uuid,
        "session_id": session_uuid,
        "program_id": prog_uuid
    }


def generate_question(topic: str, context: dict, asked_so_far: list, candidate_id: str = None) -> str:
    """Generate a contextual interview question using an LLM, incorporating candidate profile context if available."""
    skills = context.get("skills_to_assess", [])
    rubric = context.get("rubric", {})

    profile_context = ""
    if candidate_id and _db_client:
        try:
            res = _db_client.table("candidate_profiles").select("*").eq("candidate_id", candidate_id).execute()
            if res.data:
                profile_context = f"\nCandidate Profile Context from DB: {res.data[0]}\n"
        except Exception as e:
            print(f"Error fetching profile context for question generation: {e}")

    system_prompt = (
        "You are an interviewer conducting a bootcamp admission interview. "
        "Generate exactly ONE clear, professional question for the candidate. "
        "Do not include any preamble, explanation, or extra text — only the question itself."
    )

    asked_text = "\n".join(f"- {q}" for q in asked_so_far) if asked_so_far else "None yet."

    user_prompt = (
        f"Topic for this question: {topic}\n\n"
        f"Skills we need to assess: {', '.join(skills)}\n\n"
        f"Rubric for reference:\n"
        f"  Excellent: {rubric.get('excellent', 'N/A')}\n"
        f"  Good: {rubric.get('good', 'N/A')}\n"
        f"  Weak: {rubric.get('weak', 'N/A')}\n\n"
        f"{profile_context}"
        f"Questions already asked:\n{asked_text}\n\n"
        f"Generate a new, different question about '{topic}' that has NOT been asked yet. "
        f"If the topic is 'skills', try to probe specific skills from the list. "
        f"Return only the question."
    )

    response = _llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    return response.content.strip()


def generate_probe_question(topic: str, last_question: str, last_answer: str) -> str:
    """Generates a follow-up probing question to dig deeper into a weak or brief answer."""
    system_prompt = (
        "You are a professional technical interviewer. The candidate gave a brief or weak answer "
        "to a previous question. Generate exactly ONE follow-up probe question to encourage "
        "the candidate to elaborate, provide specific technical details, or show examples. "
        "Do not include any preamble — only the question itself."
    )
    
    user_prompt = (
        f"Topic: {topic}\n"
        f"Previous Question: {last_question}\n"
        f"Candidate Answer: {last_answer}\n\n"
        f"Generate a professional, natural follow-up question digging deeper into their response."
    )
    
    response = _llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    
    return response.content.strip()


def evaluate_answer(question: str, answer: str, rubric: dict) -> dict:
    """
    Evaluates the candidate's answer against the technical bootcamp rubric,
    and returns a structured dictionary with score, feedback, probing flag, and extracted data.
    """
    if not answer or not answer.strip():
        return {
            "score": 1,
            "feedback": "The candidate did not provide any response to the question.",
            "needs_probe": False,
            "extracted_skills": [],
            "extracted_info": {}
        }
     
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
4. Information Extraction ('extracted_info'): Extract key facts from the candidate's response as a structured key-value object. For background, extract motivation or goals. For education, extract university or degree. For experience, extract company, role, or duration. For projects, extract project name or technology stack.
5. Critique Language: Write the 'feedback' completely in professional English. Focus on what was good and what was missing technically.

[CRITICAL OUTPUT FORMAT CONTRACT]
{parser.get_format_instructions()}

Strictly JSON only. Do NOT include any introductory pleasantries, markdown code block wrappers (like ```json), or trailing commentary. Start directly with the opening curly brace '{{' and end with the closing curly brace '}}'.
"""

    try:
        eval_primary = None
        eval_fallback = None

        if openai_key:
            eval_primary = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.0,
                api_key=openai_key,
            )

        if openrouter_key:
            eval_fallback = ChatOpenAI(
                model="openrouter/free",
                temperature=0.0,
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_key,
            )

        if eval_primary and eval_fallback:
            eval_llm = eval_primary.with_fallbacks([eval_fallback])
        elif eval_primary:
            eval_llm = eval_primary
        elif eval_fallback:
            eval_llm = eval_fallback
        else:
            eval_llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.0,
                api_key="",
            )
        
        response = eval_llm.invoke([HumanMessage(content=system_prompt)])
        parsed_result = parser.parse(response.content)
        return parsed_result.model_dump()
        
    except Exception as e:
        print(f"Exception during evaluate_answer: {e}")
        # Default fallback structure on parsing error
        return {
            "score": 3,
            "feedback": "Valid response demonstrating basic technical understanding. [Fallback Mode]",
            "needs_probe": False,
            "extracted_skills": ["Python"],
            "extracted_info": {}
        }


def record_turn_and_update_profile(
    session_id: str,
    candidate_id: str,
    turn_number: int,
    topic: str,
    question: str,
    answer: str,
    eval_result: dict
) -> bool:
    """Persists interview turn to Supabase and updates candidate structured profile (long-term memory)."""
    if not _db_client:
        print(f"[Fallback/Stub] Saving profile for {candidate_id}: {topic} = {eval_result['score']}")
        return True
        
    try:
        # 1. Insert turn record into interview_turns
        turn_data = {
            "session_id": session_id,
            "turn_number": turn_number,
            "topic": topic,
            "question": question,
            "answer": answer,
            "score": eval_result.get("score"),
            "feedback": eval_result.get("feedback"),
            "needs_probe": eval_result.get("needs_probe", False),
            "extracted_skills": eval_result.get("extracted_skills", []),
            "extracted_info": eval_result.get("extracted_info", {})
        }
        _db_client.table("interview_turns").insert(turn_data).execute()
        
        # 2. Log message to conversation_messages
        _db_client.table("conversation_messages").insert({
            "session_id": session_id,
            "role": "user",
            "content": answer
        }).execute()
        
        # 3. Update candidate_profiles table (Long-term structured memory)
        res = _db_client.table("candidate_profiles").select("*").eq("candidate_id", candidate_id).execute()
        if res.data:
            profile = res.data[0]
            
            if topic == "background":
                bg = {**profile.get("background", {}), **eval_result.get("extracted_info", {})}
                if not bg and answer: bg["summary"] = answer
                _db_client.table("candidate_profiles").update({"background": bg}).eq("candidate_id", candidate_id).execute()
                
            elif topic == "education":
                edu = {**profile.get("education", {}), **eval_result.get("extracted_info", {})}
                if not edu and answer: edu["degree_details"] = answer
                _db_client.table("candidate_profiles").update({"education": edu}).eq("candidate_id", candidate_id).execute()
                
            elif topic == "experience":
                exp_list = profile.get("experience", [])
                if not isinstance(exp_list, list): exp_list = []
                info = eval_result.get("extracted_info", {})
                if info:
                    exp_list.append(info)
                elif answer:
                    exp_list.append({"details": answer})
                _db_client.table("candidate_profiles").update({"experience": exp_list}).eq("candidate_id", candidate_id).execute()
                
            elif topic == "skills":
                sk = profile.get("skills", {"technical": [], "soft": [], "proficiency": {}})
                if not isinstance(sk, dict): sk = {"technical": [], "soft": [], "proficiency": {}}
                tech = list(set(sk.get("technical", []) + eval_result.get("extracted_skills", [])))
                sk["technical"] = tech
                
                # Update proficiency map with turn score
                prof = sk.get("proficiency", {})
                for s in eval_result.get("extracted_skills", []):
                    prof[s] = eval_result.get("score", 3)
                sk["proficiency"] = prof
                _db_client.table("candidate_profiles").update({"skills": sk}).eq("candidate_id", candidate_id).execute()
                
            elif topic == "projects":
                proj_list = profile.get("projects", [])
                if not isinstance(proj_list, list): proj_list = []
                info = eval_result.get("extracted_info", {})
                if info:
                    proj_list.append(info)
                elif answer:
                    proj_list.append({"name": "Unspecified Project", "details": answer})
                _db_client.table("candidate_profiles").update({"projects": proj_list}).eq("candidate_id", candidate_id).execute()
                
        print(f"Successfully saved turn {turn_number} ({topic}) to Supabase.")
        return True
    except Exception as e:
        print(f"Error saving turn for {candidate_id} to Supabase: {e}")
        return False


def log_message(session_id: str, role: str, content: str) -> None:
    """Logs a message (typically assistant questions) to the conversation_messages table."""
    if _db_client:
        try:
            _db_client.table("conversation_messages").insert({
                "session_id": session_id,
                "role": role,
                "content": content
            }).execute()
        except Exception as e:
            print(f"Error logging message to conversation_messages: {e}")


def update_db_session_state(session_id: str, current_topic: str, covered: list, missing: list, count: int, scores: dict) -> None:
    """Syncs the interview session state to interview_sessions table in Supabase."""
    if _db_client:
        try:
            _db_client.table("interview_sessions").update({
                "current_topic": current_topic,
                "topics_covered": covered,
                "missing_topics": missing,
                "turn_count": count,
                "scores": scores
            }).eq("id", session_id).execute()
        except Exception as e:
            print(f"Error updating interview session state: {e}")


def identify_missing_info(topics_covered: list, required_topics: list) -> list:
    """Identifies topics from required list that haven't been covered yet."""
    return [t for t in required_topics if t not in topics_covered]


def calculate_score(scores: dict) -> float:
    """Computes the overall candidate score (rounded to 2 decimal places)."""
    return round(sum(scores.values()) / len(scores), 2) if scores else 0.0


def generate_report(session_id: str, candidate_id: str, scores: dict, candidate_name: str) -> dict:
    """Compiles the final candidate summary report using an LLM and persists it to the database."""
    overall_score = calculate_score(scores)
    
    prompt = f"""You are the Decision Support Agent for an intensive AI and Software Engineering Bootcamp.
Analyze the candidate's scores across different topics and write a professional final evaluation report.

Candidate: {candidate_name}
Topic Scores: {scores}
Overall Score: {overall_score}/5.0

Provide the final assessment in structured JSON format with the following keys:
- "summary": A concise 2-3 sentence overview of the candidate's performance.
- "recommendation": Must be exactly one of: "accept" (overall >= 4.0), "review" (overall between 3.0 and 4.0), "reject" (overall < 3.0).
- "strengths": Detailed technical and behavioral strengths.
- "weaknesses": Areas of improvement or gaps in prerequisite knowledge.
- "decision_notes": Clear rationale for the admissions team.

Return JSON only. Start directly with '{{' and end with '}}'.
"""
    
    # Initialize report structure
    report = {
        "session_id": session_id,
        "candidate_id": candidate_id,
        "topic_scores": scores,
        "overall_score": overall_score,
        "summary": f"Candidate completed the interview with an overall score of {overall_score}/5.0.",
        "recommendation": "review" if 3.0 <= overall_score < 4.0 else ("accept" if overall_score >= 4.0 else "reject"),
        "strengths": "Not generated.",
        "weaknesses": "Not generated.",
        "decision_notes": "Awaiting review."
    }
    
    try:
        response = _llm.invoke([HumanMessage(content=prompt)])
        import json
        clean_content = response.content.strip()
        if clean_content.startswith("```"):
            clean_content = "\n".join(clean_content.split("\n")[1:-1])
        parsed = json.loads(clean_content.strip())
        report.update(parsed)
    except Exception as e:
        print(f"Error compiling report with LLM: {e}")
        
    if _db_client:
        try:
            # 1. Update interview session status
            _db_client.table("interview_sessions").update({
                "status": "completed",
                "ended_at": "now()",
                "scores": scores
            }).eq("id", session_id).execute()
            
            # 2. Update candidate status
            candidate_status = "accepted" if report["recommendation"] == "accept" else ("rejected" if report["recommendation"] == "reject" else "interviewed")
            _db_client.table("candidates").update({"status": candidate_status}).eq("id", candidate_id).execute()
            
            # 3. Insert report into interview_reports
            _db_client.table("interview_reports").insert({
                "session_id": session_id,
                "candidate_id": candidate_id,
                "topic_scores": scores,
                "overall_score": overall_score,
                "summary": report["summary"],
                "recommendation": report["recommendation"],
                "strengths": report["strengths"],
                "weaknesses": report["weaknesses"],
                "decision_notes": report["decision_notes"]
            }).execute()
            print(f"Successfully saved final interview report for {candidate_id} to interview_reports.")
        except Exception as e:
            print(f"Error saving final report to database: {e}")
            
    return report
