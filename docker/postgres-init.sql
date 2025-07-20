-- docker/postgres-init.sql
-- University Data Warehouse Schema

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Create schema
CREATE SCHEMA IF NOT EXISTS dwh;
SET search_path TO dwh, public;

-- Create dimension tables

-- 1. Dimension Fakultas (Faculties)
CREATE TABLE dwh.dim_fakultas (
    fakultas_id SERIAL PRIMARY KEY,
    kode_fakultas VARCHAR(10) UNIQUE NOT NULL,
    nama_fakultas VARCHAR(100) NOT NULL,
    dekan VARCHAR(100),
    tahun_berdiri INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Dimension Program Studi (Study Programs)
CREATE TABLE dwh.dim_program_studi (
    prodi_id SERIAL PRIMARY KEY,
    fakultas_id INTEGER REFERENCES dwh.dim_fakultas(fakultas_id),
    kode_prodi VARCHAR(10) UNIQUE NOT NULL,
    nama_prodi VARCHAR(100) NOT NULL,
    jenjang VARCHAR(10) CHECK (jenjang IN ('D3', 'S1', 'S2', 'S3')),
    akreditasi VARCHAR(20) CHECK (akreditasi IN ('A', 'B', 'C', 'Unggul', 'Baik Sekali', 'Baik')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Dimension Dosen (Lecturers)
CREATE TABLE dwh.dim_dosen (
    dosen_id SERIAL PRIMARY KEY,
    fakultas_id INTEGER REFERENCES dwh.dim_fakultas(fakultas_id),
    nip VARCHAR(20) UNIQUE,
    nama_dosen VARCHAR(100) NOT NULL,
    jenis_kelamin VARCHAR(10) CHECK (jenis_kelamin IN ('Laki-laki', 'Perempuan')),
    pendidikan_terakhir VARCHAR(50),
    jabatan_fungsional VARCHAR(50),
    status_aktif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Dimension Mata Kuliah (Courses)
CREATE TABLE dwh.dim_mata_kuliah (
    matkul_id SERIAL PRIMARY KEY,
    prodi_id INTEGER REFERENCES dwh.dim_program_studi(prodi_id),
    kode_matkul VARCHAR(20) UNIQUE NOT NULL,
    nama_matkul VARCHAR(100) NOT NULL,
    sks INTEGER CHECK (sks BETWEEN 1 AND 6),
    semester INTEGER CHECK (semester BETWEEN 1 AND 8),
    jenis_matkul VARCHAR(20) CHECK (jenis_matkul IN ('Wajib', 'Pilihan')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Dimension Mahasiswa (Students)
CREATE TABLE dwh.dim_mahasiswa (
    mahasiswa_id SERIAL PRIMARY KEY,
    prodi_id INTEGER REFERENCES dwh.dim_program_studi(prodi_id),
    nim VARCHAR(20) UNIQUE NOT NULL,
    nama_mahasiswa VARCHAR(100) NOT NULL,
    jenis_kelamin VARCHAR(10) CHECK (jenis_kelamin IN ('Laki-laki', 'Perempuan')),
    tahun_masuk INTEGER,
    status_mahasiswa VARCHAR(20) CHECK (status_mahasiswa IN ('Aktif', 'Cuti', 'Lulus', 'DO')),
    ipk DECIMAL(3,2) CHECK (ipk BETWEEN 0.00 AND 4.00),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Dimension Semester
CREATE TABLE dwh.dim_semester (
    semester_id SERIAL PRIMARY KEY,
    tahun_akademik VARCHAR(20) NOT NULL,
    semester VARCHAR(20) CHECK (semester IN ('Ganjil', 'Genap')) NOT NULL,
    tanggal_mulai DATE NOT NULL,
    tanggal_selesai DATE NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tahun_akademik, semester)
);

-- Create fact tables

-- 1. Fact Nilai (Grades)
CREATE TABLE dwh.fact_nilai (
    nilai_id SERIAL PRIMARY KEY,
    mahasiswa_id INTEGER REFERENCES dwh.dim_mahasiswa(mahasiswa_id),
    matkul_id INTEGER REFERENCES dwh.dim_mata_kuliah(matkul_id),
    dosen_id INTEGER REFERENCES dwh.dim_dosen(dosen_id),
    semester_id INTEGER REFERENCES dwh.dim_semester(semester_id),
    nilai_akhir DECIMAL(5,2) CHECK (nilai_akhir BETWEEN 0 AND 100),
    nilai_huruf VARCHAR(2) CHECK (nilai_huruf IN ('A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'E')),
    nilai_mutu DECIMAL(3,2) CHECK (nilai_mutu BETWEEN 0.00 AND 4.00),
    sks INTEGER,
    kelas VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Fact Kehadiran (Attendance)
CREATE TABLE dwh.fact_kehadiran (
    kehadiran_id SERIAL PRIMARY KEY,
    mahasiswa_id INTEGER REFERENCES dwh.dim_mahasiswa(mahasiswa_id),
    matkul_id INTEGER REFERENCES dwh.dim_mata_kuliah(matkul_id),
    dosen_id INTEGER REFERENCES dwh.dim_dosen(dosen_id),
    semester_id INTEGER REFERENCES dwh.dim_semester(semester_id),
    total_pertemuan INTEGER DEFAULT 14,
    hadir INTEGER DEFAULT 0,
    izin INTEGER DEFAULT 0,
    alpha INTEGER DEFAULT 0,
    persentase_kehadiran DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Fact Pembayaran SPP (Tuition Payments)
CREATE TABLE dwh.fact_pembayaran_spp (
    pembayaran_id SERIAL PRIMARY KEY,
    mahasiswa_id INTEGER REFERENCES dwh.dim_mahasiswa(mahasiswa_id),
    semester_id INTEGER REFERENCES dwh.dim_semester(semester_id),
    jumlah_tagihan DECIMAL(12,2) NOT NULL,
    jumlah_dibayar DECIMAL(12,2) DEFAULT 0,
    tanggal_pembayaran DATE,
    status_pembayaran VARCHAR(20) CHECK (status_pembayaran IN ('Lunas', 'Belum Lunas', 'Menunggak')),
    metode_pembayaran VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_mahasiswa_nim ON dwh.dim_mahasiswa(nim);
CREATE INDEX idx_mahasiswa_prodi ON dwh.dim_mahasiswa(prodi_id);
CREATE INDEX idx_mahasiswa_status ON dwh.dim_mahasiswa(status_mahasiswa);
CREATE INDEX idx_dosen_nip ON dwh.dim_dosen(nip);
CREATE INDEX idx_matkul_kode ON dwh.dim_mata_kuliah(kode_matkul);
CREATE INDEX idx_semester_active ON dwh.dim_semester(is_active);

-- Fact table indexes
CREATE INDEX idx_nilai_mahasiswa ON dwh.fact_nilai(mahasiswa_id);
CREATE INDEX idx_nilai_matkul ON dwh.fact_nilai(matkul_id);
CREATE INDEX idx_nilai_semester ON dwh.fact_nilai(semester_id);
CREATE INDEX idx_kehadiran_mahasiswa ON dwh.fact_kehadiran(mahasiswa_id);
CREATE INDEX idx_pembayaran_mahasiswa ON dwh.fact_pembayaran_spp(mahasiswa_id);

-- Insert sample data for testing
INSERT INTO dwh.dim_fakultas (kode_fakultas, nama_fakultas, dekan, tahun_berdiri) VALUES
('FT', 'Fakultas Teknik', 'Prof. Dr. Ir. Ahmad Budi, M.T.', 1985),
('FEB', 'Fakultas Ekonomi dan Bisnis', 'Dr. Siti Rahayu, M.M.', 1987),
('FKOM', 'Fakultas Ilmu Komputer', 'Prof. Dr. Wijaya Kusuma, M.Sc.', 1995);

INSERT INTO dwh.dim_program_studi (fakultas_id, kode_prodi, nama_prodi, jenjang, akreditasi) VALUES
(1, 'TI', 'Teknik Informatika', 'S1', 'A'),
(1, 'TE', 'Teknik Elektro', 'S1', 'B'),
(2, 'MNJ', 'Manajemen', 'S1', 'A'),
(2, 'AKT', 'Akuntansi', 'S1', 'A'),
(3, 'SI', 'Sistem Informasi', 'S1', 'A');

INSERT INTO dwh.dim_semester (tahun_akademik, semester, tanggal_mulai, tanggal_selesai, is_active) VALUES
('2024/2025', 'Ganjil', '2024-08-01', '2025-01-31', TRUE),
('2024/2025', 'Genap', '2025-02-01', '2025-07-31', FALSE),
('2023/2024', 'Ganjil', '2023-08-01', '2024-01-31', FALSE),
('2023/2024', 'Genap', '2024-02-01', '2024-07-31', FALSE);

\echo 'University database schema created successfully!'
