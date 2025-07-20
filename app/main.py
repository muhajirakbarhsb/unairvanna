# app/main.py - Updated for LangGraph
import os
import sys
import asyncio
from typing import Optional
import chainlit as cl
import pandas as pd
from dotenv import load_dotenv

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import with try/except for robustness
try:
    from src.agents.langgraph_system import UniversityLangGraphSystem
except ImportError:
    # Alternative import path
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    from agents.langgraph_system import UniversityLangGraphSystem

# Load environment variables
load_dotenv()

# Global LangGraph system
langgraph_system: Optional[UniversityLangGraphSystem] = None


@cl.on_chat_start
async def start():
    """Initialize the chat session with LangGraph"""
    global langgraph_system

    # Send welcome message
    await cl.Message(
        content="🎓 **Selamat datang di University LangGraph Assistant!**\n\n"
                "Sistem AI multi-agent yang menggunakan **LangGraph** untuk analisis data universitas yang cerdas dan otomatis.\n\n"
                "🤖 **Agents yang tersedia:**\n"
                "🎯 **Router Agent**: Mengklasifikasi pertanyaan dan menentukan workflow\n"
                "🔍 **SQL Agent**: Membuat dan menjalankan query database  \n"
                "📊 **Insight Agent**: Menganalisis data dan memberikan wawasan\n"
                "📈 **Visualization Agent**: Merekomendasikan visualisasi (jika diperlukan)\n"
                "💡 **Suggestion Agent**: Memberikan pertanyaan lanjutan\n"
                "📝 **Summarizer Agent**: Merangkum hasil analisis\n\n"
                "🎯 **Keunggulan LangGraph:**\n"
                "• Agents dipilih secara **otomatis** berdasarkan jenis pertanyaan\n"
                "• **Workflow dinamis** - hanya agent yang diperlukan yang berjalan\n"
                "• **Decision making** cerdas untuk langkah selanjutnya\n"
                "• **State management** yang proper antar agents\n\n"
                "**Contoh pertanyaan:**\n"
                "• Berapa jumlah mahasiswa aktif per fakultas? (data query)\n"
                "• Bandingkan IPK mahasiswa 2023 vs 2024 (comparison)\n"
                "• Bagaimana trend pembayaran SPP 3 semester terakhir? (trend analysis)\n"
                "• Analisis korelasi kehadiran dan nilai mahasiswa (complex analysis)\n\n"
                "Silakan ajukan pertanyaan Anda! 🚀",
        author="System"
    ).send()

    # Initialize LangGraph system
    try:
        await cl.Message(
            content="🔄 Menginisialisasi LangGraph multi-agent system...",
            author="System"
        ).send()

        langgraph_system = UniversityLangGraphSystem()

        await cl.Message(
            content="✅ **LangGraph System siap digunakan!**\n\n"
                    "🎯 Router agent siap menganalisis pertanyaan Anda\n"
                    "🤖 Workflow otomatis telah dikonfigurasi\n"
                    "📊 Semua agents dalam status standby\n\n"
                    "Silakan ajukan pertanyaan untuk memulai analisis!",
            author="System"
        ).send()

    except Exception as e:
        await cl.Message(
            content=f"❌ **Error menginisialisasi LangGraph:** {str(e)}\n\n"
                    "Pastikan semua dependencies terinstall:\n"
                    "```bash\n"
                    "uv add langgraph langchain langchain-google-genai\n"
                    "```",
            author="System"
        ).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages with LangGraph workflow"""
    global langgraph_system

    if not langgraph_system:
        await cl.Message(
            content="❌ LangGraph system belum diinisialisasi. Silakan restart chat.",
            author="Assistant"
        ).send()
        return

    user_question = message.content.strip()

    # Show processing with LangGraph workflow
    async with cl.Step(name="langgraph_workflow", type="run") as step:
        step.output = "🎯 Memulai LangGraph workflow..."

        try:
            # Process through LangGraph workflow
            result = await langgraph_system.process_query(user_question)

            if not result['success']:
                await cl.Message(
                    content=f"❌ **LangGraph workflow error:**\n\n{result.get('error', 'Unknown error')}",
                    author="Assistant"
                ).send()
                return

            # Display workflow messages (agent communications)
            await display_agent_workflow(result['messages'])

            # Display query classification
            await display_query_classification(result)

            # Display SQL results
            if result['sql_query']:
                await display_sql_results(result)

            # Display data table
            if result['data'] is not None:
                await display_data_table(result['data'], user_question)

                # Display insights
                if result['insights']:
                    await display_insights(result['insights'])

                # Display suggestions with action buttons
                if result['suggestions']:
                    await display_suggestions(result['suggestions'])

        except Exception as e:
            await cl.Message(
                content=f"❌ **LangGraph workflow exception:**\n\n"
                        f"```\n{str(e)}\n```\n\n"
                        f"Silakan coba pertanyaan lain atau restart sistem.",
                author="Assistant"
            ).send()


async def display_agent_workflow(messages):
    """Display the agent workflow messages"""

    if not messages:
        return

    workflow_content = "🤖 **LangGraph Workflow:**\n\n"

    for msg in messages:
        if hasattr(msg, 'content'):
            workflow_content += f"{msg.content}\n"

    await cl.Message(
        content=workflow_content,
        author="Workflow"
    ).send()


async def display_query_classification(result):
    """Display query classification results"""

    query_type = result.get('query_type', 'Unknown')

    type_descriptions = {
        'data_query': '📊 Data Query - Pertanyaan untuk data spesifik',
        'comparison': '⚖️ Comparison - Analisis perbandingan',
        'trend_analysis': '📈 Trend Analysis - Analisis tren waktu',
        'complex_analysis': '🧠 Complex Analysis - Analisis kompleks multi-sumber',
        'simple_info': 'ℹ️ Simple Info - Informasi sederhana'
    }

    description = type_descriptions.get(query_type, f'🔍 {query_type}')

    content = f"🎯 **Query Classification:**\n\n"
    content += f"**Type**: {description}\n"
    content += f"**Original Question**: {result['question']}\n"

    await cl.Message(
        content=content,
        author="Router Agent"
    ).send()


async def display_sql_results(result):
    """Display SQL generation and execution results"""

    sql_query = result['sql_query']
    sql_result = result['sql_result']

    content = f"🔍 **SQL Agent Results:**\n\n"
    content += f"**Generated Query:**\n```sql\n{sql_query}\n```\n\n"
    content += f"**Execution Status**: {'✅ Success' if sql_result.get('success') else '❌ Failed'}\n"
    content += f"**Rows Retrieved**: {sql_result.get('row_count', 0)}\n"

    if sql_result.get('columns'):
        content += f"**Columns**: {', '.join(sql_result['columns'])}\n"

    await cl.Message(
        content=content,
        author="SQL Agent"
    ).send()


async def display_data_table(df: pd.DataFrame, question: str):
    """Display data table with smart formatting"""

    row_count = len(df)

    if row_count == 0:
        await cl.Message(
            content="📊 **Data Results**: Tidak ada data yang ditemukan.",
            author="Data Display"
        ).send()
        return

    # Smart table display based on size
    if row_count <= 8:
        # Small dataset - show all
        table_text = f"📊 **Complete Data** ({row_count} rows):\n\n```\n"
        table_text += df.to_string(index=False, max_cols=6)
        table_text += "\n```"
    else:
        # Large dataset - show sample + summary
        sample_df = df.head(6)
        table_text = f"📊 **Data Sample** (showing 6 of {row_count} rows):\n\n```\n"
        table_text += sample_df.to_string(index=False, max_cols=6)
        table_text += f"\n\n... dan {row_count - 6} baris lainnya\n```"

    await cl.Message(
        content=table_text,
        author="Data Display"
    ).send()


async def display_insights(insights: list):
    """Display insights from Insight Agent"""

    if not insights:
        return

    content = "📊 **Insight Agent Analysis:**\n\n"

    for insight in insights:
        content += f"{insight}\n\n"

    await cl.Message(
        content=content,
        author="Insight Agent"
    ).send()


async def display_suggestions(suggestions: list):
    """Display suggestions as text (simplified version)"""

    if not suggestions:
        return

    content = "💡 **Suggestion Agent Recommendations:**\n\n"
    content += "**Pertanyaan lanjutan yang disarankan:**\n\n"

    for i, suggestion in enumerate(suggestions, 1):
        content += f"{i}. {suggestion}\n"

    content += "\n*Silakan copy-paste salah satu pertanyaan di atas atau ketik pertanyaan Anda sendiri!*"

    # Send without action buttons to avoid validation errors
    await cl.Message(
        content=content,
        author="Suggestion Agent"
    ).send()


# Action callbacks for suggestion buttons
@cl.action_callback("suggestion_1")
async def handle_suggestion_1(action: cl.Action):
    await process_suggestion_click(action.value)


@cl.action_callback("suggestion_2")
async def handle_suggestion_2(action: cl.Action):
    await process_suggestion_click(action.value)


@cl.action_callback("suggestion_3")
async def handle_suggestion_3(action: cl.Action):
    await process_suggestion_click(action.value)


async def process_suggestion_click(suggestion: str):
    """Process a clicked suggestion through LangGraph workflow"""

    await cl.Message(
        content=f"🔄 **Memproses pertanyaan yang dipilih:**\n\n*{suggestion}*",
        author="User Selection"
    ).send()

    # Create mock message and process through workflow
    mock_message = type('MockMessage', (), {'content': suggestion})()
    await main(mock_message)


if __name__ == "__main__":
    # Enhanced config for LangGraph
    cl.config.ui.name = "🤖 University LangGraph Assistant"
    cl.config.ui.description = "AI Multi-Agent System dengan LangGraph untuk Analisis Data Universitas"

    # LangGraph themed colors
    cl.config.ui.theme = {
        "primary": "#1E3A8A",  # Deep blue for LangGraph
        "secondary": "#7C3AED",  # Purple for agents
        "accent": "#F59E0B",  # Orange for workflow
        "background": "#F8FAFC"  # Light background
    }

    cl.run()