import os
import json
import re
from typing import Dict, Any, List

def detect_repository(repo_path: str) -> Dict[str, Any]:
    """
    Deterministically detects repository architecture, language, framework,
    project type, build system, test runner, package manager, and deployment model.
    """
    info = {
        "language": "unknown",
        "framework": "unknown",
        "project_type": "unknown",
        "runtime": "unknown",
        "package_manager": "unknown",
        "package_manager_flags": [],
        "entrypoint": None,
        "has_build": False,
        "build_command": None,
        "build_output_dir": None,
        "has_test": False,
        "test_framework": "none",
        "test_command": None,
        "deployment_model": "unknown",
        "open_ssl_legacy_needed": False,
        "manifest_path": None,
        "files_count": 0,
        "details": ""
    }

    if not os.path.exists(repo_path):
        info["details"] = "Target workspace does not exist."
        return info

    all_rel_files: List[str] = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'venv', '__pycache__', '.vscode', '.idea', 'dist', 'build']]
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), repo_path).replace('\\', '/')
            all_rel_files.append(rel)

    info["files_count"] = len(all_rel_files)

    # 1. Inspect Node / JS / TS ecosystem
    package_json_path = os.path.join(repo_path, 'package.json')
    if os.path.exists(package_json_path):
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                pkg = json.load(f)
        except Exception:
            pkg = {}

        info["manifest_path"] = "package.json"
        is_ts = any(f.endswith(('.ts', '.tsx')) for f in all_rel_files)
        info["language"] = "typescript" if is_ts else "javascript"

        # Detect package manager
        if os.path.exists(os.path.join(repo_path, 'yarn.lock')):
            info["package_manager"] = "yarn"
        elif os.path.exists(os.path.join(repo_path, 'pnpm-lock.yaml')):
            info["package_manager"] = "pnpm"
        elif os.path.exists(os.path.join(repo_path, 'bun.lockb')):
            info["package_manager"] = "bun"
        else:
            info["package_manager"] = "npm"

        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        scripts = pkg.get("scripts", {})

        # Check for peer dependency conflict risk (e.g. react 17 with react-redux 9)
        react_ver = deps.get("react", "")
        react_redux_ver = deps.get("react-redux", "")
        if react_ver and react_redux_ver:
            if "17." in react_ver and ("9." in react_redux_ver or "^9" in react_redux_ver):
                info["package_manager_flags"].append("--legacy-peer-deps")

        # Create React App detection
        if "react-scripts" in deps:
            info["framework"] = "create_react_app"
            info["project_type"] = "frontend_spa"
            info["runtime"] = "browser"
            info["deployment_model"] = "static_spa_webserver"
            info["build_output_dir"] = "build"
            info["has_build"] = "build" in scripts
            info["build_command"] = "npm run build"
            # react-scripts 4 on Node 17+ requires openssl legacy provider
            rs_version = deps.get("react-scripts", "")
            if re.search(r'[\^~]?[1-4]\.', rs_version):
                info["open_ssl_legacy_needed"] = True

            # Entrypoint
            for candidate in ['src/index.js', 'src/index.tsx', 'src/index.jsx', 'src/App.js', 'src/App.tsx']:
                if candidate in all_rel_files:
                    info["entrypoint"] = candidate
                    break

            if "test" in scripts:
                info["has_test"] = True
                info["test_framework"] = "jest"
                # Non-interactive CI test command for CRA to avoid interactive terminal hang
                info["test_command"] = "npm test -- --watchAll=false"

            info["details"] = "React Single Page Application built with Create React App."
            return info

        # Next.js detection
        elif "next" in deps:
            info["framework"] = "nextjs"
            info["project_type"] = "ssr_app"
            info["runtime"] = "node"
            info["deployment_model"] = "node_server"
            info["build_output_dir"] = ".next"
            info["has_build"] = "build" in scripts
            info["build_command"] = "npm run build"
            info["entrypoint"] = "pages/index.js" if "pages/index.js" in all_rel_files else "app/page.js"
            if "test" in scripts:
                info["has_test"] = True
                info["test_framework"] = "jest" if "jest" in deps else "custom"
                info["test_command"] = "npm test"
            info["details"] = "Next.js Full-Stack / SSR React Application."
            return info

        # Vite React detection
        elif "vite" in deps and ("react" in deps or "@vitejs/plugin-react" in deps):
            info["framework"] = "vite_react"
            info["project_type"] = "frontend_spa"
            info["runtime"] = "browser"
            info["deployment_model"] = "static_spa_webserver"
            info["build_output_dir"] = "dist"
            info["has_build"] = "build" in scripts
            info["build_command"] = "npm run build"
            for candidate in ['src/main.jsx', 'src/main.tsx', 'src/main.js', 'src/index.jsx', 'src/index.js']:
                if candidate in all_rel_files:
                    info["entrypoint"] = candidate
                    break
            if "test" in scripts:
                info["has_test"] = True
                info["test_framework"] = "vitest" if "vitest" in deps else "jest"
                info["test_command"] = "npm test -- --run" if "vitest" in deps else "npm test"
            info["details"] = "React Single Page Application built with Vite."
            return info

        # Vue / Vite Vue
        elif "vue" in deps:
            info["framework"] = "vue"
            info["project_type"] = "frontend_spa"
            info["runtime"] = "browser"
            info["deployment_model"] = "static_spa_webserver"
            info["build_output_dir"] = "dist"
            info["has_build"] = "build" in scripts
            info["build_command"] = "npm run build"
            info["details"] = "Vue.js Single Page Application."
            return info

        # Express / Node API Backend
        elif any(k in deps for k in ["express", "fastify", "koa", "restify", "nest", "@nestjs/core"]):
            if "@nestjs/core" in deps:
                info["framework"] = "nestjs"
            elif "fastify" in deps:
                info["framework"] = "fastify"
            elif "koa" in deps:
                info["framework"] = "koa"
            else:
                info["framework"] = "express"

            info["project_type"] = "backend_api"
            info["runtime"] = "node"
            info["deployment_model"] = "node_server"
            info["has_build"] = "build" in scripts
            if info["has_build"]:
                info["build_command"] = "npm run build"
                info["build_output_dir"] = "dist"

            for candidate in ['server.js', 'index.js', 'app.js', 'src/server.js', 'src/index.js', 'src/app.js', 'src/main.ts']:
                if candidate in all_rel_files:
                    info["entrypoint"] = candidate
                    break

            if "test" in scripts:
                info["has_test"] = True
                info["test_framework"] = "jest" if "jest" in deps else "mocha" if "mocha" in deps else "custom"
                info["test_command"] = "npm test"

            info["details"] = f"Node.js Backend Server utilizing {info['framework'].capitalize()}."
            return info

        # Generic React (without CRA or Vite)
        elif "react" in deps:
            info["framework"] = "react_generic"
            info["project_type"] = "frontend_spa"
            info["runtime"] = "browser"
            info["deployment_model"] = "static_spa_webserver"
            info["has_build"] = "build" in scripts
            if info["has_build"]:
                info["build_command"] = "npm run build"
                info["build_output_dir"] = "build" if os.path.exists(os.path.join(repo_path, 'public')) else "dist"
            for candidate in ['src/index.js', 'src/index.jsx', 'src/main.js', 'src/App.js']:
                if candidate in all_rel_files:
                    info["entrypoint"] = candidate
                    break
            if "test" in scripts:
                info["has_test"] = True
                info["test_command"] = "npm test"
            info["details"] = "React Frontend Application."
            return info

        # General Node API / Tool
        else:
            info["framework"] = "node_general"
            info["project_type"] = "backend_api" if any(f.endswith('server.js') for f in all_rel_files) else "cli_tool"
            info["runtime"] = "node"
            info["deployment_model"] = "node_server"
            info["has_build"] = "build" in scripts
            if info["has_build"]:
                info["build_command"] = "npm run build"
            for candidate in ['server.js', 'index.js', 'app.js', 'main.js']:
                if candidate in all_rel_files:
                    info["entrypoint"] = candidate
                    break
            if "test" in scripts:
                info["has_test"] = True
                info["test_command"] = "npm test"
            info["details"] = "Node.js Application."
            return info

    # 2. Inspect Python ecosystem
    py_files = [f for f in all_rel_files if f.endswith('.py')]
    req_txt = os.path.join(repo_path, 'requirements.txt')
    pipfile = os.path.join(repo_path, 'Pipfile')
    pyproject = os.path.join(repo_path, 'pyproject.toml')

    if py_files or os.path.exists(req_txt) or os.path.exists(pipfile) or os.path.exists(pyproject):
        info["language"] = "python"
        info["runtime"] = "python"
        info["manifest_path"] = "requirements.txt" if os.path.exists(req_txt) else "pyproject.toml" if os.path.exists(pyproject) else "Pipfile"
        info["package_manager"] = "poetry" if os.path.exists(pyproject) else "pipenv" if os.path.exists(pipfile) else "pip"

        content = ""
        if os.path.exists(req_txt):
            try:
                with open(req_txt, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
            except Exception:
                pass

        if "fastapi" in content:
            info["framework"] = "fastapi"
            info["project_type"] = "backend_api"
            info["deployment_model"] = "python_wsgi_asgi"
        elif "flask" in content:
            info["framework"] = "flask"
            info["project_type"] = "backend_api"
            info["deployment_model"] = "python_wsgi_asgi"
        elif "django" in content:
            info["framework"] = "django"
            info["project_type"] = "fullstack"
            info["deployment_model"] = "python_wsgi_asgi"
        elif any(k in content for k in ["torch", "tensorflow", "sklearn", "scikit-learn", "pandas"]):
            info["framework"] = "python_ml"
            info["project_type"] = "library"
            info["deployment_model"] = "python_app"
        else:
            info["framework"] = "python_app"
            info["project_type"] = "backend_api" if any('app.py' in f or 'server.py' in f for f in py_files) else "cli_tool"
            info["deployment_model"] = "python_app"

        for candidate in ['app.py', 'main.py', 'server.py', 'manage.py', 'wsgi.py']:
            if candidate in all_rel_files:
                info["entrypoint"] = candidate
                break

        # Check for pytest or tests
        has_tests = any('test' in f.lower() and f.endswith('.py') for f in all_rel_files) or 'pytest' in content
        if has_tests:
            info["has_test"] = True
            info["test_framework"] = "pytest" if "pytest" in content else "unittest"
            info["test_command"] = "pytest" if "pytest" in content else "python -m unittest discover"

        info["details"] = f"Python Application ({info['framework']})."
        return info

    # 3. Inspect Go ecosystem
    if os.path.exists(os.path.join(repo_path, 'go.mod')) or any(f.endswith('.go') for f in all_rel_files):
        info["language"] = "go"
        info["framework"] = "go_module"
        info["runtime"] = "go"
        info["package_manager"] = "go"
        info["manifest_path"] = "go.mod"
        info["project_type"] = "backend_api"
        info["deployment_model"] = "go_binary"
        info["has_build"] = True
        info["build_command"] = "go build -o app ."
        info["entrypoint"] = "main.go" if "main.go" in all_rel_files else None
        if any(f.endswith('_test.go') for f in all_rel_files):
            info["has_test"] = True
            info["test_framework"] = "go_test"
            info["test_command"] = "go test ./..."
        info["details"] = "Go Module Application."
        return info

    # 4. Static Web / HTML
    if any(f.endswith(('.html', '.htm')) for f in all_rel_files):
        info["language"] = "html_css"
        info["framework"] = "static_web"
        info["project_type"] = "static_site"
        info["runtime"] = "browser"
        info["deployment_model"] = "static_spa_webserver"
        info["entrypoint"] = "index.html" if "index.html" in all_rel_files else all_rel_files[0]
        info["details"] = "Static HTML/CSS/JavaScript Website."
        return info

    info["details"] = "Generic repository codebase."
    return info
