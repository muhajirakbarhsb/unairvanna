# src/database/populate.py
import os
import sys
import random
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Faker with Indonesian locale
fake = Faker('id_ID')


class UniversityDataPopulator:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                database=os.getenv('POSTGRES_DB', 'university_dwh'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'university123'),
                port=os.getenv('POSTGRES_PORT', '5432')
            )
            self.cursor = self.conn.cursor()
            print("✅ Connected to PostgreSQL database")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            sys.exit(1)

    def populate_dosen(self, count=50):
        """Populate dosen (lecturers) data"""
        print(f"📚 Populating {count} dosen...")

        # Get fakultas IDs
        self.cursor.execute("SELECT fakultas_id FROM dwh.dim_fakultas")
        fakultas_ids = [row[0] for row in self.cursor.fetchall()]

        dosen_data = []
        for i in range(count):
            dosen_data.append((
                random.choice(fakultas_ids),
                f"NIP{random.randint(1970, 1999)}{random.randint(10, 12)}{random.randint(10, 28)}{random.randint(100, 999)}",
                fake.name(),
                random.choice(['Laki-laki', 'Perempuan']),
                random.choice(['S2', 'S3']),
                random.choice(['Asisten Ahli', 'Lektor', 'Lektor Kepala', 'Guru Besar']),
                True
            ))

        query = """
                INSERT INTO dwh.dim_dosen (fakultas_id, nip, nama_dosen, jenis_kelamin,
                                           pendidikan_terakhir, jabatan_fungsional, status_aktif)
                VALUES %s \
                """
        execute_values(self.cursor, query, dosen_data)
        self.conn.commit()
        print(f"✅ {count} dosen added")

    def populate_mata_kuliah(self, count_per_prodi=8):
        """Populate mata kuliah (courses) data"""
        print(f"📖 Populating mata kuliah...")

        # Get prodi data
        self.cursor.execute("SELECT prodi_id, nama_prodi FROM dwh.dim_program_studi")
        prodi_data = self.cursor.fetchall()

        # Course templates by study program
        course_templates = {
            'Teknik Informatika': [
                'Algoritma dan Pemrograman', 'Struktur Data', 'Basis Data',
                'Jaringan Komputer', 'Rekayasa Perangkat Lunak', 'Sistem Operasi',
                'Pemrograman Web', 'Kecerdasan Buatan'
            ],
            'Teknik Elektro': [
                'Rangkaian Listrik', 'Elektronika Dasar', 'Sistem Kontrol',
                'Mikroprosessor', 'Sistem Tenaga Listrik', 'Elektronika Daya',
                'Komunikasi Data', 'Sistem Embedded'
            ],
            'Manajemen': [
                'Manajemen Keuangan', 'Pemasaran', 'Manajemen SDM',
                'Manajemen Operasi', 'Kewirausahaan', 'Manajemen Strategis',
                'Perilaku Organisasi', 'Manajemen Risiko'
            ],
            'Akuntansi': [
                'Akuntansi Dasar', 'Akuntansi Keuangan', 'Akuntansi Biaya',
                'Auditing', 'Perpajakan', 'Sistem Informasi Akuntansi',
                'Akuntansi Manajemen', 'Analisis Laporan Keuangan'
            ],
            'Sistem Informasi': [
                'Analisis Sistem', 'Perancangan Sistem', 'Pemrograman Web',
                'Mobile Programming', 'Data Mining', 'E-Business',
                'Manajemen Proyek TI', 'Keamanan Sistem Informasi'
            ]
        }

        matkul_data = []
        for prodi_id, nama_prodi in prodi_data:
            courses = course_templates.get(nama_prodi, [
                'Mata Kuliah Dasar', 'Mata Kuliah Lanjutan', 'Mata Kuliah Pilihan',
                'Mata Kuliah Khusus', 'Mata Kuliah Praktik', 'Mata Kuliah Teori',
                'Mata Kuliah Aplikasi', 'Mata Kuliah Analisis'
            ])

            for i, course_name in enumerate(courses):
                semester = (i % 8) + 1  # Distribute across 8 semesters
                matkul_data.append((
                    prodi_id,
                    f"MK{prodi_id:02d}{semester:02d}{i + 1:02d}",
                    course_name,
                    random.choice([2, 3, 4]),
                    semester,
                    random.choice(['Wajib', 'Pilihan'])
                ))

        query = """
                INSERT INTO dwh.dim_mata_kuliah (prodi_id, kode_matkul, nama_matkul,
                                                 sks, semester, jenis_matkul)
                VALUES %s \
                """
        execute_values(self.cursor, query, matkul_data)
        self.conn.commit()
        print(f"✅ {len(matkul_data)} mata kuliah added")

    def populate_mahasiswa(self, count=200):
        """Populate mahasiswa (students) data"""
        print(f"👨‍🎓 Populating {count} mahasiswa...")

        # Get prodi IDs
        self.cursor.execute("SELECT prodi_id FROM dwh.dim_program_studi")
        prodi_ids = [row[0] for row in self.cursor.fetchall()]

        mahasiswa_data = []
        for i in range(count):
            prodi_id = random.choice(prodi_ids)
            tahun_masuk = random.randint(2020, 2024)

            mahasiswa_data.append((
                prodi_id,
                f"{tahun_masuk}{prodi_id:02d}{i + 1:04d}",
                fake.name(),
                random.choice(['Laki-laki', 'Perempuan']),
                tahun_masuk,
                random.choice(['Aktif', 'Aktif', 'Aktif', 'Cuti', 'Lulus']),  # More active students
                round(random.uniform(2.5, 4.0), 2)
            ))

        query = """
                INSERT INTO dwh.dim_mahasiswa (prodi_id, nim, nama_mahasiswa, jenis_kelamin,
                                               tahun_masuk, status_mahasiswa, ipk)
                VALUES %s \
                """
        execute_values(self.cursor, query, mahasiswa_data)
        self.conn.commit()
        print(f"✅ {count} mahasiswa added")

    def populate_fact_nilai(self, count=500):
        """Populate fact_nilai (grades) data"""
        print(f"📊 Populating {count} nilai records...")

        # Get foreign keys
        self.cursor.execute("SELECT mahasiswa_id FROM dwh.dim_mahasiswa WHERE status_mahasiswa = 'Aktif'")
        mahasiswa_ids = [row[0] for row in self.cursor.fetchall()]

        self.cursor.execute("SELECT matkul_id FROM dwh.dim_mata_kuliah")
        matkul_ids = [row[0] for row in self.cursor.fetchall()]

        self.cursor.execute("SELECT dosen_id FROM dwh.dim_dosen")
        dosen_ids = [row[0] for row in self.cursor.fetchall()]

        self.cursor.execute("SELECT semester_id FROM dwh.dim_semester")
        semester_ids = [row[0] for row in self.cursor.fetchall()]

        nilai_data = []
        for _ in range(count):
            nilai_akhir = round(random.uniform(50, 100), 1)

            # Convert to letter grade
            if nilai_akhir >= 85:
                nilai_huruf, nilai_mutu = 'A', 4.0
            elif nilai_akhir >= 80:
                nilai_huruf, nilai_mutu = 'A-', 3.7
            elif nilai_akhir >= 75:
                nilai_huruf, nilai_mutu = 'B+', 3.3
            elif nilai_akhir >= 70:
                nilai_huruf, nilai_mutu = 'B', 3.0
            elif nilai_akhir >= 65:
                nilai_huruf, nilai_mutu = 'B-', 2.7
            elif nilai_akhir >= 60:
                nilai_huruf, nilai_mutu = 'C+', 2.3
            elif nilai_akhir >= 55:
                nilai_huruf, nilai_mutu = 'C', 2.0
            else:
                nilai_huruf, nilai_mutu = 'D', 1.0

            nilai_data.append((
                random.choice(mahasiswa_ids),
                random.choice(matkul_ids),
                random.choice(dosen_ids),
                random.choice(semester_ids),
                nilai_akhir,
                nilai_huruf,
                nilai_mutu,
                random.choice([2, 3, 4]),
                random.choice(['A', 'B', 'C'])
            ))

        query = """
                INSERT INTO dwh.fact_nilai (mahasiswa_id, matkul_id, dosen_id, semester_id,
                                            nilai_akhir, nilai_huruf, nilai_mutu, sks, kelas)
                VALUES %s \
                """
        execute_values(self.cursor, query, nilai_data)
        self.conn.commit()
        print(f"✅ {count} nilai records added")

    def populate_fact_kehadiran(self, count=400):
        """Populate fact_kehadiran (attendance) data"""
        print(f"📅 Populating {count} kehadiran records...")

        # Get foreign keys (similar to nilai)
        self.cursor.execute("SELECT mahasiswa_id FROM dwh.dim_mahasiswa WHERE status_mahasiswa = 'Aktif'")
        mahasiswa_ids = [row[0] for row in self.cursor.fetchall()]

        self.cursor.execute("SELECT matkul_id FROM dwh.dim_mata_kuliah")
        matkul_ids = [row[0] for row in self.cursor.fetchall()]

        self.cursor.execute("SELECT dosen_id FROM dwh.dim_dosen")
        dosen_ids = [row[0] for row in self.cursor.fetchall()]

        self.cursor.execute("SELECT semester_id FROM dwh.dim_semester")
        semester_ids = [row[0] for row in self.cursor.fetchall()]

        kehadiran_data = []
        for _ in range(count):
            total_pertemuan = 14
            hadir = random.randint(8, 14)
            izin = random.randint(0, min(3, total_pertemuan - hadir))
            alpha = total_pertemuan - hadir - izin
            persentase = (hadir / total_pertemuan) * 100

            kehadiran_data.append((
                random.choice(mahasiswa_ids),
                random.choice(matkul_ids),
                random.choice(dosen_ids),
                random.choice(semester_ids),
                total_pertemuan,
                hadir,
                izin,
                alpha,
                round(persentase, 2)
            ))

        query = """
                INSERT INTO dwh.fact_kehadiran (mahasiswa_id, matkul_id, dosen_id, semester_id,
                                                total_pertemuan, hadir, izin, alpha, persentase_kehadiran)
                VALUES %s \
                """
        execute_values(self.cursor, query, kehadiran_data)
        self.conn.commit()
        print(f"✅ {count} kehadiran records added")

    def populate_fact_pembayaran(self, count=150):
        """Populate fact_pembayaran_spp (tuition payments) data"""
        print(f"💰 Populating {count} pembayaran records...")

        # Get foreign keys
        self.cursor.execute("SELECT mahasiswa_id FROM dwh.dim_mahasiswa WHERE status_mahasiswa = 'Aktif'")
        mahasiswa_ids = [row[0] for row in self.cursor.fetchall()]

        self.cursor.execute("SELECT semester_id FROM dwh.dim_semester")
        semester_ids = [row[0] for row in self.cursor.fetchall()]

        pembayaran_data = []
        for _ in range(count):
            jumlah_tagihan = random.choice([3500000, 4000000, 4500000, 5000000])
            status = random.choice(['Lunas', 'Lunas', 'Belum Lunas', 'Menunggak'])

            if status == 'Lunas':
                jumlah_dibayar = jumlah_tagihan
                tanggal_pembayaran = fake.date_between(start_date='-6m', end_date='today')
            elif status == 'Belum Lunas':
                jumlah_dibayar = jumlah_tagihan * random.uniform(0.3, 0.8)
                tanggal_pembayaran = fake.date_between(start_date='-3m', end_date='today')
            else:  # Menunggak
                jumlah_dibayar = 0
                tanggal_pembayaran = None

            pembayaran_data.append((
                random.choice(mahasiswa_ids),
                random.choice(semester_ids),
                jumlah_tagihan,
                jumlah_dibayar,
                tanggal_pembayaran,
                status,
                random.choice(['Transfer Bank', 'Virtual Account', 'Kartu Kredit', 'E-wallet'])
            ))

        query = """
                INSERT INTO dwh.fact_pembayaran_spp (mahasiswa_id, semester_id, jumlah_tagihan,
                                                     jumlah_dibayar, tanggal_pembayaran, status_pembayaran, \
                                                     metode_pembayaran)
                VALUES %s \
                """
        execute_values(self.cursor, query, pembayaran_data)
        self.conn.commit()
        print(f"✅ {count} pembayaran records added")

    def show_summary(self):
        """Show data summary"""
        print("\n📊 DATABASE SUMMARY")
        print("==================")

        tables = [
            ('dwh.dim_fakultas', 'Fakultas'),
            ('dwh.dim_program_studi', 'Program Studi'),
            ('dwh.dim_dosen', 'Dosen'),
            ('dwh.dim_mata_kuliah', 'Mata Kuliah'),
            ('dwh.dim_mahasiswa', 'Mahasiswa'),
            ('dwh.dim_semester', 'Semester'),
            ('dwh.fact_nilai', 'Nilai'),
            ('dwh.fact_kehadiran', 'Kehadiran'),
            ('dwh.fact_pembayaran_spp', 'Pembayaran SPP')
        ]

        for table, description in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            print(f"{description:20}: {count:6} records")

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✅ Database connection closed")


def main():
    """Main function to populate all data"""
    print("🎓 University Data Population Starting...")
    print("=" * 50)

    populator = UniversityDataPopulator()

    try:
        # Connect to database
        populator.connect()

        # Populate dimension tables
        populator.populate_dosen(50)
        populator.populate_mata_kuliah()
        populator.populate_mahasiswa(200)

        # Populate fact tables
        populator.populate_fact_nilai(500)
        populator.populate_fact_kehadiran(400)
        populator.populate_fact_pembayaran(150)

        # Show summary
        populator.show_summary()

        print("\n🎉 Data population completed successfully!")

    except Exception as e:
        print(f"❌ Error during population: {e}")
        sys.exit(1)

    finally:
        populator.close()


if __name__ == "__main__":
    main()