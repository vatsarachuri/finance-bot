import os
import asyncio
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from telegram.constants import ChatAction, ParseMode

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

from utils.expense_utils import analyze_expenses

from utils.investment_utils import (
    convert_excel_to_csv,
    predict_stock_price,
    get_portfolio_summary,
    load_and_update_portfolio,
    suggest_best_investments,
    generate_portfolio_charts,
    get_market_alerts,
    get_indian_stock_news,
)
from utils.advice_utils import give_financial_advice

from utils.database import (
    init_db,
    save_user,
    save_portfolio,
    get_latest_portfolio,
    save_chat,
    get_chat_history,
)

# =========================================================
# LOAD ENV
# =========================================================
load_dotenv()

# =========================================================
# INIT DATABASE
# =========================================================
init_db()

# =========================================================
# USER CONTEXT
# =========================================================
user_context = {}

# =========================================================
# STATES
# =========================================================
WAIT_EXPENSE_FILE, WAIT_INCOME, WAIT_TARGET, WAIT_INVEST_FILE = range(4)

MAX_CHARS = 2000

# =========================================================
# MAIN MENU
# =========================================================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton("Expenses"),
            KeyboardButton("Investments"),
        ],
        [
            KeyboardButton("Advice"),
            KeyboardButton("Profile"),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Ask anything about your finances..."
)

# =========================================================
# SPLIT LONG MESSAGES
# =========================================================
def split_message(message, max_chars=MAX_CHARS):

    return [
        message[i:i + max_chars]
        for i in range(0, len(message), max_chars)
    ]


# =========================================================
# START
# =========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    save_user(
        user.id,
        user.username
    )

    previous = get_latest_portfolio(user.id)

    if previous is not None:

        message = (
            f"<b>Welcome back, {user.first_name}</b>\n\n"
            f"Your portfolio history is available.\n"
            f"You can continue chatting naturally."
        )

    else:

        message = (
            f"<b>Hi {user.first_name}</b>\n\n"
            f"I can help you:\n\n"
            f"• Track expenses\n"
            f"• Analyze investments\n"
            f"• Predict stock trends\n"
            f"• Provide financial insights\n\n"
            f"You can either:\n"
            f"• use the buttons below\n"
            f"• or simply chat naturally."
        )

    await update.message.reply_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu
    )


# =========================================================
# MENU + AI CHAT HANDLER
# =========================================================
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    lower_text = text.lower()

    # =====================================================
    # EXPENSES
    # =====================================================
    if lower_text == "expenses":

        return await expenses(update, context)

    # =====================================================
    # INVESTMENTS
    # =====================================================
    elif lower_text == "investments":

        return await investments(update, context)

    # =====================================================
    # PROFILE
    # =====================================================
    elif lower_text == "profile":

        previous = get_latest_portfolio(
            update.effective_user.id
        )

        if previous is not None:

            await update.message.reply_text(
                "<b>Your Profile</b>\n\n"
                "Portfolio history available.\n"
                "Previous conversations remembered.",
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu
            )

        else:

            await update.message.reply_text(
                "<b>Your Profile</b>\n\n"
                "No portfolio history found yet.",
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu
            )

        return

    # =====================================================
    # ADVICE
    # =====================================================
    elif lower_text == "advice":

        await update.message.reply_text(
            "<b>AI Financial Assistant</b>\n\n"
            "You can ask naturally:\n\n"
            "• should I invest in Tata Motors?\n"
            "• how do I reduce food expenses?\n"
            "• should I hold Infosys?\n"
            "• is my portfolio diversified?\n\n"
            "I’ll remember previous conversations too.",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu
        )

        return

    # =====================================================
    # NORMAL AI CHAT
    # =====================================================

    user_id = update.effective_user.id

    context_data = user_context.get(
        user_id,
        ""
    )

    # ---------------- LOAD CHAT MEMORY ----------------

    history = get_chat_history(user_id)

    memory_context = ""

    for item in history:

        memory_context += (
            f"{item['role']}: {item['message']}\n"
        )

    final_context = (
        f"Previous conversation:\n"
        f"{memory_context}\n\n"
        f"Financial context:\n"
        f"{context_data}"
    )

    # ---------------- SAVE USER MESSAGE ----------------

    save_chat(
        user_id,
        "user",
        text
    )

    # ---------------- TYPING EFFECT ----------------

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    await asyncio.sleep(1)

    try:

        response = give_financial_advice(
            text,
            final_context
        )

        # ---------------- SAVE AI RESPONSE ----------------

        save_chat(
            user_id,
            "assistant",
            response
        )

        for chunk in split_message(response):

            await update.message.reply_text(
                chunk,
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu
            )

    except Exception as e:

        print("AI CHAT ERROR:", e)

        await update.message.reply_text(
            "I couldn't process that properly right now.",
            reply_markup=main_menu
        )


# =========================================================
# EXPENSES FLOW
# =========================================================
async def expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "<b>Expense Analysis</b>\n\n"
        "Upload your expenses file.\n"
        "CSV and Excel both work.",
        parse_mode=ParseMode.HTML
    )

    return WAIT_EXPENSE_FILE


# =========================================================
# HANDLE EXPENSE FILE
# =========================================================
async def handle_expense_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    file = await update.message.document.get_file()

    os.makedirs("data", exist_ok=True)

    file_path = f"data/{update.message.document.file_name}"

    await file.download_to_drive(file_path)

    context.user_data["expense_file"] = file_path

    await update.message.reply_text(
        "What's your monthly income?"
    )

    return WAIT_INCOME


# =========================================================
# HANDLE INCOME
# =========================================================
async def handle_income(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        income = float(update.message.text)

        context.user_data["income"] = income

        await update.message.reply_text(
            "What's your monthly savings target?"
        )

        return WAIT_TARGET

    except:

        await update.message.reply_text(
            "Please enter a valid number."
        )

        return WAIT_INCOME


# =========================================================
# HANDLE TARGET
# =========================================================
async def handle_target(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        target = float(update.message.text)

        file_path = context.user_data["expense_file"]

        income = context.user_data["income"]

        loading = await update.message.reply_text(
            "Going through your expenses..."
        )

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )

        await asyncio.sleep(1)

        await loading.edit_text(
            "Analyzing spending patterns..."
        )

        await asyncio.sleep(1)

        summary, chart_path, context_data = analyze_expenses(
            file_path,
            income,
            target
        )

        user_context[
            update.effective_user.id
        ] = str(context_data)

        await update.message.reply_text(
            f"<b>Expense Summary</b>\n\n{summary}",
            parse_mode=ParseMode.HTML
        )

        if os.path.exists(chart_path):

            await update.message.reply_photo(
                photo=open(chart_path, "rb"),
                caption="Expense breakdown"
            )

        keyboard = [
            [
                InlineKeyboardButton(
                    "Savings Tips",
                    callback_data="tips"
                ),
                InlineKeyboardButton(
                    "Insights",
                    callback_data="insights"
                ),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "What would you like to explore next?",
            reply_markup=reply_markup
        )

        return ConversationHandler.END

    except Exception as e:

        print("EXPENSE ERROR:", e)

        await update.message.reply_text(
            f"Something went wrong.\n\n{str(e)}"
        )

        return ConversationHandler.END


# =========================================================
# INVESTMENTS FLOW
# =========================================================
async def investments(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "<b>Portfolio Analysis</b>\n\n"
        "Upload your portfolio file.\n"
        "CSV and Excel both work.",
        parse_mode=ParseMode.HTML
    )

    return WAIT_INVEST_FILE


# =========================================================
# HANDLE PORTFOLIO FILE
# =========================================================
# =========================================================
# HANDLE PORTFOLIO FILE
# =========================================================
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message.document:

        await update.message.reply_text(
            "Please upload a valid CSV or Excel file."
        )

        return WAIT_INVEST_FILE

    # =====================================================
    # DOWNLOAD FILE
    # =====================================================
    file = await update.message.document.get_file()

    os.makedirs("data", exist_ok=True)

    file_path = (
        f"data/{update.message.document.file_name}"
    )

    await file.download_to_drive(file_path)

    # =====================================================
    # LOADING FLOW
    # =====================================================
    loading = await update.message.reply_text(
        "Going through your portfolio..."
    )

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    await asyncio.sleep(1)

    await loading.edit_text(
        "Fetching latest market prices..."
    )

    await asyncio.sleep(1)

    await loading.edit_text(
        "Generating portfolio insights..."
    )

    try:

        # =================================================
        # CONVERT FILE
        # =================================================
        if file_path.endswith((".xlsx", ".xls")):

            csv_path = convert_excel_to_csv(
                file_path
            )

        else:

            csv_path = file_path

        # =================================================
        # LOAD PORTFOLIO
        # =================================================
        df = load_and_update_portfolio(
            csv_path
        )

        # =================================================
        # SAVE PORTFOLIO HISTORY
        # =================================================
        save_portfolio(
            update.effective_user.id,
            df
        )

        # =================================================
        # SUMMARY
        # =================================================
        summary = get_portfolio_summary(df)

        await asyncio.sleep(1)

        await update.message.reply_text(
            f"<b>Portfolio Snapshot</b>\n\n"
            f"{summary}",
            parse_mode=ParseMode.HTML
        )

        # =================================================
        # GENERATE CHARTS
        # =================================================
        allocation_chart, performance_chart = (
            generate_portfolio_charts(df)
        )

        # =================================================
        # SEND ALLOCATION CHART
        # =================================================
        await update.message.reply_photo(
            photo=open(allocation_chart, "rb"),
            caption="Portfolio Allocation"
        )

        # =================================================
        # SEND PERFORMANCE CHART
        # =================================================
        await update.message.reply_photo(
            photo=open(performance_chart, "rb"),
            caption="Profit / Loss by Stock"
        )

        # =================================================
        # STOCK PREDICTION
        # =================================================
        top_ticker = df.iloc[0]["Ticker"]

        predicted = predict_stock_price(
            top_ticker,
            days_ahead=30
        )

        await asyncio.sleep(1)

        if predicted is not None:

            await update.message.reply_text(
                f"<b>Price Outlook</b>\n\n"
                f"{top_ticker} could move toward "
                f"₹{predicted:.2f} "
                f"over the next month.",
                parse_mode=ParseMode.HTML
            )

        else:

            await update.message.reply_text(
                "I couldn't generate a reliable "
                "prediction right now."
            )

        # =================================================
        # INVESTMENT SUGGESTIONS
        # =================================================
        _, best_stocks = suggest_best_investments(
            df
        )

        if best_stocks is not None:

            msg = (
                "<b>Stocks Worth Watching</b>\n\n"
            )

            for _, row in best_stocks.iterrows():

                msg += (
                    f"• {row['Ticker']} "
                    f"({row['Growth_%']:.1f}% "
                    f"expected growth)\n"
                )

            await asyncio.sleep(1)

            await update.message.reply_text(
                msg,
                parse_mode=ParseMode.HTML
            )

        # =================================================
        # DAILY MARKET ALERTS
        # =================================================
        alerts = get_market_alerts()

        await update.message.reply_text(
            f"<b>Today's Market Snapshot</b>\n\n"
            f"{alerts}",
            parse_mode=ParseMode.HTML
        )

        # =================================================
        # INDIAN MARKET NEWS
        # =================================================
        news = get_indian_stock_news()

        await update.message.reply_text(
            f"<b>Indian Market News</b>\n\n"
            f"{news}",
            parse_mode=ParseMode.HTML
        )

        # =================================================
        # BUTTONS
        # =================================================
        keyboard = [
            [
                InlineKeyboardButton(
                    "Suggestions",
                    callback_data="suggestions"
                ),
                InlineKeyboardButton(
                    "Risk Analysis",
                    callback_data="risk"
                ),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(
            keyboard
        )

        await update.message.reply_text(
            "What would you like to explore next?",
            reply_markup=reply_markup
        )

    except Exception as e:

        print("INVESTMENT ERROR:", e)

        await update.message.reply_text(
            f"Something went wrong while "
            f"processing the portfolio.\n\n"
            f"{str(e)}"
        )

    return ConversationHandler.END

# =========================================================
# BUTTON CALLBACKS
# =========================================================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    data = query.data

    if data == "suggestions":

        await query.message.reply_text(
            "<b>Suggestions</b>\n\n"
            "Your portfolio currently leans slightly "
            "toward growth-oriented stocks.\n\n"
            "Adding banking or FMCG exposure could "
            "make it more balanced.",
            parse_mode=ParseMode.HTML
        )

    elif data == "risk":

        await query.message.reply_text(
            "<b>Risk Analysis</b>\n\n"
            "Your current portfolio risk appears moderate.\n\n"
            "Diversifying across sectors may help reduce volatility.",
            parse_mode=ParseMode.HTML
        )

    elif data == "tips":

        await query.message.reply_text(
            "<b>Savings Tips</b>\n\n"
            "Reducing recurring discretionary expenses "
            "usually improves savings more consistently "
            "than cutting large one-time purchases.",
            parse_mode=ParseMode.HTML
        )

    elif data == "insights":

        await query.message.reply_text(
            "<b>Insights</b>\n\n"
            "Your largest spending categories "
            "have the biggest long-term impact on savings.",
            parse_mode=ParseMode.HTML
        )


# =========================================================
# MAIN
# =========================================================
def main():

    application = (
        ApplicationBuilder()
        .token(os.getenv("TELEGRAM_BOT_TOKEN"))
        .build()
    )

    # ---------------- START ----------------
    application.add_handler(
        CommandHandler("start", start)
    )

    # ---------------- CALLBACK BUTTONS ----------------
    application.add_handler(
        CallbackQueryHandler(button_callback)
    )

    # =================================================
    # EXPENSE CONVERSATION
    # =================================================
    conv_expenses = ConversationHandler(

        entry_points=[
            MessageHandler(
                filters.Regex("^Expenses$"),
                expenses
            ),
            CommandHandler(
                "expenses",
                expenses
            ),
        ],

        states={

            WAIT_EXPENSE_FILE: [
                MessageHandler(
                    filters.Document.ALL,
                    handle_expense_file
                )
            ],

            WAIT_INCOME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_income
                )
            ],

            WAIT_TARGET: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_target
                )
            ],
        },

        fallbacks=[],
    )

    application.add_handler(conv_expenses)

    # =================================================
    # INVESTMENT CONVERSATION
    # =================================================
    conv_invest = ConversationHandler(

        entry_points=[
            MessageHandler(
                filters.Regex("^Investments$"),
                investments
            ),
            CommandHandler(
                "investments",
                investments
            ),
        ],

        states={

            WAIT_INVEST_FILE: [
                MessageHandler(
                    filters.Document.ALL,
                    handle_file
                )
            ],
        },

        fallbacks=[],
    )

    application.add_handler(conv_invest)

    # ---------------- GENERAL CHAT ----------------
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            menu_handler
        ),
        group=1
    )

    print("Bot is running...")

    application.run_polling()


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    main()