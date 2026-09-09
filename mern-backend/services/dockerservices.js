const util = require('util');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const execPromise = util.promisify(exec);

const isDockerRunning = async () => {
    try {
        await execPromise('docker info --format "{{.ServerVersion}}"');
        return true;
    } catch (e) {
        return false;
    }
};

// This function takes the cloned code, builds a safe container, and runs it without failure-suppression
const testCodeInDocker = async (repoPath, repoName) => {
    const daemonLive = await isDockerRunning();
    if (!daemonLive) {
        console.log(`[DOCKER] Docker daemon is not active on host. Skipping container sandbox.`);
        return {
            status: 'skipped',
            logs: 'Docker daemon is not running on host.'
        };
    }

    console.log(`[DOCKER] Spinning up Sandbox for ${repoName}...`);
    const safeRepoName = repoName.toLowerCase().replace(/[^a-z0-9]/g, '');

    // Check if Dockerfile exists. If not, inspect repository architecture
    const dockerfilePath = path.join(repoPath, 'Dockerfile');
    if (!fs.existsSync(dockerfilePath)) {
        console.log(`[DOCKER] No Dockerfile found. Detecting project architecture...`);
        let fallbackDockerfile;

        const packageJsonPath = path.join(repoPath, 'package.json');
        if (fs.existsSync(packageJsonPath)) {
            try {
                const pkg = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
                const deps = { ...pkg.dependencies, ...pkg.devDependencies };
                if (deps['react'] || deps['react-scripts'] || deps['vite']) {
                    fallbackDockerfile = `FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
`;
                } else {
                    fallbackDockerfile = `FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 5000
CMD ["npm", "start"]
`;
                }
            } catch (e) {
                fallbackDockerfile = `FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 5000
CMD ["npm", "start"]
`;
            }
        } else {
            fallbackDockerfile = `FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
`;
        }
        fs.writeFileSync(dockerfilePath, fallbackDockerfile);
    }

    try {
        console.log(`[DOCKER] Building image: titan-${safeRepoName}...`);
        const { stdout: buildOut } = await execPromise(`docker build -t titan-${safeRepoName} "${repoPath}"`);

        console.log(`[DOCKER] Executing code in isolated container...`);
        const { stdout, stderr } = await execPromise(`docker run --rm titan-${safeRepoName}`);

        console.log(`[DOCKER] Container exited cleanly!`);
        return { status: 'success', logs: stdout };

    } catch (error) {
        console.log(`[DOCKER] Container execution failed! Captured exact output.`);
        return { 
            status: 'failed', 
            logs: error.stderr || error.message || error.stdout 
        };
    }
};

module.exports = { testCodeInDocker, isDockerRunning };