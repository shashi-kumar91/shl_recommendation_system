# SHL Assessment Recommendation System  
**Deployed at:** [https://shlrecommendationsystem-8jgbn4syxunzjwfqjhbjfb.streamlit.app/](https://shlrecommendationsystem-8jgbn4syxunzjwfqjhbjfb.streamlit.app/)  

---

## Overview  

A **smart, AI-powered recommendation engine** that suggests the most relevant **SHL assessments** based on:  
- Job descriptions  
- Natural language queries  
- Required technical & soft skills  

Built with **TF-IDF + Training Boost + Category Balancing** for **high recall** and **practical relevance**.


## Live Demo  

[Try it now!](https://shlrecommendationsystem-8jgbn4syxunzjwfqjhbjfb.streamlit.app/)  

### Example Queries  
- `I am hiring for Java developers who can collaborate effectively with business teams.`  
- `Need a QA Engineer with Selenium, Java, and SQL.`  
- `Looking for a COO who is culturally a right fit.`  

---

## Tech Stack  

| Component | Technology |
|---------|------------|
| **Frontend** | Streamlit |
| **Backend API** | Flask + Flask-CORS |
| **ML Engine** | scikit-learn (TF-IDF), pandas, numpy |
| **Data Scraping** | Selenium + BeautifulSoup |
| **Preprocessing** | Custom URL & test-type normalization |
| **Deployment** | Streamlit Community Cloud |

---

## Project Structure  

```bash
.
├── app.py                    # Streamlit UI
├── api.py                    # Flask REST API
├── final_recommend_eng.py    # Core recommendation engine
├── evaluate.py               # Mean Recall@10 evaluation
├── predictions.py            # Generate test predictions
├── preprocess_final.py       # Clean & normalize scraped data
├── scraper.py                # Scrape SHL catalog
├── test_api.py               # API health & functionality tests
├── preprocessed_assessments.json  # Clean dataset
├── Train_file.csv            # Training data (query → assessment)
├── Test_file.csv             # Test queries (for submission)
└── requirements.txt
```

---

## How It Works  

1. **Scrape** SHL catalog → `assessments_raw.json`  
2. **Preprocess** → Fix URLs, extract duration, map test types → `preprocessed_assessments.json`  
3. **Train** on `Train_file.csv` to learn query → assessment mappings  
4. **Query → TF-IDF + Boost → Rank → Balance → Recommend Top-K**

---

## Setup & Run Locally  

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd shl_recommendation_system
pip install -r requirements.txt
```

### 2. Scrape & Preprocess (One-time)

```bash
# Scrape full catalog (~480 assessments)
python scraper.py --max 0 --output assessments_raw.json

# Preprocess (fixes URLs, test types, duration)
python preprocess_final.py --input assessments_raw.json
```

### 3. Run Streamlit App

```bash
streamlit run app.py
```

### 4. Run API

```bash
python api.py
# API: http://localhost:5000
# Test: curl -X POST http://localhost:5000/recommend -H "Content-Type: application/json" -d '{"query": "Java developer"}'
```

---

## Evaluation  

```bash
python evaluate.py
```

**Sample Output:**
```
MEAN RECALL@10: 0.6821 (68.21%)
High Recall (≥50%): 42/55 queries
```

---

## API Usage  

### `POST /recommend`

```json
{
  "query": "Python developer with leadership skills",
  "top_k": 10
}
```

**Response:**
```json
{
  "query": "Python developer with leadership skills",
  "count": 10,
  "recommendations": [
    {
      "name": "Java Programming Test",
      "url": "https://www.shl.com/solutions/products/product-catalog/view/java-programming-test/",
      "test_type": ["K"],
      "duration": 30,
      "adaptive_support": true,
      "remote_support": true,
      "description": "Assesses core Java programming skills..."
    }
  ]
}
```

---

## Deployment  

Hosted on **Streamlit Community Cloud**  
- Auto-deploys on Git push  
- Free, fast, and scalable  

Link: [https://shlrecommendationsystem-8jgbn4syxunzjwfqjhbjfb.streamlit.app/](https://shlrecommendationsystem-8jgbn4syxunzjwfqjhbjfb.streamlit.app/)

---

## Future Improvements  

- [ ] Add **BERT embeddings** for semantic matching  
- [ ] Support **multi-language** queries  
- [ ] Add **assessment bundling** (e.g., Tech + Personality)  
- [ ] Export recommendations as PDF  

---

## Author  

**SHL AI Intern Assignment**  
Built with passion for smarter hiring  

---

**Star the repo** if you like it!  
**Deployed & Ready to Use**  
[https://shlrecommendationsystem-8jgbn4syxunzjwfqjhbjfb.streamlit.app/](https://shlrecommendationsystem-8jgbn4syxunzjwfqjhbjfb.streamlit.app/)
