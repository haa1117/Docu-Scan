# 📄 DocuScan – Legal Document Classifier

DocuScan is an AI-powered legal document classification and search engine tailored for law firms and legal departments. It leverages OCR, NLP, and full-text search to intelligently tag, organize, and surface key documents by case type, urgency, and client — reducing manual prep time by up to 40%.

---

## 🚀 Features

- 📎 **Upload Documents** (PDF, Word, scanned images)
- 🧠 **AI-based Tagging** using spaCy NLP
- 🔍 **Full-Text Search** with Elasticsearch
- ⚖️ **Classification by Case Type, Urgency, and Client**
- 📊 **Interactive Dashboard** with visualizations
- 🗂️ **Document Summarization & Preview**
- ⚠️ **High-Priority Detection** for urgent legal docs
- 🛠️ **Dockerized Microservices Architecture**
- 🔒 **Token-Based Auth (Optional)**
- 📁 **Export Search Results (CSV/JSON)**

---

## 🧱 Tech Stack

| Layer         | Technology        |
|---------------|-------------------|
| Backend       | FastAPI           |
| OCR           | Tesseract OCR     |
| NLP           | spaCy             |
| Search Engine | Elasticsearch     |
| Frontend      |  HTML+JS          |
| Containerization | Docker, Docker Compose |

---

## 📦 Installation (Development)

### 🔧 Prerequisites
- Docker & Docker Compose installed
- Git & Python 3.10+
- Node.js & npm (if using React frontend)

### 🛠️ Setup

```bash
# Clone the project
git clone https://github.com/your-org/docuscan.git
cd docuscan

# Launch all services
docker compose up --build -d
