import json
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# ✅ Groq API Key (Ensure this is correct)
GROQ_API_KEY = "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"

# ✅ Default AI Model
DEFAULT_GROQ_MODEL = "llama3-8b-8192"  # Using LLaMA 3-8B Model

# 🌟 System Prompt for AI
SYSTEM_PROMPT = """You are an AI financial advisor specializing in algorithmic trading strategies. 
Below are the backtest results provided by the user:
{BACKTEST_RESULTS}

Your role is to provide **short and clear** insights:
- 📊 **Explain the Results**: Highlight key strengths & weaknesses.
- ⚠️ **Identify Issues**: Spot risks like high drawdowns or low win rates.
- 💡 **Suggest Improvements**: Offer better risk management or entry/exit adjustments.
- ❓ **Answer User Questions**: Address concerns logically.
- 🔍 **Stay Neutral**: Provide unbiased, data-driven insights.

✨ Be concise, logical, and **user-friendly**! Remind users that **past performance ≠ future results**."""

# 📂 **Chat Data Store**
class ChatDataStore:
    """Stores chat history to maintain conversation context."""
    
    def __init__(self):
        self.messages = []

    def save_message(self, role, message):
        """Saves a message with a timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.messages.append({"role": role, "content": message, "timestamp": timestamp})

    def get_all_messages(self):
        """Retrieves all stored messages."""
        return self.messages

# 🔄 **Initialize Chat History**
chat_store = ChatDataStore()

# ✨ **Chat Function**
def chat_completion(user_message, backtest_results):
    """
    Handles chat completion using Groq.
    
    📌 Args:
    - user_message (str): The user's input message.
    - backtest_results (dict): Key performance metrics.

    ✅ Returns:
    - str: AI-generated response.
    """
    try:
        # 🎨 Format Backtest Results
        backtest_results_str = json.dumps(backtest_results, indent=4)
        system_prompt = SYSTEM_PROMPT.replace("{BACKTEST_RESULTS}", backtest_results_str)

        # 🔄 Store Initial System Message if Empty
        if not chat_store.get_all_messages():
            chat_store.save_message("system", system_prompt)

        # 💬 Store User Message
        chat_store.save_message("user", user_message)

        # 📝 Construct Message History
        messages = [SystemMessage(content=system_prompt)]
        for msg in chat_store.get_all_messages():
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # 🚀 **Use Groq API**
        print("\033[96m🦙 Using Groq's LLaMA 3 Model...\033[0m")
        chat_model = ChatGroq(model_name=DEFAULT_GROQ_MODEL, groq_api_key=GROQ_API_KEY, max_tokens=4096)

        # 💬 Invoke AI Model
        response = chat_model.invoke(messages)

        # ✅ **Process AI Response**
        ai_response = response.content if response else "No response generated."

        # 💾 Store AI Response
        chat_store.save_message("assistant", ai_response)

        # 🎉 **Print AI Response**
        print("\033[92m✨ AI Response: \033[0m")
        print(f"\033[94m{ai_response}\033[0m")

        return ai_response

    except Exception as error:
        print("\033[91m❌ ERROR in chat completion:", error, "\033[0m")
        return "No response due to an error."

# 🚀 **Example Usage**
if __name__ == "__main__":
    backtest_results_example = {
        "profit_loss": 10000,
        "sharpe_ratio": 1.5,
        "drawdown": 10,
        "win_rate": 55,
        "risk_reward_ratio": 2
    }

    user_message = input("\033[96m📝 Enter your message: \033[0m")

    response = chat_completion(user_message, backtest_results_example)
    print("\n🤖 AI Response:", response)
