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

# TASK 1: Dynamic Code Fix & Containerization
docker_fix_task = Task(
    description=f'''
    Analyze the files in the workspace located at {repo_path}.
    Identify the primary language and framework of the project.
    
    The user has provided the following specific instructions or bug description: 
    "{{job_data}}"
    
    1. READ AND EXECUTE THE USER INSTRUCTION: If the user asked you to create a specific file, write a specific route, or fix a specific bug in "{{job_data}}", you MUST do exactly that using your file writer tool.
    2. If the user instruction is empty or generic, perform a standard SRE containerization (create an appropriate Dockerfile and docker-compose.yml for the detected language).
    3. Make sure to use your tools to save your code to the workspace.
    ''',
    expected_output='Code fixes and containerization files written to the workspace based strictly on the user instructions.',
    agent=surgeon
)

# TASK 2: Dynamic DevSecOps Scan & RCA Report
rca_and_security_task = Task(
    description=f'''
    Now that the code is fixed according to the user's instructions, draft a highly professional "Root Cause Analysis & DevSecOps Report" in Markdown format.
    
    1. The report MUST be completely unique to the repository you just analyzed and the specific fixes you just applied based on "{{job_data}}".
    2. The report MUST include:
       - Incident Summary: Explain what the user requested ("{{job_data}}") and what you found.
       - SRE Resolution: Explain exactly what custom files you created or modified to fix the issue.
       - DevSecOps Audit: Note any real security vulnerabilities you found in THIS specific codebase.
    3. MANDATORY FINAL STEP: You MUST use your file writer tool to save this exact Markdown report to this exact path: {rca_file_path}
    ''',
    expected_output='A unique and professional TITAN_RCA_REPORT.md file successfully written to the disk.',
    agent=surgeon
)

if __name__ == "__main__":
    job_type = sys.argv[1] if len(sys.argv) > 1 else "REPO"
    passed_repo_path = sys.argv[2] if len(sys.argv) > 2 else repo_path
    
    # 👇 FIX: Capture the 4th argument (The Custom Prompt from the Frontend) 👇
    custom_instruction = sys.argv[3] if len(sys.argv) > 3 else "No specific bug described. Perform a general DevSecOps audit and containerization."

    print(f"\n[AI AGENT] 🛰️ NEURAL LINK INITIALIZED...", flush=True)
    print(f"[AI AGENT] Mode: {job_type}", flush=True)
    print(f"[AI AGENT] Target Workspace: {passed_repo_path}", flush=True)
    
    if not os.path.exists(repo_path):
        print(f"[AI AGENT] ❌ FATAL ERROR: Workspace path does not exist!", flush=True)
        sys.exit(1)

    print(f"[AI AGENT] 🧠 Injecting Custom User Prompt: {custom_instruction[:50]}...", flush=True)
    
    crew = Crew(
        agents=[surgeon], 
        tasks=[docker_fix_task, rca_and_security_task], 
        process=Process.sequential
    )
    
    # 👇 FIX: Pass the custom instruction into the Crew's memory 👇
    result = crew.kickoff(inputs={'job_data': custom_instruction})

    print("\n[AI AGENT] 🏁 MISSION COMPLETE. Final SRE & DevSecOps Report Generated.", flush=True)
    print(result, flush=True)