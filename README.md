# AutoGraph - AI-Powered Diagramming Platform

Professional diagramming and technical documentation platform with AI generation, real-time collaboration, and enterprise features.

## 🎯 Project Overview

AutoGraph is a comprehensive diagramming platform that provides:

- **AI-Powered Diagram Generation** using OpenAI, Anthropic, and Google Gemini
- **Professional Canvas** with TLDraw 2.4.0 for drawing and diagramming
- **Diagram-as-Code** with Mermaid.js 11.4.0 (flowcharts, sequence diagrams, ERDs, etc.)
- **Real-Time Collaboration** with WebSocket-based cursor presence and live editing
- **Version History** with unlimited versions and visual diff
- **Enterprise Features** including SAML SSO, SCIM provisioning, audit logging
- **Eraserbot** for codebase analysis and automatic diagram generation
- **Integrations** with GitHub, GitLab, Azure DevOps, Notion, Confluence, Slack, Jira

## 🏗️ Architecture

### Microservices (10 Services)

1. **Frontend** (Next.js 15.1.0) - Port 3000
2. **API Gateway** (FastAPI) - Port 8080
3. **Auth Service** (FastAPI) - Port 8085
4. **Diagram Service** (FastAPI) - Port 8082
5. **AI Service** (FastAPI) - Port 8084
6. **Collaboration Service** (FastAPI + Socket.IO) - Port 8083
7. **Git Service** (FastAPI) - Port 8087
8. **Export Service** (FastAPI) - Port 8097
9. **Integration Hub** (FastAPI) - Port 8099
10. **SVG Renderer** (Node.js + Express) - Port 8096

### Infrastructure

- **PostgreSQL 16.6** - Primary database (12 tables)
- **Redis 7.4.1** - Sessions, cache, pub/sub
- **MinIO** - S3-compatible object storage

## 🚀 Quick Start

### Prerequisites

- Docker Desktop
- Node.js 20.18.0+
- Python 3.12.7+
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd autograph-v3
   ```

2. **Run the initialization script**
   ```bash
   ./init.sh
   ```

   This will:
   - Create `.env` file with configuration
   - Set up project directory structure
   - Start PostgreSQL, Redis, and MinIO containers
   - Verify all services are healthy

3. **Update API keys in `.env`**
   ```bash
   # Edit .env and add your API keys
   MGA_API_KEY=your-mga-api-key
   OPENAI_API_KEY=your-openai-api-key
   ANTHROPIC_API_KEY=your-anthropic-api-key
   ```

4. **Access the services**
   - Frontend: http://localhost:3000
   - API Gateway: http://localhost:8080
   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

## 📋 Development Workflow

### Feature Development

This project uses a **feature-driven development** approach with comprehensive test cases:

1. **Check `feature_list.json`** - Contains 679 detailed test cases
2. **Select a feature** with `"passes": false`
3. **Implement the feature** following the test steps
4. **Test thoroughly** - Manual browser testing + automated tests
5. **Mark as passing** - Change `"passes": false` to `"passes": true`
6. **Commit your work**

### Testing Requirements

Every feature MUST have:
- ✅ Playwright E2E test covering complete user flow
- ✅ Unit tests for business logic (80%+ coverage)
- ✅ Manual browser verification
- ✅ Zero console errors
- ✅ Performance check
- ✅ Accessibility validation (WCAG 2.1 AA)

### Running Tests

```bash
# E2E tests with Playwright
cd tests/e2e
npm test

# Backend unit tests
cd services/<service-name>
pytest

# Frontend unit tests
cd services/frontend
npm test

# Test coverage
pytest --cov=src --cov-report=html
```

## 🛠️ Technology Stack

### Frontend
- **Framework**: Next.js 15.1.0 with App Router
- **React**: 19.0.0
- **TypeScript**: 5.7.2 (strict mode)
- **Styling**: Tailwind CSS 3.4.15
- **UI Components**: Radix UI + shadcn/ui
- **State**: Zustand 5.0.1
- **Canvas**: TLDraw 2.4.0
- **Diagrams**: Mermaid.js 11.4.0
- **Code Editor**: Monaco Editor 0.52.0
- **Real-time**: Socket.IO client 4.8.0

### Backend
- **Language**: Python 3.12.7
- **Framework**: FastAPI 0.115.0
- **Server**: Uvicorn 0.32.0
- **Database**: PostgreSQL 16.6
- **ORM**: SQLAlchemy 2.0.36 + Alembic 1.14.0
- **Validation**: Pydantic 2.10.0
- **Cache**: Redis 7.4.1
- **Storage**: MinIO (S3-compatible)

### AI Providers
- OpenAI GPT-4 Turbo
- Anthropic Claude 3.5 Sonnet  
- Google Gemini Pro

## 📊 Feature Progress

Total Features: **679**

Feature breakdown:
- Infrastructure: 80 features
- Authentication & Authorization: 50 features
- Diagram Management: 50 features
- Canvas & Drawing (TLDraw): 100 features
- Diagram-as-Code (Mermaid): 50 features
- AI Generation: 75 features
- Real-Time Collaboration: 40 features
- Comments System: 30 features
- Version History: 30 features
- Export System: 35 features
- Enterprise Features: 40 features
- Organization & Discovery: 30 features
- UX & Performance: 35 features
- Bayer-Specific Features: 25 features
- Style & Polish: 30 features

Track progress in `feature_list.json`

## 🔐 Security

- **Authentication**: JWT with 1-hour access tokens, 30-day refresh tokens
- **Password Hashing**: bcrypt with cost factor 12
- **SAML SSO**: Microsoft Entra ID, Okta, OneLogin
- **MFA**: TOTP-based two-factor authentication
- **Rate Limiting**: 100 req/min per user, 1000 req/min per IP
- **Encryption**: TLS 1.3 in transit, AES-256 at rest
- **Audit Logging**: Comprehensive logging of all actions

## 🌐 API Documentation

Once services are running:
- **API Gateway**: http://localhost:8080/docs (Swagger UI)
- **Auth Service**: http://localhost:8085/docs
- **Diagram Service**: http://localhost:8082/docs
- **AI Service**: http://localhost:8084/docs

## 🐳 Docker Commands

```bash
# Start all infrastructure services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f postgres

# Restart a service
docker-compose restart redis

# Remove all data (WARNING: deletes volumes)
docker-compose down -v
```

## 📁 Project Structure

```
autograph-v3/
├── services/
│   ├── frontend/              # Next.js frontend
│   ├── api-gateway/           # FastAPI gateway
│   ├── auth-service/          # Authentication service
│   ├── diagram-service/       # Diagram CRUD
│   ├── ai-service/            # AI generation
│   ├── collaboration-service/ # Real-time WebSocket
│   ├── git-service/           # Git integration
│   ├── export-service/        # Export to PNG/SVG/PDF
│   ├── integration-hub/       # Third-party integrations
│   └── svg-renderer/          # SVG rendering (Node.js)
├── infrastructure/
│   ├── docker/                # Docker configs
│   ├── kubernetes/            # K8s manifests
│   └── terraform/             # Infrastructure as code
├── tests/
│   ├── e2e/                   # Playwright E2E tests
│   ├── integration/           # Integration tests
│   └── unit/                  # Unit tests
├── shared/
│   ├── types/                 # Shared TypeScript types
│   └── utils/                 # Shared utilities
├── docs/                      # Documentation
├── feature_list.json          # 679 test cases
├── init.sh                    # Setup script
├── docker-compose.yml         # Infrastructure services
└── README.md                  # This file
```

## 🧪 Quality Requirements

### Performance
- Initial load: < 2 seconds
- Time to interactive: < 3 seconds
- Canvas: 60 FPS with 1000+ elements
- API response: < 200ms p95
- Real-time latency: < 200ms

### Code Quality
- Test coverage: 80%+
- TypeScript: Strict mode, no `any`
- Python: Type hints, passes mypy
- Linting: Zero errors (ESLint, Ruff)
- Security: No vulnerabilities (Snyk, Trivy)

### Accessibility
- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader support
- Color contrast: 4.5:1 minimum

## 🤝 Contributing

1. Check `feature_list.json` for features with `"passes": false`
2. Implement the feature following the test steps
3. Write tests (E2E + unit)
4. Verify manually in browser
5. Update `"passes": true` in `feature_list.json`
6. Commit with descriptive message
7. Create pull request

## 📝 License

[Add license information]

## 🙏 Acknowledgments

- Uses TLDraw for professional canvas
- Built with modern web technologies
- Designed for enterprise use

## 📞 Support

For issues or questions:
- Check documentation in `/docs`
- Review `feature_list.json` for implementation details
- Check service logs: `docker-compose logs -f`

---

**Built with:** [cursor-autonomous-harness](https://github.com/nirmalarya/cursor-autonomous-harness) - Autonomous coding harness  
**Version:** 3.0.0  
**Status:** Production-ready
