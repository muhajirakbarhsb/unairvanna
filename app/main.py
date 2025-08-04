# app/main.py - Updated with Feedback System
import os
import sys
import asyncio
from typing import Optional
import chainlit as cl
import pandas as pd
from dotenv import load_dotenv

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.agents.langgraph_system import UniversityLangGraphSystem
    from src.vanna.feedback import add_feedback_methods_to_vanna
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    from agents.langgraph_system import UniversityLangGraphSystem
    from vanna.feedback import add_feedback_methods_to_vanna

# Load environment variables
load_dotenv()

# Add feedback methods to Vanna
add_feedback_methods_to_vanna()

# Global LangGraph system
langgraph_system: Optional[UniversityLangGraphSystem] = None
current_query_id: Optional[str] = None


@cl.on_chat_start
async def start():
    """Initialize the chat session with LangGraph and Feedback System"""
    global langgraph_system

    # Send welcome message with feedback info
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
                "🔄 **Sistem Pembelajaran:**\n"
                "• **Feedback system** - beri rating pada hasil SQL query\n"
                "• **Continuous learning** - sistem belajar dari koreksi Anda\n"
                "• **Accuracy tracking** - monitor performa sistem\n\n"
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
            content="🔄 Menginisialisasi LangGraph multi-agent system dengan feedback learning...",
            author="System"
        ).send()

        langgraph_system = UniversityLangGraphSystem()

        await cl.Message(
            content="✅ **LangGraph System dengan Feedback Learning siap digunakan!**\n\n"
                    "🎯 Router agent siap menganalisis pertanyaan Anda\n"
                    "🤖 Workflow otomatis telah dikonfigurasi\n"
                    "📊 Semua agents dalam status standby\n"
                    "🔄 Feedback system aktif untuk pembelajaran berkelanjutan\n\n"
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
    """Handle incoming messages with LangGraph workflow and feedback tracking"""
    global langgraph_system, current_query_id

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

            # Display SQL results with feedback tracking
            if result['sql_query']:
                current_query_id = await display_sql_results_with_feedback(result, user_question)

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


async def display_sql_results_with_feedback(result, user_question):
    """Display SQL generation and execution results with feedback options"""

    sql_query = result['sql_query']
    sql_result = result['sql_result']

    content = f"🔍 **SQL Agent Results:**\n\n"
    content += f"**Generated Query:**\n```sql\n{sql_query}\n```\n\n"
    content += f"**Execution Status**: {'✅ Success' if sql_result.get('success') else '❌ Failed'}\n"
    content += f"**Rows Retrieved**: {sql_result.get('row_count', 0)}\n"

    if sql_result.get('columns'):
        content += f"**Columns**: {', '.join(sql_result['columns'])}\n"

    # Track query for feedback if execution was successful
    query_id = None
    if sql_result.get('success') and result.get('data') is not None:
        try:
            # Track the query execution for feedback
            vanna_instance = langgraph_system.vanna
            query_id = vanna_instance.track_query_for_feedback(
                question=user_question,
                sql=sql_query,
                result_df=result['data']
            )

            content += f"\n**Query ID**: `{query_id}` (untuk feedback)\n"

        except Exception as e:
            print(f"Warning: Could not track query for feedback: {e}")

    # Add feedback buttons if query was tracked
    actions = []
    if query_id:
        actions = [
            cl.Action(
                name="feedback_correct",
                payload={"query_id": query_id},
                description="✅ SQL Query Benar",
                label="✅ Benar"
            ),
            cl.Action(
                name="feedback_incorrect", 
                payload={"query_id": query_id},
                description="❌ SQL Query Salah",
                label="❌ Salah"
            ),
            cl.Action(
                name="show_feedback_stats",
                payload={"action": "stats"},
                description="📊 Lihat Statistik Feedback",
                label="📊 Stats"
            )
        ]

    await cl.Message(
        content=content,
        author="SQL Agent",
        actions=actions
    ).send()

    return query_id


# Feedback action handlers
@cl.action_callback("feedback_correct")
async def handle_correct_feedback(action: cl.Action):
    """Handle positive feedback"""
    query_id = action.payload.get("query_id")

    try:
        vanna_instance = langgraph_system.vanna
        success = vanna_instance.submit_query_feedback(
            query_id=query_id,
            is_correct=True,
            notes="User confirmed query is correct"
        )

        if success:
            await cl.Message(
                content="✅ **Feedback Diterima!**\n\n"
                        "Terima kasih! Query SQL telah ditandai sebagai **benar** dan ditambahkan ke training data.\n"
                        "Sistem akan belajar dari contoh positif ini untuk pertanyaan serupa di masa depan.",
                author="Feedback System"
            ).send()
        else:
            await cl.Message(
                content="❌ **Error:** Tidak dapat menyimpan feedback. Query ID mungkin tidak valid.",
                author="Feedback System"
            ).send()

    except Exception as e:
        await cl.Message(
            content=f"❌ **Error menyimpan feedback:** {str(e)}",
            author="Feedback System"
        ).send()


@cl.action_callback("feedback_incorrect")
async def handle_incorrect_feedback(action: cl.Action):
    """Handle negative feedback with correction option"""
    query_id = action.payload.get("query_id")

    # Ask for correction
    await cl.Message(
        content="❌ **SQL Query Tidak Benar**\n\n"
                "Silakan berikan **SQL query yang benar** untuk pertanyaan ini, atau ketik 'skip' jika tidak ingin memberikan koreksi.\n\n"
                "Format: Ketik SQL query yang benar, contoh:\n"
                "```sql\n"
                "SELECT COUNT(*) FROM dwh.dim_mahasiswa WHERE status_mahasiswa = 'Aktif';\n"
                "```",
        author="Feedback System"
    ).send()

    # Store query_id for the next message
    cl.user_session.set("correction_query_id", query_id)
    cl.user_session.set("awaiting_correction", True)


@cl.action_callback("show_feedback_stats")
async def handle_show_stats(action: cl.Action):
    """Show feedback statistics"""
    try:
        vanna_instance = langgraph_system.vanna
        stats = vanna_instance.get_training_stats()

        content = "📊 **Statistik Feedback & Learning**\n\n"
        content += f"**Total Queries**: {stats.get('total', 0)}\n"
        content += f"**✅ Correct**: {stats.get('correct', 0)}\n"
        content += f"**❌ Incorrect**: {stats.get('incorrect', 0)}\n"
        content += f"**⏳ No Feedback**: {stats.get('no_feedback', 0)}\n"
        content += f"**📈 Success Rate**: {stats.get('success_rate', 0):.1f}%\n"
        content += f"**🔄 Correction Rate**: {stats.get('correction_rate', 0):.1f}%\n\n"
        content += "*Semakin banyak feedback yang Anda berikan, semakin akurat sistem akan menjadi!*"

        await cl.Message(
            content=content,
            author="Feedback System"
        ).send()

    except Exception as e:
        await cl.Message(
            content=f"❌ **Error mengambil statistik:** {str(e)}",
            author="Feedback System"
        ).send()


# Handle correction input
@cl.on_message
async def handle_correction_input(message: cl.Message):
    """Handle user correction input"""
    if not cl.user_session.get("awaiting_correction", False):
        return await main(message)  # Process normally

    correction_query_id = cl.user_session.get("correction_query_id")
    user_input = message.content.strip()

    # Clear the correction state
    cl.user_session.set("awaiting_correction", False)
    cl.user_session.set("correction_query_id", None)

    if user_input.lower() == 'skip':
        # Submit negative feedback without correction
        try:
            vanna_instance = langgraph_system.vanna
            success = vanna_instance.submit_query_feedback(
                query_id=correction_query_id,
                is_correct=False,
                notes="User marked as incorrect but did not provide correction"
            )

            await cl.Message(
                content="⚠️ **Feedback tanpa koreksi diterima.**\n\n"
                        "Query ditandai sebagai salah. Pertimbangkan untuk memberikan koreksi di masa depan agar sistem dapat belajar lebih baik.",
                author="Feedback System"
            ).send()

        except Exception as e:
            await cl.Message(
                content=f"❌ **Error menyimpan feedback:** {str(e)}",
                author="Feedback System"
            ).send()
    else:
        # Submit correction
        try:
            vanna_instance = langgraph_system.vanna
            success = vanna_instance.submit_query_feedback(
                query_id=correction_query_id,
                is_correct=False,
                corrected_sql=user_input,
                notes="User provided corrected SQL query"
            )

            if success:
                await cl.Message(
                    content="🔄 **Koreksi Diterima!**\n\n"
                            "Terima kasih! SQL query yang benar telah ditambahkan ke training data.\n"
                            "Sistem akan belajar dari koreksi ini untuk memberikan hasil yang lebih akurat.\n\n"
                            f"**SQL yang benar:**\n```sql\n{user_input}\n```",
                    author="Feedback System"
                ).send()
            else:
                await cl.Message(
                    content="❌ **Error:** Tidak dapat menyimpan koreksi.",
                    author="Feedback System"
                ).send()

        except Exception as e:
            await cl.Message(
                content=f"❌ **Error menyimpan koreksi:** {str(e)}",
                author="Feedback System"
            ).send()


# Keep other existing functions unchanged
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
    """Display suggestions as text"""
    if not suggestions:
        return

    content = "💡 **Suggestion Agent Recommendations:**\n\n"
    content += "**Pertanyaan lanjutan yang disarankan:**\n\n"

    for i, suggestion in enumerate(suggestions, 1):
        content += f"{i}. {suggestion}\n"

    content += "\n*Silakan copy-paste salah satu pertanyaan di atas atau ketik pertanyaan Anda sendiri!*"

    await cl.Message(
        content=content,
        author="Suggestion Agent"
    ).send()


if __name__ == "__main__":
    cl.run()