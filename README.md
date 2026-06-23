# IPO Surge Intelligence Agent
**RaveMinds Series 2 — Project 3**

> Predictive + Adaptive AI for High Volume IPO Events

**AI Pattern:** Predictive + Adaptive AI  
**Domain:** Capital Markets — High Volume Event Management  
**Stack:** Ollama + Mistral 7B + LanceDB + DuckDB + LangGraph + Streamlit + Docker  
**API Cost:** $0 | **Data:** Never leaves your infrastructure

---

## The Problem

A high-profile IPO like SpaceX floods systems with 100x normal volume in minutes.
Ops teams have no way to predict failure points in advance, dynamically triage what
breaks first, or adjust risk thresholds in real time. Static rules flag everything
as critical — useless under surge conditions.

## What's New vs Previous Projects

| Pattern | This Project |
|---|---|
| Predictive failure modelling | Predicts before things break |
| Dynamic threshold adaptation | Adjusts what "normal" means in real time |
| Surge scenario simulation | 10x · 50x · 100x volume simulation |
| Three-phase AI behaviour | Pre / During / Post IPO |
| Confidence decay | AI certainty degrades as conditions diverge |

## Three Phases

- **Phase 1 — Pre-IPO:** Simulate surge scenarios, predict failure points, generate readiness score
- **Phase 2 — Live Surge:** Continuous monitoring, dynamic thresholds, real-time triage
- **Phase 3 — Post-IPO:** Accuracy audit, memory update, management report

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Ollama and pull Mistral
ollama pull mistral

# 3. Seed synthetic data
python scripts/seed_data.py

# 4. Run the dashboard
streamlit run ui/app.py
```

## Project Structure

```
ipo_surge_intelligence/
├── agents/
│   ├── pre_ipo_agent.py        # Surge simulation + readiness scoring
│   ├── live_surge_agent.py     # Real-time monitoring + adaptive thresholds
│   ├── post_ipo_agent.py       # Accuracy audit + memory update
│   └── orchestrator.py         # LangGraph workflow orchestration
├── core/
│   ├── database.py             # LanceDB + DuckDB management
│   ├── threshold_adapter.py    # Dynamic threshold adaptation logic
│   ├── surge_simulator.py      # Volume scenario simulation
│   ├── triage_engine.py        # Real-time priority ranking
│   └── llm_client.py          # Ollama + Mistral interface
├── data/
│   ├── historical_events.json  # Past IPO surge patterns
│   └── system_baselines.json   # Normal operating baselines
├── ui/
│   ├── app.py                  # Main Streamlit dashboard
│   ├── assets/
│   │   └── rm_logo.png         # RaveMinds logo
│   └── components/
│       ├── pre_ipo_view.py     # Pre-IPO phase UI
│       ├── live_surge_view.py  # Live surge phase UI
│       └── post_ipo_view.py    # Post-IPO phase UI
├── scripts/
│   └── seed_data.py            # Synthetic data seeder
├── tests/
│   └── test_agents.py          # Agent unit tests
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## RaveMinds Series 2

| Project | Pattern | Status |
|---|---|---|
| Trade Compliance Copilot | Human in the Loop | Done |
| Settlement Alert Agent | Autonomous Agentic Loop | Done |
| IPO Surge Intelligence Agent | Predictive + Adaptive AI | This |
