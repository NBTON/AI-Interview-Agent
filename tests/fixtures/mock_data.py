# tests/fixtures/mock_data.py
"""Mock data for testing"""

class MockData:
    """Mock data fixtures"""
    
    @staticmethod
    def candidate():
        return {
            "name": "Mock Candidate",
            "email": "mock@example.com"
        }
    
    @staticmethod
    def mcq_question():
        return {
            "type": "multiple_choice",
            "text": "Which is a Python framework?",
            "options": ["Django", "React", "Angular", "Vue"],
            "correct": "Django"
        }
    
    @staticmethod
    def scoring_result():
        return {
            "score": 4,
            "feedback": "Good answer!",
            "needs_probe": False,
            "extracted_skills": ["Python", "Django"],
            "extracted_info": {}
        }