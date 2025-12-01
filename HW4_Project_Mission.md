# HW4 Project Mission – Full Detailed Specification

## 1. Problem Definition
The assignment is to design and implement a **multi‑agent, multi‑threaded, fully orchestrated tour‑guide system** that enriches a driving route using intelligent autonomous agents.  
The system receives a start and end point, retrieves the full route using Google Maps API, and then processes each location along the route with several agents that search, fetch, analyze, and judge internet content.

This project is designed to mimic real-world hightech agent-based architecture, including concurrency, observability, modularity, and clean API-like packaging.

---

## 2. Purpose of the Project
The instructor’s goal is not only to check if we can get a YouTube video.  
The goal is to train us in **full system architecture**, including:

- Real agent orchestration  
- Thread scheduling and concurrency  
- Queue‑based synchronization models  
- Separation of concerns between modules  
- Logging and observability  
- External API integration  
- Search + Fetch tooling  
- LLM interaction (API or CLI)  
- Clean packaging and reproducibility  
- Building scalable software that could run “as if it were shipped to a client”

This is not a single script assignment.  
This is a *mini production system*.

---

## 3. Core Functional Requirements
### 3.1 Input
- User provides:
  - **FROM** location  
  - **TO** location  

### 3.2 Route Extraction (Google Maps API)
- Query Google Maps Directions API  
- Retrieve step-by-step driving instructions  
- For each step:
  - Extract coordinates, instructions, street names  
  - Assign a **transaction/location ID**  

### 3.3 Scheduler (Timing Engine)
The scheduler:
- Runs on its own thread  
- Every X seconds picks the next location  
- Sends it into a work queue for the orchestrator  
- Simulates real-time streaming behavior  
- Must be fully logged  

This is mandatory.  
A simple “for loop” over locations is not allowed.

### 3.4 Agents (Per Location)
For each location, the orchestrator must spawn three independent agents:

1. **Video Agent**  
   - Uses search tool to find relevant YouTube videos  
   - Uses fetch tool to read metadata (title, description, etc)  
   - Optionally uses LLM to verify relevance  

2. **Song Agent**  
   - Searches for a relevant song (Spotify, YouTube, TikTok)  
   - Fetches metadata  
   - Optionally uses LLM or heuristics  

3. **Knowledge Agent**  
   - Searches the web for historical/interesting information  
   - Fetches article/page  
   - Extracts text, summaries, or relevant facts  

Agents must:
- Be **independent modules**  
- Never know about each other  
- Work **in parallel**  
- Use search + fetch tools  
- Log everything (queries, chosen URL, reasoning)

### 3.5 Judge Agent
The judge is also an agent, but:
- It starts only after all three agents are finished  
- It receives:
  - Video candidate  
  - Song candidate  
  - Knowledge candidate  
- It applies a **scoring mechanism** based on:
  - Text relevance  
  - Keyword overlap  
  - Semantic similarity (optional via LLM)  
  - Heuristic rules based on step attributes  

It outputs:
- Final chosen item  
- Explanation / rationale  

Judge must be logged extensively.

### 3.6 Orchestrator
The orchestrator:
- Waits for incoming locations from scheduler  
- For each location:
  - Starts a **location worker thread**  
  - That worker:
    - Runs all 3 agents concurrently  
    - Waits for all results (queue or futures)  
    - Calls the judge  
    - Saves output  
    - Logs the entire flow  

This is the “brain” of the system.

### 3.7 Output
Final output:
- A list or JSON file containing:
  - Each location ID  
  - Its metadata  
  - The judge’s chosen item  
  - Scores and reasoning  

---

## 4. Non‑Functional Requirements (MANDATORY)
1. **Full logging** (not prints)  
2. **Threading**  
3. **Queue-based synchronization**  
4. **File-based interfaces between modules**  
5. **Config file for parameters**  
6. **CLI LLM or API LLM support**  
7. **Search + Fetch separation**  
8. **Clean Python package structure**  
9. **Reproducibility with no hard coded paths**

---

## 5. Packaging Requirements
The instructor emphasized that:

> “When you deliver a project to a client, they don’t get terminal commands or instructions. They get a PACKAGE.”

Meaning:
- The code must run immediately with:
  ```
  pip install .
  python -m hw4_tourguide
  ```
- Configuration is loaded automatically  
- No manual setup required  
- No ad-hoc scripts  
- No relative chaos  

This means:
- `pyproject.toml` or `setup.py`  
- `__main__.py` entry point  
- A proper Python package  

This is expected.

---

## 6. Mission Summary (for kickoff_agent)
1. Build a route-based multi-agent system  
2. Implement scheduler + orchestrator + worker model  
3. Implement three independent agents using search + fetch  
4. Implement judge agent with scoring  
5. Integrate Google Maps, logging, threading, queues  
6. Build a clean packaged project deliverable  
7. Output structured results per location  
8. Follow all engineering practices demonstrated by instructor

This file describes the exact mission that kickoff_agent must rely on.

