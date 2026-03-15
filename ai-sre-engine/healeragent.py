import os, sys, time
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import FileWriterTool
from crewai.tools import BaseTool

# Force UTF-8 and load environment variables
sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# --- 1. LLM SETUP ---
titan_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1 # Low temp for highly technical, predictable code output
)

# --- 2. TOOLS & PATHS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# Unified path to the workspace shared with Node.js
repo_path = os.path.normpath(os.path.join(current_dir, "..", "healer-workspace", "repo-to-heal"))
rca_file_path = os.path.normpath(os.path.join(repo_path, "TITAN_RCA_REPORT.md"))

# CUSTOM TOOL 1: Simple Reader
class SimpleReader(BaseTool):
    name: str = "simple_file_reader"
    description: str = "Reads the entire content of a file from a given path."
    def _run(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error: {str(e)}"

# CUSTOM TOOL 2: List Files
class ListRepoFilesTool(BaseTool):
    name: str = "list_repo_files"
    description: str = "Lists files in the repository workspace."
    def _run(self, directory_path: str = "default") -> str:
        files = []
        if not os.path.exists(repo_path):
            return "Error: Workspace path not found."
        for root, dirs, f_names in os.walk(repo_path):
            if any(x in root for x in ['.git', 'node_modules', 'venv']): continue
            for f in f_names: files.append(os.path.join(root, f))
        return "\n".join(files[:25])

list_tool = ListRepoFilesTool()
reader = SimpleReader()
writer = FileWriterTool()

# --- 3. AGENTS ---
surgeon = Agent(
    role='Lead DevSecOps & SRE Surgeon', 
    goal='Write code fixes, Docker configurations, and security audit reports to the workspace.', 
    backstory='You are an elite Site Reliability Engineer and DevSecOps auditor. You must ALWAYS use your file writer tool to save your work to the disk.',
    verbose=True, 
    llm=titan_llm, 
    tools=[reader, writer, list_tool]
)

# --- 4. TASKS ---

# TASK 1: The Core Fix & Dockerization
docker_fix_task = Task(
    description=f'''
    The user needs a functional Node.js container in {repo_path}. 
    1. Check for 'package.json'. If missing, create one with "express" and "cors".
    2. Apply the requested fix based on this crash data: {{job_data}}.
    3. MANDATORY: Create a 'Dockerfile' with node:18-alpine, WORKDIR /app, COPY, RUN npm install, EXPOSE 3000, and CMD ["node", "index.js"].
    4. Create 'docker-compose.yml' mapping port 3000:3000.
    ''',
    expected_output='Simplified Dockerfile, docker-compose.yml, and patched code written to the directory.',
    agent=surgeon
)

# 👇 NEW: TASK 2: DevSecOps Scan & RCA Report 👇
rca_and_security_task = Task(
    description=f'''
    Now that the code is fixed and containerized, you must act as a DevSecOps Auditor.
    1. Perform a brief security review of the files in {repo_path} (look for missing rate limiting, hardcoded secrets, or bad CORS rules).
    2. Draft a highly professional "Root Cause Analysis & DevSecOps Report" in Markdown format.
    3. The report MUST include:
       - Incident Summary (Based on: {{job_data}})
       - SRE Resolution (What Docker files you created and what code you changed)
       - DevSecOps Audit (Any security vulnerabilities you noticed or recommend fixing)
    4. MANDATORY FINAL STEP: You MUST use your file writer tool to save this exact Markdown report to this exact path: {rca_file_path}
    ''',
    expected_output='A professional TITAN_RCA_REPORT.md file successfully written to the disk.',
    agent=surgeon
)

if __name__ == "__main__":
    job_type = sys.argv[1] if len(sys.argv) > 1 else "REPO"
    job_data = sys.argv[2] if len(sys.argv) > 2 else ""

    print(f"\n[AI AGENT] 🛰️ NEURAL LINK INITIALIZED...", flush=True)
    print(f"[AI AGENT] Mode: {job_type}", flush=True)
    print(f"[AI AGENT] Target Workspace: {repo_path}", flush=True)
    
    if not os.path.exists(repo_path):
        print(f"[AI AGENT] ❌ FATAL ERROR: Workspace path does not exist!", flush=True)
        sys.exit(1)

    print(f"[AI AGENT] 🧠 Starting SRE logic for: {job_data[:50]}...", flush=True)
    
    # 👇 FIXED: Notice how BOTH tasks are now passed into the Crew 👇
    crew = Crew(
        agents=[surgeon], 
        tasks=[docker_fix_task, rca_and_security_task], 
        process=Process.sequential
    )
    
    result = crew.kickoff(inputs={'job_data': job_data})

    print("\n[AI AGENT] 🏁 MISSION COMPLETE. Final SRE & DevSecOps Report Generated.", flush=True)
    print(result, flush=True)