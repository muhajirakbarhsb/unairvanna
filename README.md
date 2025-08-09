# 🎓 UnAIRvanna - University LangGraph AI System

> **Intelligent Multi-Agent University Data Analysis System**  
> Combining LangGraph workflows, Vanna AI, and Google Gemini for natural language database queries

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.5.3-green.svg)](https://github.com/langchain-ai/langgraph)
[![Chainlit](https://img.shields.io/badge/Chainlit-1.0.504-purple.svg)](https://chainlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://postgresql.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Latest-red.svg)](https://qdrant.tech/)

## 🌟 **Features**

### 🤖 **Multi-Agent Architecture**
- **Router Agent**: Intelligently classifies questions and determines optimal workflow paths
- **SQL Agent**: Generates and executes PostgreSQL queries using Vanna AI
- **Strategy Agent**: Provides educational strategies and recommendations
- **Insight Agent**: Analyzes data patterns and generates actionable insights
- **Visualization Agent**: Recommends appropriate charts and visualizations
- **Suggestion Agent**: Creates relevant follow-up questions
- **Summarizer Agent**: Synthesizes results into comprehensive summaries

### 🎯 **Smart Query Classification**
- **Data Queries**: Statistical analysis, counts, comparisons
- **Trend Analysis**: Time-series analysis and patterns
- **Complex Analysis**: Multi-table joins and advanced analytics
- **Strategy Questions**: Educational best practices and recommendations

### 🚀 **Technology Stack**
- **LangGraph**: Advanced workflow orchestration with conditional routing
- **Vanna AI**: Natural language to SQL translation with vector similarity
- **Google Gemini**: State-of-the-art language model for analysis
- **Qdrant**: High-performance vector database for semantic search
- **PostgreSQL**: Robust relational database with Indonesian university schema
- **Chainlit**: Modern conversational AI interface

## 📁 **Project Structure**

```
unairvanna/
├── 📱 app/
│   └── main.py              # Chainlit web application
├── 🔧 src/
│   ├── agents/
│   │   ├── langgraph_system.py  # Multi-agent LangGraph workflow
│   │   └── __init__.py
│   ├── vanna/
│   │   ├── setup.py         # Vanna + Gemini + Qdrant integration
│   │   ├── training.py      # Training data and examples
│   │   ├── feedback.py      # Feedback management system
│   │   └── __init__.py
│   ├── database/
│   │   ├── populate.py      # Sample data generation
│   │   └── __init__.py
│   └── __init__.py
├── 🐳 docker/
│   ├── postgres-init.sql    # Database schema initialization
│   ├── postgresql.conf      # PostgreSQL configuration
│   └── qdrant.yaml         # Qdrant vector DB configuration
├── 📊 scripts/
│   ├── generate_graph.py    # LangGraph visualization generator
│   └── manage_feedback.py   # Feedback management utilities
├── 🔧 Configuration Files
│   ├── Dockerfile           # Container configuration
│   ├── docker-compose.yml   # Multi-service orchestration
│   ├── pyproject.toml       # Python dependencies & project config
│   ├── uv.lock             # Dependency lock file
│   └── README.md           # This file
```

## 🚀 **Quick Start**

### 1️⃣ **Prerequisites**
```bash
# Required software
- Docker & Docker Compose
- Git
```

### 2️⃣ **Clone & Setup**
```bash
git clone https://github.com/muhajirakbarhsb/unairvanna.git
cd unairvanna

# Create environment file
touch .env
```

### 3️⃣ **Environment Variables**
Edit `.env` file:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4️⃣ **Docker Commands**

**First time (complete setup):**
```bash
docker-compose --profile full up -d
```

**Run app only (after training):**
```bash
docker-compose --profile app up -d
```

**Development mode:**
```bash
docker-compose -f docker-compose.dev.yml up app-dev
```

**Step by step:**
```bash
# Infrastructure only
docker-compose up -d postgres qdrant

# Populate database
docker-compose --profile init up db-init

# Train AI (once)
docker-compose --profile train up vanna-trainer

# Start app
docker-compose --profile app up -d
```

**With database admin:**
```bash
docker-compose --profile app --profile admin up -d
```

### 🎉 **Access**
- App: **http://localhost:8000**
- PgAdmin: **http://localhost:8080**

## 🔧 **Configuration**

### 📊 **Database Configuration**
```bash
# PostgreSQL Settings
POSTGRES_DB=university_dwh
POSTGRES_USER=postgres
POSTGRES_PASSWORD=university123
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Database URL
DATABASE_URL=postgresql://postgres:university123@localhost:5432/university_dwh
```

### 🔍 **Vector Database (Qdrant)**
```bash
# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=qdrant123
QDRANT_URL=http://localhost:6333
```

### 🤖 **AI Model Settings**
```bash
# Vanna + Gemini Configuration
VANNA_MODEL=gemini-2.0-flash-exp
VANNA_TEMPERATURE=0.1
VANNA_MAX_TOKENS=2000
VANNA_COLLECTION_NAME=university_sql_collection
```

### 🏫 **University Settings**
```bash
# University Information
UNIVERSITY_NAME=Universitas Indonesia Raya
UNIVERSITY_CODE=UIR
CURRENT_ACADEMIC_YEAR=2024/2025
```

## 💬 **Usage Examples**

### 📊 **Data Analysis Questions**
```
✅ "Berapa jumlah mahasiswa aktif per fakultas?"
✅ "Siapa mahasiswa dengan IPK tertinggi?"
✅ "Bandingkan rata-rata IPK tahun 2023 vs 2024"
✅ "Analisis trend pembayaran SPP 3 semester terakhir"
```

### 📈 **Trend Analysis**
```
✅ "Bagaimana trend kehadiran mahasiswa semester ini?"
✅ "Perkembangan jumlah mahasiswa baru 5 tahun terakhir"
✅ "Analisis performa akademik per program studi"
```

### 🎯 **Strategic Questions**
```
✅ "Bagaimana meningkatkan tingkat kehadiran mahasiswa?"
✅ "Strategi untuk meningkatkan IPK program studi"
✅ "Rekomendasi pengelolaan keuangan mahasiswa"
```

### 🔍 **Complex Analysis**
```
✅ "Korelasi antara kehadiran dan nilai akhir mahasiswa"
✅ "Analisis prediktif risiko dropout mahasiswa"
✅ "Efektivitas metode pembayaran SPP"
```

## 🏗️ **Architecture Overview**

### 🔄 **LangGraph Workflow Visualization**

![LangGraph Workflow](langgraph_workflow_20250720_182238.png)

*Complete LangGraph multi-agent workflow generated from the actual system*

### 📊 **Workflow Description**
```mermaid
graph TD
    A[User Question] --> B[Router Agent]
    B -->|Data Query| C[SQL Agent]
    B -->|Strategy Question| D[Strategy Agent]
    
    C --> E[Insight Agent]
    E -->|Needs Viz| F[Visualization Agent]
    E -->|No Viz| G[Suggestion Agent]
    F --> G
    
    D --> H[Strategy Suggestion Agent]
    
    G --> I[Summarizer Agent]
    H --> I
    I --> J[Final Response]
```

> 💡 **Generate Your Own Workflow Diagram:**
> ```bash
> # Generate updated workflow visualization
> python scripts/generate_graph.py
> ```

### 🤖 **Agent Responsibilities**

| Agent | Purpose | Input | Output |
|-------|---------|-------|--------|
| **Router** | Query classification & routing | User question | Query type + routing decision |
| **SQL** | Database query generation & execution | Natural language question | SQL query + results |
| **Strategy** | Educational recommendations | Strategy questions | Actionable recommendations |
| **Insight** | Data pattern analysis | Query results | Business insights |
| **Visualization** | Chart recommendations | Data structure | Visualization suggestions |
| **Suggestion** | Follow-up questions | Analysis context | Relevant next questions |
| **Summarizer** | Final synthesis | All agent outputs | Comprehensive summary |

## 📊 **Database Schema**

### 🏛️ **Dimension Tables**
- **`dim_fakultas`**: Faculties (Engineering, Business, Computer Science)
- **`dim_program_studi`**: Study programs with accreditation info
- **`dim_dosen`**: Lecturers with qualifications and status
- **`dim_mata_kuliah`**: Courses with credits and semester info
- **`dim_mahasiswa`**: Students with GPA and enrollment status
- **`dim_semester`**: Academic semesters with date ranges

### 📈 **Fact Tables**
- **`fact_nilai`**: Student grades with letter grades and GPA
- **`fact_kehadiran`**: Attendance records with percentages
- **`fact_pembayaran_spp`**: Tuition payments and status

## 🛠️ **Development**

### 🔨 **Adding New Agents**
```python
# 1. Define agent function in langgraph_system.py
def my_new_agent(self, state: AgentState) -> AgentState:
    # Agent logic here
    return state

# 2. Add node to graph
workflow.add_node("my_agent", self.my_new_agent)

# 3. Define routing logic
workflow.add_conditional_edges(...)
```

### 📊 **Training New Query Types**
```python
# Add to src/vanna/training.py
training_pairs = [
    {
        "question": "Your Indonesian question here",
        "sql": "SELECT ... FROM dwh.table_name ..."
    }
]
```

### 🎨 **Customizing UI**
```python
# Modify app/main.py for Chainlit customization
cl.config.ui.name = "Your University Name"
cl.config.ui.theme = {
    "primary": "#your-color",
    "secondary": "#your-color"
}
```

## 🧪 **Testing**

### ✅ **Run Tests**
```bash
# Integration tests
python src/vanna/setup.py  # Test Vanna connection
python scripts/generate_graph.py  # Test LangGraph
```

### 🔍 **Manual Testing**
```bash
# Test database connection
python src/database/populate.py

# Test Vanna AI training
python src/vanna/training.py

# Test complete system
chainlit run app/main.py
```

## 📈 **Performance Optimization**

### 🚀 **Database Optimization**
- ✅ Indexed foreign keys for fast joins
- ✅ Optimized PostgreSQL configuration
- ✅ Connection pooling for concurrent users

### 🤖 **AI Performance**
- ✅ Vector similarity search with Qdrant
- ✅ Cached embeddings for common queries
- ✅ Optimized Gemini API calls with temperature control

### 🔧 **System Performance**
- ✅ Async processing with LangGraph
- ✅ Efficient state management between agents
- ✅ Minimal memory footprint for data processing

## 🚀 **Production Deployment**

### 🐳 **Docker Production**
```bash
# Production environment
docker-compose -f docker-compose.prod.yml up -d

# With SSL and load balancer
docker-compose -f docker-compose.prod.yml -f docker-compose.ssl.yml up -d
```

### ☁️ **Cloud Deployment Options**
- **AWS**: ECS + RDS + DocumentDB
- **Google Cloud**: Cloud Run + Cloud SQL + Vertex AI
- **Azure**: Container Instances + PostgreSQL + Cognitive Services

### 🔒 **Security Considerations**
- ✅ API key encryption and rotation
- ✅ Database connection encryption
- ✅ Input validation and SQL injection prevention
- ✅ Rate limiting for API endpoints

## 🛠️ **Troubleshooting**

### ❌ **Common Issues**

#### Database Connection Failed
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check connection
psql -h localhost -U postgres -d university_dwh
```

#### Gemini API Errors
```bash
# Verify API key
echo $GEMINI_API_KEY

# Check quota and billing
# Visit: https://console.cloud.google.com/apis/api/generativeai.googleapis.com/
```

#### Qdrant Connection Issues
```bash
# Check Qdrant service
curl http://localhost:6333/collections

# Reset collections
docker-compose restart qdrant
```

#### Training Data Issues
```bash
# Retrain Vanna
python src/vanna/training.py

# Check training data
python -c "from src.vanna.setup import UniversityVannaGemini; vn = UniversityVannaGemini(); print(vn.get_training_data())"
```

## 📚 **Documentation**

### 📖 **Additional Resources**
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Vanna AI Documentation](https://vanna.ai/docs/)
- [Chainlit Documentation](https://docs.chainlit.io/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)

### 🎓 **Learning Materials**
- [Multi-Agent Systems with LangGraph](https://langchain-ai.github.io/langgraph/tutorials/)
- [Text-to-SQL with Vanna](https://vanna.ai/docs/tutorials/)
- [Building Conversational AI with Chainlit](https://docs.chainlit.io/get-started/overview)

## 🤝 **Contributing**

### 🔄 **Development Workflow**
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and test thoroughly
4. Commit with descriptive messages
5. Push to branch: `git push origin feature/amazing-feature`
6. Submit a Pull Request

### 📋 **Contribution Guidelines**
- Follow Python PEP 8 style guidelines
- Add tests for new features
- Update documentation for changes
- Ensure backward compatibility
- Test with sample university data

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **LangChain Team** for the amazing LangGraph framework
- **Vanna AI** for text-to-SQL capabilities
- **Google** for the powerful Gemini API
- **Qdrant** for high-performance vector search
- **Chainlit** for the beautiful conversational interface

## 📞 **Support**

### 🆘 **Getting Help**
- 📧 **Email**: muhajirakbarhsb@gmail.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/muhajirakbarhsb/unairvanna/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/muhajirakbarhsb/unairvanna/discussions)

### 🌟 **Show Your Support**
If this project helps you, please consider:
- ⭐ Starring the repository
- 🍴 Forking for your own use
- 📢 Sharing with other educators
- 🐛 Reporting bugs and issues
- 💡 Suggesting new features

---

