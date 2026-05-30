#!/usr/bin/env bash
# ============================================================
# DevPulse Performance Test Script
# Runs all 3 wrk benchmark scenarios and prints a summary.
#
# Prerequisites:
#   - wrk installed (https://github.com/wg/wrk)
#   - Backend running on http://localhost:8000
#
# Usage:
#   chmod +x scripts/perf-test.sh
#   bash scripts/perf-test.sh
# ============================================================

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
DURATION="${DURATION:-30s}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_FILE="${SCRIPT_DIR}/../docs/perf-report-0.5.0.md"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ---- Helpers ----
print_header() {
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
}

print_result() {
    local scenario="$1"
    local target_p99="$2"
    local errors="$3"
    local p99="$4"
    local result="PASS"

    if [ "$errors" -gt 0 ] 2>/dev/null; then
        result="${RED}FAIL${NC}"
    elif [ -n "$p99" ] && [ "$p99" != "N/A" ]; then
        # Compare numerically if possible
        if awk "BEGIN {exit !($p99 > $target_p99)}" 2>/dev/null; then
            result="${YELLOW}WARN${NC} (P99 exceeded target)"
        else
            result="${GREEN}PASS${NC}"
        fi
    fi

    printf "  %-20s | errors=%-6s | P99=%-10s | target_p99=%-10s | %b\n" \
        "$scenario" "$errors" "${p99:-N/A}" "${target_p99}ms" "$result"
}

check_prereqs() {
    print_header "Pre-flight Checks"

    if ! command -v wrk &>/dev/null; then
        echo -e "${RED}[ERROR] wrk is not installed. Please install it first:${NC}"
        echo "  macOS:  brew install wrk"
        echo "  Ubuntu: sudo apt-get install wrk"
        echo "  Build:  https://github.com/wg/wrk"
        exit 1
    fi
    echo -e "${GREEN}[OK] wrk found: $(wrk --version 2>&1 | head -1)${NC}"

    if ! curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health" | grep -q "200"; then
        echo -e "${RED}[ERROR] Backend is not responding at ${BASE_URL}/health${NC}"
        echo "  Please start the backend first:"
        echo "  cd backend && uvicorn devpulse.main:app --host 0.0.0.0 --port 8000"
        exit 1
    fi
    echo -e "${GREEN}[OK] Backend is alive at ${BASE_URL}/health${NC}"
    echo ""
}

# ---- Benchmark Functions ----
run_scenario_1() {
    print_header "Scenario 1: Health Endpoint (1000 concurrency)"
    echo "Command: wrk -t4 -c1000 -d${DURATION} ${BASE_URL}/health"
    echo "Target:  0 errors, P99 < 100ms"
    echo ""

    wrk -t4 -c1000 -d"${DURATION}" "${BASE_URL}/health" 2>&1 || true

    echo ""
    echo -e "${YELLOW}  => Check output above. Verify 0 socket errors and P99 < 100ms.${NC}"
}

run_scenario_2() {
    print_header "Scenario 2: Trending List (500 concurrency)"
    echo "Command: wrk -t4 -c500 -d${DURATION} ${BASE_URL}/api/v1/repos/trending"
    echo "Target:  0 5xx, P99 < 1000ms"
    echo ""

    wrk -t4 -c500 -d"${DURATION}" "${BASE_URL}/api/v1/repos/trending" 2>&1 || true

    echo ""
    echo -e "${YELLOW}  => Check output above. Verify 0 Non-2xx/3xx responses and P99 < 1s.${NC}"
}

run_scenario_3() {
    print_header "Scenario 3: Recommended Endpoint (100 concurrency)"
    echo "Command: wrk -t2 -c100 -d${DURATION} ${BASE_URL}/api/v1/repos/recommended"
    echo "Target:  0 5xx, P99 < 2000ms"
    echo ""

    wrk -t2 -c100 -d"${DURATION}" "${BASE_URL}/api/v1/repos/recommended" 2>&1 || true

    echo ""
    echo -e "${YELLOW}  => Check output above. Verify 0 Non-2xx/3xx responses and P99 < 2s.${NC}"
}

# ---- Summary ----
print_summary() {
    print_header "Performance Test Summary"
    echo -e "  ${CYAN}Scenario                 Concurrency   Target P99   Result${NC}"
    echo "  -----------------------  ------------  -----------  ------"
    echo "  Health endpoint          1000          < 100ms      (see output above)"
    echo "  Trending list            500           < 1000ms     (see output above)"
    echo "  Recommended endpoint     100           < 2000ms     (see output above)"
    echo ""
    echo -e "  ${YELLOW}Report template: ${REPORT_FILE}${NC}"
    echo -e "  ${YELLOW}Fill in actual numbers from the runs above into the report.${NC}"
    echo ""
}

# ---- Main ----
main() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║        DevPulse Phase 5 — Performance Test Suite        ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"

    check_prereqs
    run_scenario_1
    run_scenario_2
    run_scenario_3
    print_summary

    echo -e "${GREEN}[DONE] All 3 scenarios completed.${NC}"
    echo "Review the output above and fill in docs/perf-report-0.5.0.md."
}

main "$@"
