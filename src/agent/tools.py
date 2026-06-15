import os
import uuid
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
try:
    from supabase import create_client, Client
except Exception as exc:
    create_client = None
    Client = object
    print(f"Supabase client import unavailable; using local fallback mode: {exc}")

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load variables from the project-root .env file, overriding any pre-existing environment variables.
load_dotenv(PROJECT_ROOT / ".env", override=True)

_supabase_url = os.environ.get("SUPABASE_URL")
_supabase_key = os.environ.get("SUPABASE_KEY")
_db_client: Client = None

if create_client and _supabase_url and _supabase_key and _supabase_key != "your_supabase_service_role_key_here":
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
                    "max_turns": min(max(int(prog.get("max_turns") or 30), 10), 30),
                    "min_turns": 10
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
        "min_turns": 10,
        "max_turns": 30
    }


openai_key = os.environ.get("OPENAI_API_KEY")
openrouter_key = os.environ.get("OPENROUTER_API_KEY")
openai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

OPENROUTER_MODELS = [
    "nex-agi/nex-n2-pro:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "openrouter/owl-alpha",
    "poolside/laguna-m.1:free",
    "poolside/laguna-xs.2:free",
    "nvidia/nemotron-3-super-120b-a12b:free"
]

def _configured_key(value: str | None) -> bool:
    return bool(value and value.strip() and not value.startswith("your_"))


def _make_openai_llm(temperature: float = 0.7):
    if not _configured_key(openai_key):
        return None

    return ChatOpenAI(
        model=openai_model,
        temperature=temperature,
        api_key=openai_key,
        timeout=30,
    )


def _make_openrouter_llm(temperature: float = 0.7):
    if not _configured_key(openrouter_key):
        return None

    instances = [
        ChatOpenAI(
            model=model_name,
            temperature=temperature,
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            timeout=20,
        )
        for model_name in OPENROUTER_MODELS
    ]
    return instances[0].with_fallbacks(instances[1:])


def _make_llm(temperature: float = 0.7):
    """Use OpenAI as the primary provider and OpenRouter only as fallback."""
    primary = _make_openai_llm(temperature)
    fallback = _make_openrouter_llm(temperature)

    if primary and fallback:
        return primary.with_fallbacks([fallback])
    if primary:
        return primary
    if fallback:
        return fallback

    return None


_llm = _make_llm(temperature=0.7)


def ensure_candidate_and_session(candidate_id: str, candidate_name: str, program_id: str = None) -> dict:
    """Ensures candidate, session, and profile exist in Supabase and returns verified UUIDs."""
    raw_candidate_id = candidate_id

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
                "email": raw_candidate_id if "@" in raw_candidate_id else f"{candidate_name.lower().replace(' ', '')}@example.com",
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
    """Generate a contextual structured interview question using an LLM, incorporating candidate profile context if available."""
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

    # Determine question types based on topic
    if topic in ["background", "education", "experience", "projects"]:
        allowed_types = ["open_ended", "multiple_choice", "true_false"]
        type_guideline = "The question type MUST be randomly chosen from 'open_ended', 'multiple_choice', or 'true_false'."
    else: # skills
        allowed_types = ["open_ended", "coding", "multiple_choice", "true_false"]
        type_guideline = "The question type MUST be randomly chosen from 'open_ended', 'coding', 'multiple_choice', or 'true_false'."

    system_prompt = (
        "You are an interviewer conducting a bootcamp admission interview. "
        "Generate exactly ONE structured question for the candidate in JSON format. "
        "Do not include any preamble, markdown code blocks, or extra text — only the raw JSON. "
        "The JSON must have the following keys:\n"
        f"- 'type': The type of the question. Valid values: " + ", ".join([f"'{t}'" for t in allowed_types]) + ".\n"
        "- 'text': The question text/description. For 'coding', it is the programming problem description.\n"
        "- 'options': A list of 4 options (for multiple_choice), ['True', 'False'] (for true_false). For others, it must be null.\n"
        "- 'initial_code': A Python template code snippet to be completed, debugged, or extended (for coding). For others, it must be null.\n"
        "- 'solution_test': A brief description of the expected output or test case (for coding). For others, it must be null."
    )

    asked_text = "\n".join(f"- {q}" for q in asked_so_far) if asked_so_far else "None yet."

    # Adaptive questioning: determine technical difficulty level from context
    scores = context.get("scores", {})
    bg_score = scores.get("background")
    is_experienced = bg_score is not None and bg_score >= 4
    
    if is_experienced:
        difficulty_guideline = "Since the candidate has high scores/strong background, generate an ADVANCED technical question requiring deep implementation details or complex problem-solving."
    else:
        difficulty_guideline = "Since the candidate is a beginner/student, generate a FOUNDATIONAL or ENTRY-LEVEL question assessing core programming concepts and basic database understanding."

    user_prompt = (
        f"Topic for this question: {topic}\n\n"
        f"Skills we need to assess: {', '.join(skills)}\n\n"
        f"Rubric for reference:\n"
        f"  Excellent: {rubric.get('excellent', 'N/A')}\n"
        f"  Good: {rubric.get('good', 'N/A')}\n"
        f"  Weak: {rubric.get('weak', 'N/A')}\n\n"
        f"{profile_context}"
        f"Questions already asked:\n{asked_text}\n\n"
        f"Difficulty Level Guideline:\n{difficulty_guideline}\n\n"
        f"{type_guideline}\n"
        "Coding questions should vary across tasks such as fixing a bug, completing a function, explaining output, or improving a naive implementation.\n"
        f"Generate a new, different question about '{topic}' that has NOT been asked yet.\n"
        f"Return ONLY valid JSON."
    )

    import json
    import random
    
    # Fallback generator for clean offline operations
    def make_fallback(topic_name):
        if topic_name == "background":
            stype = random.choice(["open_ended", "multiple_choice", "true_false"])
            if stype == "multiple_choice":
                return json.dumps({
                    "type": "multiple_choice",
                    "text": "Which background best matches your current preparation for an AI software bootcamp?",
                    "options": ["A) No programming exposure", "B) Basic Python or scripting experience", "C) Built several software or data projects", "D) Professional software or AI engineering experience"],
                    "initial_code": None,
                    "solution_test": None
                })
            if stype == "true_false":
                return json.dumps({"type": "true_false", "text": "True or False: Prior hands-on project work is useful preparation for an intensive AI bootcamp.", "options": ["True", "False"], "initial_code": None, "solution_test": None})
            return json.dumps({"type": "open_ended", "text": "Tell me about your background in software development and AI.", "options": None, "initial_code": None, "solution_test": None})
        elif topic_name == "education":
            return json.dumps({"type": "open_ended", "text": "What is your educational background, and how did it prepare you for this bootcamp?", "options": None, "initial_code": None, "solution_test": None})
        elif topic_name == "experience":
            return json.dumps({"type": "open_ended", "text": "Can you describe your professional experience working with software or data projects?", "options": None, "initial_code": None, "solution_test": None})
        elif topic_name == "projects":
            return json.dumps({"type": "open_ended", "text": "Tell me about a technical project you built. What was your role and what technologies did you use?", "options": None, "initial_code": None, "solution_test": None})
        else: # skills
            stype = random.choice(["open_ended", "coding", "multiple_choice", "true_false"])
            if stype == "coding":
                return json.dumps({
                    "type": "coding",
                    "text": "Complete the Python function `find_primes(n)` that returns a list of all prime numbers up to n.",
                    "options": None,
                    "initial_code": "def find_primes(n):\n    # Write your code here\n    pass",
                    "solution_test": "find_primes(10) == [2, 3, 5, 7]"
                })
            elif stype == "multiple_choice":
                return json.dumps({
                    "type": "multiple_choice",
                    "text": "Which of the following database query techniques retrieves data fastest for large tables?",
                    "options": ["A) Table scan", "B) Index scan/seek", "C) Nested loop join", "D) Full text search"],
                    "initial_code": None,
                    "solution_test": None
                })
            elif stype == "true_false":
                return json.dumps({
                    "type": "true_false",
                    "text": "Python's standard library `multiprocessing` allows true parallel thread execution on multi-core systems by bypassing the Global Interpreter Lock (GIL). True or False?",
                    "options": ["True", "False"],
                    "initial_code": None,
                    "solution_test": None
                })
            else:
                return json.dumps({
                    "type": "open_ended",
                    "text": "Explain how you would use Python to load a dataset, clean missing values, and train a simple machine learning model.",
                    "options": None,
                    "initial_code": None,
                    "solution_test": None
                })

    try:
        if _llm is None:
            raise RuntimeError("No LLM provider is configured.")

        response = _llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        content = response.content.strip()
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                content = "\n".join(lines[1:-1])
        data = json.loads(content)
        if "type" in data and "text" in data:
            return json.dumps(data)
        raise ValueError("Invalid format")
    except Exception as e:
        print(f"[Fallback Mode] generate_question LLM failed: {e}")
        return make_fallback(topic)


def generate_probe_question(topic: str, last_question: str, last_answer: str) -> str:
    """Generates a follow-up probing question to dig deeper into a weak or brief answer."""
    orig_q_text = last_question
    try:
        import json
        q_data = json.loads(last_question)
        if isinstance(q_data, dict) and "text" in q_data:
            orig_q_text = q_data["text"]
    except:
        pass

    system_prompt = (
        "You are a professional technical interviewer. The candidate gave a brief or weak answer "
        "to a previous question. Generate exactly ONE follow-up probe question to encourage "
        "the candidate to elaborate, provide specific technical details, or show examples. "
        "Do not include any preamble — only the question itself."
    )
    
    user_prompt = (
        f"Topic: {topic}\n"
        f"Previous Question: {orig_q_text}\n"
        f"Candidate Answer: {last_answer}\n\n"
        f"Generate a professional, natural follow-up question digging deeper into their response."
    )
    
    try:
        if _llm is None:
            raise RuntimeError("No LLM provider is configured.")

        response = _llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        q_text = response.content.strip()
    except Exception as e:
        print(f"[Fallback Mode] generate_probe_question LLM failed: {e}")
        q_text = f"That's interesting. Can you go into more detail about your response for {topic} and provide some specific examples?"

    import json
    return json.dumps({
        "type": "open_ended",
        "text": q_text,
        "options": None,
        "initial_code": None,
        "solution_test": None
    })


def evaluate_answer(question: str, answer: str, rubric: dict) -> dict:
    """
    Evaluates the candidate's answer against the technical bootcamp rubric,
    handling different question types (text, multiple_choice, true_false, coding).
    """
    if not answer or not answer.strip():
        return {
            "score": 1,
            "feedback": "The candidate did not provide any response to the question.",
            "needs_probe": False,
            "extracted_skills": [],
            "extracted_info": {}
        }

    import json
    q_text = question
    q_type = "text"
    q_options = None
    q_initial_code = None
    q_solution_test = None
    try:
        q_data = json.loads(question)
        if isinstance(q_data, dict) and "type" in q_data:
            q_text = q_data.get("text", "")
            q_type = q_data.get("type", "text")
            q_options = q_data.get("options")
            q_initial_code = q_data.get("initial_code")
            q_solution_test = q_data.get("solution_test")
    except:
        pass

    parser = PydanticOutputParser(pydantic_object=EvaluationResult)

    if q_type == "multiple_choice" or q_type == "true_false":
        system_prompt = f"""You are an elite, objective technical interviewer evaluating candidate answers for an intensive AI and Software Engineering Bootcamp.
Your goal is to parse the candidate's selection, evaluate if it is correct, and return a structured JSON object.

[CONTEXT]
Question Asked:
<question>
{q_text}
</question>

Options provided:
<options>
{q_options}
</options>

Candidate's Answer to Evaluate:
<candidate_answer>
{answer}
</candidate_answer>

Bootcamp Rubric Guidelines:
- Correct selection (Score 5): The candidate selected the correct option.
- Incorrect selection (Score 1): The candidate selected an incorrect option.

[STRICT EVALUATION INSTRUCTIONS]
1. Grading: Assign 5 for correct, 1 for incorrect.
2. Probing Flag ('needs_probe'): Must be `false` since MCQs/True-False do not need probing.
3. Skill Extraction: Scan the <question> and <candidate_answer> and extract explicit technical terms, frameworks, libraries, or architectural patterns mentioned.
4. Information Extraction ('extracted_info'): Extract key facts if any.
5. Critique Language: Write the 'feedback' completely in professional English, explaining why the selected option is correct or incorrect.

[CRITICAL OUTPUT FORMAT CONTRACT]
{parser.get_format_instructions()}

Strictly JSON only. Do NOT include any markdown code blocks. Start directly with the opening curly brace '{{' and end with the closing curly brace '}}'.
"""
    elif q_type == "likert_scale":
        system_prompt = f"""You are an elite, objective technical interviewer evaluating candidate answers for an intensive AI and Software Engineering Bootcamp.
Your goal is to parse the candidate's Likert scale self-assessment, evaluate the response, and return a structured JSON object.

[CONTEXT]
Question Asked:
<question>
{q_text}
</question>

Candidate's Selected Rating:
<candidate_answer>
{answer}
</candidate_answer>

Bootcamp Rubric Guidelines:
- Extract the numeric score (1 to 5) chosen by the candidate from their selection (e.g. "4 - Agree" means score is 4).
- If the answer has no number, default to 3.

[STRICT EVALUATION INSTRUCTIONS]
1. Grading: Assign the candidate's self-assessed score (integer from 1 to 5).
2. Probing Flag ('needs_probe'): Must be `false`.
3. Skill Extraction: Scan the <question> and extract any explicit technical terms or frameworks.
4. Critique Language: Write the 'feedback' completely in professional English, acknowledging their self-assessed proficiency level and how it relates to the bootcamp's expectations.

[CRITICAL OUTPUT FORMAT CONTRACT]
{parser.get_format_instructions()}

Strictly JSON only. Do NOT include any markdown code blocks. Start directly with the opening curly brace '{{' and end with the closing curly brace '}}'.
"""
    elif q_type == "coding":
        system_prompt = f"""You are an elite, objective technical interviewer evaluating candidate answers for an intensive AI and Software Engineering Bootcamp.
Your goal is to evaluate the candidate's submitted Python code for a programming exercise.

[CONTEXT]
Programming Problem:
<question>
{q_text}
</question>

Initial Code Template:
<initial_code>
{q_initial_code}
</initial_code>

Expected Test/Outcome:
<solution_test>
{q_solution_test}
</solution_test>

Candidate's Submitted Code:
<candidate_answer>
{answer}
</candidate_answer>

Bootcamp Rubric Guidelines:
- Excellent (Score 5): Clean, correct, well-structured code with correct logic and optimal time complexity.
- Good (Score 3-4): Code has minor logical issues, styling bugs, or sub-optimal complexity but functions.
- Weak (Score 1-2): Syntax errors, completely incorrect logic, or empty solution.

[STRICT EVALUATION INSTRUCTIONS]
1. Grading: Assign an integer from 1 to 5. Be fair but strict.
2. Probing Flag ('needs_probe'): Set this to `false` as coding exercises do not require probing.
3. Skill Extraction: Extract explicit technical terms, libraries, or patterns used (e.g. 'Python', 'List comprehension', 'Primes').
4. Information Extraction ('extracted_info'): Extract any key facts.
5. Critique Language: Write the 'feedback' in professional English, highlighting syntax correctness, clean structure, complexity, and how it can be improved.

[CRITICAL OUTPUT FORMAT CONTRACT]
{parser.get_format_instructions()}

Strictly JSON only. Do NOT include any markdown code blocks. Start directly with the opening curly brace '{{' and end with the closing curly brace '}}'.
"""
    else: # text
        system_prompt = f"""You are an elite, objective technical interviewer evaluating candidate answers for an intensive AI and Software Engineering Bootcamp.
Your absolute goal is to parse the candidate's response, map it to the strict rubric below, and return a structured JSON object.

[CONTEXT]
Question Asked:
<question>
{q_text}
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
3. Skill Extraction: Scan the <candidate_answer> and extract explicit technical terms, frameworks, libraries, or architectural patterns mentioned.
4. Information Extraction ('extracted_info'): Extract key facts from the candidate's response.
5. Critique Language: Write the 'feedback' completely in professional English.

[CRITICAL OUTPUT FORMAT CONTRACT]
{parser.get_format_instructions()}

Strictly JSON only. Do NOT include any markdown code blocks. Start directly with the opening curly brace '{{' and end with the closing curly brace '}}'.
"""

    try:
        eval_llm = _make_llm(temperature=0.0)
        if eval_llm is None:
            raise RuntimeError("No LLM provider is configured.")
        
        response = eval_llm.invoke([HumanMessage(content=system_prompt)])
        content = response.content.strip()
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                content = "\n".join(lines[1:-1])
        parsed_result = parser.parse(content)
        return parsed_result.model_dump()
        
    except Exception as e:
        print(f"[Fallback Mode] evaluate_answer LLM failed: {e}")
        words = answer.strip().split()
        word_count = len(words)
        
        keywords = ["python", "sql", "javascript", "react", "streamlit", "machine learning", "ml", "ai", "pandas", "numpy", "scikit-learn", "git", "postgre", "database", "supabase", "html", "css", "django", "fastapi", "pyspark", "spark", "redis", "pytorch", "tensorflow", "keras", "yolo", "aws", "docker", "github", "langgraph", "langchain", "faiss"]
        extracted = []
        for kw in keywords:
            if kw in answer.lower():
                fmt = kw.capitalize() if kw not in ["sql", "ml", "ai", "html", "css", "git", "aws"] else kw.upper()
                if kw == "scikit-learn":
                    fmt = "Scikit-Learn"
                elif kw == "langgraph":
                    fmt = "LangGraph"
                elif kw == "langchain":
                    fmt = "LangChain"
                extracted.append(fmt)
                
        if q_type == "multiple_choice" or q_type == "true_false":
            is_correct = False
            if q_type == "true_false":
                if "true" in answer.lower() and "false" not in answer.lower():
                    is_correct = True
            else:
                if "b" in answer.lower() or "index" in answer.lower():
                    is_correct = True
            
            return {
                "score": 5 if is_correct else 1,
                "feedback": f"Your selected answer is correct. [Fallback Mode]" if is_correct else f"Your selected answer is incorrect. [Fallback Mode]",
                "needs_probe": False,
                "extracted_skills": extracted,
                "extracted_info": {}
            }
        elif q_type == "likert_scale":
            import re
            match_digit = re.search(r'\d', answer)
            score_val = int(match_digit.group()) if match_digit else 3
            if not (1 <= score_val <= 5):
                score_val = 3
            return {
                "score": score_val,
                "feedback": f"Thank you for rating your proficiency. Your self-assessed level is {score_val}/5. [Fallback Mode]",
                "needs_probe": False,
                "extracted_skills": extracted,
                "extracted_info": {}
            }
        elif q_type == "coding":
            has_syntax_error = False
            syntax_error_msg = ""
            try:
                compile(answer, "<string>", "exec")
            except Exception as se:
                has_syntax_error = True
                syntax_error_msg = str(se)
            
            if has_syntax_error:
                return {
                    "score": 2,
                    "feedback": f"Your code has syntax errors: {syntax_error_msg}. Please fix the syntax. [Fallback Mode]",
                    "needs_probe": False,
                    "extracted_skills": extracted,
                    "extracted_info": {}
                }
            else:
                return {
                    "score": 5 if len(answer) > 20 else 3,
                    "feedback": "Your Python code compiles successfully and looks correct! [Fallback Mode]",
                    "needs_probe": False,
                    "extracted_skills": extracted,
                    "extracted_info": {}
                }
        else:
            if word_count < 10:
                return {
                    "score": 2,
                    "feedback": "Your response is quite brief. Could you elaborate and provide more detail about your experience? [Fallback Mode]",
                    "needs_probe": True,
                    "extracted_skills": extracted if extracted else ["Python"],
                    "extracted_info": {}
                }
            elif word_count < 20:
                return {
                    "score": 3,
                    "feedback": "Good response, but providing more specific examples would be helpful. [Fallback Mode]",
                    "needs_probe": False,
                    "extracted_skills": extracted if extracted else ["Python"],
                    "extracted_info": {}
                }
            else:
                score = 5 if extracted else 4
                return {
                    "score": score,
                    "feedback": "Excellent detailed response! [Fallback Mode]" if score == 5 else "Good response with reasonable details. [Fallback Mode]",
                    "needs_probe": False,
                    "extracted_skills": extracted if extracted else ["Python"],
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
        if _llm is None:
            raise RuntimeError("No LLM provider is configured.")

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
