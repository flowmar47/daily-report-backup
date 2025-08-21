#!/bin/bash
# Claude Hooks Configuration for OhmsAlertsReports/daily-report
# Project-specific settings for Claude Code hooks

# Hook Controls
CLAUDE_HOOKS_ENABLED=true
CLAUDE_HOOKS_DEBUG=0
CLAUDE_HOOKS_TIMING=1

# Python-specific settings
CLAUDE_HOOKS_PYTHON_ENABLED=true
CLAUDE_HOOKS_PYTHON_USE_RUFF=true
CLAUDE_HOOKS_PYTHON_USE_BLACK=true
CLAUDE_HOOKS_PYTHON_USE_MYPY=true

# Shell script settings
CLAUDE_HOOKS_SHELL_ENABLED=true
CLAUDE_HOOKS_SHELL_USE_SHELLCHECK=true

# Test settings
CLAUDE_HOOKS_TEST_ENABLED=true
CLAUDE_HOOKS_TEST_MODE=focused  # focused, package, all

# NTFY Notifications (optional)
NTFY_ENABLED=false
NTFY_TOPIC=ohms-alerts-daily-report
NTFY_PRIORITY=low

# Project-specific lint commands
# The hooks will look for these patterns:
# 1. make lint (if Makefile exists with lint target)
# 2. scripts/lint.sh (if exists)
# 3. Fall back to language-specific linting

# Project-specific test commands
# The hooks will look for these patterns:
# 1. make test (if Makefile exists with test target)
# 2. scripts/test.sh (if exists)
# 3. Fall back to language-specific testing

# Financial automation specific settings
# Disable hooks for sensitive files that contain credentials
CLAUDE_HOOKS_SKIP_SENSITIVE=true

# Files to always skip (in addition to .claude-hooks-ignore)
CLAUDE_HOOKS_SKIP_PATTERNS=(
    "*.env"
    "*.key"
    "*credentials*"
    "*session*"
    "browser_sessions/**"
    "logs/**"
)

# Custom validation for financial data files
validate_financial_data() {
    local file="$1"
    
    # Skip validation for test files
    if [[ "$file" == *test* ]]; then
        return 0
    fi
    
    # Check for prohibited synthetic data patterns
    if grep -q "FAKE\|MOCK\|SYNTHETIC\|PLACEHOLDER" "$file" 2>/dev/null; then
        echo "[ERROR] Prohibited synthetic data detected in $file" >&2
        return 1
    fi
    
    return 0
}

# Export custom validation function
export -f validate_financial_data