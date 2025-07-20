# src/vanna/setup.py
import os
import sys
from typing import List, Dict, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from vanna.base import VannaBase
import hashlib
import json

# Load environment variables
load_dotenv()


class UniversityVannaGemini(VannaBase):
    """
    Custom Vanna implementation using Google Gemini and Qdrant
    """

    def __init__(self, config: Optional[Dict] = None):
        VannaBase.__init__(self, config=config)

        # Configuration
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model_name = os.getenv('VANNA_MODEL', 'gemini-1.5-pro')
        self.qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
        self.qdrant_api_key = os.getenv('QDRANT_API_KEY', 'qdrant123')
        self.collection_name = os.getenv('VANNA_COLLECTION_NAME', 'university_sql_collection')

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        # Initialize Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
            timeout=60
        )

        # Create collection if it doesn't exist
        self._create_collection()

        print(f"✅ Vanna initialized with Gemini ({self.model_name}) and Qdrant")

    # Required abstract methods implementation
    def system_message(self, message: str) -> any:
        """Format system message"""
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> any:
        """Format user message"""
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> any:
        """Format assistant message"""
        return {"role": "assistant", "content": message}

    def submit_prompt(self, prompt, **kwargs) -> str:
        """Submit prompt to Gemini API"""
        try:
            # Handle both string prompts and message arrays
            if isinstance(prompt, list):
                # Extract content from message format
                content_parts = []
                for msg in prompt:
                    if isinstance(msg, dict) and "content" in msg:
                        content_parts.append(msg["content"])
                    else:
                        content_parts.append(str(msg))
                full_prompt = "\n".join(content_parts)
            else:
                full_prompt = str(prompt)

            # Generate response using Gemini
            response = self.model.generate_content(full_prompt)
            return response.text

        except Exception as e:
            print(f"❌ Error submitting prompt: {e}")
            return "Error generating response"

    def remove_training_data(self, id: str, **kwargs) -> bool:
        """Remove training data by ID"""
        try:
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=[id]
            )
            print(f"✅ Removed training data: {id}")
            return True
        except Exception as e:
            print(f"❌ Error removing training data: {e}")
            return False

    def _create_collection(self):
        """Create Qdrant collection for storing embeddings"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                # Create collection with 768 dimensions (typical for text embeddings)
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=768,  # Gemini embedding dimension
                        distance=Distance.COSINE
                    ),
                )
                print(f"✅ Created Qdrant collection: {self.collection_name}")
            else:
                print(f"✅ Using existing Qdrant collection: {self.collection_name}")

        except Exception as e:
            print(f"❌ Error creating Qdrant collection: {e}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini"""
        try:
            # Use Gemini's embedding model
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            return []

    def add_question_sql(self, question: str, sql: str) -> str:
        """Add a question-SQL pair to the vector database"""
        try:
            # Create a unique ID for this pair
            content = f"Question: {question}\nSQL: {sql}"
            doc_id = hashlib.md5(content.encode()).hexdigest()

            # Generate embedding
            embedding = self.generate_embedding(content)
            if not embedding:
                return "Failed to generate embedding"

            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=doc_id,
                        vector=embedding,
                        payload={
                            "question": question,
                            "sql": sql,
                            "type": "question_sql",
                            "content": content
                        }
                    )
                ]
            )

            print(f"✅ Added question-SQL pair: {question[:50]}...")
            return doc_id

        except Exception as e:
            print(f"❌ Error adding question-SQL: {e}")
            return "Error"

    def add_ddl(self, ddl: str) -> str:
        """Add DDL (schema information) to the vector database"""
        try:
            # Create a unique ID for this DDL
            doc_id = hashlib.md5(ddl.encode()).hexdigest()

            # Generate embedding
            embedding = self.generate_embedding(ddl)
            if not embedding:
                return "Failed to generate embedding"

            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=doc_id,
                        vector=embedding,
                        payload={
                            "ddl": ddl,
                            "type": "ddl",
                            "content": ddl
                        }
                    )
                ]
            )

            print(f"✅ Added DDL: {ddl[:50]}...")
            return doc_id

        except Exception as e:
            print(f"❌ Error adding DDL: {e}")
            return "Error"

    def add_documentation(self, documentation: str) -> str:
        """Add documentation to the vector database"""
        try:
            # Create a unique ID
            doc_id = hashlib.md5(documentation.encode()).hexdigest()

            # Generate embedding
            embedding = self.generate_embedding(documentation)
            if not embedding:
                return "Failed to generate embedding"

            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=doc_id,
                        vector=embedding,
                        payload={
                            "documentation": documentation,
                            "type": "documentation",
                            "content": documentation
                        }
                    )
                ]
            )

            print(f"✅ Added documentation: {documentation[:50]}...")
            return doc_id

        except Exception as e:
            print(f"❌ Error adding documentation: {e}")
            return "Error"

    def get_related_ddl(self, question: str, **kwargs) -> List[str]:
        """Get related DDL for a question using vector similarity"""
        try:
            # Generate embedding for the question
            question_embedding = self.generate_embedding(question)
            if not question_embedding:
                return []

            # Search for similar DDL
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=question_embedding,
                query_filter={
                    "must": [
                        {"key": "type", "match": {"value": "ddl"}}
                    ]
                },
                limit=3
            )

            ddl_list = []
            for point in search_result:
                if point.payload and "ddl" in point.payload:
                    ddl_list.append(point.payload["ddl"])

            return ddl_list

        except Exception as e:
            print(f"❌ Error getting related DDL: {e}")
            return []

    def get_related_documentation(self, question: str, **kwargs) -> List[str]:
        """Get related documentation for a question"""
        try:
            # Generate embedding for the question
            question_embedding = self.generate_embedding(question)
            if not question_embedding:
                return []

            # Search for similar documentation
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=question_embedding,
                query_filter={
                    "must": [
                        {"key": "type", "match": {"value": "documentation"}}
                    ]
                },
                limit=2
            )

            doc_list = []
            for point in search_result:
                if point.payload and "documentation" in point.payload:
                    doc_list.append(point.payload["documentation"])

            return doc_list

        except Exception as e:
            print(f"❌ Error getting related documentation: {e}")
            return []

    def get_similar_question_sql(self, question: str, **kwargs) -> List[str]:
        """Get similar question-SQL pairs"""
        try:
            # Generate embedding for the question
            question_embedding = self.generate_embedding(question)
            if not question_embedding:
                return []

            # Search for similar questions
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=question_embedding,
                query_filter={
                    "must": [
                        {"key": "type", "match": {"value": "question_sql"}}
                    ]
                },
                limit=3
            )

            similar_pairs = []
            for point in search_result:
                if point.payload and "content" in point.payload:
                    similar_pairs.append(point.payload["content"])

            return similar_pairs

        except Exception as e:
            print(f"❌ Error getting similar questions: {e}")
            return []

    def generate_sql(self, question: str, **kwargs) -> str:
        """Generate SQL using Gemini with context from Qdrant"""
        try:
            # Get related context
            related_ddl = self.get_related_ddl(question)
            related_docs = self.get_related_documentation(question)
            similar_questions = self.get_similar_question_sql(question)

            # Build context
            context_parts = []

            if related_ddl:
                context_parts.append("Relevant database schema:")
                context_parts.extend(related_ddl)

            if related_docs:
                context_parts.append("\nRelevant documentation:")
                context_parts.extend(related_docs)

            if similar_questions:
                context_parts.append("\nSimilar examples:")
                context_parts.extend(similar_questions)

            context = "\n".join(context_parts)

            # Create prompt
            prompt = f"""You are an expert SQL query generator for an Indonesian University Data Warehouse.

Context:
{context}

Database Information:
- Schema: dwh
- Main tables: dim_fakultas, dim_program_studi, dim_dosen, dim_mata_kuliah, dim_mahasiswa, dim_semester
- Fact tables: fact_nilai, fact_kehadiran, fact_pembayaran_spp
- Language: Use Indonesian field names and values appropriately

Question: {question}

Generate a PostgreSQL query that answers this question. Return only the SQL query without explanation.
"""

            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            sql = response.text.strip()

            # Clean up the SQL (remove markdown formatting if present)
            if sql.startswith("```sql"):
                sql = sql[6:-3] if sql.endswith("```") else sql[6:]
            elif sql.startswith("```"):
                sql = sql[3:-3] if sql.endswith("```") else sql[3:]

            return sql.strip()

        except Exception as e:
            print(f"❌ Error generating SQL: {e}")
            return "-- Error generating SQL query"

    def connect_to_postgres(self, host: str, dbname: str, user: str, password: str, port: int = 5432):
        """Connect to PostgreSQL database using SQLAlchemy"""
        try:
            from sqlalchemy import create_engine, text

            # Create connection URL
            connection_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

            # Create SQLAlchemy engine
            self.db_engine = create_engine(connection_url)

            # Test connection
            with self.db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            print(f"✅ Connected to PostgreSQL: {dbname}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise

    def run_sql(self, sql: str) -> any:
        """Execute SQL query and return results"""
        try:
            import pandas as pd

            if not hasattr(self, 'db_engine'):
                raise Exception("Database not connected. Call connect_to_postgres() first.")

            # Execute query using pandas with SQLAlchemy engine
            df = pd.read_sql_query(sql, self.db_engine)
            return df

        except Exception as e:
            print(f"❌ Error executing SQL: {e}")
            return None

    def get_training_data(self) -> str:
        """Get summary of training data"""
        try:
            # Get collection info
            collection_info = self.qdrant_client.get_collection(self.collection_name)

            # Count different types
            ddl_count = len(self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter={"must": [{"key": "type", "match": {"value": "ddl"}}]},
                limit=1000
            )[0])

            question_count = len(self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter={"must": [{"key": "type", "match": {"value": "question_sql"}}]},
                limit=1000
            )[0])

            doc_count = len(self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter={"must": [{"key": "type", "match": {"value": "documentation"}}]},
                limit=1000
            )[0])

            summary = f"""
Training Data Summary:
- Total vectors: {collection_info.points_count}
- DDL statements: {ddl_count}
- Question-SQL pairs: {question_count}
- Documentation: {doc_count}
- Collection: {self.collection_name}
"""
            return summary

        except Exception as e:
            return f"Error getting training data: {e}"


def create_vanna_instance() -> UniversityVannaGemini:
    """Create and return a configured Vanna instance"""
    return UniversityVannaGemini()


def test_vanna_connection():
    """Test Vanna setup"""
    print("🧪 Testing Vanna AI setup...")

    try:
        # Create Vanna instance
        vn = create_vanna_instance()

        # Test database connection
        vn.connect_to_postgres(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            dbname=os.getenv('POSTGRES_DB', 'university_dwh'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'university123'),
            port=int(os.getenv('POSTGRES_PORT', '5432'))
        )

        # Test simple query
        test_question = "Berapa jumlah mahasiswa aktif?"
        print(f"🔍 Testing question: {test_question}")

        sql = vn.generate_sql(test_question)
        print(f"📝 Generated SQL: {sql}")

        # Try to execute the query
        result = vn.run_sql(sql)
        if result is not None:
            print(f"✅ Query executed successfully")
            print(f"📊 Result shape: {result.shape}")

        print(f"🎉 Vanna AI test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Vanna test failed: {e}")
        return False


if __name__ == "__main__":
    test_vanna_connection()