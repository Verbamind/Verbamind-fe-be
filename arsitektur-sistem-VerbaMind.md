# Arsitektur Sistem VerbaMind

## Arsitektur Umum

VerbaMind merupakan aplikasi desktop **offline** berbasis **PySide6**
dengan arsitektur modular yang memisahkan antarmuka pengguna, logika
aplikasi, pemrosesan AI, keamanan data, dan penyimpanan data. Seluruh
proses berjalan secara lokal (*localhost*) sehingga data pasien tidak
dikirim ke layanan cloud.

``` text
PySide6 GUI
      │
      ▼
Localhost Backend Service
      │
 ├── Audio Module
 ├── AI Pipeline
 ├── Security Module
 └── Database Module
```

## Komponen Utama

### 1. Presentation Layer

-   PySide6 Desktop GUI
-   Dashboard
-   Recording Session
-   Playback
-   Transcript Viewer
-   AI Summary (BIRP)
-   Session Management
-   Settings

### 2. Backend Layer

Backend berjalan sebagai **FastAPI Localhost Service** yang menangani: -
Recording Controller - Playback Controller - Session Manager - AI
Pipeline Controller - Encryption Controller - Database Controller

### 3. Audio Acquisition

Menggunakan **Dual-channel Audio Interface**.

``` text
Input 1 → Pasien
Input 2 → Psikolog
```

Konfigurasi peran mikrofon dilakukan melalui GUI menggunakan
**QComboBox**.

### 4. AI Pipeline

``` text
Encrypted Audio
      │
   Decrypt
      │
      ▼
 ┌───────────────┬─────────────────┐
 ▼                               ▼
Speech to Verbal Text     Speech to Non-Verbal Text
 └───────────────┬─────────────────┘
                 ▼
          Merged Verbatim
                 │
                 ▼
             RAG System
                 │
                 ▼
      Qwen2.5:7B-Instruct
                 │
                 ▼
           JSON BIRP Output
```

#### Speech to Verbal Text

-   Verbatim
-   Timestamp
-   Speaker Identification

#### Speech to Non-Verbal Text

-   Speech Emotion Recognition
-   Karakteristik non-verbal suara

#### LLM

Menggunakan **Qwen2.5:7B-Instruct** dengan pendekatan
**Retrieval-Augmented Generation (RAG)**.

Output berupa JSON dengan format: - Behavior - Intervention - Response -
Plan (BIRP)

## Database

Metadata disimpan pada **MySQL**, meliputi: - Data pasien - Data
psikolog - Data sesi - Transcript - Hasil SER - Hasil BIRP - Lokasi file
audio

Audio disimpan sebagai file terenkripsi dengan ekstensi khusus:

``` text
recordings/
└── interview001.vera
```

## Security Layer

### AES-256

Semua file audio dienkripsi menggunakan AES-256.

``` text
Record Audio
      │
      ▼
AES-256 Encrypt
      │
      ▼
interview001.vera
```

### Windows DPAPI

AES Key dibuat sekali saat aktivasi aplikasi, kemudian diamankan
menggunakan Windows DPAPI.

``` text
Generate Random AES Key
        │
        ▼
Windows DPAPI
        │
        ▼
Protected AES Key
```

Keuntungan: - Tidak memerlukan password pengguna. - AES key berbeda pada
setiap instalasi/perangkat. - File audio tidak dapat dibuka di komputer
lain.

### Playback

``` text
Open Recording
      │
      ▼
DPAPI
      │
      ▼
AES Key
      │
      ▼
Decrypt
      │
      ▼
Playback / Whisper / SER
```

## Aktivasi Aplikasi

``` text
Setup.exe
    │
    ▼
Install
    │
    ▼
Input License Key
    │
    ▼
Hardware ID Verification
    │
    ▼
Activation Success
    │
    ▼
Generate AES-256 Key
    │
    ▼
Protect using DPAPI
    │
    ▼
Application Ready
```

## Struktur Folder

``` text
VerbaMind/
├── VerbaMind.exe
├── backend.exe
├── database/
├── recordings/
│   └── *.vera
├── config/
│   ├── key.dat
│   └── config.json
├── models/
│   ├── whisper/
│   ├── ser/
│   └── llm/
├── assets/
└── logs/
```

## Teknologi

  Komponen           Teknologi
  ------------------ ------------------------------
  GUI                PySide6
  Backend            FastAPI (Localhost)
  Database           MySQL
  Audio              Dual-channel Audio Interface
  STT                Whisper
  SER                Speech Emotion Recognition
  LLM                Qwen2.5:7B-Instruct
  RAG                Local Knowledge Base
  Audio Encryption   AES-256
  Key Protection     Windows DPAPI
  Installer          Inno Setup
  Packaging          Nuitka

## Alur Sistem

``` text
User
 │
 ▼
PySide6 GUI
 │
 ▼
Localhost Backend
 │
 ▼
Record Audio
 │
 ▼
AES-256 Encrypt
 │
 ▼
Encrypted Audio (.vera)
 │
 ▼
DPAPI → AES Key
 │
 ▼
Decrypt (Memory)
 │
 ▼
Whisper + SER
 │
 ▼
Merged Verbatim
 │
 ▼
Knowledge Base (RAG)
 │
 ▼
Qwen2.5:7B-Instruct
 │
 ▼
JSON BIRP
 │
 ▼
MySQL
```
