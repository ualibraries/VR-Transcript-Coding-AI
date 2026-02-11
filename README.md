# VR-Transcript-Coding-AI
Python-based NLP pipeline and API orchestration used to classify over 35,000 virtual reference transcripts
# Virtual Reference Analysis: Scalable Intent Classification (35k Corpus)

This repository contains the Python-based NLP pipeline and API orchestration used to classify over 35,000 virtual reference transcripts across multiple academic library systems. 

## 📌 Project Overview
As academic libraries face increasing demand for virtual support, this research evaluates the efficacy of Large Language Models (LLMs) in replicating professional librarian judgment for transcript coding. This project specifically compares **Aggressive Linguistic Preprocessing** (VBA/Lemmatization) against **Structural Natural Language Processing** (Python/API) to identify the "Semantic Gap" in automated intent classification.



## 🛠 Methodology: The "Light-Touch" Pipeline
Unlike traditional keyword-matching models, this pipeline utilizes a **Structural Preprocessing** approach designed for LLM optimization:

* **Redaction & Anonymization:** Removal of PII and long-string alphanumeric identifiers.
* **Structural Cleaning:** Regex-based removal of system timestamps to prevent temporal bias.
* **Entity Preservation:** Preservation of domain-specific "Semantic Anchors" (e.g., format descriptions like "print" or "microfilm") to prevent contextual erasure.
* **Deterministic Execution:** API configuration set to $Temperature = 0.0$ to ensure computational reproducibility.

## 📂 Repository Structure
* `coding_logic.py`: The main Python script using the Gemini 1.5 Flash API.
* `codebook.json`: The 41-category hierarchical taxonomy used for classification.
* `preprocessing_utils.py`: Regex utilities for timestamp and metadata stripping.
* `pilot_results/`: Comparative data from the 100-row head-to-head testing phase.

## 🚀 Key Discovery: The Preprocessing Paradox
Our pilot phase revealed that **lemmatization** (reducing words to roots) actually degraded model performance by removing the syntactic nuance required to distinguish between "Printing a document" (Tech Support) and "A print magazine" (Known Item). By pivoting to raw natural language with structural cleaning, accuracy in intent mapping increased significantly.
