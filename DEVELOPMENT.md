# Continuity Stack - Development Guide

## Local Development Setup

### Backend Development

1. **Setup Python environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Start Neo4j (via Docker):**
   ```bash
   docker-compose up neo4j -d
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env if needed for local development
   ```

4. **Run the backend:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

5. **Access API documentation:**
   - Interactive docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### Frontend Development

1. **Setup Node.js environment:**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local if backend is on different URL
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Access the UI:**
   - Frontend: http://localhost:3000

### Running Tests

**Backend tests:**
```bash
cd backend
pytest -v                        # All tests
pytest test_continuity_core.py   # Core tests only
pytest test_memmachine.py        # MemMachine tests only
```

**Test coverage:**
```bash
cd backend
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

## Code Structure

### Backend Structure
```
backend/
├── main.py                 # FastAPI application & endpoints
├── continuity_core.py      # Self-reflecting agent logic
├── memmachine.py          # Persistent memory system
├── neo4j_client.py        # Graph database client
├── test_*.py              # Test files
├── requirements.txt       # Python dependencies
└── Dockerfile            # Backend container config
```

### Frontend Structure
```
frontend/
├── pages/
│   ├── index.tsx         # Main page with tabs
│   ├── _app.tsx          # App wrapper
│   └── _document.tsx     # HTML document
├── components/
│   ├── ChatInterface.tsx      # Chat UI component
│   ├── ProfileTimeline.tsx    # Timeline view
│   └── DemoScenario.tsx       # Demo runner
├── lib/
│   └── api.ts            # API client functions
├── styles/
│   └── globals.css       # Global styles
└── package.json          # Dependencies
```

## Adding New Features

### Adding a New API Endpoint

1. **Define Pydantic model in `main.py`:**
   ```python
   class MyRequest(BaseModel):
       field1: str
       field2: int
   ```

2. **Add endpoint:**
   ```python
   @app.post("/api/my-endpoint")
   async def my_endpoint(request: MyRequest):
       # Your logic here
       return {"result": "success"}
   ```

3. **Add to API client (`frontend/lib/api.ts`):**
   ```typescript
   async myEndpoint(data: MyRequest) {
     const response = await api.post('/api/my-endpoint', data);
     return response.data;
   }
   ```

### Adding a New Reflection Pattern

Edit `continuity_core.py` in the `Reflection.analyze_failure()` method:

```python
elif "new_pattern" in str(self.error).lower():
    self.lesson_learned = "Lesson about the new pattern"
    self.improvement_strategy = "How to handle it next time"
```

### Adding a New Graph Relationship

1. **Update Neo4j schema in `neo4j_client.py`:**
   ```python
   def create_new_relationship(self, from_id, to_id):
       query = """
       MATCH (a {id: $from_id}), (b {id: $to_id})
       CREATE (a)-[:NEW_RELATIONSHIP]->(b)
       """
       with self.driver.session() as session:
           session.run(query, from_id=from_id, to_id=to_id)
   ```

2. **Add API endpoint in `main.py`**

3. **Document in `CYPHER_QUERIES.md`**

### Adding a New UI Component

1. **Create component file:**
   ```bash
   touch frontend/components/MyComponent.tsx
   ```

2. **Implement component:**
   ```typescript
   export default function MyComponent() {
     return <div>My Component</div>;
   }
   ```

3. **Import in page:**
   ```typescript
   import MyComponent from '../components/MyComponent';
   ```

## Debugging

### Backend Debugging

**View logs:**
```bash
docker-compose logs -f backend
```

**Check specific endpoint:**
```bash
curl -X GET http://localhost:8000/api/agent/status | jq
```

**Interactive debugging:**
Add `import pdb; pdb.set_trace()` in Python code and run directly (not in Docker).

### Frontend Debugging

**View console:**
Open browser DevTools (F12) → Console tab

**Check API calls:**
DevTools → Network tab → XHR filter

**React DevTools:**
Install React DevTools browser extension

### Neo4j Debugging

**Browse data:**
1. Open http://localhost:7474
2. Login (neo4j/continuity123)
3. Run Cypher queries

**Check connections:**
```bash
docker-compose exec neo4j cypher-shell -u neo4j -p continuity123
```

**View logs:**
```bash
docker-compose logs -f neo4j
```

## Performance Optimization

### Backend Optimization

1. **Add caching:**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def expensive_function(param):
       pass
   ```

2. **Async operations:**
   Already using async/await in FastAPI

3. **Database connection pooling:**
   Neo4j driver handles this automatically

### Frontend Optimization

1. **React.memo for components:**
   ```typescript
   export default React.memo(MyComponent);
   ```

2. **Debounce API calls:**
   ```typescript
   import { debounce } from 'lodash';
   ```

3. **Code splitting:**
   ```typescript
   const MyComponent = dynamic(() => import('../components/MyComponent'));
   ```

## Environment Variables

### Backend (.env)
```bash
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=continuity123
MEMMACHINE_PATH=./memmachine_data
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Troubleshooting

### "Module not found" errors

**Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
rm -rf node_modules package-lock.json
npm install
```

### Docker issues

**Rebuild containers:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

**Clean Docker:**
```bash
docker system prune -a
```

### Neo4j won't start

1. Check ports 7474 and 7687 are available
2. Check disk space
3. Remove `neo4j_data` and restart

### Frontend build errors

```bash
cd frontend
rm -rf .next
npm run build
```

## Git Workflow

1. **Create feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and test**

3. **Commit with clear message:**
   ```bash
   git add .
   git commit -m "Add: description of feature"
   ```

4. **Push and create PR:**
   ```bash
   git push origin feature/my-feature
   ```

## Production Deployment

### Build Production Images

```bash
docker-compose -f docker-compose.prod.yml build
```

### Environment Configuration

1. Update Neo4j password
2. Add authentication to API
3. Configure CORS properly
4. Use environment-specific .env files
5. Set up SSL/TLS

### Health Checks

Monitor these endpoints:
- Backend: `/health`
- Neo4j: Port 7474 HTTP
- Frontend: Root path `/`

## Useful Commands

```bash
# View all containers
docker-compose ps

# View logs
docker-compose logs -f [service]

# Restart a service
docker-compose restart [service]

# Execute command in container
docker-compose exec backend python
docker-compose exec neo4j cypher-shell

# Clean up everything
docker-compose down -v
rm -rf memmachine_data neo4j_data neo4j_logs

# Run tests in Docker
docker-compose exec backend pytest -v

# Access Neo4j shell
docker-compose exec neo4j cypher-shell -u neo4j -p continuity123
```

## Best Practices

1. **Always write tests** for new features
2. **Document API changes** in README
3. **Use type hints** in Python
4. **Use TypeScript** in frontend
5. **Add error handling** for all API calls
6. **Log important events** for debugging
7. **Keep components small** and focused
8. **Use environment variables** for config
9. **Never commit secrets** or credentials
10. **Review code** before committing
