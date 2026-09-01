#!/bin/bash
# FASE 1 Quick Validation Script
# Checks structure, syntax, and docker-compose before deployment

set -e

echo "=========================================="
echo "FASE 1 Validation"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check function
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅${NC} $1"
        return 0
    else
        echo -e "${RED}❌${NC} $1"
        return 1
    fi
}

# Counter
PASSED=0
FAILED=0

# 1. File structure
echo "1️⃣  Checking file structure..."
files=(
    "cjhirashi-career-api/src/services/redis_client.py"
    "cjhirashi-career-api/src/services/workers/linkedin_worker.py"
    "cjhirashi-career-api/src/services/workers/task_worker.py"
    "cjhirashi-career-api/workers/worker_linkedin.py"
    "cjhirashi-career-api/workers/worker_tasks.py"
    "TESTING_FASE_1.md"
)

for f in "${files[@]}"; do
    if [ -f "$f" ]; then
        echo -e "${GREEN}✅${NC} $f"
        ((PASSED++))
    else
        echo -e "${RED}❌${NC} $f MISSING"
        ((FAILED++))
    fi
done
echo ""

# 2. Python syntax
echo "2️⃣  Checking Python syntax..."
python_files=(
    "cjhirashi-career-api/src/services/redis_client.py"
    "cjhirashi-career-api/src/services/workers/linkedin_worker.py"
    "cjhirashi-career-api/src/services/workers/task_worker.py"
    "cjhirashi-career-api/src/routes/linkedin.py"
    "cjhirashi-career-api/src/services/task_scheduler.py"
)

for f in "${python_files[@]}"; do
    python3 -m py_compile "$f" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅${NC} $f"
        ((PASSED++))
    else
        echo -e "${RED}❌${NC} $f (syntax error)"
        ((FAILED++))
    fi
done
echo ""

# 3. Docker compose validation
echo "3️⃣  Checking docker-compose.yml..."
docker compose config --quiet >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅${NC} docker-compose.yml is valid"
    ((PASSED++))
else
    echo -e "${RED}❌${NC} docker-compose.yml has errors"
    docker compose config 2>&1 | head -10
    ((FAILED++))
fi
echo ""

# 4. Key modifications
echo "4️⃣  Checking key modifications..."

# Check app.py has schedulers disabled
if grep -q "# linkedin_task = asyncio.create_task" cjhirashi-career-api/src/app.py; then
    echo -e "${GREEN}✅${NC} app.py: schedulers disabled (commented out)"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️${NC} app.py: schedulers may not be disabled (check manually)"
fi

# Check linkedin.py has XADD
if grep -q "XADD\|xadd" cjhirashi-career-api/src/routes/linkedin.py; then
    echo -e "${GREEN}✅${NC} linkedin.py: enqueuing integrated (XADD found)"
    ((PASSED++))
else
    echo -e "${RED}❌${NC} linkedin.py: enqueuing not found"
    ((FAILED++))
fi

# Check task_scheduler.py has XADD
if grep -q "_enqueue_task_to_redis" cjhirashi-career-api/src/services/task_scheduler.py; then
    echo -e "${GREEN}✅${NC} task_scheduler.py: enqueuing integrated (_enqueue_task_to_redis found)"
    ((PASSED++))
else
    echo -e "${RED}❌${NC} task_scheduler.py: enqueuing not found"
    ((FAILED++))
fi
echo ""

# 5. Requirements check
echo "5️⃣  Checking requirements.txt..."
if grep -q "redis" cjhirashi-career-api/requirements.txt; then
    echo -e "${GREEN}✅${NC} redis dependency added"
    ((PASSED++))
else
    echo -e "${RED}❌${NC} redis dependency missing"
    ((FAILED++))
fi
echo ""

# 6. Git status
echo "6️⃣  Checking git commits..."
recent_commits=$(git log --oneline -5 | grep -c "FASE 1" || true)
if [ "$recent_commits" -gt 0 ]; then
    echo -e "${GREEN}✅${NC} FASE 1 commits found"
    git log --oneline -3
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️${NC} No recent FASE 1 commits"
fi
echo ""

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $PASSED"
echo -e "${RED}Failed:${NC} $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ FASE 1 structure is ready for testing!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Read TESTING_FASE_1.md for detailed testing guide"
    echo "  2. Run: docker compose up redis worker-linkedin worker-tasks postgres api ..."
    echo "  3. Monitor: docker logs -f worker_linkedin"
    echo "  4. Verify: Create LinkedIn post with scheduled_at in past"
    exit 0
else
    echo -e "${RED}❌ Please fix the above issues before proceeding${NC}"
    exit 1
fi
