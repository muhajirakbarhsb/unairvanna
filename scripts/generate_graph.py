# scripts/generate_graph.py
"""
Standalone script to generate and save LangGraph workflow visualization
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.agents.langgraph_system import UniversityLangGraphSystem
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def generate_graph_visualization():
    """Generate and save LangGraph visualization"""

    print("🎨 LangGraph Visualization Generator")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    # Check for required API key
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not found in environment variables")
        print("Please set your Gemini API key in .env file")
        return False

    try:
        print("🔄 Initializing LangGraph system...")

        # Initialize the system
        system = UniversityLangGraphSystem()

        print("✅ LangGraph system initialized successfully")
        print("📊 Generating graph visualization...")

        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Generate different formats
        outputs = []

        # 1. PNG Image
        try:
            png_filename = f"langgraph_workflow_{timestamp}.png"
            success = system.save_graph_image(png_filename)
            if success:
                outputs.append(f"📸 PNG: {png_filename}")
            else:
                print("⚠️  PNG generation failed")
        except Exception as e:
            print(f"⚠️  PNG generation error: {e}")

        # 2. Mermaid diagram
        try:
            mermaid_code = system.get_mermaid_graph()
            if mermaid_code:
                mermaid_filename = f"langgraph_workflow_{timestamp}.mmd"
                with open(mermaid_filename, 'w', encoding='utf-8') as f:
                    f.write(mermaid_code)
                outputs.append(f"🔷 Mermaid: {mermaid_filename}")
        except Exception as e:
            print(f"⚠️  Mermaid generation error: {e}")

        # 3. Text structure
        try:
            text_filename = f"langgraph_structure_{timestamp}.txt"
            with open(text_filename, 'w', encoding='utf-8') as f:
                f.write("LangGraph Structure\n")
                f.write("=" * 30 + "\n\n")

                # Get nodes and edges
                graph_obj = system.graph.get_graph()
                nodes = list(graph_obj.nodes)
                edges = list(graph_obj.edges)

                f.write(f"Nodes ({len(nodes)}):\n")
                for i, node in enumerate(nodes, 1):
                    f.write(f"  {i}. {node}\n")

                f.write(f"\nEdges ({len(edges)}):\n")
                for i, edge in enumerate(edges, 1):
                    f.write(f"  {i}. {edge}\n")

                f.write(f"\nWorkflow Description:\n")
                f.write("- Router Agent decides between SQL and Strategy paths\n")
                f.write("- SQL path: sql_agent → insight_agent → visualization_agent → suggestion_agent\n")
                f.write("- Strategy path: strategy_agent → strategy_suggestion_agent\n")
                f.write("- Both paths end at summarizer → END\n")

            outputs.append(f"📄 Text: {text_filename}")
        except Exception as e:
            print(f"⚠️  Text structure error: {e}")

        # 4. HTML visualization (Mermaid embedded)
        try:
            if 'mermaid_code' in locals():
                html_filename = f"langgraph_workflow_{timestamp}.html"
                html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>University LangGraph Workflow</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1E3A8A;
            text-align: center;
            margin-bottom: 30px;
        }}
        .description {{
            background: #E0F2FE;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 4px solid #0369A1;
        }}
        #diagram {{
            text-align: center;
            margin: 30px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 University LangGraph Workflow</h1>

        <div class="description">
            <h3>🤖 Multi-Agent System Architecture</h3>
            <p><strong>Router Agent:</strong> Intelligently decides between SQL and Strategy paths based on question type</p>
            <p><strong>SQL Path:</strong> For data queries → SQL Agent → Insight Agent → Visualization Agent → Suggestion Agent</p>
            <p><strong>Strategy Path:</strong> For strategy questions → Strategy Agent → Strategy Suggestion Agent</p>
            <p><strong>Convergence:</strong> Both paths converge at Summarizer Agent before ending</p>
        </div>

        <div id="diagram">
            <div class="mermaid">
{mermaid_code}
            </div>
        </div>

        <div class="description">
            <p><em>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</em></p>
        </div>
    </div>

    <script>
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'default',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true
            }}
        }});
    </script>
</body>
</html>"""

                with open(html_filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                outputs.append(f"🌐 HTML: {html_filename}")
        except Exception as e:
            print(f"⚠️  HTML generation error: {e}")

        # Show results
        if outputs:
            print("\n🎉 Graph visualization generated successfully!")
            print("\nGenerated files:")
            for output in outputs:
                print(f"  ✅ {output}")

            print(f"\n📂 Files saved in current directory:")
            print(f"   {os.getcwd()}")

            # Show usage instructions
            print(f"\n🔍 How to view:")
            if any("PNG" in output for output in outputs):
                print("  • Open .png file in any image viewer")
            if any("HTML" in output for output in outputs):
                print("  • Open .html file in web browser for interactive view")
            if any("Mermaid" in output for output in outputs):
                print("  • Upload .mmd file to https://mermaid.live for editing")
        else:
            print("❌ No files generated. Check error messages above.")
            return False

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def get_mermaid_graph(system):
    """Get Mermaid diagram code"""
    try:
        return system.graph.get_graph().draw_mermaid()
    except Exception as e:
        print(f"Error generating Mermaid: {e}")
        return None


def main():
    """Main function"""
    if not generate_graph_visualization():
        print("\n💡 Troubleshooting:")
        print("  1. Install dependencies: uv add graphviz pillow")
        print("  2. Install system graphviz:")
        print("     - macOS: brew install graphviz")
        print("     - Ubuntu: sudo apt-get install graphviz")
        print("     - Windows: Download from https://graphviz.org/download/")
        print("  3. Set GEMINI_API_KEY in .env file")
        sys.exit(1)


if __name__ == "__main__":
    main()