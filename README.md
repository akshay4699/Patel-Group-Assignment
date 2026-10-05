# Multi-Agent Book Writer: Pay Me on UPI

An autonomous multi-agent system built using **LangGraph** and **Groq (openai/gpt-oss-120b)** that researches, drafts, verifies, edits, and compiles a complete three-chapter book with authentic, numbered citations and zero bullet points, tailored for first-time small-business owners in India.

---

## 📖 Book Information
* **Title:** *Pay Me on UPI: How Digital Payments Changed Small Business in India*
* **Target Audience:** First-time small-business owners in India (kirana stores, chai stalls, small retailers, traders).
* **Length:** 3 chapters (600–900 words per chapter).
* **Tone:** Friendly, encouraging, and clear mentor tone; plain English with zero unexplained jargon.
* **Format:** Continuous, flowing prose without any bullet points or numbered lists in chapter text, ending with a single `Takeaway:` line followed by references.

---

## 🏛️ System Architecture

The multi-agent architecture is orchestrated as a state graph using **LangGraph**, where each agent operates as a specialized node with defined state contracts and conditional review cycles:

```mermaid
flowchart TD
    Start([Start]) --> Planner[1. Planner Agent\nDesigns 3-chapter narrative arc]
    Planner --> Researcher[2. Researcher Agent\nSources authentic NPCI/RBI/PIB citations]
    Researcher --> Writer[3. Writer Agent\nDrafts 600-900 words flowing prose with [n] citations]
    Writer --> Factchecker[4. Fact-Checker Agent\nVerifies citations & audits claims]
    Factchecker --> Editor[5. Editor Agent\nChecks tone, word count, grammar & no-bullet rule]
    Editor --> Decision{Both Approved OR\nMax Revisions Met?}
    
    Decision -- No: Needs Fixes --> Revise[Increment Revision Count\nAttach Critique]
    Revise --> Writer
    
    Decision -- Yes: Chapter Approved --> CheckMore{More Chapters\nRemaining?}
    CheckMore -- Yes --> NextChapter[Advance Chapter Index]
    NextChapter --> Researcher
    
    CheckMore -- No --> Compile[6. Compiler Node\nAssembles Table of Contents & Manuscript]
    Compile --> End([Finish: output/Pay_Me_on_UPI.md])
```

---

## 🤖 Agent Roles & Responsibilities

| Agent | Responsibility | Key Output / Verification |
| :--- | :--- | :--- |
| **Planner** | Outlines the 3 cohesive chapters, themes, and narrative milestones for Indian shopkeepers. | Generates structured `BookOutline` with data targets. |
| **Researcher** | Fetches and validates real facts, dates, and URLs from official repositories (NPCI, RBI, PIB, Reputable Press). | Produces numbered `ResearchItem` list with genuine URLs. |
| **Writer** | Composes flowing prose (600–900 words) using a warm, mentor-like voice with numbered in-text citations `[n]` and ending with `Takeaway:`. | Drafts continuous chapter text without bullet points. |
| **Fact-checker** | Cross-references every statistic and date against the research library; checks for broken or fabricated links. | `FactCheckFeedback` (`approved: bool`, unverified claims). |
| **Editor** | Evaluates readability, tone, word count (600–900 words), absence of bullet points, and grammar. | `ChapterReviewFeedback` (`approved: bool`, actionable fixes). |
| **Compiler** | Consolidates all accepted chapters into a clean, markdown manuscript. | Exports final book to `output/Pay_Me_on_UPI.md`. |

---

## ⚙️ Project Structure

```text
├── config.py                 # Configuration, API keys, constants, and LLM factory
├── state.py                  # Pydantic schemas and LangGraph TypedDict state
├── workflow.py               # LangGraph state machine, nodes, edges, and conditional router
├── main.py                   # CLI entry point with live streaming execution logs
├── requirements.txt          # Python dependencies
├── .env.example              # Template for environment variables
├── src/
│   ├── __init__.py
│   ├── prompts.py            # Strict prompts for all 5 agents matching assignment brief
│   ├── planner.py            # Chapter planning node
│   ├── researcher.py         # Fact and source discovery node
│   ├── writer.py             # Chapter drafting and revision node
│   ├── factchecker.py        # Citation audit node
│   └── editor.py             # Tone, style, and word-count reviewer node
└── output/                   # Directory where finalized book manuscript is saved
```

---

## 🚀 Setup & Execution Instructions

### 1. Prerequisites
* Python 3.10+ (Python 3.11–3.13 supported)
* A free Groq API Key (from [console.groq.com](https://console.groq.com/keys))

### 2. Environment Setup
Clone the repository and activate your virtual environment:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure API Key
Create a `.env` file in the project root directory (you can copy `.env.example`):

```bash
cp .env.example .env
```

Add your Groq API key:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
MAX_REVISION_ROUNDS=2
```

### 4. Run the Multi-Agent System
Run the main script:
```bash
python main.py
```

### 5. Inspect the Output
Once the system completes its autonomous execution, the full book manuscript will be available at:
```text
output/Pay_Me_on_UPI.md
```

---

## 🛡️ Key Design Choices & Safeguards

1. **Strict Plain-Prose Guardrail:**
   The Editor and Fact-checker deterministically enforce the brief's constraint forbidding bullet points, hyphens, and numbered lists inside the chapter body.
2. **Bounded Revision Cycles:**
   To prevent runaway API consumption or infinite loops, the system features a configurable `MAX_REVISION_ROUNDS` guardrail (default: 2). If an edge case is not resolved within the limit, the best draft is finalized and logged.
3. **Authentic Ground-Truth Benchmarking:**
   Sources originate from official government and regulatory authorities (Reserve Bank of India, National Payments Corporation of India, Press Information Bureau) and national financial journalism, preventing citation fabrication.
4. **Transparent State Tracking:**
   Every event, word count audit, and critique is streamed live to the console and preserved in the LangGraph execution state.
