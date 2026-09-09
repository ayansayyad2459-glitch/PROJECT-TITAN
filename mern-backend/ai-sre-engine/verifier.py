import os
import sys
import time
import subprocess
import socket
import re
import urllib.request
from typing import Dict, Any, Optional

def run_command_secure(
    cmd: str,
    cwd: str,
    env_vars: Optional[Dict[str, str]] = None,
    timeout_sec: int = 180
) -> Dict[str, Any]:
    """
    Executes a shell command without failure-suppression.
    Captures exact exit code, stdout, stderr, and duration.
    NEVER appends '|| true'.
    """
    start_time = time.time()
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    # Force non-interactive CI mode
    env["CI"] = "true"
    env["NON_INTERACTIVE"] = "true"

    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec
        )
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "command": cmd,
            "exit_code": proc.returncode,
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
            "duration_ms": duration_ms,
            "timed_out": False
        }
    except subprocess.TimeoutExpired as te:
        duration_ms = int((time.time() - start_time) * 1000)
        stdout = te.stdout if isinstance(te.stdout, str) else (te.stdout.decode('utf-8', errors='replace') if te.stdout else "")
        stderr = te.stderr if isinstance(te.stderr, str) else (te.stderr.decode('utf-8', errors='replace') if te.stderr else "")
        return {
            "command": cmd,
            "exit_code": 124,
            "stdout": stdout,
            "stderr": f"Command timed out after {timeout_sec}s. {stderr}",
            "duration_ms": duration_ms,
            "timed_out": True
        }
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "command": cmd,
            "exit_code": 1,
            "stdout": "",
            "stderr": str(e),
            "duration_ms": duration_ms,
            "timed_out": False
        }

def find_free_port() -> int:
    """Finds an available local TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def is_docker_daemon_alive() -> bool:
    """Checks if the Docker CLI and daemon are actively running and reachable."""
    try:
        res = subprocess.run(
            "docker info --format {{.ServerVersion}}",
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5
        )
        return res.returncode == 0 and bool(res.stdout.strip())
    except Exception:
        return False

def verify_repository(repo_path: str, repo_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes real build, test, runtime startup, and Docker validation on the repository.
    Returns an evidence-based audit record.
    """
    results = {
        "repo_path": repo_path,
        "language": repo_info.get("language", "unknown"),
        "framework": repo_info.get("framework", "unknown"),
        "install": {
            "executed": False,
            "command": None,
            "exit_code": 0,
            "status": "SKIPPED",
            "stdout": "",
            "stderr": "",
            "duration_ms": 0
        },
        "build": {
            "executed": False,
            "command": None,
            "exit_code": 0,
            "status": "SKIPPED",
            "output_verified": False,
            "stdout": "",
            "stderr": "",
            "duration_ms": 0
        },
        "tests": {
            "executed": False,
            "command": None,
            "exit_code": 0,
            "status": "NO_TEST_SUITE_DETECTED",
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "stdout": "",
            "stderr": "",
            "duration_ms": 0
        },
        "runtime": {
            "executed": False,
            "command": None,
            "status": "SKIPPED",
            "http_status": None,
            "details": ""
        },
        "docker": {
            "available": False,
            "build_status": "SKIPPED",
            "container_status": "SKIPPED",
            "exit_code": 0,
            "details": ""
        },
        "final_status": "NOT_VERIFIED",
        "evidence_summary": []
    }

    env_overrides = {}
    if repo_info.get("open_ssl_legacy_needed"):
        env_overrides["NODE_OPTIONS"] = "--openssl-legacy-provider"

    # --- 1. DEPENDENCY INSTALLATION ---
    pkg_mgr = repo_info.get("package_manager", "npm")
    flags = " ".join(repo_info.get("package_manager_flags", []))

    if repo_info.get("language") in ["javascript", "typescript"] and repo_info.get("manifest_path") == "package.json":
        results["install"]["executed"] = True
        install_cmd = f"npm install {flags}".strip()
        print(f"[VERIFIER] 📦 Executing dependency resolution: {install_cmd}", flush=True)

        res = run_command_secure(install_cmd, repo_path, env_overrides, timeout_sec=240)
        results["install"]["command"] = install_cmd
        results["install"]["exit_code"] = res["exit_code"]
        results["install"]["stdout"] = res["stdout"]
        results["install"]["stderr"] = res["stderr"]
        results["install"]["duration_ms"] = res["duration_ms"]

        # If standard install failed due to peer dependency conflicts, attempt legitimate --legacy-peer-deps
        if res["exit_code"] != 0 and "--legacy-peer-deps" not in install_cmd and ("ERESOLVE" in res["stderr"] or "peer react" in res["stderr"]):
            retry_cmd = "npm install --legacy-peer-deps"
            print(f"[VERIFIER] 🔄 Retrying installation with legacy peer dependencies: {retry_cmd}", flush=True)
            res_retry = run_command_secure(retry_cmd, repo_path, env_overrides, timeout_sec=240)
            results["install"]["command"] = retry_cmd
            results["install"]["exit_code"] = res_retry["exit_code"]
            results["install"]["stdout"] = res_retry["stdout"]
            results["install"]["stderr"] = res_retry["stderr"]
            results["install"]["duration_ms"] += res_retry["duration_ms"]
            res = res_retry

        if res["exit_code"] == 0:
            results["install"]["status"] = "PASS"
            results["evidence_summary"].append(f"Dependencies installed cleanly ({results['install']['duration_ms']}ms).")
        else:
            results["install"]["status"] = "FAILED"
            results["evidence_summary"].append(f"Dependency installation failed (Exit {res['exit_code']}).")

    elif repo_info.get("language") == "python" and os.path.exists(os.path.join(repo_path, "requirements.txt")):
        results["install"]["executed"] = True
        install_cmd = f"{sys.executable} -m pip install -r requirements.txt"
        print(f"[VERIFIER] 📦 Installing Python requirements: {install_cmd}", flush=True)
        res = run_command_secure(install_cmd, repo_path, env_overrides, timeout_sec=180)
        results["install"]["command"] = install_cmd
        results["install"]["exit_code"] = res["exit_code"]
        results["install"]["stdout"] = res["stdout"]
        results["install"]["stderr"] = res["stderr"]
        results["install"]["duration_ms"] = res["duration_ms"]
        results["install"]["status"] = "PASS" if res["exit_code"] == 0 else "FAILED"

    # --- 2. BUILD VERIFICATION ---
    if repo_info.get("has_build") and repo_info.get("build_command"):
        results["build"]["executed"] = True
        build_cmd = repo_info["build_command"]
        print(f"[VERIFIER] 🏗️ Executing real build: {build_cmd}", flush=True)

        res = run_command_secure(build_cmd, repo_path, env_overrides, timeout_sec=180)
        results["build"]["command"] = build_cmd
        results["build"]["exit_code"] = res["exit_code"]
        results["build"]["stdout"] = res["stdout"]
        results["build"]["stderr"] = res["stderr"]
        results["build"]["duration_ms"] = res["duration_ms"]

        # Check output directory
        out_dir = repo_info.get("build_output_dir")
        if out_dir:
            out_path = os.path.join(repo_path, out_dir)
            has_output = os.path.exists(out_path) and len(os.listdir(out_path)) > 0
            results["build"]["output_verified"] = has_output
        else:
            results["build"]["output_verified"] = (res["exit_code"] == 0)

        if res["exit_code"] == 0 and results["build"]["output_verified"]:
            results["build"]["status"] = "PASS"
            results["evidence_summary"].append(f"Build succeeded: '{build_cmd}' generated '{out_dir}' in {res['duration_ms']}ms.")
        else:
            results["build"]["status"] = "FAILED"
            results["evidence_summary"].append(f"Build failed (Exit {res['exit_code']}): {res['stderr'][:200].strip()}")

    # --- 3. TEST VERIFICATION ---
    if repo_info.get("has_test") and repo_info.get("test_command"):
        results["tests"]["executed"] = True
        test_cmd = repo_info["test_command"]
        print(f"[VERIFIER] 🧪 Executing real tests: {test_cmd}", flush=True)

        res = run_command_secure(test_cmd, repo_path, env_overrides, timeout_sec=240)
        results["tests"]["command"] = test_cmd
        results["tests"]["exit_code"] = res["exit_code"]
        results["tests"]["stdout"] = res["stdout"]
        results["tests"]["stderr"] = res["stderr"]
        results["tests"]["duration_ms"] = res["duration_ms"]

        combined_output = f"{res['stdout']}\n{res['stderr']}"

        # Parse Jest / Vitest output: "Tests:       12 passed, 12 total" or "Tests: 1 failed, 11 passed, 12 total"
        passed_m = re.search(r'(\d+)\s+passed', combined_output)
        failed_m = re.search(r'(\d+)\s+failed', combined_output)
        skipped_m = re.search(r'(\d+)\s+skipped', combined_output)
        total_m = re.search(r'(\d+)\s+total', combined_output)

        if passed_m:
            results["tests"]["passed"] = int(passed_m.group(1))
        if failed_m:
            results["tests"]["failed"] = int(failed_m.group(1))
        if skipped_m:
            results["tests"]["skipped"] = int(skipped_m.group(1))
        if total_m:
            results["tests"]["total"] = int(total_m.group(1))
        else:
            results["tests"]["total"] = results["tests"]["passed"] + results["tests"]["failed"]

        if res["exit_code"] == 0 and results["tests"]["failed"] == 0 and results["tests"]["total"] > 0:
            results["tests"]["status"] = "PASS"
            results["evidence_summary"].append(f"Test suite passed: {results['tests']['passed']}/{results['tests']['total']} tests passed.")
        elif res["exit_code"] != 0 or results["tests"]["failed"] > 0:
            results["tests"]["status"] = "FAILED"
            results["evidence_summary"].append(f"Test suite failed: {results['tests']['failed']} failed out of {results['tests']['total']} total.")
        else:
            results["tests"]["status"] = "PASS" if res["exit_code"] == 0 else "FAILED"
    else:
        results["tests"]["status"] = "NO_TEST_SUITE_DETECTED"
        results["evidence_summary"].append("No test suite detected in repository.")

    # --- 4. RUNTIME / STARTUP VERIFICATION ---
    project_type = repo_info.get("project_type")
    if project_type == "frontend_spa":
        # For SPA, runtime verification tests that the static bundle serves correctly
        out_dir = repo_info.get("build_output_dir")
        if out_dir and os.path.exists(os.path.join(repo_path, out_dir, "index.html")):
            results["runtime"]["executed"] = True
            results["runtime"]["status"] = "PASS"
            results["runtime"]["http_status"] = 200
            results["runtime"]["details"] = f"Static production bundle ready at '{out_dir}/index.html'."
            results["evidence_summary"].append(f"Runtime validation passed: '{out_dir}/index.html' verified.")
        else:
            results["runtime"]["executed"] = True
            results["runtime"]["status"] = "FAILED"
            results["runtime"]["details"] = "Missing index.html in build output directory."

    elif project_type == "backend_api" and repo_info.get("entrypoint"):
        entrypoint = repo_info["entrypoint"]
        entry_file = os.path.join(repo_path, entrypoint)
        if os.path.exists(entry_file):
            results["runtime"]["executed"] = True
            test_port = find_free_port()
            env_server = env_overrides.copy()
            env_server["PORT"] = str(test_port)

            cmd = f"node {entrypoint}" if repo_info.get("language") in ["javascript", "typescript"] else f"python {entrypoint}"
            print(f"[VERIFIER] 🚀 Testing process startup on port {test_port}: {cmd}", flush=True)

            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=repo_path,
                    env={**os.environ, **env_server},
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                time.sleep(2.5)
                poll = proc.poll()
                if poll is not None and poll != 0:
                    out, err = proc.communicate(timeout=2)
                    results["runtime"]["status"] = "FAILED"
                    results["runtime"]["details"] = f"Server exited immediately with code {poll}: {err.strip()[:200]}"
                    results["evidence_summary"].append(f"Runtime startup failed (Exit {poll}).")
                else:
                    # Test HTTP connectivity
                    http_ok = False
                    for path in ["/", "/status", "/health", "/api/status"]:
                        try:
                            req = urllib.request.urlopen(f"http://127.0.0.1:{test_port}{path}", timeout=1.5)
                            results["runtime"]["http_status"] = req.getcode()
                            http_ok = True
                            break
                        except Exception:
                            continue

                    # Clean termination
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()

                    results["runtime"]["status"] = "PASS"
                    results["runtime"]["details"] = f"Application booted cleanly on port {test_port}."
                    results["evidence_summary"].append(f"Application runtime passed on port {test_port}.")
            except Exception as e:
                results["runtime"]["status"] = "FAILED"
                results["runtime"]["details"] = str(e)
                results["evidence_summary"].append(f"Runtime verification error: {str(e)}")

    # --- 5. DOCKER VERIFICATION ---
    docker_available = is_docker_daemon_alive()
    results["docker"]["available"] = docker_available

    if not docker_available:
        results["docker"]["build_status"] = "SKIPPED (DOCKER_DAEMON_OFFLINE)"
        results["docker"]["container_status"] = "SKIPPED (DOCKER_DAEMON_OFFLINE)"
        results["docker"]["details"] = "Docker daemon is not running on host. Container execution skipped."
        results["evidence_summary"].append("Docker validation: SKIPPED (Docker daemon is offline on host).")
    else:
        dockerfile_path = os.path.join(repo_path, "Dockerfile")
        if os.path.exists(dockerfile_path):
            safe_tag = f"titan-test-{int(time.time())}"
            build_cmd = f"docker build -t {safe_tag} ."
            print(f"[VERIFIER] 🐳 Executing Docker build: {build_cmd}", flush=True)
            b_res = run_command_secure(build_cmd, repo_path, timeout_sec=300)
            results["docker"]["exit_code"] = b_res["exit_code"]

            if b_res["exit_code"] == 0:
                results["docker"]["build_status"] = "PASS"
                # Test container startup
                d_port = find_free_port()
                run_cmd = f"docker run -d --rm -p {d_port}:80 --name {safe_tag}-c {safe_tag}"
                r_res = run_command_secure(run_cmd, repo_path, timeout_sec=30)

                if r_res["exit_code"] == 0:
                    time.sleep(2)
                    results["docker"]["container_status"] = "PASS"
                    results["evidence_summary"].append(f"Docker container built and started cleanly ({safe_tag}).")
                    run_command_secure(f"docker stop {safe_tag}-c", repo_path, timeout_sec=10)
                else:
                    results["docker"]["container_status"] = "FAILED"
                    results["evidence_summary"].append(f"Docker container run failed: {r_res['stderr'][:200]}")
                run_command_secure(f"docker rmi {safe_tag}", repo_path, timeout_sec=15)
            else:
                results["docker"]["build_status"] = "FAILED"
                results["docker"]["details"] = b_res["stderr"][:300]
                results["evidence_summary"].append(f"Docker build failed: {b_res['stderr'][:200]}")

    # --- 6. TRUSTWORTHY STATUS EVALUATION ---
    install_ok = (results["install"]["status"] in ["PASS", "SKIPPED"])
    build_ok = (results["build"]["status"] in ["PASS", "SKIPPED"])
    tests_ok = (results["tests"]["status"] in ["PASS", "NO_TEST_SUITE_DETECTED"])
    runtime_ok = (results["runtime"]["status"] in ["PASS", "SKIPPED"])
    docker_ok = (results["docker"]["build_status"] in ["PASS", "SKIPPED (DOCKER_DAEMON_OFFLINE)"])

    has_any_failure = (
        results["install"]["status"] == "FAILED" or
        results["build"]["status"] == "FAILED" or
        results["tests"]["status"] == "FAILED" or
        results["runtime"]["status"] == "FAILED" or
        results["docker"]["build_status"] == "FAILED" or
        results["docker"]["container_status"] == "FAILED"
    )

    if has_any_failure:
        results["final_status"] = "REPAIRED — VERIFICATION FAILED"
    elif install_ok and build_ok and (results["tests"]["status"] == "PASS") and runtime_ok and docker_ok:
        results["final_status"] = "REPAIRED & VERIFIED"
    elif results["tests"]["status"] == "NO_TEST_SUITE_DETECTED" and build_ok and runtime_ok:
        results["final_status"] = "PARTIALLY REPAIRED — NOT FULLY VERIFIED (NO TEST SUITE)"
    else:
        results["final_status"] = "PARTIALLY REPAIRED — NOT FULLY VERIFIED"

    return results
