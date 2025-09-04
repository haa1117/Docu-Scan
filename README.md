# 📄 DocuScan – Legal Document Classifier

<img width="1912" height="976" alt="Screenshot 2025-06-23 040436" src="https://github.com/user-attachments/assets/8a144080-c967-440a-aa43-d57a58c5bdaf" />
<img width="1907" height="951" alt="Screenshot 2025-06-23 131551" src="https://github.com/user-attachments/assets/cd14b4d6-d9b2-43ff-991d-abc3ffc92aca" />
<img width="1883" height="752" alt="Screenshot 2025-06-23 131523" src="https://github.com/user-attachments/assets/c5edbdc9-b07f-40c2-914e-3b1cf0961fac" />
<img width="1913" height="957" alt="Screenshot 2025-06-23 131426" src="https://github.com/user-attachments/assets/a5fc272e-c240-403f-8874-87cafe0f46cc" />
<img width="1885" height="971" alt="Screenshot 2025-06-23 131335" src="https://github.com/user-attachments/assets/53fec251-058b-4619-a66f-6335129db5a7" />
<img width="1900" height="992" alt="Screenshot 2025-06-23 131300" src="https://github.com/user-attachments/assets/821b5bd9-866d-48b0-bbb3-33ed7e0059bc" />


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
