# 🤖 FinanceBot: AI-Powered Personal Finance Assistant

FinanceBot is a sophisticated Telegram bot designed to help users manage their finances, analyze investments, and get AI-driven financial advice. By combining data analysis, stock market forecasting, and Retrieval-Augmented Generation (RAG), FinanceBot provides a comprehensive financial cockpit right inside Telegram.

## 🌟 Key Features

### 📉 Expense Analysis
- **File Upload:** Support for CSV and Excel files.
- **Smart Analysis:** Analyze spending patterns based on your monthly income and savings targets.
- **Visual Insights:** Automatically generates expense breakdown charts to identify spending leaks.

### 📈 Portfolio Management
- **Portfolio Snapshot:** Upload your current holdings to get a detailed summary.
- **Visualizations:** Get allocation pie charts and profit/loss bar charts for your stocks.
- **Price Prediction:** AI-powered 30-day price outlook for your top holdings.
- **Smart Suggestions:** Receive diversified investment recommendations based on your current risk profile.

### 📰 Market Intelligence
- **Daily Snapshots:** Get a quick overview of the current market state.
- **Indian Market News:** Stay updated with the latest news from the Indian stock market.

### 🧠 AI Financial Advisor (RAG)
- **Natural Conversations:** Ask questions like *"Should I invest in Tata Motors?"* or *"How do I reduce my food expenses?"*
- **Context Awareness:** The bot remembers your previous conversations and considers your uploaded financial data to provide personalized advice.
- **Powered by LLMs:** Uses Groq and sentence-transformers for high-performance, context-aware responses.

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Bot Framework:** `python-telegram-bot`
- **Data Analysis:** `pandas`, `numpy`, `scikit-learn`
- **Financial Data:** `yfinance`, `feedparser`
- **AI/ML:** `Groq` (LLM), `FAISS` (Vector Store), `sentence-transformers`
- **Visualization:** `matplotlib`
- **Database:** SQLite (for user and chat history)

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- A Groq API Key

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/finance-bot.git
   cd finance-bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup:**
   Create a `.env` file in the root directory and add your keys:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Run the Bot:**
   ```bash
   python finance_bot.py
   ```

## 📁 Project Structure

```text
finance-bot/
├── ai/                # AI logic, RAG pipeline, and LLM integration
├── charts/            # Generated financial visualizations
├── data/              # Local storage for user uploads and vector indices
├── utils/             # Helper modules for expenses, investments, and DB
├── finance_bot.py    # Main entry point and Telegram handlers
├── requirements.txt   # Project dependencies
└── render.yaml        # Deployment configuration for Render
```

## 🛡️ Disclaimer
*This bot is for educational and informational purposes only. It does not provide professional financial advice. Always consult with a certified financial advisor before making investment decisions.*
