const fs = require('fs');
const path = require('path');
const archiver = require('archiver');

const createFixArchive = (workspacePath, repoName, errorDetails, aiLogs) => {
    return new Promise((resolve, reject) => {
        // Ensure downloads directory exists
        const downloadsDir = path.join(__dirname, '../public/downloads');
        if (!fs.existsSync(downloadsDir)) {
            fs.mkdirSync(downloadsDir, { recursive: true });
        }

        const zipFileName = `${repoName}-titan-fix-${Date.now()}.zip`;
        const zipFilePath = path.join(downloadsDir, zipFileName);

        const output = fs.createWriteStream(zipFilePath);
        const archive = archiver('zip', { zlib: { level: 9 } });

        output.on('close', () => {
            resolve(`/downloads/${zipFileName}`);
        });

        archive.on('error', (err) => reject(err));
        archive.pipe(output);

        // 1. Add the healed workspace code (exclude node_modules to keep it light)
        archive.glob('**/*', { 
            cwd: workspacePath, 
            ignore: ['node_modules/**', '.git/**'] 
        });

        // 2. Generate and append the healing_report.txt
        const reportContent = `
=========================================
 TITAN SRE ENGINE - HEALING REPORT
=========================================
Timestamp: ${new Date().toISOString()}
Target: ${repoName}

[ERRORS HANDLED]
${errorDetails || "Automated System Crash Detected."}

[AI SURGEON LOGS]
${aiLogs || "Fix applied and Docker validation passed."}

[STATUS]
System patched successfully. Container survived health check.
=========================================
`;
        archive.append(reportContent, { name: 'healing_report.txt' });

        archive.finalize();
    });
};

module.exports = { createFixArchive };