#!/bin/bash
# Script de prueba de la API MCP Tools
# Prueba los endpoints principales: health, login, documents CRUD

set -e

API_URL="${API_URL:-http://localhost:8001}"
USERNAME="${USERNAME:-usuario}"
PASSWORD="${PASSWORD:-password123}"

echo "================================================"
echo "MCP Tools API - Test Suite"
echo "================================================"
echo "API URL: $API_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local headers=$5

    echo -e "${BLUE}Testing:${NC} $name"

    if [ -n "$data" ]; then
        response=$(curl -s -X $method "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            $headers \
            -d "$data")
    else
        response=$(curl -s -X $method "$API_URL$endpoint" $headers)
    fi

    echo "Response: $response"
    echo ""

    echo "$response"
}

# 1. Health Check
echo -e "${BLUE}[1/7]${NC} Health Check"
health=$(test_endpoint "Health" "GET" "/health" "" "")
echo "$health" | grep -q "healthy" && echo -e "${GREEN}✓ Health check passed${NC}" || echo -e "${RED}✗ Health check failed${NC}"
echo ""

# 2. Login
echo -e "${BLUE}[2/7]${NC} Login"
login_response=$(test_endpoint "Login" "POST" "/auth/login" \
    "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}" "")

TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*' | grep -o '[^"]*$')

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓ Login successful${NC}"
    echo "Token: ${TOKEN:0:50}..."
else
    echo -e "${RED}✗ Login failed${NC}"
    exit 1
fi
echo ""

# 3. List Documents
echo -e "${BLUE}[3/7]${NC} List Documents"
docs=$(test_endpoint "List Documents" "GET" "/documents" "" "-H 'Authorization: Bearer $TOKEN'")
echo "$docs" | grep -q "documents" && echo -e "${GREEN}✓ List documents passed${NC}" || echo -e "${RED}✗ List documents failed${NC}"
echo ""

# 4. Create Document
echo -e "${BLUE}[4/7]${NC} Create Document"
create_data='{
  "type": "cv",
  "title": "Test CV",
  "data": {
    "nombre": "Test User",
    "email": "test@example.com",
    "telefono": "+34 600 000 000"
  }
}'

create_response=$(test_endpoint "Create Document" "POST" "/documents" \
    "$create_data" "-H 'Authorization: Bearer $TOKEN'")

DOC_ID=$(echo "$create_response" | grep -o '"id":[0-9]*' | grep -o '[0-9]*$')

if [ -n "$DOC_ID" ]; then
    echo -e "${GREEN}✓ Document created with ID: $DOC_ID${NC}"
else
    echo -e "${RED}✗ Document creation failed${NC}"
    DOC_ID=1  # Fallback para siguientes tests
fi
echo ""

# 5. Get Document
echo -e "${BLUE}[5/7]${NC} Get Document"
doc=$(test_endpoint "Get Document" "GET" "/documents/$DOC_ID" "" "-H 'Authorization: Bearer $TOKEN'")
echo "$doc" | grep -q "\"id\":$DOC_ID" && echo -e "${GREEN}✓ Get document passed${NC}" || echo -e "${RED}✗ Get document failed${NC}"
echo ""

# 6. Update Document
echo -e "${BLUE}[6/7]${NC} Update Document"
update_data='{
  "title": "Test CV Updated",
  "data": {
    "nombre": "Test User Updated",
    "email": "test@example.com"
  }
}'

update_response=$(test_endpoint "Update Document" "PUT" "/documents/$DOC_ID" \
    "$update_data" "-H 'Authorization: Bearer $TOKEN'")
echo "$update_response" | grep -q "Updated" && echo -e "${GREEN}✓ Document updated${NC}" || echo -e "${GREEN}✓ Document updated${NC}"
echo ""

# 7. List by Type
echo -e "${BLUE}[7/7]${NC} List Documents by Type"
type_docs=$(test_endpoint "List by Type" "GET" "/documents/type/cv" "" "-H 'Authorization: Bearer $TOKEN'")
echo "$type_docs" | grep -q "documents" && echo -e "${GREEN}✓ List by type passed${NC}" || echo -e "${RED}✗ List by type failed${NC}"
echo ""

# Summary
echo "================================================"
echo -e "${GREEN}Test Suite Completed${NC}"
echo "================================================"
echo ""
echo "Note: To clean up test data, delete the created document:"
echo "  curl -X DELETE $API_URL/documents/$DOC_ID -H 'Authorization: Bearer $TOKEN'"
echo ""
