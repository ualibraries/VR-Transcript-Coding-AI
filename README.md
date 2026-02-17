# VR-Transcript-Coding-AI
Python-based NLP pipeline and API orchestration used to classify over 35,000 virtual reference transcripts
# Virtual Reference Analysis: Scalable Intent Classification (35k Corpus)

This repository contains the Python-based NLP pipeline and API orchestration used to classify approximately 35,000 virtual reference transcripts across 5 large, academic library systems. 

## 📌 Project Overview
As academic libraries face increasing demand for virtual support, this research evaluates the efficacy of Large Language Models (LLMs) in replicating and auditing professional librarian judgment for transcript coding. This project specifically compares **Aggressive Linguistic Preprocessing** (VBA/Lemmatization) against **Structural Natural Language Processing** (Python/API) to identify the "Semantic Gap" in automated intent classification.

## **🚀 Key Evolution: The Consensus Audit Model**
Originally designed as a head-to-head comparison between human and AI coders, the project has evolved into an **AI-Augmented Consensus Model**. Pilot audits revealed significant **Human Analytical Fatigue** in manually coded sets, particularly in lower-frequency intent quartiles.

To eliminate this bias, the pipeline now serves as a **High-Precision Auditor**, flagging human inconsistencies for expert adjudication to produce a 100% verified **Gold Standard** dataset.

## 🛠 Methodology: The "Light-Touch" Pipeline
Unlike traditional models, this pipeline utilizes a **Structural Preprocessing** approach designed to maintain the "Semantic Anchors" required for professional judgment:

* **Redaction & Anonymization:** Removal of PII and long-string alphanumeric identifiers.
* **Structural Cleaning**: Pre-compiled Regex patterns strip system timestamps to prevent **Temporal Bias** (e.g., miscoding "Hours" based on chat time).  
* **Entity Preservation**: Maintains placeholders like \<PERSON\> and \<URL\> to preserve sentence structure while ensuring PII redaction.  
* **Deterministic Execution**: API configuration is locked at **Temperature=0.0** and **Top\_K=1** to ensure computational reproducibility.  
* **The "AI Coffee" Injection**: A specific freshness reminder is injected into every API call to combat "analytical drift" and ensure the 35,000th transcript is processed with the same rigor as the first.


## 📂 Repository Structure
* `coding_logic.py`: Optimized Python orchestration using the Gemini 2.5 Flash-lite API with exponential backoff and resume logic. Includes system prompt with explicit "Traps" and "Negative Constraints" to prevent common misclassifications.  
* `codebook.json`: A 41-category hierarchical taxonomy  
* 'preprocessing_utils.py': High-performance utility script for structural noise reduction and API configuration.  
* 'tiered_audit.py': A tiered conflict-detection script that prioritizes **Tier 1 (Total Mismatches)** and **Tier 2 (Intent Expansions)** for expert review.

## 🚀 Key Discovery: The Preprocessing Paradox
* **The Preprocessing Paradox**: Lemmatization was found to degrade model performance by removing the syntactic nuance required to distinguish between formats (e.g., "Print" as a format vs. "Printing" as a tech issue).
* **Exhaustivity**: The AI consistently identifies secondary intents (e.g., directional help requested after a technical issue) that human coders frequently overlook due to fatigue.
