#!/usr/bin/env python3
"""
Test runner script for FirmableWebAI
Run all tests or specific test suites
"""

import sys
import os
import argparse
import subprocess


def run_command(cmd):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run FirmableWebAI tests")
    parser.add_argument(
        "--suite",
        choices=["all", "unit", "integration", "api", "scraper", "llm", "db"],
        default="all",
        help="Test suite to run"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--markers",
        "-m",
        help="Run tests with specific markers (e.g., 'not slow')"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = "python3 -m pytest"
    
    # Add test path based on suite
    if args.suite == "all":
        cmd += " tests/"
    elif args.suite == "unit":
        cmd += " tests/unit/"
    elif args.suite == "integration":
        cmd += " tests/integration/"
    elif args.suite == "api":
        cmd += " tests/unit/test_api_endpoints.py"
    elif args.suite == "scraper":
        cmd += " tests/unit/test_scraper.py"
    elif args.suite == "llm":
        cmd += " tests/unit/test_llm_client.py"
    elif args.suite == "db":
        cmd += " tests/unit/test_database_client.py"
    
    # Add coverage if requested
    if args.coverage:
        cmd += " --cov=app --cov=models --cov-report=term-missing --cov-report=html"
    
    # Add verbose if requested
    if args.verbose:
        cmd += " -v"
    
    # Add markers if specified
    if args.markers:
        cmd += f" -m '{args.markers}'"
    
    # Add color output
    cmd += " --color=yes"
    
    print("=" * 60)
    print("FirmableWebAI Test Runner")
    print("=" * 60)
    print(f"Suite: {args.suite}")
    print(f"Coverage: {args.coverage}")
    print(f"Verbose: {args.verbose}")
    if args.markers:
        print(f"Markers: {args.markers}")
    print("=" * 60)
    
    # Check if pytest is installed
    check_cmd = "python3 -m pytest --version"
    if run_command(check_cmd) != 0:
        print("\nError: pytest not installed!")
        print("Install with: pip install pytest pytest-asyncio pytest-cov pytest-mock")
        return 1
    
    # Run the tests
    print("\nRunning tests...\n")
    exit_code = run_command(cmd)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    # Show coverage report location if generated
    if args.coverage and exit_code == 0:
        print("\n📊 Coverage report generated:")
        print("   - Terminal: See above")
        print("   - HTML: Open htmlcov/index.html in your browser")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
