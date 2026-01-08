#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
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

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI (gh) not found. Install it with: brew install gh"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    print_error "Not authenticated with GitHub CLI. Run: gh auth login"
    exit 1
fi

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep -E '^version = ' pyproject.toml | sed -E 's/version = "(.*)"/\1/')
print_info "Current version: ${CURRENT_VERSION}"

# Ask for new version
echo ""
read -p "Enter new version (e.g., 0.2.3): " NEW_VERSION

if [ -z "$NEW_VERSION" ]; then
    print_error "Version cannot be empty"
    exit 1
fi

# Validate version format (basic check)
if ! [[ $NEW_VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    print_error "Invalid version format. Use semantic versioning (e.g., 0.2.3)"
    exit 1
fi

print_info "New version: ${NEW_VERSION}"

# Ask for release type
echo ""
echo "Select release type:"
echo "  1) patch (bug fixes)"
echo "  2) minor (new features, backwards compatible)"
echo "  3) major (breaking changes)"
read -p "Enter choice [1-3]: " RELEASE_TYPE

case $RELEASE_TYPE in
    1) RELEASE_TYPE_NAME="patch" ;;
    2) RELEASE_TYPE_NAME="minor" ;;
    3) RELEASE_TYPE_NAME="major" ;;
    *) print_error "Invalid choice"; exit 1 ;;
esac

print_info "Release type: ${RELEASE_TYPE_NAME}"

# Confirm
echo ""
print_warning "This will:"
echo "  1. Update version in pyproject.toml to ${NEW_VERSION}"
echo "  2. Run tests"
echo "  3. Build package"
echo "  4. Commit changes"
echo "  5. Create and push tag v${NEW_VERSION}"
echo "  6. Create GitHub release"
echo "  7. Trigger deploys in all configured Cloud Functions"
echo ""
read -p "Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Aborted"
    exit 0
fi

# Update version in pyproject.toml
print_info "Updating version in pyproject.toml..."
sed -i '' "s/version = \"${CURRENT_VERSION}\"/version = \"${NEW_VERSION}\"/" pyproject.toml
print_success "Version updated"

# Run tests
print_info "Running tests..."
if command -v pytest &> /dev/null; then
    if ! pytest tests/ -v; then
        print_error "Tests failed. Reverting changes..."
        git checkout pyproject.toml
        exit 1
    fi
    print_success "Tests passed"
else
    print_warning "pytest not found, skipping tests"
fi

# Build package
print_info "Building package..."
if command -v python3 &> /dev/null; then
    if ! python3 -m build; then
        print_error "Build failed. Reverting changes..."
        git checkout pyproject.toml
        exit 1
    fi
    print_success "Package built"
else
    print_warning "python3 not found, skipping build"
fi

# Git operations
print_info "Committing changes..."
git add pyproject.toml
git commit -m "chore: bump version to ${NEW_VERSION}"
print_success "Changes committed"

print_info "Creating tag v${NEW_VERSION}..."
git tag "v${NEW_VERSION}"
print_success "Tag created"

print_info "Pushing to remote..."
git push origin main
git push origin "v${NEW_VERSION}"
print_success "Pushed to remote"

# Create GitHub release
print_info "Creating GitHub release..."
RELEASE_NOTES=$(cat <<EOF
## What's Changed

Release of version ${NEW_VERSION} (${RELEASE_TYPE_NAME}).

### Installation

\`\`\`bash
pip install --upgrade equidade-data-package
\`\`\`

Or with specific version:

\`\`\`bash
pip install equidade-data-package==${NEW_VERSION}
\`\`\`

### Automated Deploys

This release will automatically trigger deploys in all configured Cloud Functions.
Check the [Actions tab](https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions) to monitor progress.
EOF
)

if gh release create "v${NEW_VERSION}" \
    --title "v${NEW_VERSION}" \
    --notes "$RELEASE_NOTES" \
    --verify-tag; then
    print_success "GitHub release created"
else
    print_error "Failed to create GitHub release"
    exit 1
fi

# Show summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_success "Release v${NEW_VERSION} created successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_info "Next steps:"
echo "  1. Monitor deploy triggers: gh run list"
echo "  2. Check Cloud Functions: gcloud functions list"
echo "  3. View release: gh release view v${NEW_VERSION}"
echo ""
print_info "Package will be available at:"
echo "  https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/releases/tag/v${NEW_VERSION}"
echo ""
