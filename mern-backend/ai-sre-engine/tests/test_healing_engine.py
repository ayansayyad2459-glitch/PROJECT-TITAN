import os
import sys
import json
import shutil
import tempfile
import unittest

# Add parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from detector import detect_repository
from verifier import verify_repository, run_command_secure
from healeragent import generate_framework_dockerfile, apply_sre_remediations, render_rca_report

class TestHealingEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="titan_test_")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_case_1_working_react_repository_detection(self):
        """Case 1: Working React repository detection and structure preservation."""
        pkg = {
            "name": "working-react-app",
            "version": "0.1.0",
            "dependencies": {
                "react": "^17.0.2",
                "react-dom": "^17.0.2",
                "react-scripts": "4.0.3"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test"
            }
        }
        with open(os.path.join(self.test_dir, "package.json"), "w") as f:
            json.dump(pkg, f)

        src_dir = os.path.join(self.test_dir, "src")
        os.makedirs(src_dir, exist_ok=True)
        with open(os.path.join(src_dir, "App.js"), "w") as f:
            f.write("function App() { return <div>Hello World</div>; }\nexport default App;\n")

        info = detect_repository(self.test_dir)
        self.assertEqual(info["language"], "javascript")
        self.assertEqual(info["framework"], "create_react_app")
        self.assertEqual(info["project_type"], "frontend_spa")
        self.assertEqual(info["runtime"], "browser")
        self.assertEqual(info["deployment_model"], "static_spa_webserver")
        self.assertTrue(info["has_build"])
        self.assertTrue(info["has_test"])
        self.assertTrue(info["open_ssl_legacy_needed"])

        # Remediation on working app should preserve src/App.js without corruption
        remediations = apply_sre_remediations(self.test_dir, info, "Scan working app")
        with open(os.path.join(src_dir, "App.js"), "r") as f:
            app_content = f.read()
        self.assertIn("function App()", app_content)

    def test_case_2_broken_react_repository_repair(self):
        """Case 2: Broken repository detects and repairs syntax / stub errors."""
        pkg = {
            "name": "broken-react-app",
            "dependencies": {
                "react": "17.0.2",
                "react-scripts": "4.0.3"
            },
            "scripts": {
                "build": "react-scripts build"
            }
        }
        with open(os.path.join(self.test_dir, "package.json"), "w") as f:
            json.dump(pkg, f)

        src_dir = os.path.join(self.test_dir, "src")
        os.makedirs(src_dir, exist_ok=True)
        broken_file = os.path.join(src_dir, "api.js")
        with open(broken_file, "w") as f:
            f.write("const client = fakeDatabaseConnection;\nexport default client;\n")

        info = detect_repository(self.test_dir)
        remediations = apply_sre_remediations(self.test_dir, info, "Fix broken syntax/references")

        with open(broken_file, "r") as f:
            repaired_content = f.read()

        self.assertNotIn("fakeDatabaseConnection", repaired_content)
        self.assertIn("null", repaired_content)
        # Verify remediation records before/after diff
        patched_diffs = [r for r in remediations if "api.js" in r["file"]]
        self.assertTrue(len(patched_diffs) > 0)
        self.assertIn("fakeDatabaseConnection", patched_diffs[0]["diff"])

    def test_case_3_invalid_dockerfile_replacement(self):
        """Case 3: Invalid Dockerfile (node src/index.js + || true) is replaced with multi-stage Nginx."""
        pkg = {
            "name": "react-spa",
            "dependencies": {
                "react": "17.0.2",
                "react-scripts": "4.0.3"
            },
            "scripts": {
                "build": "react-scripts build"
            }
        }
        with open(os.path.join(self.test_dir, "package.json"), "w") as f:
            json.dump(pkg, f)

        # Write the user's exact buggy Dockerfile
        invalid_dockerfile = (
            "FROM node:18-alpine\n"
            "WORKDIR /app\n"
            "COPY package*.json ./\n"
            "RUN npm install --production --ignore-scripts || true\n"
            "COPY . .\n"
            "EXPOSE 5000\n"
            "CMD [\"node\", \"src/index.js\"]\n"
        )
        dockerfile_path = os.path.join(self.test_dir, "Dockerfile")
        with open(dockerfile_path, "w") as f:
            f.write(invalid_dockerfile)

        info = detect_repository(self.test_dir)
        remediations = apply_sre_remediations(self.test_dir, info, "Audit Dockerfile")

        with open(dockerfile_path, "r") as f:
            new_dockerfile = f.read()

        # Must NOT contain || true or CMD ["node"
        self.assertNotIn("|| true", new_dockerfile)
        self.assertNotIn('CMD ["node", "src/index.js"]', new_dockerfile)
        # Must contain multi-stage Nginx build for React SPA
        self.assertIn("FROM node:18-alpine AS builder", new_dockerfile)
        self.assertIn("RUN npm run build", new_dockerfile)
        self.assertIn("FROM nginx:alpine", new_dockerfile)
        self.assertIn("/usr/share/nginx/html", new_dockerfile)

        # Remediations must record the diff
        docker_rem = [r for r in remediations if r["file"] == "Dockerfile"]
        self.assertTrue(len(docker_rem) > 0)
        self.assertIn("|| true", docker_rem[0]["diff"])

    def test_case_4_injected_build_failure(self):
        """Case 4: Injected build failure causes final_status to be 'REPAIRED — VERIFICATION FAILED', NEVER 'VERIFIED'."""
        info = {
            "language": "javascript",
            "framework": "create_react_app",
            "project_type": "frontend_spa",
            "has_build": True,
            "build_command": 'node -e "console.error(\'SyntaxError in build\'); process.exit(1)"',
            "build_output_dir": "build",
            "has_test": False,
            "manifest_path": None,
            "open_ssl_legacy_needed": False
        }

        results = verify_repository(self.test_dir, info)
        self.assertEqual(results["build"]["status"], "FAILED")
        self.assertEqual(results["build"]["exit_code"], 1)
        self.assertEqual(results["final_status"], "REPAIRED — VERIFICATION FAILED")
        self.assertNotEqual(results["final_status"], "REPAIRED & VERIFIED")

    def test_case_5_injected_test_failure(self):
        """Case 5: Injected test failure causes final_status to be 'REPAIRED — VERIFICATION FAILED', NEVER 'VERIFIED'."""
        info = {
            "language": "javascript",
            "framework": "create_react_app",
            "project_type": "frontend_spa",
            "has_build": False,
            "has_test": True,
            "test_command": 'node -e "console.error(\'Tests: 1 failed, 2 total\'); process.exit(1)"',
            "manifest_path": None,
            "open_ssl_legacy_needed": False
        }

        results = verify_repository(self.test_dir, info)
        self.assertEqual(results["tests"]["status"], "FAILED")
        self.assertEqual(results["tests"]["exit_code"], 1)
        self.assertEqual(results["tests"]["failed"], 1)
        self.assertEqual(results["final_status"], "REPAIRED — VERIFICATION FAILED")
        self.assertNotEqual(results["final_status"], "REPAIRED & VERIFIED")

    def test_case_6_runtime_crash_failure(self):
        """Case 6: Runtime startup crash / missing build artifacts causes verification failure."""
        info = {
            "language": "javascript",
            "framework": "create_react_app",
            "project_type": "frontend_spa",
            "has_build": False,
            "build_output_dir": "non_existent_build",
            "has_test": False,
            "manifest_path": None,
            "open_ssl_legacy_needed": False
        }

        results = verify_repository(self.test_dir, info)
        self.assertEqual(results["runtime"]["status"], "FAILED")
        self.assertEqual(results["final_status"], "REPAIRED — VERIFICATION FAILED")
        self.assertNotEqual(results["final_status"], "REPAIRED & VERIFIED")

    def test_case_7_command_failure_without_failure_suppression(self):
        """Case 7: Command failure returns exact non-zero exit code without any '|| true' masking."""
        res = run_command_secure('node -e "process.exit(42)"', self.test_dir)
        self.assertEqual(res["exit_code"], 42)
        self.assertFalse(res["timed_out"])
        self.assertNotIn("|| true", res["command"])

    def test_case_8_repo_with_no_tests(self):
        """Case 8: Repo with no tests accurately reports 'NO_TEST_SUITE_DETECTED' and NEVER claims tests passed."""
        pkg = {
            "name": "untested-app",
            "dependencies": {}
            # No scripts, no test runner
        }
        with open(os.path.join(self.test_dir, "package.json"), "w") as f:
            json.dump(pkg, f)

        # Create mock build index.html to satisfy build and runtime
        build_dir = os.path.join(self.test_dir, "build")
        os.makedirs(build_dir, exist_ok=True)
        with open(os.path.join(build_dir, "index.html"), "w") as f:
            f.write("<html><body>App</body></html>")

        info = detect_repository(self.test_dir)
        self.assertFalse(info["has_test"])
        self.assertEqual(info["test_framework"], "none")

        # Set mock passing build
        info["has_build"] = True
        info["build_command"] = 'node -e "process.exit(0)"'
        info["build_output_dir"] = "build"

        results = verify_repository(self.test_dir, info)
        self.assertEqual(results["tests"]["status"], "NO_TEST_SUITE_DETECTED")
        self.assertEqual(results["final_status"], "PARTIALLY REPAIRED — NOT FULLY VERIFIED (NO TEST SUITE)")
        self.assertNotEqual(results["final_status"], "REPAIRED & VERIFIED")

    def test_report_generation_honesty(self):
        """Case 9: Report contains exact status, diffs, metrics, and bans false positives."""
        info = {
            "language": "javascript",
            "framework": "create_react_app",
            "project_type": "frontend_spa",
            "runtime": "browser",
            "package_manager": "npm",
            "deployment_model": "static_spa_webserver",
            "entrypoint": "src/index.js",
            "details": "Deterministic scan"
        }
        remediations = [{
            "file": "Dockerfile",
            "issue": "Invalid Dockerfile with || true",
            "old_behavior": "Suppressed errors",
            "new_behavior": "Multi-stage Nginx",
            "reason": "Production SPA standards",
            "diff": "- RUN npm install || true\n+ RUN npm run build"
        }]
        ver_results = {
            "repo_path": self.test_dir,
            "final_status": "REPAIRED — VERIFICATION FAILED",
            "install": {"command": "npm install", "exit_code": 0, "status": "PASS", "duration_ms": 1200},
            "build": {"command": "npm run build", "exit_code": 1, "status": "FAILED", "output_verified": False, "duration_ms": 3000, "stdout": "", "stderr": "Build failed"},
            "tests": {"command": "npm test", "exit_code": 0, "status": "PASS", "passed": 5, "failed": 0, "skipped": 0, "stdout": "Tests: 5 passed, 5 total", "stderr": ""},
            "runtime": {"command": "SPA Static Probe", "status": "SKIPPED", "http_status": None, "details": "Build failed"},
            "docker": {"build_status": "SKIPPED (DOCKER_DAEMON_OFFLINE)", "container_status": "SKIPPED", "exit_code": 0, "details": "Daemon offline"}
        }

        report = render_rca_report(info, remediations, ver_results, "Trigger scan")
        self.assertIn("REPAIRED — VERIFICATION FAILED", report)
        self.assertIn("🔴", report)
        self.assertIn("- RUN npm install || true", report)
        self.assertIn("SKIPPED (DOCKER_DAEMON_OFFLINE)", report)
        self.assertNotIn("🟢 TITAN Autonomous SRE Remediation & Verification Report", report)

    def test_case_10_compiler_diagnostics_parsing(self):
        """Case 10: Compiler and test diagnostics correctly parse ESLint warnings and Jest missing modules."""
        from compiler_diagnostics import parse_build_output, parse_test_output

        build_stdout = """
Failed to compile.

src/App.js
  Line 1:8:  'logo' is defined but never used  no-unused-vars
  Line 4:10:  'Switch' is defined but never used  no-unused-vars
"""
        diags = parse_build_output(build_stdout, "", self.test_dir)
        self.assertEqual(len(diags), 2)
        self.assertEqual(diags[0].symbol, "logo")
        self.assertEqual(diags[0].rule, "no-unused-vars")
        self.assertEqual(diags[0].line, 1)
        self.assertEqual(diags[1].symbol, "Switch")

        test_stderr = "Cannot find module 'zustand' from 'src/app/zustandStore.js'"
        t_diags = parse_test_output("", test_stderr, self.test_dir)
        self.assertEqual(len(t_diags), 1)
        self.assertEqual(t_diags[0].symbol, "zustand")
        self.assertEqual(t_diags[0].rule, "missing-module")

    def test_case_11_unused_import_removal_safety(self):
        """Case 11: Unused import removal safely removes 0-usage import and guards used symbols."""
        from patch_engine import remove_unused_import

        # Test A: Genuinely unused import
        app_js = os.path.join(self.test_dir, "App.js")
        with open(app_js, "w", encoding="utf-8") as f:
            f.write("import logo from './logo.svg';\nimport React from 'react';\nfunction App() { return <div>App</div>; }\nexport default App;\n")

        res = remove_unused_import(self.test_dir, "App.js", "logo", 1)
        self.assertTrue(res["applied"])
        self.assertEqual(res["confidence"], "HIGH")

        with open(app_js, "r", encoding="utf-8") as f:
            updated = f.read()
        self.assertNotIn("logo", updated)
        self.assertIn("function App()", updated)

        # Test B: Symbol that IS used in file body (SAFETY GUARD: must NOT remove)
        with open(app_js, "w", encoding="utf-8") as f:
            f.write("import Header from './Header';\nfunction App() { return <Header />; }\nexport default App;\n")

        guard_res = remove_unused_import(self.test_dir, "App.js", "Header", 1)
        self.assertFalse(guard_res["applied"])
        self.assertIn("UNSAFE TO AUTOFIX", guard_res["reason"])

    def test_case_12_relative_import_resolution(self):
        """Case 12: Broken relative import is resolved to correct relative path in src."""
        from patch_engine import resolve_broken_relative_import

        src_dir = os.path.join(self.test_dir, "src")
        components_dir = os.path.join(src_dir, "components")
        features_dir = os.path.join(src_dir, "features", "counter")
        os.makedirs(components_dir, exist_ok=True)
        os.makedirs(features_dir, exist_ok=True)

        # Create target slice
        with open(os.path.join(features_dir, "counterSlice.js"), "w", encoding="utf-8") as f:
            f.write("export const counterSlice = {};\n")

        # Create component with broken import
        comp_file = os.path.join(components_dir, "ReduxCounter.js")
        with open(comp_file, "w", encoding="utf-8") as f:
            f.write("import React from 'react';\nimport { counterSlice } from './counterSlice';\n")

        res = resolve_broken_relative_import(self.test_dir, "src/components/ReduxCounter.js", "./counterSlice")
        self.assertTrue(res["applied"])

        with open(comp_file, "r", encoding="utf-8") as f:
            updated = f.read()
        self.assertIn("../features/counter/counterSlice", updated)

    def test_case_13_autonomous_healer_bounded_loop(self):
        """Case 13: AutonomousHealer executes bounded loop and records iterations."""
        from autonomous_healer import AutonomousHealer

        pkg = {"name": "test-loop-app", "dependencies": {}}
        with open(os.path.join(self.test_dir, "package.json"), "w") as f:
            json.dump(pkg, f)

        # Mock build command that fails first with an unused var, then passes after file edit
        src_dir = os.path.join(self.test_dir, "src")
        os.makedirs(src_dir, exist_ok=True)
        file_path = os.path.join(src_dir, "index.js")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("import unusedVal from './unusedVal';\nconsole.log('Main');\n")

        info = {
            "language": "javascript",
            "framework": "create_react_app",
            "project_type": "frontend_spa",
            "has_build": True,
            # Node build script that checks if 'unusedVal' is in src/index.js
            "build_command": f'node -e "const fs = require(\'fs\'); if (fs.readFileSync(\'src/index.js\', \'utf8\').includes(\'unusedVal\')) {{ console.error(\'src/index.js\\n  Line 1:8:  \\\'unusedVal\\\' is defined but never used  no-unused-vars\'); process.exit(1); }} else {{ process.exit(0); }}"',
            "build_output_dir": "build",
            "has_test": False,
            "manifest_path": "package.json",
            "package_manager_flags": [],
            "open_ssl_legacy_needed": False
        }

        # Create dummy build output dir to satisfy runtime check
        os.makedirs(os.path.join(self.test_dir, "build"), exist_ok=True)
        with open(os.path.join(self.test_dir, "build", "index.html"), "w") as f:
            f.write("<html><body>Ready</body></html>")

        healer = AutonomousHealer(self.test_dir, info, max_attempts=3)
        results = healer.execute_healing_loop()

        self.assertTrue(len(results["iterations"]) >= 2)
        # Verify first attempt was FAILED
        self.assertEqual(results["iterations"][0]["status"], "FAILED")
        # Verify second attempt was PASS
        self.assertEqual(results["iterations"][1]["status"], "PASS")
        # Verify file was healed
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("unusedVal", content)

if __name__ == "__main__":
    unittest.main()
