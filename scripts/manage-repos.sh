#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

WORKFLOW_FILE=".github/workflows/trigger-deploys.yml"

if [ ! -f "$WORKFLOW_FILE" ]; then
    print_error "Workflow file not found: $WORKFLOW_FILE"
    exit 1
fi

# Get current org name
CURRENT_ORG=$(grep "GITHUB_ORG:" "$WORKFLOW_FILE" | sed -E "s/.*GITHUB_ORG: '(.*)'.*/\1/")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Manage Deployment Repositories"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

print_info "Current organization: ${CURRENT_ORG}"
echo ""

# Get current repos
echo "Current repositories:"
grep -A 100 "repo:" "$WORKFLOW_FILE" | grep "^[[:space:]]*-" | sed "s/^[[:space:]]*- '/  - /" | sed "s/'$//"

echo ""
echo "What would you like to do?"
echo "  1) List current repositories"
echo "  2) Add a repository"
echo "  3) Remove a repository"
echo "  4) Change organization name"
echo "  5) Test repository access"
echo "  6) Exit"
echo ""
read -p "Enter choice [1-6]: " CHOICE

case $CHOICE in
    1)
        echo ""
        print_info "Current repositories in ${CURRENT_ORG}:"
        grep -A 100 "repo:" "$WORKFLOW_FILE" | grep "^[[:space:]]*-" | sed "s/^[[:space:]]*- '/  ${CURRENT_ORG}\//" | sed "s/'$//"
        ;;

    2)
        echo ""
        read -p "Enter repository name (without org prefix): " REPO_NAME
        if [ -z "$REPO_NAME" ]; then
            print_error "Repository name cannot be empty"
            exit 1
        fi

        # Check if repo already exists in workflow
        if grep -q "- '${REPO_NAME}'" "$WORKFLOW_FILE"; then
            print_warning "Repository '${REPO_NAME}' already exists in workflow"
            exit 1
        fi

        # Find the line number to insert before
        LINE_NUM=$(grep -n "# Add more repository names here" "$WORKFLOW_FILE" | cut -d: -f1)

        # Insert new repo
        sed -i '' "${LINE_NUM}i\\
          - '${REPO_NAME}'
" "$WORKFLOW_FILE"

        print_success "Added repository: ${CURRENT_ORG}/${REPO_NAME}"
        print_info "Don't forget to:"
        echo "  1. Configure workflow in ${REPO_NAME}"
        echo "  2. Add GCP_SA_KEY secret to ${REPO_NAME}"
        echo "  3. Commit and push changes"
        ;;

    3)
        echo ""
        read -p "Enter repository name to remove: " REPO_NAME
        if [ -z "$REPO_NAME" ]; then
            print_error "Repository name cannot be empty"
            exit 1
        fi

        if ! grep -q "- '${REPO_NAME}'" "$WORKFLOW_FILE"; then
            print_error "Repository '${REPO_NAME}' not found in workflow"
            exit 1
        fi

        # Remove the line
        sed -i '' "/- '${REPO_NAME}'/d" "$WORKFLOW_FILE"

        print_success "Removed repository: ${REPO_NAME}"
        print_warning "Don't forget to commit and push changes"
        ;;

    4)
        echo ""
        read -p "Enter new organization name: " NEW_ORG
        if [ -z "$NEW_ORG" ]; then
            print_error "Organization name cannot be empty"
            exit 1
        fi

        sed -i '' "s/GITHUB_ORG: '${CURRENT_ORG}'/GITHUB_ORG: '${NEW_ORG}'/" "$WORKFLOW_FILE"

        print_success "Changed organization from '${CURRENT_ORG}' to '${NEW_ORG}'"
        print_warning "Don't forget to commit and push changes"
        ;;

    5)
        echo ""
        if ! command -v gh &> /dev/null; then
            print_error "GitHub CLI (gh) not found. Install it with: brew install gh"
            exit 1
        fi

        print_info "Testing repository access..."
        echo ""

        # Get all repos from workflow
        REPOS=$(grep -A 100 "repo:" "$WORKFLOW_FILE" | grep "^[[:space:]]*-" | sed "s/^[[:space:]]*- '//;s/'$//")

        for REPO in $REPOS; do
            FULL_REPO="${CURRENT_ORG}/${REPO}"
            if gh repo view "$FULL_REPO" &> /dev/null; then
                print_success "${FULL_REPO} - accessible"
            else
                print_error "${FULL_REPO} - NOT accessible or doesn't exist"
            fi
        done
        ;;

    6)
        print_info "Goodbye!"
        exit 0
        ;;

    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
