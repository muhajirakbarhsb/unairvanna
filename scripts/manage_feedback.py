# scripts/manage_feedback.py
"""
Feedback Management Script for Vanna AI Learning System
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import argparse

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.vanna.setup import UniversityVannaGemini
from src.vanna.feedback import VannaFeedbackSystem, add_feedback_methods_to_vanna
from dotenv import load_dotenv

load_dotenv()


class FeedbackManager:
    """
    Manage and analyze Vanna AI feedback data
    """

    def __init__(self):
        # Initialize Vanna with feedback methods
        add_feedback_methods_to_vanna()

        self.vanna = UniversityVannaGemini()
        self.vanna.connect_to_postgres(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            dbname=os.getenv('POSTGRES_DB', 'university_dwh'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'university123'),
            port=int(os.getenv('POSTGRES_PORT', '5432'))
        )

        self.feedback_system = VannaFeedbackSystem(self.vanna)

    def show_statistics(self):
        """Display comprehensive feedback statistics"""
        print("📊 VANNA AI FEEDBACK STATISTICS")
        print("=" * 50)

        stats = self.feedback_system.get_feedback_stats()

        print(f"📈 Total Queries: {stats.get('total', 0)}")
        print(f"✅ Correct: {stats.get('correct', 0)}")
        print(f"❌ Incorrect: {stats.get('incorrect', 0)}")
        print(f"⏳ Awaiting Feedback: {stats.get('no_feedback', 0)}")
        print(f"📊 Success Rate: {stats.get('success_rate', 0):.1f}%")
        print(f"🔄 Correction Rate: {stats.get('correction_rate', 0):.1f}%")

        # Additional analytics
        self._show_detailed_analytics()

    def _show_detailed_analytics(self):
        """Show detailed analytics from feedback log"""
        try:
            if not os.path.exists("feedback_log.json"):
                print("\n⚠️ No feedback log found")
                return

            with open("feedback_log.json", 'r') as f:
                logs = json.load(f)

            if not logs:
                print("\n⚠️ No feedback data available")
                return

            df = pd.DataFrame(logs)

            print(f"\n📅 TEMPORAL ANALYSIS")
            print("-" * 30)

            # Convert timestamps
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date

            # Daily query count
            daily_counts = df.groupby('date').size()
            print(f"📊 Queries per day (last 7 days):")
            for date, count in daily_counts.tail(7).items():
                print(f"   {date}: {count} queries")

            # Success analysis
            if 'feedback_rating' in df.columns:
                feedback_df = df[df['feedback_received'] == True]
                if not feedback_df.empty:
                    print(f"\n✅ FEEDBACK ANALYSIS")
                    print("-" * 30)

                    success_by_day = feedback_df.groupby(['date', 'feedback_rating']).size().unstack(fill_value=0)
                    print("Recent feedback trends:")
                    print(success_by_day.tail(5))

            # Execution success analysis
            print(f"\n🔧 EXECUTION ANALYSIS")
            print("-" * 30)
            execution_success = df['execution_success'].value_counts()
            print(f"Successful executions: {execution_success.get(True, 0)}")
            print(f"Failed executions: {execution_success.get(False, 0)}")

        except Exception as e:
            print(f"❌ Error analyzing feedback data: {e}")

    def list_pending_feedback(self, limit: int = 10):
        """List queries that need feedback"""
        print(f"⏳ QUERIES AWAITING FEEDBACK (Top {limit})")
        print("=" * 60)

        pending = self.feedback_system.get_queries_for_review(limit)

        if not pending:
            print("✅ No queries awaiting feedback!")
            return

        for i, query in enumerate(pending, 1):
            print(f"\n{i}. Query ID: {query['query_id']}")
            print(f"   📅 Time: {query['timestamp'][:19]}")
            print(f"   ❓ Question: {query['question']}")
            print(f"   🔍 SQL: {query['generated_sql'][:100]}...")
            print(f"   ✅ Success: {query['execution_success']}")
            print(f"   📊 Rows: {query.get('result_count', 0)}")
            print("-" * 60)

    def interactive_feedback_session(self):
        """Interactive session to provide feedback on pending queries"""
        print("🎯 INTERACTIVE FEEDBACK SESSION")
        print("=" * 50)

        pending = self.feedback_system.get_queries_for_review(50)

        if not pending:
            print("✅ No queries awaiting feedback!")
            return

        print(f"Found {len(pending)} queries awaiting feedback.")
        print("Commands: 'c' = correct, 'i' = incorrect, 's' = skip, 'q' = quit")
        print("-" * 50)

        for i, query in enumerate(pending, 1):
            print(f"\n📝 Query {i}/{len(pending)}")
            print(f"❓ Question: {query['question']}")
            print(f"🔍 Generated SQL:")
            print(f"```sql\n{query['generated_sql']}\n```")
            print(f"✅ Execution: {'Success' if query['execution_success'] else 'Failed'}")
            print(f"📊 Result rows: {query.get('result_count', 0)}")

            while True:
                feedback = input("\n👉 Feedback (c/i/s/q): ").lower().strip()

                if feedback == 'q':
                    print("👋 Feedback session ended.")
                    return
                elif feedback == 's':
                    print("⏭️ Skipped.")
                    break
                elif feedback == 'c':
                    # Mark as correct
                    success = self.feedback_system.submit_feedback(
                        query_id=query['query_id'],
                        is_correct=True,
                        feedback_notes="Marked as correct in interactive session"
                    )
                    if success:
                        print("✅ Marked as correct and added to training!")
                    else:
                        print("❌ Error submitting feedback.")
                    break
                elif feedback == 'i':
                    # Mark as incorrect, ask for correction
                    correction = input("🔧 Enter correct SQL (or press Enter to skip): ").strip()

                    success = self.feedback_system.submit_feedback(
                        query_id=query['query_id'],
                        is_correct=False,
                        corrected_sql=correction if correction else None,
                        feedback_notes="Marked as incorrect in interactive session"
                    )

                    if success:
                        if correction:
                            print("🔄 Marked as incorrect with correction!")
                        else:
                            print("❌ Marked as incorrect.")
                    else:
                        print("❌ Error submitting feedback.")
                    break
                else:
                    print("❌ Invalid input. Use 'c', 'i', 's', or 'q'.")

    def export_feedback_data(self, filename: str = None):
        """Export feedback data to CSV"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"feedback_export_{timestamp}.csv"

        try:
            if not os.path.exists("feedback_log.json"):
                print("❌ No feedback log found")
                return

            with open("feedback_log.json", 'r') as f:
                logs = json.load(f)

            if not logs:
                print("❌ No feedback data to export")
                return

            df = pd.DataFrame(logs)
            df.to_csv(filename, index=False)

            print(f"✅ Feedback data exported to: {filename}")
            print(f"📊 Exported {len(df)} records")

        except Exception as e:
            print(f"❌ Error exporting data: {e}")

    def import_feedback_corrections(self, filename: str):
        """Import feedback corrections from CSV"""
        try:
            df = pd.read_csv(filename)

            required_columns = ['query_id', 'is_correct']
            if not all(col in df.columns for col in required_columns):
                print(f"❌ CSV must contain columns: {required_columns}")
                return

            corrections = []
            for _, row in df.iterrows():
                correction = {
                    'query_id': row['query_id'],
                    'is_correct': bool(row['is_correct']),
                    'corrected_sql': row.get('corrected_sql', ''),
                    'notes': row.get('notes', 'Imported from CSV')
                }
                corrections.append(correction)

            applied_count = self.feedback_system.bulk_apply_corrections(corrections)
            print(f"✅ Applied {applied_count}/{len(corrections)} corrections")

        except Exception as e:
            print(f"❌ Error importing corrections: {e}")

    def cleanup_old_feedback(self, days: int = 30):
        """Clean up feedback data older than specified days"""
        try:
            if not os.path.exists("feedback_log.json"):
                print("❌ No feedback log found")
                return

            with open("feedback_log.json", 'r') as f:
                logs = json.load(f)

            cutoff_date = datetime.now() - timedelta(days=days)

            # Filter recent logs
            recent_logs = []
            removed_count = 0

            for log in logs:
                log_date = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                if log_date > cutoff_date:
                    recent_logs.append(log)
                else:
                    removed_count += 1

            # Write back filtered logs
            with open("feedback_log.json", 'w') as f:
                json.dump(recent_logs, f, indent=2, ensure_ascii=False)

            print(f"🧹 Cleaned up {removed_count} old feedback records")
            print(f"📊 Kept {len(recent_logs)} recent records")

        except Exception as e:
            print(f"❌ Error cleaning up feedback: {e}")

    def analyze_query_patterns(self):
        """Analyze patterns in successful vs failed queries"""
        try:
            if not os.path.exists("feedback_log.json"):
                print("❌ No feedback log found")
                return

            with open("feedback_log.json", 'r') as f:
                logs = json.load(f)

            df = pd.DataFrame(logs)

            print("🔍 QUERY PATTERN ANALYSIS")
            print("=" * 50)

            # Analyze feedback patterns
            if 'feedback_rating' in df.columns:
                feedback_df = df[df['feedback_received'] == True]

                if not feedback_df.empty:
                    print("\n📊 Feedback Distribution:")
                    feedback_counts = feedback_df['feedback_rating'].value_counts()
                    for rating, count in feedback_counts.items():
                        percentage = (count / len(feedback_df)) * 100
                        print(f"   {rating}: {count} queries ({percentage:.1f}%)")

                # Analyze query types by success
                print("\n🎯 Success by Query Characteristics:")

                # Simple pattern analysis
                correct_queries = feedback_df[feedback_df['feedback_rating'] == 'correct']
                incorrect_queries = feedback_df[feedback_df['feedback_rating'] == 'incorrect']

                if not correct_queries.empty:
                    print(f"\n✅ Successful Query Patterns:")
                    self._analyze_sql_patterns(correct_queries['generated_sql'].tolist())

                if not incorrect_queries.empty:
                    print(f"\n❌ Failed Query Patterns:")
                    self._analyze_sql_patterns(incorrect_queries['generated_sql'].tolist())

        except Exception as e:
            print(f"❌ Error analyzing patterns: {e}")

    def _analyze_sql_patterns(self, sql_queries: List[str]):
        """Analyze common patterns in SQL queries"""
        patterns = {
            'SELECT COUNT': 0,
            'JOIN': 0,
            'GROUP BY': 0,
            'ORDER BY': 0,
            'WHERE': 0,
            'HAVING': 0,
            'SUBQUERY': 0
        }

        for sql in sql_queries:
            sql_upper = sql.upper()
            if 'SELECT COUNT' in sql_upper:
                patterns['SELECT COUNT'] += 1
            if 'JOIN' in sql_upper:
                patterns['JOIN'] += 1
            if 'GROUP BY' in sql_upper:
                patterns['GROUP BY'] += 1
            if 'ORDER BY' in sql_upper:
                patterns['ORDER BY'] += 1
            if 'WHERE' in sql_upper:
                patterns['WHERE'] += 1
            if 'HAVING' in sql_upper:
                patterns['HAVING'] += 1
            if sql_upper.count('SELECT') > 1:
                patterns['SUBQUERY'] += 1

        total = len(sql_queries)
        for pattern, count in patterns.items():
            if count > 0:
                percentage = (count / total) * 100
                print(f"   {pattern}: {count}/{total} ({percentage:.1f}%)")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Vanna AI Feedback Management")
    parser.add_argument('command', choices=[
        'stats', 'pending', 'interactive', 'export', 'import', 'cleanup', 'patterns'
    ], help='Command to execute')
    parser.add_argument('--file', help='File for import/export operations')
    parser.add_argument('--days', type=int, default=30, help='Days for cleanup operation')
    parser.add_argument('--limit', type=int, default=10, help='Limit for pending queries')

    args = parser.parse_args()

    manager = FeedbackManager()

    try:
        if args.command == 'stats':
            manager.show_statistics()

        elif args.command == 'pending':
            manager.list_pending_feedback(args.limit)

        elif args.command == 'interactive':
            manager.interactive_feedback_session()

        elif args.command == 'export':
            manager.export_feedback_data(args.file)

        elif args.command == 'import':
            if not args.file:
                print("❌ --file parameter required for import")
                return
            manager.import_feedback_corrections(args.file)

        elif args.command == 'cleanup':
            manager.cleanup_old_feedback(args.days)

        elif args.command == 'patterns':
            manager.analyze_query_patterns()

    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()