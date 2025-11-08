from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
import requests
import os
import google.generativeai as genai

from dotenv import load_dotenv
load_dotenv()

# Configuration
SECRET_KEY = "your-secret-key-change-this"
ALGORITHM = "HS256"
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Initialize
app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
else:
    gemini_model = None

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database setup
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)''')

    # Reports table
    c.execute('''CREATE TABLE IF NOT EXISTS reports
                 (id INTEGER PRIMARY KEY, user_id INTEGER, stock TEXT, analysis TEXT, 
                  recommendation TEXT, timestamp TEXT)''')

    # Portfolio table
    c.execute('''CREATE TABLE IF NOT EXISTS portfolios
                 (id INTEGER PRIMARY KEY, 
                  user_id INTEGER, 
                  stock_symbol TEXT,
                  quantity REAL,
                  purchase_price REAL,
                  timestamp TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')

    conn.commit()
    conn.close()


init_db()


# Models
class User(BaseModel):
    username: str
    password: str
    role: str  # "analyst" or "investor"


class LoginRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    stock_symbol: str
    question: Optional[str] = "Analyze this stock"


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str


# Helper functions
def create_token(username: str, role: str):
    expire = datetime.utcnow() + timedelta(hours=24)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_stock_data(symbol: str):
    """Fetch current stock data from yfinance"""
    try:
        import yfinance as yf

        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="1d")

        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            prev_close = info.get('previousClose', current_price)
            change = current_price - prev_close
            percent_change = (change / prev_close) * 100 if prev_close else 0

            # Get company name
            company_name = info.get('longName') or info.get('shortName') or symbol

            return {
                "symbol": symbol,
                "name": company_name,
                "price": round(current_price, 2),
                "change": round(change, 2),
                "percent_change": round(percent_change, 2),
                "high": round(hist['High'].iloc[-1], 2),
                "low": round(hist['Low'].iloc[-1], 2),
                "volume": int(hist['Volume'].iloc[-1])
            }
    except Exception as e:
        print(f"Error fetching stock data: {e}")

    # Fallback
    return {
        "symbol": symbol,
        "name": symbol,
        "price": 0,
        "change": 0,
        "percent_change": 0,
        "high": 0,
        "low": 0,
        "volume": 0
    }


def get_historical_data(symbol: str, days: int = 30):
    """Fetch historical stock data using yfinance"""
    try:
        import yfinance as yf
        from datetime import datetime, timedelta

        # Fetch data for the last 30 days
        stock = yf.Ticker(symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        hist = stock.history(start=start_date, end=end_date)

        if not hist.empty:
            dates = [date.strftime('%m/%d') for date in hist.index]
            prices = hist['Close'].tolist()

            return {
                "dates": dates,
                "prices": prices
            }

        # Fallback if no data
        return {
            "dates": [f"Day {i + 1}" for i in range(days)],
            "prices": [150.0] * days
        }
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return {
            "dates": [f"Day {i + 1}" for i in range(days)],
            "prices": [150.0] * days
        }


def analyze_with_ai(stock_data: dict, question: str, historical: dict):
    """Use Gemini to analyze stock with historical context"""
    if not gemini_model:
        # Mock response for testing
        return {
            "analysis": f"Technical analysis of {stock_data['symbol']}: The stock is showing positive momentum with a {stock_data['percent_change']}% change.",
            "recommendation": "BUY",
            "portfolio_percent": 15,
            "reasoning": "Strong upward trend with good volume support."
        }

    # Calculate 30-day trend
    trend_start_price = historical['prices'][0] if historical['prices'] else stock_data['price']
    trend_end_price = historical['prices'][-1] if historical['prices'] else stock_data['price']
    trend_change_pct = ((trend_end_price - trend_start_price) / trend_start_price * 100) if trend_start_price else 0

    # Determine trend direction
    if trend_change_pct > 5:
        trend_desc = "strong upward trend"
    elif trend_change_pct > 2:
        trend_desc = "moderate upward trend"
    elif trend_change_pct > -2:
        trend_desc = "sideways/consolidating"
    elif trend_change_pct > -5:
        trend_desc = "moderate downward trend"
    else:
        trend_desc = "strong downward trend"

    prompt = f"""You are a professional stock market analyst providing portfolio allocation advice.

Stock: {stock_data['symbol']}

TODAY'S DATA:
- Current Price: ${stock_data['price']}
- Daily Change: {stock_data['change']} ({stock_data['percent_change']}%)
- High: ${stock_data['high']} | Low: ${stock_data['low']}
- Volume: {stock_data['volume']:,}

30-DAY TREND ANALYSIS:
- Starting Price (30 days ago): ${trend_start_price:.2f}
- Current Price: ${trend_end_price:.2f}
- 30-Day Change: {trend_change_pct:.2f}%
- Trend: {trend_desc}

IMPORTANT: Your recommendation must consider BOTH:
1. Today's price action (short-term sentiment)
2. The 30-day trend (medium-term direction)

RECOMMENDATION RULES:
- STRONG BUY: Strong 30-day uptrend (>5%) + positive/neutral daily → 18-25% allocation
- BUY: Moderate uptrend OR recovery setup → 10-17% allocation
- HOLD: Sideways trend, mixed signals → 5-12% allocation (maintain positions)
- SELL: Downtrend confirmed by both timeframes → 0-5% allocation (reduce exposure)
- STRONG SELL: Strong downtrend (<-5%) with negative daily → 0% allocation (exit)

CONSISTENCY RULES (CRITICAL):
- If you say SELL or STRONG SELL → allocation MUST be 0-5%
- If you say BUY or STRONG BUY → allocation MUST be 10-25%
- If you say HOLD → allocation MUST be 5-12%
- Never recommend BUY with 0% or SELL with 20% - this is contradictory!

Your analysis should:
1. Acknowledge today's movement BUT prioritize the 30-day trend
2. Explain if short-term and medium-term signals conflict
3. Be consistent: don't say SELL but allocate 15%

Format your response EXACTLY as:
ANALYSIS: [2-3 sentences: discuss both daily action and 30-day trend, explain which matters more]
RECOMMENDATION: [STRONG BUY/BUY/HOLD/SELL/STRONG SELL]
ALLOCATION: [number matching the recommendation: 0-5 for SELL, 5-12 for HOLD, 10-25 for BUY]%
REASONING: [3-4 bullet points: trend analysis, volume interpretation, risk factors, action plan]
"""

    try:
        response = gemini_model.generate_content(prompt)
        response_text = response.text

        # Parse response
        lines = response_text.split('\n')
        result = {
            "analysis": "",
            "recommendation": "HOLD",
            "portfolio_percent": 0,
            "reasoning": ""
        }

        for line in lines:
            line = line.strip()
            if line.startswith("ANALYSIS:"):
                result["analysis"] = line.replace("ANALYSIS:", "").strip()
            elif line.startswith("RECOMMENDATION:"):
                rec = line.replace("RECOMMENDATION:", "").strip()
                result["recommendation"] = rec
            elif line.startswith("ALLOCATION:"):
                try:
                    alloc_text = line.replace("ALLOCATION:", "").replace("%", "").strip()
                    result["portfolio_percent"] = int(alloc_text)
                except:
                    result["portfolio_percent"] = 0
            elif line.startswith("REASONING:"):
                result["reasoning"] = line.replace("REASONING:", "").strip()

        # VALIDATION: Enforce consistency between recommendation and allocation
        rec = result["recommendation"].upper()
        allocation = result["portfolio_percent"]

        if "STRONG BUY" in rec and allocation < 10:
            result["portfolio_percent"] = 20
        elif "BUY" in rec and "STRONG" not in rec and allocation < 10:
            result["portfolio_percent"] = 12
        elif "SELL" in rec and allocation > 5:
            result["portfolio_percent"] = 0
        elif "HOLD" in rec and (allocation < 5 or allocation > 12):
            result["portfolio_percent"] = 8

        return result
    except Exception as e:
        print(f"AI analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")


# Routes
@app.post("/register")
def register(user: User):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try:
        hashed = pwd_context.hash(user.password)
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  (user.username, hashed, user.role))
        conn.commit()
        return {"message": "User created successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()


@app.post("/login", response_model=Token)
def login(request: LoginRequest):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT password, role FROM users WHERE username=?", (request.username,))
    result = c.fetchone()
    conn.close()

    if not result or not pwd_context.verify(request.password, result[0]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(request.username, result[1])
    return {"access_token": token, "token_type": "bearer", "role": result[1]}


@app.post("/chat")
def chat(request: ChatRequest, token: str):
    user_data = verify_token(token)

    # Get stock data
    stock_data = get_stock_data(request.stock_symbol)
    if not stock_data or stock_data["price"] == 0:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Get historical data
    historical = get_historical_data(request.stock_symbol, days=30)

    # Analyze with AI (now includes historical context)
    analysis = analyze_with_ai(stock_data, request.question, historical)

    # Save report
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (user_data["sub"],))
    user_id = c.fetchone()[0]

    c.execute("""INSERT INTO reports (user_id, stock, analysis, recommendation, timestamp)
                 VALUES (?, ?, ?, ?, ?)""",
              (user_id, request.stock_symbol, analysis["analysis"],
               analysis["recommendation"], datetime.now().isoformat()))
    conn.commit()
    conn.close()

    return {
        "stock_data": stock_data,
        "analysis": analysis,
        "chart_data": {
            "labels": historical["dates"],
            "prices": historical["prices"]
        }
    }


@app.get("/reports")
def get_reports(token: str):
    user_data = verify_token(token)

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (user_data["sub"],))
    user_id = c.fetchone()[0]

    c.execute("""SELECT stock, analysis, recommendation, timestamp 
                 FROM reports WHERE user_id=? ORDER BY timestamp DESC LIMIT 10""",
              (user_id,))
    reports = [{"stock": r[0], "analysis": r[1], "recommendation": r[2], "timestamp": r[3]}
               for r in c.fetchall()]
    conn.close()

    return {"reports": reports}


@app.get("/investors")
def get_investors(token: str):
    """Analyst only: Get all investors"""
    user_data = verify_token(token)

    if user_data["role"] != "analyst":
        raise HTTPException(status_code=403, detail="Analysts only")

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, username, role FROM users WHERE role='investor'")
    investors = [{"id": r[0], "username": r[1]} for r in c.fetchall()]
    conn.close()

    return {"investors": investors}


@app.get("/portfolio/consolidated/{user_id}")
def get_consolidated_portfolio(user_id: int, token: str):
    """Get consolidated portfolio (aggregated by stock)"""
    user_data = verify_token(token)

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (user_data["sub"],))
    current_user_id = c.fetchone()[0]

    # Check permissions
    if user_data["role"] == "investor" and current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Can only view your own portfolio")

    # Aggregate quantities by stock
    c.execute("""
        SELECT stock_symbol, 
               SUM(quantity) as total_quantity,
               AVG(purchase_price) as avg_price
        FROM portfolios 
        WHERE user_id=? 
        GROUP BY stock_symbol
        HAVING SUM(quantity) > 0
    """, (user_id,))

    portfolio = []
    for row in c.fetchall():
        stock_symbol = row[0]
        total_qty = row[1]
        avg_price = row[2]

        # Get current price
        current_data = get_stock_data(stock_symbol)
        current_price = current_data["price"] if current_data else avg_price

        total_value = total_qty * current_price
        cost_basis = total_qty * avg_price
        profit_loss = total_value - cost_basis
        profit_loss_pct = (profit_loss / cost_basis * 100) if cost_basis else 0

        portfolio.append({
            "stock": stock_symbol,
            "quantity": round(total_qty, 2),
            "purchase_price": round(avg_price, 2),
            "current_price": round(current_price, 2),
            "total_value": round(total_value, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_loss_pct": round(profit_loss_pct, 2)
        })

    conn.close()

    # Calculate summary
    total_portfolio_value = sum(h["total_value"] for h in portfolio)
    total_profit_loss = sum(h["profit_loss"] for h in portfolio)

    return {
        "portfolio": portfolio,
        "summary": {
            "total_value": round(total_portfolio_value, 2),
            "total_profit_loss": round(total_profit_loss, 2),
            "total_positions": len(portfolio)
        }
    }


@app.get("/portfolio/{user_id}")
def get_portfolio(user_id: int, token: str):
    """Get portfolio for a user - redirects to consolidated"""
    return get_consolidated_portfolio(user_id, token)


@app.post("/portfolio/add")
def add_to_portfolio(token: str, stock_symbol: str, quantity: float, purchase_price: float):
    """Add stock to investor's portfolio"""
    user_data = verify_token(token)

    if user_data["role"] != "investor":
        raise HTTPException(status_code=403, detail="Only investors can add to portfolio")

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (user_data["sub"],))
    user_id = c.fetchone()[0]

    c.execute("""INSERT INTO portfolios (user_id, stock_symbol, quantity, purchase_price, timestamp)
                 VALUES (?, ?, ?, ?, ?)""",
              (user_id, stock_symbol.upper(), quantity, purchase_price, datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return {"message": "Added to portfolio successfully"}


@app.delete("/portfolio/remove")
def remove_from_portfolio(stock_symbol: str, token: str):
    """Remove all positions of a stock from portfolio"""
    user_data = verify_token(token)

    if user_data["role"] != "investor":
        raise HTTPException(status_code=403, detail="Only investors can modify portfolio")

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE username=?", (user_data["sub"],))
    user_id = c.fetchone()[0]

    c.execute("DELETE FROM portfolios WHERE user_id=? AND stock_symbol=?", (user_id, stock_symbol))
    conn.commit()
    conn.close()

    return {"message": f"Removed all {stock_symbol} positions"}


@app.get("/reports/{user_id}")
def get_reports_for_user(user_id: int, token: str):
    """Get reports for a specific user"""
    user_data = verify_token(token)

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (user_data["sub"],))
    current_user_id = c.fetchone()[0]

    # Check permissions
    if user_data["role"] == "investor" and current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Can only view your own reports")

    c.execute("""SELECT stock, analysis, recommendation, timestamp 
                 FROM reports WHERE user_id=? ORDER BY timestamp DESC LIMIT 20""", (user_id,))

    reports = [{"stock": r[0], "analysis": r[1], "recommendation": r[2], "timestamp": r[3]}
               for r in c.fetchall()]
    conn.close()

    return {"reports": reports}


@app.get("/")
def root():
    return {"message": "Stock Analyst API", "status": "running"}