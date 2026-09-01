#!/bin/bash
# Jinba Auto Export - Deployment Script
# This script helps deploy the new SEO content

echo "=== Jinba Auto Export - Traffic Growth Deployment ==="
echo ""

# Check if in correct directory
if [ ! -f "sitemap.xml" ]; then
    echo "Error: Please run this script from the china-jinba-used-cars directory"
    exit 1
fi

# Step 1: Add all new files
echo "Step 1: Adding new files to git..."
git add -A

# Step 2: Check what will be committed
echo ""
echo "Files to commit:"
git status --short

# Step 3: Ask for confirmation
echo ""
read -p "Commit these changes? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

# Step 4: Commit
echo ""
echo "Committing changes..."
git commit -m "Add SEO content: market guides, FAQ, and blog pages

New content:
- /en/guides/import-used-cars-to-uae/
- /en/guides/import-used-cars-to-russia/
- /en/guides/import-used-cars-to-africa/
- /en/guides/import-used-cars-to-southeast-asia/
- /en/faq/
- /en/blog/

These pages target long-tail keywords and improve SEO."

# Step 5: Push
echo ""
echo "Pushing to GitHub..."
git push origin main

# Step 6: Update sitemap
echo ""
echo "Updating sitemap..."
cp sitemap-updated.xml sitemap.xml

# Step 7: Final commit
echo ""
echo "Committing sitemap update..."
git add sitemap.xml
git commit -m "Update sitemap with new SEO pages"
git push origin main

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Submit sitemap to Google Search Console: https://search.google.com/search-console"
echo "2. Submit sitemap to Bing: https://www.bing.com/webmasters"
echo "3. Share new pages on social media"
echo "4. Build backlinks from relevant websites"
echo ""
echo "URLs to share:"
echo "- https://jinbacars.com/en/guides/import-used-cars-to-uae/"
echo "- https://jinbacars.com/en/guides/import-used-cars-to-russia/"
echo "- https://jinbacars.com/en/guides/import-used-cars-to-africa/"
echo "- https://jinbacars.com/en/guides/import-used-cars-to-southeast-asia/"
echo "- https://jinbacars.com/en/faq/"
echo "- https://jinbacars.com/en/blog/"
