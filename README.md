# 🚀 TITAN: Autonomous DevSecOps & SRE Engine

**TITAN** is an advanced, AI-driven Site Reliability Engineering (SRE) platform designed to automate incident response, perform semantic code analysis, and dynamically containerize patches. Built for modern DevSecOps workflows, TITAN acts as an autonomous tier-1 support engineer that intercepts fatal server crashes, deploys a Python-based agentic swarm to remediate the code, and generates verified, deployable artifacts.

---

## 🌩️ Architecture Overview

The platform operates on a decoupled microservices architecture bridging a MERN stack with a CrewAI Python engine:
* **The Dashboard (React/Vite):** A high-fidelity, liquid-glass UI for monitoring real-time swarm telemetry, managing the SRE Ledger, and triggering Chaos Engineering simulations.
* **The Interceptor (Node.js/Express):** A resilient backend featuring a Global Middleware Trap that catches unhandled exceptions, logs immutable telemetry to MongoDB, and triggers the asynchronous AI pipeline.
* **The Swarm Engine (Python/CrewAI):** An isolated workspace where specialized LLM agents (powered by Groq/Llama3) clone repositories, perform semantic logic audits, and write structural DevSecOps patches.
* **The Sandbox (Docker):** Ephemeral, programmatically generated Alpine Linux containers that isolate and verify the AI's logic before archiving the payload.

---

## 🔥 Key Features

* **Agentic Semantic Analysis:** Moves beyond fragile regex or basic string manipulation. TITAN utilizes LLM-driven contextual parsing to comprehend deep code logic and isolate points of failure.
* **Ephemeral Docker Sandboxing:** Integrates the Docker Engine API via Node.js `child_process`. It spins up isolated containers to verify structural integrity, completely destroying the environment post-validation (`--rm`) to prevent resource bleeding.
* **Global SRE Middleware Trap:** Features an Express.js global error handler that catches fatal runtime crashes, freezes the state, and alerts the SRE Ledger instantly.
* **Chaos Engineering Simulator:** Built-in "Chaos Monkey" tools to inject deliberate fatal faults into the backend, validating the interception and auto-remediation pipeline.
* **Immutable Audit Ledger:** Cryptographically logs all AI operations, crash reports, and auto-remediations to a secure NoSQL MongoDB cluster.

---

## 📂 Project Structure

```text
PROJECT-TITAN/
├── mern-backend/       # Node.js API, Docker & SRE Trap
│   ├── controllers/    # Route logic & AI triggers
│   ├── models/         # MongoDB Schemas
│   ├── healer-workspace/ 
│   └── server.js       # Global SRE Entry Point
├── frontend/           # React + Vite UI
└── README.md           # System Documentation

## 🛠️ Installation & Setup

### Prerequisites
* **Node.js:** v18 or newer
* **Python:** v3.10 or newer (with `pip`)
* **Docker Desktop:** Must be installed and running in the background for the Sandbox verification.
* **MongoDB:** A running local instance or MongoDB Atlas cluster.
* **Groq API Key:** Required for the CrewAI swarm logic.

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/PROJECT-TITAN.git
cd PROJECT-TITAN

2. Configure the Node.js Backend
Bash
cd mern-backend
npm install

Create a .env file in the mern-backend directory:
PORT=5000
MONGO_URI=mongodb+srv://<your_cluster_url>
JWT_SECRET=your_super_secret_key

3. Configure the Python Swarm Engine
Ensure you are still inside the mern-backend directory, as the Node server triggers the Python script directly.

Bash
pip install crewai langchain-groq python-dotenv litellm

Create a .env file specifically inside mern-backend/healer-workspace for the agents:
GROQ_API_KEY=gsk_your_groq_api_key_here

4. Configure the React Frontend:
Bash'
cd ../frontend
npm install
bash'''

5. Boot the Architecture
You will need two terminal windows:

-Terminal 1 (Backend): cd mern-backend && node server.js

-Terminal 2 (Frontend): cd frontend && npm run dev


🚦 System Usage & Workflow

1. **Trigger the Trap:** Navigate to the **Chaos** tab on the dashboard and deploy the Chaos Payload. This simulates a fatal server crash.

2. **Observe the Ledger:** The crash will instantly be intercepted and logged in the Operations Ledger.

3. **Deploy the Swarm:** Navigate to the **Healer** tab. Input the target repository URL and deploy the swarm.

4. **Sandboxing:** Watch the backend terminal as Docker dynamically pulls an Alpine image, mounts the patched repository, runs security checks, and self-destructs.

5. **Artifact Extraction:** Download the verified `.zip` payload directly from the dashboard.


🐞 Troubleshooting & SRE Notes
Docker Sandbox Failing: If you see failed to connect to the docker API, ensure Docker Desktop is actively running on your host machine before triggering the swarm.

CrewAI/Groq Rate Limits (429): If the swarm fails mid-generation, you may have hit the Groq free-tier rate limit. Wait 60 seconds and retry, or upgrade your API tier.

Cross-Origin (CORS) Blocks: Ensure your frontend URL (http://localhost:5173) is explicitly allowed in the server.js CORS configuration.


📜 License
Built for educational and enterprise-architecture demonstration purposes by Ayan Sayyad. Licensed under the MIT License.