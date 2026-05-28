# GitHub Profile README Deployment Script
# This script initializes Git, commits the files, creates the public repository on GitHub, and pushes.

$ErrorActionPreference = "Stop"

# Clear GITHUB_TOKEN environment variable for this process so gh CLI uses keyring credentials
$env:GITHUB_TOKEN = ""

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Deploying GitHub Profile README" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Check gh CLI authentication status
try {
    Write-Host "[1/5] Checking GitHub CLI (gh) authentication..." -ForegroundColor Green
    $authStatus = gh auth status 2>&1
    Write-Host "Successfully authenticated!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Please make sure you are logged in to the GitHub CLI (gh)." -ForegroundColor Red
    Write-Host "You can login by running: gh auth login" -ForegroundColor Yellow
    exit 1
}

# 2. Git Initialization
Write-Host "[2/5] Initializing Git repository locally..." -ForegroundColor Green
if (!(Test-Path .git)) {
    git init
    Write-Host "Git repository initialized." -ForegroundColor Gray
} else {
    Write-Host "Git repository already initialized." -ForegroundColor Gray
}

# 3. Add and Commit files
Write-Host "[3/5] Staging and committing files..." -ForegroundColor Green
git add .
try {
    git commit -m "feat: initial commit of profile README and snake game workflow"
    Write-Host "Committed successfully." -ForegroundColor Gray
} catch {
    # If there's nothing to commit, that's fine too
    Write-Host "No changes to commit or already committed." -ForegroundColor Gray
}

# Rename active branch to main
git branch -M main
Write-Host "Branch renamed to 'main'." -ForegroundColor Gray

# 4. Create GitHub repository & Push
Write-Host "[4/5] Creating GitHub repository 'tom613951' and pushing..." -ForegroundColor Green
try {
    # Try to create repository via gh CLI and push
    # --source=. specifies the current directory, --remote=origin sets origin remote, --push pushes the branch
    gh repo create tom613951 --public --source=. --remote=origin --push
    Write-Host "Successfully created GitHub repository and pushed main branch!" -ForegroundColor Green
} catch {
    # Check if repo already exists
    $repoExists = gh repo view tom613951/tom613951 2>&1
    if ($repoExists -match "Could not resolve to a Repository" -or $repoExists -match "not found") {
        Write-Host "Failed to create repository: $_" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "Repository 'tom613951/tom613951' already exists on GitHub." -ForegroundColor Yellow
        Write-Host "Setting remote origin and pushing..." -ForegroundColor Green
        try {
            git remote remove origin 2>$null
        } catch {}
        git remote add origin https://github.com/tom613951/tom613951.git
        git push -u origin main --force
        Write-Host "Successfully pushed to existing repository!" -ForegroundColor Green
    }
}

# 5. Done
Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "🎉 GitHub Profile README successfully deployed!" -ForegroundColor Green
Write-Host "Link: https://github.com/tom613951" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Green
Write-Host "NOTE: To see the dynamic Contribution Snake Game, wait about 1-2 minutes" -ForegroundColor Yellow
Write-Host "for the first run of the GitHub Action to generate the snake image." -ForegroundColor Yellow
Write-Host "You can manually trigger it here:" -ForegroundColor Yellow
Write-Host "https://github.com/tom613951/tom613951/actions" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Green
