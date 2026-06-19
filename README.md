# ClimbCP 

ClimbCP is a professional, advanced analytics and AI-powered training assistant for Competitive Programmers. Designed to help users track their performance metrics, analyze their strengths and weaknesses, discover similar peers, and receive personalized problem recommendations and AI coaching, ClimbCP connects directly to Codeforces to build a rich profile of your coding journey.

---

##  Key Features

### 1. Authentication & Onboarding
*   **User Registration:** Secure user registration with live validation of Codeforces handles.
*   **JWT-Based Auth & Session Persistence:** Tokens persist user sessions across page reloads.
*   **Initial Codeforces Sync:** Fetches user ratings, submissions, and contest history automatically upon registration.
*   **Protected Routes:** Solid middleware-backed protection for all analytics and coaching APIs.

### 2. Rich Analytics & Topic Intelligence
*   **Activity Statistics:** Track submissions, solve counts, and active coding streaks.
*   **Topic Mastery Engine:** Calculates a mastery score (0-100) across 18 core competitive programming concepts (e.g., Dynamic Programming, Trees, Greedy, Flows).
*   **Weakness & Strength Detection:** Automatically identifies topics that represent bottlenecks or fields of expertise based on historical submission accuracy and ratings.

### 3. Personalized Recommendation System
*   **Problem Recommendations (V1):** Recommends specific competitive programming problems tailored to your target rating and weakness areas.
*   **Practice Sets:** Generate custom problem lists tailored to targeted subskills.
*   **Learning Roadmap:** Dynamically generated roadmap guiding you through new concepts with concrete problem milestones.

### 4. AI-Powered Coaching
*   **AI Contest Review:** Upload and analyze contest performances to see where you lost points or struggled.
*   **Rating Loss Explanation:** Deep explanation of why a rating drop occurred in a recent contest.
*   **Performance Bottleneck Analysis:** Pinpoint exact areas in reasoning, speed, or implementation where your performance lags.

### 5. Advanced Vector Intelligence
*   **Problem Embeddings:** Uses SentenceTransformers (`all-MiniLM-L6-v2`) to embed competitive programming problems into vectors based on title, tags, and difficulty.
*   **User Embeddings:** Generates a 128-dimensional profile vector mapping user mastery and performance.
*   **Peer Discovery:** Locates users with similar learning trajectories and solving behaviors using cosine similarity (native `pgvector` HNSW index on PostgreSQL or NumPy fallback on SQLite).

### 6. Future Features (In Pipeline)
*   **Predictive Analytics:**
    *   **Rating Predictor:** Estimate rating changes and forecast upcoming performance trends.
    *   **Contest Readiness Score:** Evaluate preparation levels for scheduled rounds based on dynamic topic mastery and recent practice.
    *   **Target Rating Milestones:** Build specialized roadmap paths targeted directly at achieving specific CF ranks (e.g., Expert, Candidate Master).
*   **Multi-Platform Integration:**
    *   **CodeChef Support:** Sync submission logs, ratings, and contest performances from CodeChef accounts.
    *   **Cross-Platform Analytics:** View merged charts and insights across all connected platforms in a unified dashboard.
    *   **Unified Skill Score:** A singular, standardized metric reflecting overall global competitive programming expertise.

---

## Tech Stack

### Backend
*   **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
*   **Database:** PostgreSQL (with `pgvector` extension) / SQLite (as local dev fallback)
*   **ORM:** SQLAlchemy 2.0
*   **AI & ML Integration:** 
    *   [SentenceTransformers](https://www.sbert.net/) for semantic text embeddings.
    *   OpenRouter / OpenAI APIs for advanced LLM coaching.
*   **Rate Limiting:** Built-in endpoint rate limiting for security.

### Frontend
*   **Framework:** [React 19](https://react.dev/) + [Vite](https://vite.dev/)
*   **Styling:** Tailwind CSS (Modern, premium interface design)
*   **Visualization:** [Recharts](https://recharts.org/) (Interactive charts for Rating History, Strengths/Weaknesses, Topic Radars, and Activity)
*   **Component Library:** Base UI & Lucide React icons

---

## Repository Structure

```text
ClimbCP/
├── backend/                  # FastAPI Web Server
│   ├── app/
│   │   ├── core/             # Configuration & security middleware
│   │   ├── database/         # DB connection & seeding logic
│   │   ├── models/           # SQLAlchemy DB models (User, Problem, embedding vectors, etc.)
│   │   ├── routers/          # API route definitions
│   │   ├── schemas/          # Pydantic schemas for request/response serialization
│   │   └── services/         # Main business logic, AI coach, recommendation, & embeddings
│   ├── reset_db.py           # Database migration & seed helper script
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Template for environment variables
│
├── frontend/                 # React Web App
│   ├── src/
│   │   ├── components/       # Shared UI components
│   │   ├── layouts/          # UI templates
│   │   ├── pages/            # View pages (Dashboard, AI Coach, Similar Users, etc.)
│   │   ├── services/         # API connection handlers
│   │   └── App.jsx           # Main routing & React tree
│   ├── package.json          # Node dependencies & run scripts
│   ├── tailwind.config.js    # Styling design tokens
│   └── .env.example          # Template for frontend environment variables
│
└── remaining.md              # Project Phase Roadmap
```

---

## Setup & Installation

### Backend Configuration

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**
    Create a `.env` file in the `backend/` directory with the following structure:
    ```ini
    # Database Configuration
    DATABASE_URL=postgresql://username:password@localhost:5432/climbcp
    # (Or sqlite:///./test_phase5.db for lightweight local testing)

    # LLM Provider Configuration
    # Supported: openrouter | openai | gemini | ollama
    LLM_PROVIDER=openrouter
    LLM_MODEL=qwen/qwen3-32b
    OPENROUTER_API_KEY=your-api-key-here
    OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

    # AI Cache Duration (hours before refreshing AI Coach reports)
    AI_REPORT_CACHE_HOURS=6

    # API Rate Limiting Configuration
    LIMIT_LOGIN=5/60
    LIMIT_REGISTER=3/3600
    LIMIT_AI=5/60
    LIMIT_DEFAULT=60/60
    ```

5.  **Initialize & Seed the Database:**
    ClimbCP seeds a standard vocabulary of 18 core competitive programming concepts automatically.
    ```bash
    python reset_db.py
    ```

6.  **Start the Server:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The Swagger interactive documentation will be available at `http://localhost:8000/docs`.

---

### Frontend Configuration

1.  **Navigate to the frontend directory:**
    ```bash
    cd ../frontend
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Configure environment variables:**
    Create a `.env` file in the `frontend/` directory pointing to the API URL:
    ```ini
    VITE_API_BASE_URL=http://localhost:8000
    ```

4.  **Start the local development server:**
    ```bash
    npm run dev
    ```
    Open `http://localhost:5173` in your browser.

---

## Roadmap & Phase Progression

Below is the implementation status of ClimbCP's features:

| Phase | Description | Key Deliverables | Status |
| :--- | :--- | :--- | :---: |
| **Phase 0** | **Auth & Onboarding** | Codeforces handle registration, JWT, session restore, initial sync | **✅ Complete** |
| **Phase 1** | **Analytics Foundation** | Rating history, submissions tracker, contest stats APIs | **✅ Complete** |
| **Phase 2** | **Topic Intelligence** | Topic mastery analysis, strengths & weaknesses engines | **✅ Complete** |
| **Phase 3** | **Recommendations** | Personalized practice problems, practice set generator, roadmaps | **✅ Complete** |
| **Phase 4** | **AI Features** | AI Contest reviews, rating drop reasons, performance bottleneck analysis | **✅ Complete** |
| **Phase 5** | **Advanced Intelligence** | SentenceTransformers embedding pipelines, user similarity matches | **✅ Complete** |
| **Phase 6** | **Prediction** | Rating predictors, target forecasting, contest readiness score | **⏳ Planned** |
| **Phase 7** | **Multi-Platform** | CodeChef integration, cross-platform metrics, unified score | **⏳ Planned** |
| **Phase 8** | **Frontend Client** | Dashboard UI, Recharts radar/line charts, AI coach interface, login | **✅ Complete** |

---

## Contributing

Contributions are welcome! Please create an issue or pull request to suggest additions, optimizations, or feature expansions.
