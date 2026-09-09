import os
import re
import json
import difflib
from typing import Dict, Any, Optional, List
from verifier import run_command_secure

def remove_unused_import(repo_path: str, file_rel_path: str, symbol: str, line_hint: Optional[int] = None) -> Dict[str, Any]:
    """
    Surgically removes an unused import from a JS/TS source file.
    CRITICAL SAFETY GUARD: Verifies that the symbol has 0 references in the file body.
    """
    abs_file = os.path.normpath(os.path.join(repo_path, file_rel_path))
    if not os.path.exists(abs_file):
        return {"applied": False, "reason": f"File '{file_rel_path}' does not exist on disk"}

    try:
        with open(abs_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return {"applied": False, "reason": f"Could not read file: {str(e)}"}

    original_content = "".join(lines)
    symbol_word_regex = re.compile(r'\b' + re.escape(symbol) + r'\b')

    # Step 1: Identify all import lines vs body lines
    import_line_indices = set()
    in_multi_import = False

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('import{') or in_multi_import:
            import_line_indices.add(idx)
            if ';' in stripped or ("from" in stripped and not stripped.endswith(',')):
                in_multi_import = False
            elif '{' in stripped and '}' not in stripped:
                in_multi_import = True
        elif 'require(' in stripped:
            import_line_indices.add(idx)

    # Step 2: Safety Check - count occurrences outside import statements
    body_usages = 0
    for idx, line in enumerate(lines):
        if idx not in import_line_indices:
            # Strip comments
            code_only = re.sub(r'//.*$', '', line)
            matches = symbol_word_regex.findall(code_only)
            body_usages += len(matches)

    if body_usages > 0:
        return {
            "applied": False,
            "reason": f"UNSAFE TO AUTOFIX: Symbol '{symbol}' is referenced {body_usages} time(s) in {file_rel_path} body"
        }

    # Step 3: Locate the import line that introduces this symbol
    target_idx = None
    if line_hint and 1 <= line_hint <= len(lines):
        # Check around line_hint first
        hint_idx = line_hint - 1
        for offset in [0, 1, -1, 2, -2]:
            cand = hint_idx + offset
            if 0 <= cand < len(lines) and cand in import_line_indices and symbol_word_regex.search(lines[cand]):
                target_idx = cand
                break

    if target_idx is None:
        for idx in sorted(import_line_indices):
            if symbol_word_regex.search(lines[idx]):
                target_idx = idx
                break

    if target_idx is None:
        return {
            "applied": False,
            "reason": f"Could not locate import statement for '{symbol}' in {file_rel_path}"
        }

    target_line = lines[target_idx]
    modified_line = None
    deleted_entire_line = False

    # Case A: Default import: "import logo from './logo.svg';"
    default_import_match = re.match(r'^(\s*import\s+)' + re.escape(symbol) + r'(\s+from\s+[\'"][^\'"]+[\'"];?\s*)$', target_line)
    if default_import_match:
        deleted_entire_line = True

    # Case B: Named import sole item: "import { TodoList } from './TodoList';"
    elif re.match(r'^\s*import\s*\{\s*' + re.escape(symbol) + r'\s*\}\s*from\s+[\'"][^\'"]+[\'"];?\s*$', target_line):
        deleted_entire_line = True

    # Case C: Named import with multiple items: "import { a, TodoList, b } from '...';"
    elif '{' in target_line and '}' in target_line:
        # Pattern 1: symbol with trailing comma: "TodoList,\s*"
        subbed = re.sub(r'\b' + re.escape(symbol) + r'\b\s*,\s*', '', target_line)
        if subbed == target_line:
            # Pattern 2: symbol with leading comma: ",\s*TodoList"
            subbed = re.sub(r',\s*\b' + re.escape(symbol) + r'\b', '', target_line)
        if subbed != target_line:
            modified_line = subbed
        else:
            deleted_entire_line = True
    else:
        # Fallback: if symbol alone is imported
        deleted_entire_line = True

    new_lines = list(lines)
    if deleted_entire_line:
        new_lines.pop(target_idx)
    elif modified_line is not None:
        new_lines[target_idx] = modified_line

    new_content = "".join(new_lines)
    if new_content == original_content:
        return {"applied": False, "reason": "No changes generated"}

    # Write file safely
    try:
        with open(abs_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        return {"applied": False, "reason": f"Failed to write patch: {str(e)}"}

    diff = "".join(difflib.unified_diff(
        original_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{file_rel_path}",
        tofile=f"b/{file_rel_path}"
    ))

    return {
        "applied": True,
        "file": file_rel_path,
        "line": target_idx + 1,
        "rule": "no-unused-vars",
        "symbol": symbol,
        "reason": f"Removed unused import '{symbol}' after verifying 0 references in {file_rel_path}",
        "old_code": target_line.strip(),
        "new_code": modified_line.strip() if modified_line else "(line removed)",
        "confidence": "HIGH",
        "diff": diff
    }

def resolve_broken_relative_import(repo_path: str, file_rel_path: str, broken_module: str) -> Dict[str, Any]:
    """
    Finds where a broken relative import lives in the repository and updates the import path.
    Example: from './counterSlice' in 'src/components/ReduxCounter.js' -> '../features/counter/counterSlice'
    """
    abs_importing_file = os.path.normpath(os.path.join(repo_path, file_rel_path))
    if not os.path.exists(abs_importing_file):
        return {"applied": False, "reason": f"File '{file_rel_path}' does not exist"}

    target_base = os.path.basename(broken_module)
    clean_target_name = re.sub(r'\.(js|jsx|ts|tsx)$', '', target_base)

    # Search repo for clean_target_name.(js|jsx|ts|tsx)
    matching_paths = []
    src_dir = os.path.join(repo_path, "src")
    search_root = src_dir if os.path.exists(src_dir) else repo_path

    for root, dirs, files in os.walk(search_root):
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'build', 'dist', '__pycache__']]
        for f in files:
            f_name_without_ext = os.path.splitext(f)[0]
            if f_name_without_ext == clean_target_name and f.endswith(('.js', '.jsx', '.ts', '.tsx')):
                matching_paths.append(os.path.join(root, f))

    if len(matching_paths) != 1:
        return {
            "applied": False,
            "reason": f"UNSAFE TO AUTOFIX: Found {len(matching_paths)} matches for module '{clean_target_name}'"
        }

    target_full_path = matching_paths[0]
    importing_dir = os.path.dirname(abs_importing_file)

    # Compute relative path
    rel_path_to_target = os.path.relpath(target_full_path, importing_dir).replace('\\', '/')
    # Remove file extension for module import
    rel_path_no_ext = re.sub(r'\.(js|jsx|ts|tsx)$', '', rel_path_to_target)
    if not rel_path_no_ext.startswith('.'):
        rel_path_no_ext = f"./{rel_path_no_ext}"

    # Read importing file
    try:
        with open(abs_importing_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"applied": False, "reason": str(e)}

    # Replace import
    # Look for quotes around broken_module: e.g. from "./counterSlice" or from './counterSlice'
    pattern = re.compile(r'([\'"])' + re.escape(broken_module) + r'([\'"])')
    new_content, count = pattern.subn(r'\1' + rel_path_no_ext + r'\2', content)

    if count == 0 or new_content == content:
        return {"applied": False, "reason": f"Could not find exact import string '{broken_module}' in {file_rel_path}"}

    try:
        with open(abs_importing_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        return {"applied": False, "reason": f"Failed to write patch: {str(e)}"}

    diff = "".join(difflib.unified_diff(
        content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{file_rel_path}",
        tofile=f"b/{file_rel_path}"
    ))

    return {
        "applied": True,
        "file": file_rel_path,
        "line": 0,
        "rule": "unresolved-relative-import",
        "symbol": broken_module,
        "reason": f"Resolved relative import '{broken_module}' to '{rel_path_no_ext}'",
        "old_code": broken_module,
        "new_code": rel_path_no_ext,
        "confidence": "HIGH",
        "diff": diff
    }

def install_missing_npm_dependency(repo_path: str, pkg_name: str) -> Dict[str, Any]:
    """
    Safely installs a missing npm dependency into package.json.
    """
    if pkg_name.startswith('.') or pkg_name.startswith('/') or pkg_name.startswith('@') and '/' not in pkg_name:
        return {"applied": False, "reason": f"'{pkg_name}' is not a valid npm package name"}

    pkg_json_path = os.path.join(repo_path, "package.json")
    if not os.path.exists(pkg_json_path):
        return {"applied": False, "reason": "package.json not found in repository"}

    try:
        with open(pkg_json_path, 'r', encoding='utf-8') as f:
            pkg_data = json.load(f)
    except Exception as e:
        return {"applied": False, "reason": f"Could not parse package.json: {str(e)}"}

    deps = pkg_data.get("dependencies", {})
    pkg_target = pkg_name
    react_v = deps.get("react", "")
    if "17." in react_v or react_v.startswith("^17") or react_v.startswith("~17"):
        if pkg_name == "zustand":
            pkg_target = "zustand@3"
        elif pkg_name == "react-redux":
            pkg_target = "react-redux@8"

    cmd = f"npm install {pkg_target} --legacy-peer-deps"

    print(f"[PATCH ENGINE] 📦 Installing/aligning dependency: {cmd}", flush=True)
    res = run_command_secure(cmd, repo_path, timeout_sec=180)

    if res["exit_code"] != 0:
        return {
            "applied": False,
            "reason": f"Failed to install package '{pkg_name}' (exit code {res['exit_code']}): {res['stderr'][:200]}"
        }

    return {
        "applied": True,
        "file": "package.json",
        "line": 0,
        "rule": "missing-module",
        "symbol": pkg_name,
        "reason": f"Installed missing dependency '{pkg_name}' into package.json",
        "old_code": "Missing dependency",
        "new_code": f"\"dependencies\": {{ ... \"{pkg_name}\": \"...\" }}",
        "confidence": "HIGH",
        "diff": f"+ \"{pkg_name}\": \"latest\""
    }

def patch_missing_store_export(repo_path: str, test_file_rel_path: str, missing_symbol: str = "createStore") -> Dict[str, Any]:
    """
    Patches test-supporting store export stubs (e.g. createStore factory function for Redux Toolkit store).
    """
    if missing_symbol != "createStore":
        return {"applied": False, "reason": f"UNSAFE TO AUTOFIX: Unknown missing export '{missing_symbol}'"}

    # Search for store.js in src/app or src/
    candidate_files = [
        os.path.join(repo_path, "src", "app", "store.js"),
        os.path.join(repo_path, "src", "store.js"),
        os.path.join(repo_path, "src", "app", "store.ts")
    ]
    store_file = None
    for cand in candidate_files:
        if os.path.exists(cand):
            store_file = cand
            break

    if not store_file:
        return {"applied": False, "reason": "Could not locate store.js"}

    rel_store_path = os.path.relpath(store_file, repo_path).replace('\\', '/')

    try:
        with open(store_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"applied": False, "reason": str(e)}

    if "createStore" in content:
        return {"applied": False, "reason": "createStore already defined in store.js"}

    # Locate configureStore call
    cs_idx = content.find("configureStore(")
    if cs_idx == -1:
        return {"applied": False, "reason": "UNSAFE TO AUTOFIX: Could not find configureStore call in store.js"}

    # Extract balanced configureStore(...) call
    open_paren = cs_idx + len("configureStore")
    depth = 0
    end_paren = -1
    for i in range(open_paren, len(content)):
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
            if depth == 0:
                end_paren = i
                break

    if end_paren == -1:
        return {"applied": False, "reason": "UNSAFE TO AUTOFIX: Malformed configureStore call in store.js"}

    config_expr = content[cs_idx:end_paren + 1]
    new_export = f"\n// TITAN AUTO-HEAL: Isolated store factory for unit tests\nexport const createStore = () => {config_expr};\n"

    new_content = content + new_export

    try:
        with open(store_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        return {"applied": False, "reason": f"Failed to write patch to {rel_store_path}: {str(e)}"}

    diff = "".join(difflib.unified_diff(
        content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{rel_store_path}",
        tofile=f"b/{rel_store_path}"
    ))

    return {
        "applied": True,
        "file": rel_store_path,
        "line": len(content.splitlines()),
        "rule": "missing-export",
        "symbol": "createStore",
        "reason": "Exported isolated createStore factory function for unit testing",
        "old_code": "No createStore export",
        "new_code": "export const createStore = () => configureStore(...)",
        "confidence": "HIGH",
        "diff": diff
    }
