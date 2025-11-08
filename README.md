# 📈 Stock Analyst AI

A full-stack web application for real-time stock market analysis and portfolio management, integrating AI-powered recommendations with live market data.

**🎥 [Project Presentation](https://drive.google.com/drive/folders/1Tmq1WvOqb9WMdyyf0J7crds86ReImtyn?usp=drive_link)**

---

## 🎯 Overview

Stock Analyst AI provides intelligent stock market analysis through integration of real-time financial data and AI-powered insights. The platform serves two user types:

- **Investors**: Manage personal portfolios, analyze stocks, and view AI recommendations
- **Analysts**: Access portfolios and reports of assigned investor accounts

---

## ✨ Key Features

- **Real-Time Stock Data**: Integration with Yahoo Finance for live market prices and historical data
- **AI-Powered Analysis**: Google Gemini API generates trading recommendations (BUY/SELL/HOLD) with portfolio allocation percentages
- **30-Day Trend Visualization**: Interactive charts showing technical price trends
- **Portfolio Management**: Transaction-based system with consolidated views, P/L tracking, and buy/sell operations
- **Role-Based Access Control**: Secure authentication with JWT tokens and differentiated access for analysts and investors
- **Analysis Reports**: Historical archive of AI-generated stock analyses

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite
- **Authentication**: JWT with bcrypt password hashing
- **APIs**: 
  - Yahoo Finance (via yfinance library)
  - Google Gemini 2.0 Flash (AI analysis)

### Frontend
- **Framework**: React 18+ with Vite
- **HTTP Client**: Axios
- **Visualization**: Recharts
- **Styling**: Custom CSS

---

## 📁 Project Structure
```
stock-analyst-ai/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── database.db          # SQLite database
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Main React component
│   │   └── App.css         # Styling
│   ├── package.json        # Node dependencies
│   └── vite.config.js      # Vite configuration
└── README.md
```

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- pip and npm

### Backend Setup

1. **Navigate to backend directory**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install fastapi uvicorn sqlalchemy pydantic python-jose passlib bcrypt yfinance google-generativeai python-dotenv
```

4. **Create `.env` file**
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

5. **Run the server**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`

---

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Update API URL** (if needed)
   - Open `src/App.jsx`
   - Modify `API_URL` constant if backend is not on `localhost:8000`

4. **Run development server**
```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

---

## 💡 Usage

### 1. **Register an Account**
   - Choose role: Investor or Analyst
   - Create username and password

### 2. **Login**
   - Use credentials to access the platform

### 3. **Analyze Stocks**
   - Enter stock ticker (e.g., AAPL, TSLA, GOOGL)
   - View AI-powered analysis with recommendations
   - See 30-day price trend charts

### 4. **Manage Portfolio**
   - Buy/sell stocks directly from analysis view
   - View consolidated portfolio with P/L tracking
   - Remove positions as needed

### 5. **View Reports**
   - Access historical analysis reports
   - Track past recommendations

---

## 🔐 Security Features

- **Password Hashing**: Bcrypt with work factor 12
- **Token-Based Auth**: JWT with 24-hour expiration
- **Role-Based Access**: API endpoint protection by user role
- **SQL Injection Prevention**: Parameterized queries
- **Input Validation**: API-level validation and sanitization

---

## 📊 API Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/register` | User registration | Public |
| POST | `/login` | User authentication | Public |
| POST | `/chat` | Stock analysis request | Authenticated |
| GET | `/reports` | User's analysis reports | Authenticated |
| GET | `/portfolio/consolidated/{user_id}` | Consolidated portfolio | Authenticated |
| POST | `/portfolio/add` | Add stock position | Investor |
| DELETE | `/portfolio/remove` | Remove stock position | Investor |
| GET | `/investors` | List investors | Analyst |

---

## 🎨 Screenshots

### Login/Register
User authentication with role selection

### Stock Analysis
AI-powered recommendations with 30-day charts

### Portfolio Management
Consolidated view with P/L tracking and transaction history

### Analyst Dashboard
Investor oversight with portfolio and report access

---

## 🧪 Key Implementation Challenges

### 1. **Data Source Selection**
- **Challenge**: Finnhub API free tier limitations
- **Solution**: Migrated to Yahoo Finance via yfinance

### 2. **AI Consistency**
- **Challenge**: Inconsistent recommendations vs. allocations
- **Solution**: Structured prompt engineering + post-processing validation

### 3. **Portfolio Aggregation**
- **Challenge**: Multiple transactions creating duplicates
- **Solution**: SQL GROUP BY with SUM/AVG consolidation

### 4. **State Management**
- **Challenge**: Stale data between view switches
- **Solution**: useEffect hooks with automatic reloading

---

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| API Response Time | < 2 seconds |
| AI Analysis Generation | 3-5 seconds |
| Portfolio Load Time | < 1 second |
| Chart Rendering | < 500ms |

---

## 🔮 Potential Future Enhancements

- Additional technical indicators (RSI, MACD, Bollinger Bands)
- Watchlist functionality with price alerts
- Portfolio performance analytics
- News feed integration
- Report export (CSV, PDF)
- Mobile-responsive design improvements

---

## 📝 License

This project is developed as a technical assignment for educational purposes.

---

## 👤 Author

**Nishad Bagade** (MT2024102)

📧 Contact: [Your Email]  
🔗 GitHub: [dyinghorizon](https://github.com/dyinghorizon)

---

## 🙏 Acknowledgments

- Yahoo Finance for market data API
- Google Gemini for AI analysis capabilities
- FastAPI and React communities for excellent documentation
