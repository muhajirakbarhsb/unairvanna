# src/agents/langgraph_system.py - COMPLETE VERSION
import os
import asyncio
from typing import Dict, Any, List, Annotated, Literal
from typing_extensions import TypedDict
import pandas as pd

from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

import io
import base64
from PIL import Image

# Import Vanna - use try/except for flexible imports
try:
    from ..vanna.setup import UniversityVannaGemini
except (ImportError, ValueError):
    # Fallback for when running directly or different import context
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from vanna.setup import UniversityVannaGemini


# Define the state that gets passed between agents
class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    user_question: str
    query_type: str
    sql_query: str
    sql_result: Dict[str, Any]
    data: pd.DataFrame
    insights: List[str]
    suggestions: List[str]
    strategy_response: str
    visualization_needed: bool
    current_agent: str
    next_action: str
    error: str


class UniversityLangGraphSystem:
    """Enhanced LangGraph-based multi-agent system for university data analysis"""

    def __init__(self):
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv('GEMINI_API_KEY'),
            temperature=0.1
        )

        # Initialize Vanna for SQL generation
        self.vanna = UniversityVannaGemini()
        self.vanna.connect_to_postgres(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            dbname=os.getenv('POSTGRES_DB', 'university_dwh'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'university123'),
            port=int(os.getenv('POSTGRES_PORT', '5432'))
        )

        # Build the agent graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the enhanced LangGraph workflow"""

        # Create the graph
        workflow = StateGraph(AgentState)

        # Add nodes (agents)
        workflow.add_node("router", self.router_agent)
        workflow.add_node("sql_agent", self.sql_agent)
        workflow.add_node("strategy_agent", self.strategy_agent)
        workflow.add_node("insight_agent", self.insight_agent)
        workflow.add_node("suggestion_agent", self.suggestion_agent)
        workflow.add_node("strategy_suggestion_agent", self.strategy_suggestion_agent)
        workflow.add_node("visualization_agent", self.visualization_agent)
        workflow.add_node("summarizer", self.summarizer_agent)

        # Define the workflow edges
        workflow.add_edge(START, "router")

        # Router decides: SQL path or Strategy path
        workflow.add_conditional_edges(
            "router",
            self.route_decision,
            {
                "sql": "sql_agent",
                "strategy": "strategy_agent",
                "error": END
            }
        )

        # SQL path: After SQL, go to insights
        workflow.add_conditional_edges(
            "sql_agent",
            self.post_sql_decision,
            {
                "insights": "insight_agent",
                "error": END
            }
        )

        # Strategy path: After strategy, go to strategy suggestions
        workflow.add_edge("strategy_agent", "strategy_suggestion_agent")

        # After insights, check if visualization is needed
        workflow.add_conditional_edges(
            "insight_agent",
            self.post_insight_decision,
            {
                "visualization": "visualization_agent",
                "suggestions": "suggestion_agent"
            }
        )

        # After visualization, go to suggestions
        workflow.add_edge("visualization_agent", "suggestion_agent")

        # After suggestions (data path), summarize
        workflow.add_edge("suggestion_agent", "summarizer")

        # After strategy suggestions, summarize
        workflow.add_edge("strategy_suggestion_agent", "summarizer")

        # End at summarizer
        workflow.add_edge("summarizer", END)

        return workflow.compile()

    def router_agent(self, state: AgentState) -> AgentState:
        """Enhanced Router agent - decides if question needs data query or direct answer"""

        question = state["user_question"]

        # Use LLM to classify the query with enhanced logic
        system_prompt = """
        You are an intelligent Router Agent for a university data analysis system.

        Analyze the user question and determine:
        1. Does this question require DATABASE QUERY to answer? 
        2. Or can it be answered with GENERAL KNOWLEDGE/STRATEGY?

        DATABASE QUERY needed for:
        - Questions asking for specific numbers, counts, statistics
        - Questions about "berapa", "siapa", "apa saja", "daftar"
        - Questions requiring actual data from the university database
        - Comparisons needing real data

        GENERAL KNOWLEDGE/STRATEGY for:
        - Questions asking "bagaimana", "strategi", "cara", "metode"
        - Questions about recommendations, best practices
        - Questions about general educational concepts
        - Questions that can be answered without specific university data

        Also determine visualization needs and query complexity.

        Respond in this exact format:
        Needs Database: [yes/no]
        Query Type: [data_query/comparison/trend_analysis/complex_analysis/strategy_question]
        Visualization Needed: [true/false]
        Reasoning: [brief explanation]
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analyze this university question: {question}")
        ]

        try:
            response = self.llm.invoke(messages)
            response_text = response.content

            # Parse the response
            lines = response_text.split('\n')
            needs_database = False
            query_type = "strategy_question"  # default
            viz_needed = False
            reasoning = ""

            for line in lines:
                if line.startswith("Needs Database:"):
                    needs_database = line.split(":")[1].strip().lower() == "yes"
                elif line.startswith("Query Type:"):
                    query_type = line.split(":")[1].strip()
                elif line.startswith("Visualization Needed:"):
                    viz_needed = line.split(":")[1].strip().lower() == "true"
                elif line.startswith("Reasoning:"):
                    reasoning = line.split(":")[1].strip()

            state["query_type"] = query_type
            state["visualization_needed"] = viz_needed
            state["current_agent"] = "router"

            if needs_database:
                state["next_action"] = "sql"
                state["messages"].append(
                    AIMessage(
                        content=f"🎯 **Router Agent**: Query memerlukan data dari database. Tipe: '{query_type}', visualisasi {'diperlukan' if viz_needed else 'tidak diperlukan'}")
                )
            else:
                state["next_action"] = "strategy"
                state["messages"].append(
                    AIMessage(
                        content=f"🎯 **Router Agent**: Query dapat dijawab langsung sebagai strategi/rekomendasi. Tipe: '{query_type}'")
                )

        except Exception as e:
            state["error"] = f"Router error: {str(e)}"
            state["next_action"] = "error"

        return state

    def sql_agent(self, state: AgentState) -> AgentState:
        """SQL Agent - generates and executes SQL queries"""

        try:
            question = state["user_question"]

            # Generate SQL using Vanna
            sql_query = self.vanna.generate_sql(question)
            state["sql_query"] = sql_query

            # Execute SQL
            result_df = self.vanna.run_sql(sql_query)

            if result_df is not None and not result_df.empty:
                state["data"] = result_df
                state["sql_result"] = {
                    "success": True,
                    "row_count": len(result_df),
                    "columns": list(result_df.columns)
                }
                state["next_action"] = "insights"

                state["messages"].append(
                    AIMessage(
                        content=f"🔍 **SQL Agent**: Query berhasil dijalankan, ditemukan {len(result_df)} baris data")
                )
            else:
                state["sql_result"] = {"success": False, "message": "No data returned"}
                state["next_action"] = "error"

        except Exception as e:
            state["error"] = f"SQL Agent error: {str(e)}"
            state["next_action"] = "error"

        state["current_agent"] = "sql"
        return state

    def strategy_agent(self, state: AgentState) -> AgentState:
        """Strategy Agent - answers questions that don't need database queries"""

        try:
            question = state["user_question"]
            query_type = state["query_type"]

            system_prompt = f"""
            You are a Strategy Agent for university management and education.
            Provide comprehensive, actionable strategies and recommendations.

            You specialize in:
            - University management strategies
            - Student academic improvement methods  
            - Faculty development approaches
            - Educational best practices
            - Student engagement techniques
            - Academic program optimization

            Question Type: {query_type}

            Provide detailed, practical strategies in Indonesian.
            Structure your response with:
            1. Main strategy overview
            2. Specific action steps
            3. Implementation considerations
            4. Expected outcomes

            Be comprehensive but concise. Use bullet points and clear formatting.
            """

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Pertanyaan: {question}")
            ]

            response = self.llm.invoke(messages)
            strategy_content = response.content

            state["messages"].append(
                AIMessage(content=f"📋 **Strategy Agent**: Menghasilkan strategi komprehensif untuk pertanyaan")
            )

            # Store the strategy response
            state["strategy_response"] = strategy_content
            state["current_agent"] = "strategy"
            state["next_action"] = "strategy_suggestions"

        except Exception as e:
            state["error"] = f"Strategy Agent error: {str(e)}"
            state["strategy_response"] = "Maaf, tidak dapat menghasilkan strategi saat ini."
            state["next_action"] = "error"

        return state

    def insight_agent(self, state: AgentState) -> AgentState:
        """Enhanced Insight Agent - generates data-driven insights"""

        try:
            question = state["user_question"]
            data = state["data"]
            query_type = state["query_type"]

            # Generate insights using LLM with focus on data
            system_prompt = f"""
            You are a Data Insight Agent for university analytics.
            Generate actionable insights from university data in Indonesian.

            Query Type: {query_type}

            Focus on:
            1. Key findings from the data
            2. Patterns and trends
            3. Actionable recommendations for university management
            4. Comparative analysis
            5. Areas of concern or opportunity

            Provide 3-4 specific insights based on the actual data shown.
            Each insight should be practical and actionable.
            Start each insight with an emoji and make it conversational.
            """

            # Prepare detailed data summary
            data_summary = f"""
            Original Question: {question}
            Data Shape: {data.shape}
            Columns: {list(data.columns)}

            Complete Data:
            {data.to_string()}

            Statistical Summary:
            {data.describe().to_string() if len(data.select_dtypes(include=['number']).columns) > 0 else 'No numeric data for statistics'}
            """

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Analyze this university data:\n\n{data_summary}")
            ]

            response = self.llm.invoke(messages)
            insights_text = response.content

            # Parse insights into list - be more flexible with parsing
            insights = []
            for line in insights_text.split('\n'):
                line = line.strip()
                if line and (any(emoji in line for emoji in ['📊', '💡', '🔍', '📈', '⚠️', '✅', '🎯', '📋', '🔄']) or
                             line.startswith(('•', '-', '*', '1.', '2.', '3.', '4.'))):
                    insights.append(line)

            # If no emoji-based insights found, try to extract meaningful sentences
            if not insights:
                sentences = [s.strip() for s in insights_text.split('.') if len(s.strip()) > 20]
                insights = [f"💡 {s}" for s in sentences[:4]]

            state["insights"] = insights
            state["current_agent"] = "insight"

            if state["visualization_needed"]:
                state["next_action"] = "visualization"
            else:
                state["next_action"] = "suggestions"

            state["messages"].append(
                AIMessage(content=f"📊 **Insight Agent**: Menghasilkan {len(insights)} insights dari analisis data")
            )

        except Exception as e:
            state["error"] = f"Insight Agent error: {str(e)}"
            state["insights"] = [f"❌ Error menghasilkan insights: {str(e)}"]
            state["next_action"] = "suggestions"

        return state

    def suggestion_agent(self, state: AgentState) -> AgentState:
        """Suggestion Agent - generates follow-up questions for data queries"""

        try:
            question = state["user_question"]
            insights = state.get("insights", [])
            query_type = state["query_type"]

            system_prompt = f"""
            You are a Suggestion Agent for university data analysis.
            Based on the current analysis, suggest 3-4 relevant follow-up questions in Indonesian.

            Original Query Type: {query_type}

            Suggestions should:
            1. Build upon the current analysis
            2. Provide additional business value for university management
            3. Be specific and actionable
            4. Lead to deeper insights

            Return only the questions, one per line, without numbering.
            """

            context = f"""
            Original Question: {question}

            Generated Insights:
            {chr(10).join(insights)}
            """

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=context)
            ]

            response = self.llm.invoke(messages)
            suggestions_text = response.content

            # Parse suggestions
            suggestions = [line.strip() for line in suggestions_text.split('\n') if line.strip() and '?' in line]

            state["suggestions"] = suggestions[:4]  # Limit to 4
            state["current_agent"] = "suggestion"
            state["next_action"] = "summarize"

            state["messages"].append(
                AIMessage(content=f"💡 **Suggestion Agent**: Menghasilkan {len(suggestions)} pertanyaan lanjutan")
            )

        except Exception as e:
            state["error"] = f"Suggestion Agent error: {str(e)}"
            state["suggestions"] = ["Coba analisis data dari perspektif yang berbeda"]

        return state

    def strategy_suggestion_agent(self, state: AgentState) -> AgentState:
        """Generate suggestions for strategy questions"""

        try:
            question = state["user_question"]

            system_prompt = """
            Generate 3-4 follow-up questions related to university strategy and management.
            Focus on practical implementation, measurement, and optimization aspects.

            Return questions in Indonesian, one per line, without numbering.
            """

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Original question: {question}")
            ]

            response = self.llm.invoke(messages)
            suggestions_text = response.content

            # Parse suggestions
            suggestions = [line.strip() for line in suggestions_text.split('\n') if line.strip() and '?' in line]

            state["suggestions"] = suggestions[:4]
            state["current_agent"] = "strategy_suggestion"
            state["next_action"] = "summarize"

            state["messages"].append(
                AIMessage(
                    content=f"💡 **Strategy Suggestion Agent**: Menghasilkan {len(suggestions)} pertanyaan lanjutan")
            )

        except Exception as e:
            state["error"] = f"Strategy Suggestion Agent error: {str(e)}"
            state["suggestions"] = ["Bagaimana mengukur efektivitas strategi ini?"]

        return state

    def visualization_agent(self, state: AgentState) -> AgentState:
        """Visualization Agent - determines what visualizations would be helpful"""

        try:
            data = state["data"]
            query_type = state["query_type"]

            # Analyze data for visualization opportunities
            viz_recommendations = []

            numeric_cols = data.select_dtypes(include=['number']).columns
            categorical_cols = data.select_dtypes(include=['object']).columns

            if len(numeric_cols) > 0 and len(categorical_cols) > 0:
                viz_recommendations.append("📊 Bar chart untuk perbandingan kategori")

            if len(numeric_cols) > 1:
                viz_recommendations.append("📈 Scatter plot untuk korelasi")

            if 'tahun' in str(data.columns).lower() or 'semester' in str(data.columns).lower():
                viz_recommendations.append("📉 Line chart untuk trend waktu")

            if len(viz_recommendations) == 0:
                viz_recommendations.append("📋 Tabel data sudah optimal untuk visualisasi")

            state["messages"].append(
                AIMessage(content=f"📊 **Visualization Agent**: {', '.join(viz_recommendations)}")
            )

            state["current_agent"] = "visualization"
            state["next_action"] = "suggestions"

        except Exception as e:
            state["error"] = f"Visualization Agent error: {str(e)}"

        return state

    def summarizer_agent(self, state: AgentState) -> AgentState:
        """Summarizer Agent - creates final summary"""

        try:
            question = state["user_question"]
            sql_result = state.get("sql_result", {})
            insights = state.get("insights", [])
            suggestions = state.get("suggestions", [])
            strategy_response = state.get("strategy_response", "")

            if strategy_response:
                summary = f"""
                🎯 **Analisis Strategi Selesai untuk**: {question}

                📋 **Strategi**: Rekomendasi komprehensif telah diberikan
                💡 **Saran**: {len(suggestions)} pertanyaan lanjutan tersedia

                ✅ **Status**: Analisis strategi berhasil diselesaikan
                """
            else:
                summary = f"""
                🎯 **Analisis Selesai untuk**: {question}

                📊 **Hasil**: {sql_result.get('row_count', 0)} baris data ditemukan
                💡 **Insights**: {len(insights)} wawasan dihasilkan
                🔍 **Saran**: {len(suggestions)} pertanyaan lanjutan tersedia

                ✅ **Status**: Analisis multi-agent berhasil diselesaikan
                """

            state["messages"].append(
                AIMessage(content=summary)
            )

            state["current_agent"] = "summarizer"

        except Exception as e:
            state["error"] = f"Summarizer error: {str(e)}"

        return state

    # Enhanced decision functions
    def route_decision(self, state: AgentState) -> Literal["sql", "strategy", "error"]:
        """Decide whether to use SQL path or Strategy path"""
        if state.get("error"):
            return "error"
        return state.get("next_action", "sql")

    def save_graph_image(self, filepath: str = "langgraph_workflow.png") -> bool:
        """Save graph visualization as PNG file"""
        try:
            img_data = self.graph.get_graph().draw_mermaid_png()

            with open(filepath, 'wb') as f:
                f.write(img_data)

            print(f"✅ Graph saved as {filepath}")
            return True

        except Exception as e:
            print(f"❌ Error saving graph: {e}")
            return False

    def get_mermaid_graph(self) -> str:
        """Get Mermaid diagram code for the graph"""
        try:
            return self.graph.get_graph().draw_mermaid()
        except Exception as e:
            print(f"Error generating Mermaid graph: {e}")
            return "graph TD\n    A[Error generating graph]"

    def get_graph_info(self) -> dict:
        """Get graph structure information"""
        try:
            graph_obj = self.graph.get_graph()
            return {
                'nodes': list(graph_obj.nodes),
                'edges': list(graph_obj.edges),
                'node_count': len(graph_obj.nodes),
                'edge_count': len(graph_obj.edges)
            }
        except Exception as e:
            print(f"Error getting graph info: {e}")
            return {'nodes': [], 'edges': [], 'node_count': 0, 'edge_count': 0}

    def post_sql_decision(self, state: AgentState) -> Literal["insights", "error"]:
        """Decide what to do after SQL execution"""
        return "error" if state.get("error") or not state["sql_result"]["success"] else "insights"

    def post_insight_decision(self, state: AgentState) -> Literal["visualization", "suggestions"]:
        """Decide whether to use visualization agent"""
        return "visualization" if state.get("visualization_needed", False) else "suggestions"

    async def process_query(self, question: str) -> Dict[str, Any]:
        """Process a query through the LangGraph workflow"""

        # Initialize state
        initial_state = AgentState(
            messages=[],
            user_question=question,
            query_type="",
            sql_query="",
            sql_result={},
            data=None,
            insights=[],
            suggestions=[],
            strategy_response="",
            visualization_needed=False,
            current_agent="",
            next_action="",
            error=""
        )

        try:
            # Run the graph
            final_state = await asyncio.to_thread(self.graph.invoke, initial_state)

            return {
                "success": not bool(final_state.get("error")),
                "question": question,
                "query_type": final_state.get("query_type", ""),
                "sql_query": final_state.get("sql_query", ""),
                "sql_result": final_state.get("sql_result", {}),
                "data": final_state.get("data"),
                "insights": final_state.get("insights", []),
                "suggestions": final_state.get("suggestions", []),
                "strategy_response": final_state.get("strategy_response", ""),
                "messages": final_state.get("messages", []),
                "error": final_state.get("error", "")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Graph execution error: {str(e)}",
                "question": question,
                "sql_query": "",
                "sql_result": {},
                "data": None,
                "insights": [],
                "suggestions": [],
                "strategy_response": "",
                "messages": []
            }