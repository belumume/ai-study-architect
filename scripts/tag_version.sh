#!/bin/bash
# Version tagging script for AI Study Architect
# Usage: ./scripts/tag_version.sh [major|minor|patch]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the latest tag
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
echo "Latest tag: $LATEST_TAG"

# Parse current version
VERSION=${LATEST_TAG#v}
IFS='.' read -ra VERSION_PARTS <<< "$VERSION"
MAJOR=${VERSION_PARTS[0]:-0}
MINOR=${VERSION_PARTS[1]:-0}
PATCH=${VERSION_PARTS[2]:-0}

# Determine version bump type
BUMP_TYPE=${1:-patch}

case $BUMP_TYPE in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        echo -e "${YELLOW}Major version bump${NC}"
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        echo -e "${YELLOW}Minor version bump${NC}"
        ;;
    patch)
        PATCH=$((PATCH + 1))
        echo -e "${YELLOW}Patch version bump${NC}"
        ;;
    *)
        echo -e "${RED}Invalid bump type. Use: major, minor, or patch${NC}"
        exit 1
        ;;
esac

# Create new version
NEW_VERSION="v${MAJOR}.${MINOR}.${PATCH}"
echo -e "New version: ${GREEN}$NEW_VERSION${NC}"

# Get commit messages since last tag
echo -e "\n${YELLOW}Changes since $LATEST_TAG:${NC}"
git log --oneline --no-decorate $LATEST_TAG..HEAD

# Confirm with user
echo -e "\nTag this as ${GREEN}$NEW_VERSION${NC}?"
read -p "Enter tag message (or 'cancel' to abort): " TAG_MESSAGE

if [ "$TAG_MESSAGE" = "cancel" ]; then
    echo -e "${RED}Cancelled${NC}"
    exit 0
fi

# Create annotated tag
git tag -a "$NEW_VERSION" -m "$TAG_MESSAGE"
echo -e "${GREEN}✅ Created tag $NEW_VERSION${NC}"

# Ask if should push
read -p "Push tag to remote? (y/n): " PUSH_CONFIRM
if [ "$PUSH_CONFIRM" = "y" ]; then
    git push origin "$NEW_VERSION"
    echo -e "${GREEN}✅ Pushed $NEW_VERSION to origin${NC}"
    
    # Create GitHub release notes
    echo -e "\n${YELLOW}GitHub Release Notes:${NC}"
    echo "----------------------------------------"
    echo "## Release $NEW_VERSION"
    echo ""
    echo "$TAG_MESSAGE"
    echo ""
    echo "### Changes"
    git log --pretty=format:"- %s" $LATEST_TAG..HEAD
    echo ""
    echo "----------------------------------------"
    echo -e "${YELLOW}Copy the above for GitHub release${NC}"
fi

echo -e "\n${GREEN}Done!${NC}"