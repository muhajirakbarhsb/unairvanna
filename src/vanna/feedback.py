# src/vanna/feedback.py
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import os
from .setup import UniversityVannaGemini


class VannaFeedbackSystem:
    """
    Feedback system for Vanna AI to learn from user corrections
    """

    def __init__(self, vanna_instance: UniversityVannaGemini):
        self.vanna = vanna_instance
        self.feedback_file = "feedback_log.json"
        self.pending_corrections = {}  # Store corrections before applying

    def log_query_execution(self, question: str, generated_sql: str,
                            execution_success: bool, result_data: Any = None) -> str:
        """
        Log a query execution for potential feedback
        Returns a unique query_id for feedback reference
        """
        query_id = str(uuid.uuid4())

        log_entry = {
            "query_id": query_id,
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "generated_sql": generated_sql,
            "execution_success": execution_success,
            "result_count": len(result_data) if result_data is not None else 0,
            "feedback_received": False,
            "feedback_rating": None,
            "corrected_sql": None,
            "feedback_notes": None
        }

        # Store for potential feedback
        self.pending_corrections[query_id] = log_entry

        # Also log to file
        self._append_to_feedback_log(log_entry)

        return query_id

    def submit_feedback(self, query_id: str, is_correct: bool,
                        corrected_sql: Optional[str] = None,
                        feedback_notes: Optional[str] = None) -> bool:
        """
        Submit feedback for a previously executed query
        """
        if query_id not in self.pending_corrections:
            print(f"❌ Query ID {query_id} not found")
            return False

        query_data = self.pending_corrections[query_id]

        # Update feedback information
        query_data.update({
            "feedback_received": True,
            "feedback_rating": "correct" if is_correct else "incorrect",
            "corrected_sql": corrected_sql,
            "feedback_notes": feedback_notes,
            "feedback_timestamp": datetime.now().isoformat()
        })

        if is_correct:
            # Positive feedback - add to training data
            self._add_positive_training_data(query_data)
            print(f"✅ Positive feedback received. Added to training data.")
        else:
            # Negative feedback - handle correction
            if corrected_sql:
                self._handle_correction(query_data, corrected_sql)
                print(f"🔄 Correction received and applied to training data.")
            else:
                self._handle_negative_feedback(query_data)
                print(f"❌ Negative feedback logged. Consider providing correct SQL.")

        # Update log file
        self._update_feedback_log(query_data)

        # Remove from pending
        del self.pending_corrections[query_id]

        return True

    def _add_positive_training_data(self, query_data: Dict[str, Any]):
        """Add positively rated query to training data"""
        try:
            # Add the confirmed good question-SQL pair
            training_id = self.vanna.add_question_sql(
                question=query_data["question"],
                sql=query_data["generated_sql"]
            )

            query_data["training_id"] = training_id
            print(f"✅ Added positive example to training: {training_id}")

        except Exception as e:
            print(f"❌ Error adding positive training data: {e}")

    def _handle_correction(self, query_data: Dict[str, Any], corrected_sql: str):
        """Handle user correction by adding corrected version to training"""
        try:
            # Add the corrected question-SQL pair
            training_id = self.vanna.add_question_sql(
                question=query_data["question"],
                sql=corrected_sql
            )

            query_data["corrected_training_id"] = training_id
            print(f"✅ Added corrected example to training: {training_id}")

            # Optionally: Remove or flag the incorrect version
            # This depends on your Vanna implementation

        except Exception as e:
            print(f"❌ Error adding corrected training data: {e}")

    def _handle_negative_feedback(self, query_data: Dict[str, Any]):
        """Handle negative feedback without correction"""
        # Log for review but don't add to training
        print(f"⚠️ Negative feedback logged for review: {query_data['question']}")

        # Could implement logic to:
        # 1. Flag similar queries for manual review
        # 2. Reduce confidence in similar patterns
        # 3. Request manual intervention

    def _append_to_feedback_log(self, log_entry: Dict[str, Any]):
        """Append log entry to feedback file"""
        try:
            # Read existing logs
            if os.path.exists(self.feedback_file):
                with open(self.feedback_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            # Append new entry
            logs.append(log_entry)

            # Write back
            with open(self.feedback_file, 'w') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"❌ Error writing to feedback log: {e}")

    def _update_feedback_log(self, updated_entry: Dict[str, Any]):
        """Update existing entry in feedback log"""
        try:
            if not os.path.exists(self.feedback_file):
                return

            with open(self.feedback_file, 'r') as f:
                logs = json.load(f)

            # Find and update the entry
            for i, entry in enumerate(logs):
                if entry["query_id"] == updated_entry["query_id"]:
                    logs[i] = updated_entry
                    break

            # Write back
            with open(self.feedback_file, 'w') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"❌ Error updating feedback log: {e}")

    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get statistics about feedback received"""
        try:
            if not os.path.exists(self.feedback_file):
                return {"total": 0, "correct": 0, "incorrect": 0, "no_feedback": 0}

            with open(self.feedback_file, 'r') as f:
                logs = json.load(f)

            stats = {
                "total": len(logs),
                "correct": len([l for l in logs if l.get("feedback_rating") == "correct"]),
                "incorrect": len([l for l in logs if l.get("feedback_rating") == "incorrect"]),
                "no_feedback": len([l for l in logs if not l.get("feedback_received", False)]),
                "correction_rate": 0,
                "success_rate": 0
            }

            if stats["total"] > 0:
                feedback_total = stats["correct"] + stats["incorrect"]
                if feedback_total > 0:
                    stats["success_rate"] = (stats["correct"] / feedback_total) * 100
                    stats["correction_rate"] = (stats["incorrect"] / feedback_total) * 100

            return stats

        except Exception as e:
            print(f"❌ Error getting feedback stats: {e}")
            return {"error": str(e)}

    def get_queries_for_review(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get queries that need feedback or review"""
        try:
            if not os.path.exists(self.feedback_file):
                return []

            with open(self.feedback_file, 'r') as f:
                logs = json.load(f)

            # Filter queries without feedback
            need_feedback = [
                log for log in logs
                if not log.get("feedback_received", False)
            ]

            # Sort by timestamp (newest first)
            need_feedback.sort(key=lambda x: x["timestamp"], reverse=True)

            return need_feedback[:limit]

        except Exception as e:
            print(f"❌ Error getting queries for review: {e}")
            return []

    def bulk_apply_corrections(self, corrections: List[Dict[str, Any]]) -> int:
        """Apply multiple corrections at once"""
        applied_count = 0

        for correction in corrections:
            query_id = correction.get("query_id")
            is_correct = correction.get("is_correct", False)
            corrected_sql = correction.get("corrected_sql")
            notes = correction.get("notes", "")

            if self.submit_feedback(query_id, is_correct, corrected_sql, notes):
                applied_count += 1

        return applied_count


# Update to setup.py to integrate feedback
def add_feedback_methods_to_vanna():
    """
    Add feedback methods directly to UniversityVannaGemini class
    """

    def track_query_for_feedback(self, question: str, sql: str, result_df) -> str:
        """Track a query execution for potential feedback"""
        if not hasattr(self, '_feedback_system'):
            from .feedback import VannaFeedbackSystem
            self._feedback_system = VannaFeedbackSystem(self)

        execution_success = result_df is not None and not result_df.empty
        query_id = self._feedback_system.log_query_execution(
            question=question,
            generated_sql=sql,
            execution_success=execution_success,
            result_data=result_df
        )

        return query_id

    def submit_query_feedback(self, query_id: str, is_correct: bool,
                              corrected_sql: str = None, notes: str = None) -> bool:
        """Submit feedback for a query"""
        if not hasattr(self, '_feedback_system'):
            from .feedback import VannaFeedbackSystem
            self._feedback_system = VannaFeedbackSystem(self)

        return self._feedback_system.submit_feedback(
            query_id=query_id,
            is_correct=is_correct,
            corrected_sql=corrected_sql,
            feedback_notes=notes
        )

    def get_training_stats(self) -> Dict[str, Any]:
        """Get training and feedback statistics"""
        if not hasattr(self, '_feedback_system'):
            from .feedback import VannaFeedbackSystem
            self._feedback_system = VannaFeedbackSystem(self)

        return self._feedback_system.get_feedback_stats()

    # Add methods to the class
    UniversityVannaGemini.track_query_for_feedback = track_query_for_feedback
    UniversityVannaGemini.submit_query_feedback = submit_query_feedback
    UniversityVannaGemini.get_training_stats = get_training_stats


# Example usage and testing
def test_feedback_system():
    """Test the feedback system"""
    from .setup import UniversityVannaGemini, add_feedback_methods_to_vanna

    # Add feedback methods
    add_feedback_methods_to_vanna()

    # Initialize Vanna
    vn = UniversityVannaGemini()
    vn.connect_to_postgres(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        dbname=os.getenv('POSTGRES_DB', 'university_dwh'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'university123'),
        port=int(os.getenv('POSTGRES_PORT', '5432'))
    )

    # Test query
    question = "Berapa jumlah mahasiswa aktif?"
    sql = vn.generate_sql(question)
    result = vn.run_sql(sql)

    # Track for feedback
    query_id = vn.track_query_for_feedback(question, sql, result)
    print(f"🆔 Query tracked with ID: {query_id}")

    # Simulate positive feedback
    success = vn.submit_query_feedback(query_id, is_correct=True)
    print(f"✅ Feedback submitted: {success}")

    # Get stats
    stats = vn.get_training_stats()
    print(f"📊 Training stats: {stats}")


if __name__ == "__main__":
    test_feedback_system()