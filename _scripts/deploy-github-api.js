#!/usr/bin/env node
/**
 * Deploy jinbacars.com to GitHub Pages via GitHub API
 * Reads files from the workspace mount and pushes to jian522/usedchinesecars main branch
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const GITHUB_TOKEN = 'YOUR_GITHUB_TOKEN';
const OWNER = 'jian522';
const REPO = 'usedchinesecars';
const BRANCH = 'main';
const API_HOST = 'api.github.com';

// Files to deploy (relative paths in the repo)
const FILES_TO_DEPLOY = [
  'index.html',
  'cars-detail.html',
  'cars.html',
  'about.html',
  'services.html',
  'contact.html',
  '404.html',
  'css/style.css',
  'js/cars-data.js',
  'js/slug-map.js',
  'js/i18n.js',
  'CNAME',
  '.nojekyll',
  'robots.txt',
  'sitemap.xml',
  'favicon.svg',
  'sw.js'
];

// Source directory - the workspace mount for the user's website
const SRC_DIR = process.argv[2] || '/sessions/elegant-charming-hypatia/mnt/金霸二手车网站';

function apiRequest(method, apiPath, body = null) {
  return new Promise((resolve, reject) => {
    const fullPath = '/repos/' + OWNER + '/' + REPO + apiPath;
    const options = {
      hostname: API_HOST,
      path: fullPath,
      method,
      headers: {
        'Authorization': 'Bearer ' + GITHUB_TOKEN,
        'User-Agent': 'jinba-deploy-script',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        let parsed;
        try { parsed = JSON.parse(data); } catch(e) { parsed = data; }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(parsed);
        } else {
          reject(new Error('API ' + method + ' ' + apiPath + ' returned ' + res.statusCode + ': ' + JSON.stringify(parsed).substring(0, 500)));
        }
      });
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function deploy() {
  console.log('=== Deploying jinbacars.com to GitHub Pages ===\n');

  // Verify source directory
  if (!fs.existsSync(SRC_DIR)) {
    console.error('ERROR: Source directory not found: ' + SRC_DIR);
    process.exit(1);
  }

  // Step 1: Get current HEAD reference
  console.log('1. Getting current HEAD reference...');
  let ref;
  try {
    ref = await apiRequest('GET', '/git/refs/heads/' + BRANCH);
    console.log('   HEAD SHA: ' + ref.object.sha);
  } catch (e) {
    console.error('   ERROR: ' + e.message);
    process.exit(1);
  }

  const baseSha = ref.object.sha;

  // Step 2: Get the base tree
  console.log('\n2. Getting base commit tree...');
  let baseCommit;
  try {
    baseCommit = await apiRequest('GET', '/git/commits/' + baseSha);
    console.log('   Base tree SHA: ' + baseCommit.tree.sha);
  } catch (e) {
    console.error('   ERROR: ' + e.message);
    process.exit(1);
  }

  const baseTreeSha = baseCommit.tree.sha;

  // Step 3: Create blobs for each file
  console.log('\n3. Creating blobs for files...');
  const treeEntries = [];

  for (const filePath of FILES_TO_DEPLOY) {
    const fullPath = path.join(SRC_DIR, filePath);

    if (!fs.existsSync(fullPath)) {
      console.log('   SKIP (not found): ' + filePath);
      continue;
    }

    try {
      const textContent = fs.readFileSync(fullPath, 'utf-8');
      const blobResponse = await apiRequest('POST', '/git/blobs', {
        content: textContent,
        encoding: 'utf-8'
      });

      treeEntries.push({
        path: filePath,
        mode: '100644',
        type: 'blob',
        sha: blobResponse.sha
      });
      const sizeKB = (Buffer.byteLength(textContent, 'utf-8') / 1024).toFixed(1);
      console.log('   OK: ' + filePath + ' (' + sizeKB + ' KB) -> SHA: ' + blobResponse.sha.substring(0, 7));
    } catch (e) {
      console.error('   ERROR uploading ' + filePath + ': ' + e.message);
    }
  }

  console.log('\n   Total files to update: ' + treeEntries.length);

  // Step 4: Create a new tree
  console.log('\n4. Creating new tree...');
  let newTree;
  try {
    newTree = await apiRequest('POST', '/git/trees', {
      base_tree: baseTreeSha,
      tree: treeEntries
    });
    console.log('   New tree SHA: ' + newTree.sha);
  } catch (e) {
    console.error('   ERROR: ' + e.message);
    process.exit(1);
  }

  // Step 5: Create a commit
  console.log('\n5. Creating commit...');
  const commitMessage = 'Deploy: bug fixes - brand filter links (Chinese->English), gallery thumbs with dedup, fix duplicate slug-map.js loading\n\n'
    + '- index.html: footer brand links use English brand names (BYD, MG, Chery, etc.)\n'
    + '- index.html: removed duplicate slug-map.js loading\n'
    + '- cars-detail.html: added gallery thumbs with image deduplication\n'
    + '- cars.html: fixed duplicate slug-map.js loading\n'
    + '- about/services/contact: fixed footer brand links to use English brand names\n';

  let newCommit;
  try {
    newCommit = await apiRequest('POST', '/git/commits', {
      message: commitMessage,
      author: {
        name: 'Jinba Deploy Bot',
        email: 'deploy@jinbacars.com',
        date: new Date().toISOString()
      },
      parents: [baseSha],
      tree: newTree.sha
    });
    console.log('   Commit SHA: ' + newCommit.sha);
  } catch (e) {
    console.error('   ERROR: ' + e.message);
    process.exit(1);
  }

  // Step 6: Update branch reference
  console.log('\n6. Updating branch reference...');
  try {
    const result = await apiRequest('PATCH', '/git/refs/heads/' + BRANCH, {
      sha: newCommit.sha,
      force: false
    });
    console.log('   SUCCESS! Branch updated to: ' + result.object.sha);
  } catch (e) {
    console.error('   ERROR: ' + e.message);
    process.exit(1);
  }

  console.log('\n========================================');
  console.log('  DEPLOYMENT COMPLETE!');
  console.log('========================================');
  console.log('  Commit: ' + newCommit.sha);
  console.log('  Files updated: ' + treeEntries.length);
  console.log('  Site will be live at https://jinbacars.com within minutes');
  console.log('========================================\n');
}

deploy().catch(err => {
  console.error('Deployment failed: ' + err.message);
  process.exit(1);
});
