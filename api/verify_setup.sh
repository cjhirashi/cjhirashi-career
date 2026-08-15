#!/bin/bash
# Script de verificación de instalación de MCP Tools API
# Verifica que todos los componentes estén correctamente configurados

set -e

echo "================================================"
echo "MCP Tools API - Setup Verification"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check counter
CHECKS_PASSED=0
TOTAL_CHECKS=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo -e "${BLUE}1. Checking File Structure${NC}"
echo "-----------------------------------"

# Check required files
REQUIRED_FILES=(
    "app.py"
    "config.py"
    "database.py"
    "requirements.txt"
    "Dockerfile"
    "init.sql"
    ".env.example"
)

for file in "${REQUIRED_FILES[@]}"; do
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ -f "$file" ]; then
        check_pass "$file exists"
    else
        check_fail "$file missing"
    fi
done

echo ""
echo -e "${BLUE}2. Checking Directory Structure${NC}"
echo "-----------------------------------"

# Check required directories
REQUIRED_DIRS=(
    "models"
    "schemas"
    "routes"
    "middleware"
    "utils"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ -d "$dir" ]; then
        check_pass "$dir/ directory exists"
    else
        check_fail "$dir/ directory missing"
    fi
done

echo ""
echo -e "${BLUE}3. Checking Python Dependencies${NC}"
echo "-----------------------------------"

if command -v python3 &> /dev/null; then
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    check_pass "Python 3 installed"

    # Check if we can import key packages (if venv is activated)
    if python3 -c "import fastapi" 2>/dev/null; then
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        check_pass "FastAPI available"
    else
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        check_warn "FastAPI not found (install with: pip install -r requirements.txt)"
    fi
else
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    check_fail "Python 3 not found"
fi

echo ""
echo -e "${BLUE}4. Checking Docker Setup${NC}"
echo "-----------------------------------"

if command -v docker &> /dev/null; then
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    check_pass "Docker installed"

    # Check if Docker daemon is running
    if docker ps &> /dev/null; then
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        check_pass "Docker daemon running"

        # Check if API container exists
        if docker ps -a | grep -q mcp_api; then
            TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
            check_pass "mcp_api container exists"

            # Check if container is running
            if docker ps | grep -q mcp_api; then
                TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
                check_pass "mcp_api container is running"
            else
                TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
                check_warn "mcp_api container exists but not running"
            fi
        else
            TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
            check_warn "mcp_api container not found (run: docker compose up -d mcp-api)"
        fi

        # Check if Postgres container exists
        if docker ps -a | grep -q mcp_postgres; then
            TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
            check_pass "mcp_postgres container exists"

            # Check if container is running
            if docker ps | grep -q mcp_postgres; then
                TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
                check_pass "mcp_postgres container is running"
            else
                TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
                check_warn "mcp_postgres container exists but not running"
            fi
        else
            TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
            check_warn "mcp_postgres container not found"
        fi
    else
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        check_fail "Docker daemon not running"
    fi
else
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    check_fail "Docker not installed"
fi

echo ""
echo -e "${BLUE}5. Checking Network Connectivity${NC}"
echo "-----------------------------------"

# Check if API is accessible
if curl -s http://localhost:8001/health &> /dev/null; then
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    check_pass "API is accessible at http://localhost:8001"

    # Check health endpoint
    HEALTH_RESPONSE=$(curl -s http://localhost:8001/health)
    if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        check_pass "Health endpoint returns 'healthy'"
    else
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        check_fail "Health endpoint not responding correctly"
    fi
else
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    check_warn "API not accessible (start with: docker compose up -d mcp-api)"
fi

echo ""
echo -e "${BLUE}6. Checking Environment Configuration${NC}"
echo "-----------------------------------"

if [ -f ".env" ]; then
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    check_pass ".env file exists"

    # Check for required env vars
    if grep -q "DATABASE_URL" .env; then
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        check_pass "DATABASE_URL configured"
    else
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        check_warn "DATABASE_URL not found in .env"
    fi

    if grep -q "SECRET_KEY" .env; then
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        check_pass "SECRET_KEY configured"
    else
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        check_warn "SECRET_KEY not found in .env"
    fi
else
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    check_warn ".env file not found (copy from .env.example)"
fi

echo ""
echo "================================================"
echo -e "${BLUE}Summary${NC}"
echo "================================================"
echo "Checks passed: $CHECKS_PASSED/$TOTAL_CHECKS"
echo ""

if [ $CHECKS_PASSED -eq $TOTAL_CHECKS ]; then
    echo -e "${GREEN}All checks passed! ✓${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Access Swagger UI: http://localhost:8001/docs"
    echo "  2. Run tests: ./test_api.sh"
    echo "  3. View logs: docker logs mcp_api -f"
    exit 0
elif [ $CHECKS_PASSED -gt $((TOTAL_CHECKS / 2)) ]; then
    echo -e "${YELLOW}Setup is partially complete${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review failed checks above"
    echo "  2. Start services: cd .. && docker compose up -d"
    echo "  3. Create .env file: cp .env.example .env"
    exit 1
else
    echo -e "${RED}Setup incomplete${NC}"
    echo ""
    echo "Required actions:"
    echo "  1. Install missing dependencies: pip install -r requirements.txt"
    echo "  2. Start Docker services: cd .. && docker compose up -d"
    echo "  3. Create .env file: cp .env.example .env"
    exit 1
fi
