const fs = require('fs');
const path = require('path');
const archiver = require('archiver');

const createFixArchive = (workspacePath, repoName, errorDetails, aiLogs) => {
    return new Promise((resolve, reject) => {
        const downloadsDir = path.join(__dirname, '../../public/downloads');
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

        // Add the healed workspace code (exclude node_modules to keep it light)
        archive.glob('**/*', { 
            cwd: workspacePath, 
            ignore: ['node_modules/**', '.git/**', 'venv/**'] 
        });

        archive.finalize();
    });
};

module.exports = { createFixArchive };