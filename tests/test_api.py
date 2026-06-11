"""
test_api.py - Test all API endpoints
Run with: python test_api.py
"""
import requests
import json

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def print_response(title, response):
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_health():
    print("\n🔍 Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print_response("Health Check", response)
    return response.status_code == 200

def test_root():
    print("\n🔍 Testing Root Endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print_response("Root Endpoint", response)
    return response.status_code == 200

def test_candidate_verify():
    print("\n🔍 Testing Candidate Verification...")
    response = requests.post(
        f"{API_URL}/candidates/verify",
        json={"email": "ahmed@example.com"}
    )
    print_response("Candidate Verification", response)
    return response

def test_get_all_candidates():
    print("\n🔍 Testing Get All Candidates...")
    response = requests.get(f"{API_URL}/candidates")
    print_response("All Candidates", response)
    return response

def test_recruiter_login():
    print("\n🔍 Testing Recruiter Login...")
    response = requests.post(
        f"{API_URL}/recruiter/login",
        json={"email": "admin@example.com", "password": "12345"}
    )
    print_response("Recruiter Login", response)
    return response

def test_interview_flow():
    print("\n🔍 Testing Interview Flow...")
    
    # 1. Start interview
    print("\n📝 Step 1: Starting interview...")
    response = requests.post(
        f"{API_URL}/interview/start",
        json={
            "candidate_name": "Ahmed Al-Rashidi",
            "candidate_email": "ahmed@example.com"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to start interview: {response.text}")
        return
    
    session_data = response.json()
    session_id = session_data["session_id"]
    print(f"✅ Session created: {session_id}")
    print(f"📝 First question: {session_data['first_question']}")
    
    # 2. Submit first answer
    print("\n📝 Step 2: Submitting first answer...")
    response = requests.post(
        f"{API_URL}/interview/answer",
        json={
            "session_id": session_id,
            "answer": "I am a software engineer with 5 years of experience in Python and AI."
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to submit answer: {response.text}")
        return
    
    answer_data = response.json()
    print(f"✅ Answer submitted")
    print(f"📊 Score: {answer_data.get('score', 'N/A')}")
    print(f"💬 Feedback: {answer_data.get('feedback', 'N/A')}")
    
    if not answer_data.get("is_complete"):
        print(f"📝 Next question: {answer_data['next_question']}")
    
    # 3. Check session status
    print("\n📝 Step 3: Checking session status...")
    response = requests.get(f"{API_URL}/interview/session/{session_id}")
    
    if response.status_code == 200:
        status_data = response.json()
        print(f"✅ Session status retrieved")
        print(f"📊 Question: {status_data.get('question_number', 0)}/{status_data.get('total_questions', 0)}")
        print(f"📈 Average score: {status_data.get('average_score', 0):.1f}%")
    
    return session_id

def test_candidate_by_name(candidate_name="Ahmed Al-Rashidi"):
    print(f"\n🔍 Testing Get Candidate by Name: {candidate_name}...")
    response = requests.get(f"{API_URL}/candidates/{candidate_name}")
    print_response(f"Candidate: {candidate_name}", response)
    return response

def run_all_tests():
    print("\n" + "="*60)
    print("🚀 STARTING API TESTS")
    print("="*60)
    
    # First check if backend is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Backend is not running!")
        print("Please start the backend first:")
        print("  uvicorn backend.main:app --reload --port 8000")
        return
    
    tests = [
        ("Health Check", test_health),
        ("Root Endpoint", test_root),
        ("Candidate Verification", test_candidate_verify),
        ("Get All Candidates", test_get_all_candidates),
        ("Get Candidate by Name", lambda: test_candidate_by_name("Ahmed Al-Rashidi")),
        ("Recruiter Login", test_recruiter_login),
        ("Interview Flow", test_interview_flow),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, True, None))
        except Exception as e:
            results.append((name, False, str(e)))
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for name, passed, error in results:
        if passed:
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {error}")
    
    print("="*60)

if __name__ == "__main__":
    run_all_tests()