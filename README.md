# this is a basic readme file 
#### API Endpoints
| Endpoint | Method | Status |
|----------|--------|--------|
| `/health` | GET | ✅ Working |
| `/api/candidates/verify` | POST | ✅ Working |
| `/api/candidates` | GET | ✅ Working |
| `/api/candidates/{name}` | GET | ✅ Working |
| `/api/recruiter/login` | POST | ✅ Working |
| `/api/interview/start` | POST | ✅ Working |
| `/api/interview/answer` | POST | ✅ Working |
| `/api/interview/session/{id}` | GET | ✅ Working |

# running app
# Start backend
`uvicorn backend.main:app --reload --port 8000`

# Start frontend (new terminal)
`streamlit run streamlit/app.py`


