# tests/fixtures/personas.py
"""
Candidate personas for scenario testing
"""

from typing import Dict, Any

class CandidatePersonas:
    """Three candidate personas as defined in README"""
    
    @staticmethod
    def strong_candidate() -> Dict[str, Any]:
        """
        Strong Candidate:
        - Provides detailed, high-quality responses on first try
        - No probing needed
        """
        return {
            "name": "Strong Candidate",
            "email": "strong@example.com",
            "type": "strong",
            "responses": {
                "background": "I have a Master's in Computer Science and 5 years of industry experience.",
                "skills": "Python, TensorFlow, PyTorch, Docker, Kubernetes, AWS.",
                "projects": "Built a recommendation system serving 1M+ users with 40% engagement increase.",
                "experience": "Lead ML Engineer at TechCorp, built production ML pipelines.",
                "education": "M.S. in CS from Stanford, GPA 3.9."
            },
            "default_response": "I have extensive experience in this area with proven results."
        }
    
    @staticmethod
    def improving_candidate() -> Dict[str, Any]:
        """
        Improving Candidate:
        - Starts vague/brief
        - When probed, provides detailed responses
        """
        return {
            "name": "Improving Candidate",
            "email": "improving@example.com",
            "type": "improving",
            "responses": {
                "background": "I'm a developer with some experience.",
                "skills": "Python, some ML.",
                "projects": "Worked on some projects.",
                "experience": "Junior developer.",
                "education": "CS degree."
            },
            "detailed_responses": {
                "background": "I have a Bachelor's in CS and 3 years of experience building web apps.",
                "skills": "Python, Pandas, Scikit-learn, FastAPI, and have deployed ML models.",
                "projects": "Built a predictive maintenance system for manufacturing equipment.",
                "experience": "Worked on multiple projects using ML and data analysis.",
                "education": "B.S. in Computer Science."
            },
            "default_response": "I have some experience in this area."
        }
    
    @staticmethod
    def weak_candidate() -> Dict[str, Any]:
        """
        Weak Candidate:
        - Fails to provide details initially and when probed
        - Forces max probes
        """
        return {
            "name": "Weak Candidate",
            "email": "weak@example.com",
            "type": "weak",
            "responses": {
                "background": "I know some programming.",
                "skills": "Python.",
                "projects": "I've done some things.",
                "experience": "I worked somewhere.",
                "education": "I went to school."
            },
            "default_response": "I don't really know much about that."
        }
    
    @staticmethod
    def get_persona(persona_type: str) -> Dict[str, Any]:
        """Get a persona by type"""
        personas = {
            "strong": CandidatePersonas.strong_candidate,
            "improving": CandidatePersonas.improving_candidate,
            "weak": CandidatePersonas.weak_candidate
        }
        return personas[persona_type]()