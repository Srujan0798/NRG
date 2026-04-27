# 🚀 NRG Dashboard is LIVE!

## 🌐 Access URLs

| Service | URL | Status |
|---------|-----|--------|
| **Dashboard** | http://localhost:3000 | ✅ RUNNING |
| **API** | http://localhost:8000 | ✅ RUNNING |
| **API Docs** | http://localhost:8000/docs | ✅ Available |
| **API Health** | http://localhost:8000/health | ✅ Healthy |

---

## 👤 Login Credentials

Click any persona button on the login page:

| Persona | Username | Password |
|---------|----------|----------|
| 🔬 Researcher | `researcher_user` | `researcher-pass` |
| 🏛️ Government | `gov_user` | `gov-pass` |
| 🏭 Industry | `industry_user` | `industry-pass` |

---

## 📊 Dashboard Features

### Researcher Dashboard
- Search researchers by state/research area
- View publication lists
- Research collaboration network

### Government Dashboard
- Aggregate statistics
- State-wise researcher distribution
- Research trend analytics

### Industry Dashboard
- Lab partnerships
- Technology transfer opportunities
- Expert finder

---

## 🧪 Quick Test

```bash
# Test API directly
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}'

# Test query
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"find robotics researchers in Gujarat"}'
```

---

## 🛑 To Stop

```bash
# Stop API
kill $(lsof -ti:8000)

# Stop Frontend
kill $(lsof -ti:3000)
```

---

## System Status

- ✅ Database: 200 researchers, 500 publications
- ✅ JWT Auth: RS256 with key files
- ✅ Text-to-SQL: Working with SQLite
- ✅ NVIDIA LLM: meta/llama-3.1-70b-instruct
- ✅ Audit Chain: HMAC-SHA256
- ✅ Relations: 689 RP, 1202 PK, 278 RL

---

**Open http://localhost:3000 in your browser NOW! 🎉**
