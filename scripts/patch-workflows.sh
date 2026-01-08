#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

# Repositórios da lista
REPOS=(
  "equidade-download-data-function"
  "iu-file-checker-function"
  "gf_treatment_data_function"
  "gf_raw_data_function"
  "iu-dataset-update-function"
  "consistency_checker_function"
  "pi_treatment_data_function"
  "pi_raw_data_function"
  "etl-surveycto-function"
  "dataset-update-function"
  "equidade-data-package"
  "equidade-access-cloud-functions"
  "trigger-dash"
)

ORG="Instituto-Equidade-info"
TEMP_DIR="/tmp/workflow-patches"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Patch Workflows - Add repository_dispatch Trigger"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

print_warning "This will:"
echo "  1. Clone each repository temporarily"
echo "  2. Find the workflow file"
echo "  3. Add repository_dispatch trigger if not present"
echo "  4. Commit and push changes"
echo "  5. Clean up temporary files"
echo ""
read -p "Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Aborted"
    exit 0
fi

# Check gh CLI
if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI (gh) not found. Install: brew install gh"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    print_error "Not authenticated. Run: gh auth login"
    exit 1
fi

# Create temp directory
mkdir -p "$TEMP_DIR"

# Summary counters
UPDATED=0
SKIPPED=0
FAILED=0

echo ""
print_info "Processing ${#REPOS[@]} repositories..."
echo ""

for REPO in "${REPOS[@]}"; do
    FULL_REPO="${ORG}/${REPO}"
    REPO_DIR="${TEMP_DIR}/${REPO}"

    echo "──────────────────────────────────────────────────"
    print_info "Processing: ${FULL_REPO}"

    # Check if repo exists
    if ! gh repo view "$FULL_REPO" &> /dev/null; then
        print_error "Repository not accessible or doesn't exist"
        ((FAILED++))
        continue
    fi

    # Clone repo
    print_info "Cloning repository..."
    if ! git clone -q "https://github.com/${FULL_REPO}.git" "$REPO_DIR" 2>/dev/null; then
        print_error "Failed to clone repository"
        ((FAILED++))
        continue
    fi

    cd "$REPO_DIR"

    # Find workflow file
    WORKFLOW_FILE=$(find .github/workflows -type f \( -name "*.yml" -o -name "*.yaml" \) 2>/dev/null | head -1)

    if [ -z "$WORKFLOW_FILE" ]; then
        print_warning "No workflow file found in .github/workflows/"
        ((SKIPPED++))
        cd - > /dev/null
        continue
    fi

    print_info "Found workflow: ${WORKFLOW_FILE}"

    # Check if already has repository_dispatch
    if grep -q "repository_dispatch" "$WORKFLOW_FILE"; then
        print_warning "Already has repository_dispatch trigger - skipping"
        ((SKIPPED++))
        cd - > /dev/null
        continue
    fi

    # Backup original
    cp "$WORKFLOW_FILE" "${WORKFLOW_FILE}.backup"

    # Add repository_dispatch trigger
    # Find the line with 'on:' and add after it
    if grep -q "^on:" "$WORKFLOW_FILE"; then
        # Create temp file with the addition
        awk '
        /^on:/ {
            print
            print "  repository_dispatch:"
            print "    types: [package-updated]"
            print ""
            next
        }
        { print }
        ' "$WORKFLOW_FILE" > "${WORKFLOW_FILE}.tmp"

        mv "${WORKFLOW_FILE}.tmp" "$WORKFLOW_FILE"

        print_success "Added repository_dispatch trigger"

        # Show diff
        echo ""
        echo "Changes:"
        diff -u "${WORKFLOW_FILE}.backup" "$WORKFLOW_FILE" | tail -n +3 || true
        echo ""

        # Commit and push
        git add "$WORKFLOW_FILE"
        git commit -m "feat: add repository_dispatch trigger for automatic package updates

This allows the workflow to be triggered automatically when
equidade-data-package releases a new version.

Triggered by: equidade-data-package automation setup"

        if git push origin main 2>/dev/null || git push origin master 2>/dev/null; then
            print_success "Changes committed and pushed"
            ((UPDATED++))
        else
            print_error "Failed to push changes"
            ((FAILED++))
        fi
    else
        print_error "Could not find 'on:' section in workflow file"
        ((FAILED++))
    fi

    cd - > /dev/null
done

# Cleanup
print_info "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_success "Updated: ${UPDATED}"
print_warning "Skipped: ${SKIPPED}"
print_error "Failed: ${FAILED}"
echo ""

if [ $UPDATED -gt 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_success "Workflow patches applied successfully!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    print_info "Next steps:"
    echo "  1. Test trigger: ./scripts/release.sh"
    echo "  2. Monitor: gh run list"
    echo "  3. Check individual repos if any failed"
fi

echo ""
