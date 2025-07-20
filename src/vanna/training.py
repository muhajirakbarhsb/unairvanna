# src/vanna/training.py
import os
import sys
from dotenv import load_dotenv
from setup import UniversityVannaGemini

# Load environment variables
load_dotenv()


class VannaTrainer:
    def __init__(self):
        self.vn = UniversityVannaGemini()

        # Connect to database
        self.vn.connect_to_postgres(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            dbname=os.getenv('POSTGRES_DB', 'university_dwh'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'university123'),
            port=int(os.getenv('POSTGRES_PORT', '5432'))
        )

    def train_ddl(self):
        """Train with database schema (DDL)"""
        print("📚 Training with database schema...")

        ddl_statements = [
            """
            -- Dimension Fakultas (Faculties)
            CREATE TABLE dwh.dim_fakultas
            (
                fakultas_id   SERIAL PRIMARY KEY,
                kode_fakultas VARCHAR(10) UNIQUE NOT NULL,
                nama_fakultas VARCHAR(100)       NOT NULL,
                dekan         VARCHAR(100),
                tahun_berdiri INTEGER
            );
            -- Contains faculty information including faculty ID, code, name, dean, and establishment year
            """,

            """
            -- Dimension Program Studi (Study Programs)
            CREATE TABLE dwh.dim_program_studi
            (
                prodi_id    SERIAL PRIMARY KEY,
                fakultas_id INTEGER REFERENCES dwh.dim_fakultas (fakultas_id),
                kode_prodi  VARCHAR(10) UNIQUE NOT NULL,
                nama_prodi  VARCHAR(100)       NOT NULL,
                jenjang     VARCHAR(10) CHECK (jenjang IN ('D3', 'S1', 'S2', 'S3')),
                akreditasi  VARCHAR(20) CHECK (akreditasi IN ('A', 'B', 'C', 'Unggul', 'Baik Sekali', 'Baik'))
            );
            -- Contains study program information including program ID, faculty reference, code, name, level, and accreditation
            """,

            """
            -- Dimension Dosen (Lecturers)
            CREATE TABLE dwh.dim_dosen
            (
                dosen_id            SERIAL PRIMARY KEY,
                fakultas_id         INTEGER REFERENCES dwh.dim_fakultas (fakultas_id),
                nip                 VARCHAR(20) UNIQUE,
                nama_dosen          VARCHAR(100) NOT NULL,
                jenis_kelamin       VARCHAR(10) CHECK (jenis_kelamin IN ('Laki-laki', 'Perempuan')),
                pendidikan_terakhir VARCHAR(50),
                jabatan_fungsional  VARCHAR(50),
                status_aktif        BOOLEAN DEFAULT TRUE
            );
            -- Contains lecturer information including lecturer ID, faculty reference, employee number (NIP), name, gender, education, position, and active status
            """,

            """
            -- Dimension Mata Kuliah (Courses)
            CREATE TABLE dwh.dim_mata_kuliah
            (
                matkul_id    SERIAL PRIMARY KEY,
                prodi_id     INTEGER REFERENCES dwh.dim_program_studi (prodi_id),
                kode_matkul  VARCHAR(20) UNIQUE NOT NULL,
                nama_matkul  VARCHAR(100)       NOT NULL,
                sks          INTEGER CHECK (sks BETWEEN 1 AND 6),
                semester     INTEGER CHECK (semester BETWEEN 1 AND 8),
                jenis_matkul VARCHAR(20) CHECK (jenis_matkul IN ('Wajib', 'Pilihan'))
            );
            -- Contains course information including course ID, program reference, course code, name, credits (SKS), semester, and course type
            """,

            """
            -- Dimension Mahasiswa (Students)
            CREATE TABLE dwh.dim_mahasiswa
            (
                mahasiswa_id     SERIAL PRIMARY KEY,
                prodi_id         INTEGER REFERENCES dwh.dim_program_studi (prodi_id),
                nim              VARCHAR(20) UNIQUE NOT NULL,
                nama_mahasiswa   VARCHAR(100)       NOT NULL,
                jenis_kelamin    VARCHAR(10) CHECK (jenis_kelamin IN ('Laki-laki', 'Perempuan')),
                tahun_masuk      INTEGER,
                status_mahasiswa VARCHAR(20) CHECK (status_mahasiswa IN ('Aktif', 'Cuti', 'Lulus', 'DO')),
                ipk              DECIMAL(3, 2) CHECK (ipk BETWEEN 0.00 AND 4.00)
            );
            -- Contains student information including student ID, program reference, student number (NIM), name, gender, admission year, status, and GPA (IPK)
            """,

            """
            -- Dimension Semester
            CREATE TABLE dwh.dim_semester
            (
                semester_id     SERIAL PRIMARY KEY,
                tahun_akademik  VARCHAR(20)                                         NOT NULL,
                semester        VARCHAR(20) CHECK (semester IN ('Ganjil', 'Genap')) NOT NULL,
                tanggal_mulai   DATE                                                NOT NULL,
                tanggal_selesai DATE                                                NOT NULL,
                is_active       BOOLEAN DEFAULT FALSE
            );
            -- Contains semester information including semester ID, academic year, semester type (odd/even), start/end dates, and active status
            """,

            """
            -- Fact Nilai (Grades)
            CREATE TABLE dwh.fact_nilai
            (
                nilai_id     SERIAL PRIMARY KEY,
                mahasiswa_id INTEGER REFERENCES dwh.dim_mahasiswa (mahasiswa_id),
                matkul_id    INTEGER REFERENCES dwh.dim_mata_kuliah (matkul_id),
                dosen_id     INTEGER REFERENCES dwh.dim_dosen (dosen_id),
                semester_id  INTEGER REFERENCES dwh.dim_semester (semester_id),
                nilai_akhir  DECIMAL(5, 2) CHECK (nilai_akhir BETWEEN 0 AND 100),
                nilai_huruf  VARCHAR(2) CHECK (nilai_huruf IN
                                               ('A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'E')),
                nilai_mutu   DECIMAL(3, 2) CHECK (nilai_mutu BETWEEN 0.00 AND 4.00),
                sks          INTEGER,
                kelas        VARCHAR(10)
            );
            -- Fact table containing grade information with foreign keys to student, course, lecturer, and semester dimensions
            """,

            """
            -- Fact Kehadiran (Attendance)
            CREATE TABLE dwh.fact_kehadiran
            (
                kehadiran_id         SERIAL PRIMARY KEY,
                mahasiswa_id         INTEGER REFERENCES dwh.dim_mahasiswa (mahasiswa_id),
                matkul_id            INTEGER REFERENCES dwh.dim_mata_kuliah (matkul_id),
                dosen_id             INTEGER REFERENCES dwh.dim_dosen (dosen_id),
                semester_id          INTEGER REFERENCES dwh.dim_semester (semester_id),
                total_pertemuan      INTEGER DEFAULT 14,
                hadir                INTEGER DEFAULT 0,
                izin                 INTEGER DEFAULT 0,
                alpha                INTEGER DEFAULT 0,
                persentase_kehadiran DECIMAL(5, 2)
            );
            -- Fact table containing attendance information including total meetings, present, excused, and absent counts
            """,

            """
            -- Fact Pembayaran SPP (Tuition Payments)
            CREATE TABLE dwh.fact_pembayaran_spp
            (
                pembayaran_id      SERIAL PRIMARY KEY,
                mahasiswa_id       INTEGER REFERENCES dwh.dim_mahasiswa (mahasiswa_id),
                semester_id        INTEGER REFERENCES dwh.dim_semester (semester_id),
                jumlah_tagihan     DECIMAL(12, 2) NOT NULL,
                jumlah_dibayar     DECIMAL(12, 2) DEFAULT 0,
                tanggal_pembayaran DATE,
                status_pembayaran  VARCHAR(20) CHECK (status_pembayaran IN ('Lunas', 'Belum Lunas', 'Menunggak')),
                metode_pembayaran  VARCHAR(50)
            );
            -- Fact table containing tuition payment information including amounts, dates, and payment status
            """
        ]

        for ddl in ddl_statements:
            self.vn.add_ddl(ddl.strip())

    def train_sample_questions(self):
        """Train with sample question-SQL pairs"""
        print("🤖 Training with sample questions...")

        training_pairs = [
            {
                "question": "Berapa jumlah mahasiswa aktif?",
                "sql": "SELECT COUNT(*) as total_mahasiswa_aktif FROM dwh.dim_mahasiswa WHERE status_mahasiswa = 'Aktif';"
            },
            {
                "question": "Berapa total mahasiswa aktif?",
                "sql": "SELECT COUNT(mahasiswa_id) as total_mahasiswa FROM dwh.dim_mahasiswa WHERE status_mahasiswa = 'Aktif';"
            },
            {
                "question": "Siapa mahasiswa dengan IPK tertinggi?",
                "sql": "SELECT nim, nama_mahasiswa, ipk FROM dwh.dim_mahasiswa WHERE status_mahasiswa = 'Aktif' ORDER BY ipk DESC LIMIT 1;"
            },
            {
                "question": "Berapa rata-rata IPK per program studi?",
                "sql": """
                       SELECT ps.nama_prodi,
                              ROUND(AVG(m.ipk), 2)  as rata_rata_ipk,
                              COUNT(m.mahasiswa_id) as jumlah_mahasiswa
                       FROM dwh.dim_mahasiswa m
                                JOIN dwh.dim_program_studi ps ON m.prodi_id = ps.prodi_id
                       WHERE m.status_mahasiswa = 'Aktif'
                       GROUP BY ps.prodi_id, ps.nama_prodi
                       ORDER BY rata_rata_ipk DESC;
                       """
            },
            {
                "question": "Daftar fakultas dengan jumlah mahasiswa terbanyak",
                "sql": """
                       SELECT f.nama_fakultas,
                              COUNT(m.mahasiswa_id) as jumlah_mahasiswa
                       FROM dwh.dim_fakultas f
                                JOIN dwh.dim_program_studi ps ON f.fakultas_id = ps.fakultas_id
                                JOIN dwh.dim_mahasiswa m ON ps.prodi_id = m.prodi_id
                       WHERE m.status_mahasiswa = 'Aktif'
                       GROUP BY f.fakultas_id, f.nama_fakultas
                       ORDER BY jumlah_mahasiswa DESC;
                       """
            },
            {
                "question": "Berapa jumlah dosen per fakultas?",
                "sql": """
                       SELECT f.nama_fakultas,
                              COUNT(d.dosen_id) as jumlah_dosen
                       FROM dwh.dim_fakultas f
                                LEFT JOIN dwh.dim_dosen d ON f.fakultas_id = d.fakultas_id
                       WHERE d.status_aktif = TRUE
                       GROUP BY f.fakultas_id, f.nama_fakultas
                       ORDER BY jumlah_dosen DESC;
                       """
            },
            {
                "question": "Mata kuliah dengan nilai rata-rata tertinggi",
                "sql": """
                       SELECT mk.nama_matkul,
                              ROUND(AVG(n.nilai_akhir), 2) as rata_rata_nilai,
                              COUNT(n.nilai_id)            as jumlah_mahasiswa
                       FROM dwh.dim_mata_kuliah mk
                                JOIN dwh.fact_nilai n ON mk.matkul_id = n.matkul_id
                       GROUP BY mk.matkul_id, mk.nama_matkul
                       HAVING COUNT(n.nilai_id) >= 5
                       ORDER BY rata_rata_nilai DESC LIMIT 10;
                       """
            },
            {
                "question": "Berapa persentase kehadiran rata-rata per mata kuliah?",
                "sql": """
                       SELECT mk.nama_matkul,
                              ROUND(AVG(k.persentase_kehadiran), 2) as rata_rata_kehadiran,
                              COUNT(k.kehadiran_id)                 as jumlah_record
                       FROM dwh.dim_mata_kuliah mk
                                JOIN dwh.fact_kehadiran k ON mk.matkul_id = k.matkul_id
                       GROUP BY mk.matkul_id, mk.nama_matkul
                       ORDER BY rata_rata_kehadiran DESC;
                       """
            },
            {
                "question": "Status pembayaran SPP mahasiswa aktif",
                "sql": """
                       SELECT status_pembayaran,
                              COUNT(*)                                          as jumlah_mahasiswa,
                              ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as persentase
                       FROM dwh.fact_pembayaran_spp fp
                                JOIN dwh.dim_mahasiswa m ON fp.mahasiswa_id = m.mahasiswa_id
                       WHERE m.status_mahasiswa = 'Aktif'
                       GROUP BY status_pembayaran
                       ORDER BY jumlah_mahasiswa DESC;
                       """
            },
            {
                "question": "Mahasiswa dengan kehadiran di bawah 75%",
                "sql": """
                       SELECT m.nim,
                              m.nama_mahasiswa,
                              mk.nama_matkul,
                              k.persentase_kehadiran
                       FROM dwh.dim_mahasiswa m
                                JOIN dwh.fact_kehadiran k ON m.mahasiswa_id = k.mahasiswa_id
                                JOIN dwh.dim_mata_kuliah mk ON k.matkul_id = mk.matkul_id
                       WHERE k.persentase_kehadiran < 75
                         AND m.status_mahasiswa = 'Aktif'
                       ORDER BY k.persentase_kehadiran ASC;
                       """
            }
        ]

        for pair in training_pairs:
            self.vn.add_question_sql(pair["question"], pair["sql"])

    def train_documentation(self):
        """Train with documentation about the university system"""
        print("📖 Training with documentation...")

        documentation_texts = [
            """
            Indonesian University Terms:
            - Mahasiswa = Student
            - Dosen = Lecturer/Professor  
            - Mata Kuliah = Course/Subject
            - Fakultas = Faculty
            - Program Studi = Study Program/Major
            - SKS = Credit Units (Sistem Kredit Semester)
            - NIM = Student ID Number (Nomor Induk Mahasiswa)
            - NIP = Lecturer ID Number (Nomor Induk Pegawai)
            - IPK = GPA (Indeks Prestasi Kumulatif)
            - Semester Ganjil = Odd Semester (Fall)
            - Semester Genap = Even Semester (Spring)
            """,

            """
            University Business Rules:
            - IPK (GPA) ranges from 0.00 to 4.00
            - Status mahasiswa: 'Aktif' (Active), 'Cuti' (Leave), 'Lulus' (Graduated), 'DO' (Dropped Out)
            - Akreditasi program studi: 'A', 'B', 'C', 'Unggul', 'Baik Sekali', 'Baik'
            - Jenjang pendidikan: 'D3' (Diploma), 'S1' (Bachelor), 'S2' (Master), 'S3' (Doctorate)
            - Minimum attendance requirement: 75% to be eligible for exams
            - Standard semester duration: 14 meetings per course
            """,

            """
            Database Structure:
            - Schema name: dwh (data warehouse)
            - Primary keys use _id suffix (mahasiswa_id, dosen_id, etc.)
            - Foreign key relationships link dimensions to facts
            - Fact tables store measurable data (grades, attendance, payments)
            - Dimension tables store descriptive attributes
            - Use proper JOINs to connect related tables
            """
        ]

        for doc in documentation_texts:
            self.vn.add_documentation(doc.strip())

    def test_trained_model(self):
        """Test the trained model with sample questions"""
        print("🧪 Testing trained model...")

        test_questions = [
            "Berapa jumlah mahasiswa aktif?",
            "Siapa dosen dengan mahasiswa terbanyak?",
            "Program studi mana yang memiliki IPK tertinggi?"
        ]

        for question in test_questions:
            print(f"\n❓ Question: {question}")
            sql = self.vn.generate_sql(question)
            print(f"🔍 Generated SQL: {sql}")

            try:
                result = self.vn.run_sql(sql)
                if result is not None and not result.empty:
                    print(f"✅ Query successful, returned {len(result)} rows")
                    print(f"📊 Sample result: {result.head(1).to_dict('records')}")
                else:
                    print("⚠️ Query returned no results")
            except Exception as e:
                print(f"❌ Query failed: {e}")

    def run_full_training(self):
        """Run complete training process"""
        print("🎓 Starting University Vanna AI Training")
        print("=" * 50)

        # Train with different types of data
        self.train_ddl()
        self.train_sample_questions()
        self.train_documentation()

        # Show training summary
        summary = self.vn.get_training_data()
        print(summary)

        # Test the trained model
        self.test_trained_model()

        print("\n🎉 Training completed successfully!")
        print("Your Vanna AI is now ready to generate SQL queries for university data!")


def main():
    """Main training function"""
    try:
        trainer = VannaTrainer()
        trainer.run_full_training()
    except Exception as e:
        print(f"❌ Training failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()