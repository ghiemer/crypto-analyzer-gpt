# 🚀 Development Branch - Crypto Analyzer GPT

## 🔄 **Git Workflow**

### 🌟 **Branch Strategy**
```
main (Production) ← develop (Development) ← feature/bugfix branches
```

- **`main`**: Production-ready code, deployed to Render.com
- **`develop`**: Development branch for new features and testing
- **`feature/*`**: Individual feature development branches

### 📋 **Development Workflow**

1. **Neue Features entwickeln:**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/new-feature
   # ... development work ...
   git commit -m "✨ Add new feature"
   git push origin feature/new-feature
   ```

2. **Feature zu develop mergen:**
   ```bash
   git checkout develop
   git merge feature/new-feature
   git push origin develop
   ```

3. **Production Release:**
   ```bash
   git checkout main
   git merge develop
   git push origin main
   # Automatic Render deployment triggers
   ```

## 🛡️ **Safety Guidelines**

### ❌ **NIEMALS direkt zu main pushen**
- Alle Entwicklung erfolgt über `develop` Branch
- `main` Branch ist nur für Production Releases
- Features werden in separaten Branches entwickelt

### ✅ **Sichere Entwicklung:**
- `develop` Branch für alle neuen Features
- Tests lokal ausführen vor Push
- Code Review bei größeren Changes
- Environment Variables für verschiedene Umgebungen

## 🔧 **Development Setup**

### 🏃 **Quick Start:**
```bash
# Zu develop branch wechseln
git checkout develop

# Dependencies installieren
pip install -r requirements.txt

# Development server starten
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 📝 **Environment Configuration:**
```bash
# .env für Development
API_KEY=development_key_here
DATABASE_URL=postgresql://localhost:5432/crypto_dev
TG_BOT_TOKEN=your_dev_bot_token
ENVIRONMENT=development
DEBUG=true
```

## 🎯 **Current Development Focus**

Basierend auf der System-Analyse (`SYSTEM_ANALYSIS.md`):

1. **Alert System Konsolidierung** 
   - Legacy Alert System deaktivieren
   - Nur Simple Alert System verwenden

2. **Performance Optimierungen**
   - Cache Strategy verbessern
   - Rate Limiting implementieren

3. **Real-time Features**
   - WebSocket Integration
   - Live Price Updates

4. **Frontend Development**
   - Dashboard für bessere UX
   - Alert Management Interface

## 📊 **Testing Strategy**

### 🧪 **Local Testing:**
```bash
# API Tests
python -m pytest tests/

# Import Tests
python test_imports.py

# Manual API Testing
curl -H "X-API-Key: your_key" http://localhost:8000/health
```

### 🔍 **Production Verification:**
```bash
# Health Check
curl https://crypto-analyzer-gpt.onrender.com/health

# Service Status (with auth)
curl -H "X-API-Key: your_key" https://crypto-analyzer-gpt.onrender.com/status
```

## 📈 **Development Milestones**

- [x] **System Analysis** completed
- [x] **Security Cleanup** completed  
- [x] **Production Deployment** stable
- [ ] **Alert System Refactoring**
- [ ] **WebSocket Integration**
- [ ] **Performance Optimization**
- [ ] **Frontend Dashboard**

---

**Happy Coding! 🚀**

*Remember: develop → test → merge → deploy*
