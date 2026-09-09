import os
import sys
import time
from typing import Dict, Any, List, Optional

from verifier import run_command_secure, verify_repository
from compiler_diagnostics import parse_build_output, parse_test_output, Diagnostic
from patch_engine import (
    remove_unused_import,
    resolve_broken_relative_import,
    install_missing_npm_dependency,
    patch_missing_store_export
)

class AutonomousHealer:
    def __init__(self, repo_path: str, repo_info: Dict[str, Any], max_attempts: int = 5):
        self.repo_path = repo_path
        self.repo_info = repo_info
        self.max_attempts = max_attempts
        self.iterations: List[Dict[str, Any]] = []
        self.applied_patches: List[Dict[str, Any]] = []
        self.file_backups: Dict[str, str] = {}

    def backup_file(self, rel_path: str):
        """Creates a snapshot of file content before patching."""
        abs_p = os.path.normpath(os.path.join(self.repo_path, rel_path))
        if os.path.exists(abs_p) and rel_path not in self.file_backups:
            try:
                with open(abs_p, 'r', encoding='utf-8') as f:
                    self.file_backups[rel_path] = f.read()
            except Exception:
                pass

    def rollback_file(self, rel_path: str):
        """Rolls back a file to its snapshot if regression is detected."""
        if rel_path in self.file_backups:
            abs_p = os.path.normpath(os.path.join(self.repo_path, rel_path))
            try:
                with open(abs_p, 'w', encoding='utf-8') as f:
                    f.write(self.file_backups[rel_path])
                print(f"[HEALER LOOP] ⚠️ Rolled back regression in {rel_path}", flush=True)
            except Exception:
                pass

    def execute_healing_loop(self) -> Dict[str, Any]:
        """
        Executes bounded iterative healing:
        Diagnose -> Patch -> Verify -> Analyze -> Re-patch -> Re-verify
        """
        print(f"\n[AUTONOMOUS HEALER] 🔄 Starting bounded healing loop (MAX_ATTEMPTS = {self.max_attempts})...", flush=True)

        env_overrides = {}
        if self.repo_info.get("open_ssl_legacy_needed"):
            env_overrides["NODE_OPTIONS"] = "--openssl-legacy-provider"

        # 0. Initial dependency install check
        install_cmd = f"npm install {' '.join(self.repo_info.get('package_manager_flags', []))}".strip()
        print(f"[HEALER LOOP] 📦 Verifying base dependencies: {install_cmd}", flush=True)
        i_res = run_command_secure(install_cmd, self.repo_path, env_overrides, timeout_sec=240)
        if i_res["exit_code"] != 0 and "--legacy-peer-deps" not in install_cmd:
            retry_cmd = "npm install --legacy-peer-deps"
            i_res = run_command_secure(retry_cmd, self.repo_path, env_overrides, timeout_sec=240)

        attempt = 1
        healing_finished = False

        while attempt <= self.max_attempts and not healing_finished:
            print(f"\n--- [HEALER ITERATION {attempt}/{self.max_attempts}] ---", flush=True)
            iter_record = {
                "attempt": attempt,
                "phase": "BUILD",
                "status": "UNKNOWN",
                "command": "",
                "exit_code": 0,
                "issues": [],
                "patches": [],
                "details": ""
            }

            # --- STEP A: BUILD VERIFICATION ---
            build_cmd = self.repo_info.get("build_command") or "npm run build"
            iter_record["command"] = build_cmd
            print(f"[HEALER LOOP] 🏗️ Executing build gate: {build_cmd}", flush=True)

            b_res = run_command_secure(build_cmd, self.repo_path, env_overrides, timeout_sec=180)
            iter_record["exit_code"] = b_res["exit_code"]

            if b_res["exit_code"] != 0:
                iter_record["phase"] = "BUILD"
                iter_record["status"] = "FAILED"
                print(f"[HEALER LOOP] ❌ Build failed with exit code {b_res['exit_code']}. Analyzing diagnostics...", flush=True)

                diagnostics = parse_build_output(b_res["stdout"], b_res["stderr"], self.repo_path)
                iter_record["issues"] = [d.to_dict() for d in diagnostics]

                if not diagnostics:
                    iter_record["details"] = "UNSAFE TO AUTOFIX: Unrecognized compiler failure without structured diagnostic"
                    self.iterations.append(iter_record)
                    print(f"[HEALER LOOP] 🛑 {iter_record['details']}", flush=True)
                    break

                patches_in_this_step = []
                for diag in diagnostics:
                    print(f"[HEALER LOOP] 🔍 Diagnosed {diag.rule} in {diag.file_path}: {diag.message}", flush=True)
                    self.backup_file(diag.file_path)

                    if diag.rule == "no-unused-vars" and diag.symbol:
                        p_res = remove_unused_import(self.repo_path, diag.file_path, diag.symbol, diag.line)
                        if p_res.get("applied"):
                            patches_in_this_step.append(p_res)
                            self.applied_patches.append(p_res)
                            print(f"[HEALER LOOP] 🩹 Applied patch: {p_res['reason']}", flush=True)
                        else:
                            print(f"[HEALER LOOP] ⚠️ Patch skipped: {p_res.get('reason')}", flush=True)

                    elif diag.rule == "unresolved-relative-import" and diag.symbol:
                        p_res = resolve_broken_relative_import(self.repo_path, diag.file_path, diag.symbol)
                        if p_res.get("applied"):
                            patches_in_this_step.append(p_res)
                            self.applied_patches.append(p_res)
                            print(f"[HEALER LOOP] 🩹 Applied patch: {p_res['reason']}", flush=True)

                    elif diag.rule == "missing-module" and diag.symbol:
                        p_res = install_missing_npm_dependency(self.repo_path, diag.symbol)
                        if p_res.get("applied"):
                            patches_in_this_step.append(p_res)
                            self.applied_patches.append(p_res)
                            print(f"[HEALER LOOP] 🩹 Applied patch: {p_res['reason']}", flush=True)

                iter_record["patches"] = patches_in_this_step

                if not patches_in_this_step:
                    iter_record["details"] = "UNSAFE TO AUTOFIX: No high-confidence patches available for remaining build issues"
                    self.iterations.append(iter_record)
                    print(f"[HEALER LOOP] 🛑 {iter_record['details']}", flush=True)
                    break

                iter_record["details"] = f"Applied {len(patches_in_this_step)} patch(es). Advancing to next re-verification attempt."
                self.iterations.append(iter_record)
                attempt += 1
                continue

            # Build Passed!
            iter_record["phase"] = "BUILD"
            iter_record["status"] = "PASS"
            iter_record["details"] = "Build completed cleanly with 0 errors."
            print(f"[HEALER LOOP] ✅ Build passed cleanly (Exit 0)!", flush=True)

            # --- STEP B: TEST VERIFICATION ---
            if not self.repo_info.get("has_test"):
                iter_record["details"] += " (No test suite detected in repository)."
                self.iterations.append(iter_record)
                healing_finished = True
                break

            test_cmd = self.repo_info.get("test_command") or "npm test -- --watchAll=false"
            iter_record_test = {
                "attempt": attempt,
                "phase": "TESTS",
                "status": "UNKNOWN",
                "command": test_cmd,
                "exit_code": 0,
                "issues": [],
                "patches": [],
                "details": ""
            }
            print(f"[HEALER LOOP] 🧪 Executing test gate: {test_cmd}", flush=True)

            t_res = run_command_secure(test_cmd, self.repo_path, env_overrides, timeout_sec=180)
            iter_record_test["exit_code"] = t_res["exit_code"]

            if t_res["exit_code"] == 0 and "FAIL " not in t_res["stdout"] and "FAIL " not in t_res["stderr"]:
                iter_record_test["status"] = "PASS"
                iter_record_test["details"] = "All test suites passed cleanly."
                print(f"[HEALER LOOP] ✅ Test suite passed cleanly (Exit 0)!", flush=True)
                self.iterations.append(iter_record)
                self.iterations.append(iter_record_test)
                healing_finished = True
                break

            # Tests Failed
            iter_record_test["status"] = "FAILED"
            print(f"[HEALER LOOP] ❌ Tests failed with exit code {t_res['exit_code']}. Analyzing test diagnostics...", flush=True)

            t_diags = parse_test_output(t_res["stdout"], t_res["stderr"], self.repo_path)
            iter_record_test["issues"] = [d.to_dict() for d in t_diags]

            if not t_diags:
                iter_record_test["details"] = "UNSAFE TO AUTOFIX: Unrecognized test failure without deterministic diagnostic"
                self.iterations.append(iter_record)
                self.iterations.append(iter_record_test)
                print(f"[HEALER LOOP] 🛑 {iter_record_test['details']}", flush=True)
                break

            t_patches = []
            for diag in t_diags:
                print(f"[HEALER LOOP] 🔍 Diagnosed test issue: {diag.rule} in {diag.file_path}: {diag.message}", flush=True)
                if diag.file_path:
                    self.backup_file(diag.file_path)

                if diag.rule == "unresolved-relative-import" and diag.symbol:
                    p_res = resolve_broken_relative_import(self.repo_path, diag.file_path, diag.symbol)
                    if p_res.get("applied"):
                        t_patches.append(p_res)
                        self.applied_patches.append(p_res)
                        print(f"[HEALER LOOP] 🩹 Applied patch: {p_res['reason']}", flush=True)

                elif diag.rule in ["missing-module", "incompatible-peer-dep"] and diag.symbol:
                    p_res = install_missing_npm_dependency(self.repo_path, diag.symbol)
                    if p_res.get("applied"):
                        t_patches.append(p_res)
                        self.applied_patches.append(p_res)
                        print(f"[HEALER LOOP] 🩹 Applied patch: {p_res['reason']}", flush=True)

                elif diag.rule == "missing-export" and diag.symbol:
                    p_res = patch_missing_store_export(self.repo_path, diag.file_path, diag.symbol)
                    if p_res.get("applied"):
                        t_patches.append(p_res)
                        self.applied_patches.append(p_res)
                        print(f"[HEALER LOOP] 🩹 Applied patch: {p_res['reason']}", flush=True)

            iter_record_test["patches"] = t_patches
            self.iterations.append(iter_record)
            self.iterations.append(iter_record_test)

            if not t_patches:
                iter_record_test["details"] = "UNSAFE TO AUTOFIX: No high-confidence safe patches for test failures"
                print(f"[HEALER LOOP] 🛑 {iter_record_test['details']}", flush=True)
                break

            iter_record_test["details"] = f"Applied {len(t_patches)} test patch(es). Advancing to next re-verification attempt."
            attempt += 1

        # --- STEP C: FINAL DETERMINISTIC AUDIT ---
        print(f"\n[AUTONOMOUS HEALER] ⚡ Executing Final Deterministic Verification Pipeline...", flush=True)
        final_verification = verify_repository(self.repo_path, self.repo_info)

        return {
            "iterations": self.iterations,
            "applied_patches": self.applied_patches,
            "verification_results": final_verification
        }
