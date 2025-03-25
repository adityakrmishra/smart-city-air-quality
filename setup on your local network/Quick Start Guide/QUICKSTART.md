## 5-Minute Setup

1. Clone repository
```bash
git clone https://github.com/adityakrmishra/smart-city-air-quality
cd smart-city-air-quality
```
2. Install dependencies
 ```
python -m venv .env && source .env/bin/activate
pip install -r requirements.txt
```
3. Start services
   ```
   chmod +x run.sh test_system.sh
   ./run.sh
   ```


## Key Endpoints
- API Docs: http://localhost:8000/docs

- Dashboard: http://localhost:3000

- Grafana: http://localhost:4000


---

### **5. Service Health Check**
**File:** `backend/api/health.py**
```
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "OK",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": check_postgres(),
            "kafka": check_kafka(),
            "blockchain": check_fabric()
        }
    }

def check_postgres():
    # Implementation
    return {"status": "up"}

def check_kafka():
    # Implementation 
    return {"status": "up"}

def check_fabric():
    # Implementation
    return {"status": "up"}
   ```

6. Commit Structure
7. ```
   # Initial setup
git add requirements.txt .env.template run.sh test_system.sh
git commit -m "feat: Add core execution infrastructure" 

```
# Health monitoring
git add backend/api/health.py
git commit -m "feat: Add system health check endpoint"

# Documentation
git add QUICKSTART.md
git commit -m "docs: Add 5-minute quickstart guide"
```

7. Final Directory Structure
smart-city-air-quality/
├── run.sh
├── test_system.sh
├── .env.template
├── QUICKSTART.md
├── requirements.txt
├── devops/
│   └── docker-compose.*.yml
└── backend/
    └── api/
        └── health.py

        
