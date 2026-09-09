import os
import re
from typing import List, Dict, Any, Optional

class Diagnostic:
    def __init__(
        self,
        category: str,       # 'BUILD_LINT', 'BUILD_COMPILER', 'TEST_MODULE', 'TEST_RUNTIME', 'UNKNOWN'
        rule: str,           # 'no-unused-vars', 'missing-module', 'unresolved-relative-import', 'missing-export', etc.
        file_path: str,      # relative path to file
        line: Optional[int] = None,
        col: Optional[int] = None,
        symbol: Optional[str] = None,
        message: str = "",
        raw_snippet: str = ""
    ):
        self.category = category
        self.rule = rule
        self.file_path = file_path.replace('\\', '/')
        self.line = line
        self.col = col
        self.symbol = symbol
        self.message = message
        self.raw_snippet = raw_snippet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "rule": self.rule,
            "file_path": self.file_path,
            "line": self.line,
            "col": self.col,
            "symbol": self.symbol,
            "message": self.message,
            "raw_snippet": self.raw_snippet
        }

    def __repr__(self):
        return f"<Diagnostic {self.rule} in {self.file_path}:{self.line} symbol='{self.symbol}'>"

def parse_build_output(stdout: str, stderr: str, repo_path: str) -> List[Diagnostic]:
    """
    Parses compiler and linter output (ESLint, Webpack, TSC) into structured Diagnostic objects.
    """
    combined = f"{stdout}\n{stderr}"
    diagnostics: List[Diagnostic] = []
    seen = set()

    # 1. ESLint no-unused-vars in CRA / Webpack
    # Format:
    # src\App.js
    #   Line 1:8:   'logo' is defined but never used      no-unused-vars
    #   Line 4:10:  'Switch' is defined but never used    no-unused-vars
    current_file = None
    for line in combined.splitlines():
        trimmed = line.strip()
        # Check if line looks like a file path ending in .js/.jsx/.ts/.tsx
        if re.match(r'^(?:\./|[a-zA-Z0-9_\-\\/.]+)\.(?:js|jsx|ts|tsx)$', trimmed):
            current_file = trimmed.replace('\\', '/')
            continue

        # Check if line is "Line X:Y: 'symbol' is defined but never used no-unused-vars"
        m = re.search(r'Line\s+(\d+)(?::(\d+))?:\s+[\'"]([^\'"]+)[\'"]\s+is defined but never used', trimmed)
        if m and current_file:
            line_num = int(m.group(1))
            col_num = int(m.group(2)) if m.group(2) else None
            symbol = m.group(3)
            key = (current_file, line_num, symbol, 'no-unused-vars')
            if key not in seen:
                seen.add(key)
                diagnostics.append(Diagnostic(
                    category="BUILD_LINT",
                    rule="no-unused-vars",
                    file_path=current_file,
                    line=line_num,
                    col=col_num,
                    symbol=symbol,
                    message=f"'{symbol}' is defined but never used (no-unused-vars)",
                    raw_snippet=trimmed
                ))
    alt_eslint_regex = re.compile(
        r'([^\s:]+\.(?:js|jsx|ts|tsx)):(\d+):(\d+):\s+[\'"]([^\'"]+)[\'"]\s+is defined but never used',
        re.MULTILINE
    )
    for match in alt_eslint_regex.finditer(combined):
        raw_file, line_str, col_str, symbol = match.groups()
        rel_file = raw_file.strip().replace('\\', '/')
        line_num = int(line_str)
        col_num = int(col_str)
        key = (rel_file, line_num, symbol, 'no-unused-vars')
        if key not in seen:
            seen.add(key)
            diagnostics.append(Diagnostic(
                category="BUILD_LINT",
                rule="no-unused-vars",
                file_path=rel_file,
                line=line_num,
                col=col_num,
                symbol=symbol,
                message=f"'{symbol}' is defined but never used",
                raw_snippet=match.group(0).strip()
            ))

    # 2. Webpack / Module resolution errors in build
    # Example: Module not found: Can't resolve './zustandStore' in 'C:\...\src\components'
    webpack_module_regex = re.compile(
        r"Module not found: Can't resolve [\'\"]([^\'\"]+)[\'\"] in [\'\"]([^\'\"]+)[\'\"]",
        re.MULTILINE
    )
    for match in webpack_module_regex.finditer(combined):
        target_mod, in_dir = match.groups()
        rel_dir = os.path.relpath(in_dir, repo_path).replace('\\', '/') if os.path.isabs(in_dir) else in_dir.replace('\\', '/')
        rule = "unresolved-relative-import" if target_mod.startswith('.') else "missing-module"
        key = (rel_dir, target_mod, rule)
        if key not in seen:
            seen.add(key)
            diagnostics.append(Diagnostic(
                category="BUILD_COMPILER",
                rule=rule,
                file_path=rel_dir,
                symbol=target_mod,
                message=f"Can't resolve '{target_mod}' in '{rel_dir}'",
                raw_snippet=match.group(0).strip()
            ))

    return diagnostics

def parse_test_output(stdout: str, stderr: str, repo_path: str) -> List[Diagnostic]:
    """
    Parses Jest / Vitest test failure output into structured Diagnostic objects.
    """
    combined = f"{stdout}\n{stderr}"
    diagnostics: List[Diagnostic] = []
    seen = set()

    # 1. Cannot find module '<mod>' from '<file>'
    # Example: Cannot find module './zustandStore' from 'src/components/ZustandCounter.js'
    # Example: Cannot find module 'zustand' from 'src/app/zustandStore.js'
    cannot_find_regex = re.compile(
        r"Cannot find module [\'\"]([^\'\"]+)[\'\"] from [\'\"]([^\'\"]+)[\'\"]",
        re.MULTILINE
    )
    for match in cannot_find_regex.finditer(combined):
        mod_name, from_file = match.groups()
        rel_file = from_file.strip().replace('\\', '/')
        rule = "unresolved-relative-import" if mod_name.startswith('.') else "missing-module"
        key = (rel_file, mod_name, rule)
        if key not in seen:
            seen.add(key)
            diagnostics.append(Diagnostic(
                category="TEST_MODULE",
                rule=rule,
                file_path=rel_file,
                symbol=mod_name,
                message=f"Cannot find module '{mod_name}' from '{rel_file}'",
                raw_snippet=match.group(0).strip()
            ))

    # 2. Missing export / function stub
    # Example: TypeError: (0 , _store.createStore) is not a function
    # Example: TypeError: _store.createStore is not a function
    missing_fn_regex = re.compile(
        r"TypeError:\s+(?:\(0\s*,\s*)?(?:_([a-zA-Z0-9_$]+)\.)?([a-zA-Z0-9_$]+)(?:\))?\s+is not a function",
        re.MULTILINE
    )
    for match in missing_fn_regex.finditer(combined):
        mod_alias, fn_name = match.groups()
        key = ("test_runtime", fn_name, "missing-export")
        if key not in seen:
            seen.add(key)
            diagnostics.append(Diagnostic(
                category="TEST_RUNTIME",
                rule="missing-export",
                file_path="",  # will be resolved by inspecting test stack
                symbol=fn_name,
                message=f"Exported function '{fn_name}' on module '{mod_alias or 'unknown'}' is not a function or missing",
                raw_snippet=match.group(0).strip()
            ))

    # Also extract failing test file locations for missing exports
    # e.g.: at Object.<anonymous> (src/components/ReduxCounter.test.js:9:33)
    if any(d.rule == "missing-export" for d in diagnostics):
        stack_regex = re.compile(r"at [^\n\r]+\(([^\n\r()]+\.(?:test|spec)\.[a-zA-Z0-9]+):(\d+):(\d+)\)")
        for d in diagnostics:
            if d.rule == "missing-export" and not d.file_path:
                m = stack_regex.search(combined)
                if m:
                    raw_p = m.group(1).strip()
                    if os.path.isabs(raw_p) and repo_path:
                        d.file_path = os.path.relpath(raw_p, repo_path).replace('\\', '/')
                    else:
                        d.file_path = raw_p.replace('\\', '/')
                    d.line = int(m.group(2))

    # 3. React 17 vs React-Redux 9 / Zustand useSyncExternalStore incompatibility
    if "useSyncExternalStore is not a function" in combined:
        if "react-redux" in combined or "useSelector" in combined:
            key = ("package.json", "react-redux", "incompatible-peer-dep")
            if key not in seen:
                seen.add(key)
                diagnostics.append(Diagnostic(
                    category="TEST_RUNTIME",
                    rule="incompatible-peer-dep",
                    file_path="package.json",
                    symbol="react-redux",
                    message="react-redux requires useSyncExternalStore (React 18); use react-redux@8 for React 17",
                    raw_snippet="TypeError: useSyncExternalStore is not a function"
                ))
        if "zustand" in combined:
            key = ("package.json", "zustand", "incompatible-peer-dep")
            if key not in seen:
                seen.add(key)
                diagnostics.append(Diagnostic(
                    category="TEST_RUNTIME",
                    rule="incompatible-peer-dep",
                    file_path="package.json",
                    symbol="zustand",
                    message="zustand requires useSyncExternalStore (React 18); use zustand@3 for React 17",
                    raw_snippet="TypeError: useSyncExternalStore is not a function"
                ))

    return diagnostics
