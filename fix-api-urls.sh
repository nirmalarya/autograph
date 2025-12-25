#!/bin/bash

# Script to fix hardcoded API URLs to use API Gateway
# All frontend requests should go through http://localhost:8080/api/*

set -e

echo "Fixing hardcoded API URLs in frontend..."

# Files to fix
FILES=(
  "services/frontend/app/dashboard/page.tsx"
  "services/frontend/app/login/page.tsx"
  "services/frontend/app/register/page.tsx"
  "services/frontend/app/versions/[id]/page.tsx"
  "services/frontend/app/note/[id]/page.tsx"
  "services/frontend/app/mermaid/[id]/page.tsx"
  "services/frontend/app/version-shared/[token]/page.tsx"
  "services/frontend/app/ai-generate/page.tsx"
  "services/frontend/app/settings/security/page.tsx"
  "services/frontend/app/components/ExportDialog.tsx"
  "services/frontend/app/components/FolderTree.tsx"
  "services/frontend/app/components/ExampleDiagrams.tsx"
)

# Replacements for diagram service (8082 -> /api/diagrams)
for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "Processing $file..."

    # Replace diagram service URLs
    sed -i.bak 's|http://localhost:8082/|${API_ENDPOINTS.diagrams.base}/|g' "$file"
    sed -i.bak2 's|http://localhost:8082/\${|${API_ENDPOINTS.diagrams.base}/\${|g' "$file"

    # Replace ai service URLs (8084 -> /api/ai)
    sed -i.bak3 's|http://localhost:8084/|${API_BASE_URL}/api/ai/|g' "$file"

    # Replace export service URLs (8097 -> /api/export)
    sed -i.bak4 's|http://localhost:8097/|${API_BASE_URL}/api/export/|g' "$file"

    # Replace auth service URLs (8085 -> /api/auth)
    sed -i.bak5 's|http://localhost:8085/|${API_BASE_URL}/api/auth/|g' "$file"

    # Clean up backup files
    rm -f "$file.bak" "$file.bak2" "$file.bak3" "$file.bak4" "$file.bak5"

    echo "  ✓ Fixed $file"
  else
    echo "  ⚠ File not found: $file"
  fi
done

echo ""
echo "✓ All files processed!"
echo "Note: You still need to add 'import { API_ENDPOINTS, API_BASE_URL } from '@/lib/api-config';' to each file"
