"""
Test runner script for CampHub backend
Run with: python -m pytest tests/ -v
"""

import sys
import subprocess


def run_tests():
    """Run all tests with coverage report."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--disable-warnings",
    ]

    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def run_specific_test(test_name):
    """Run specific test file or test function."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        f"tests/{test_name}",
        "-v",
        "--tb=short",
    ]

    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        exit_code = run_specific_test(test_name)
    else:
        # Run all tests
        exit_code = run_tests()

    sys.exit(exit_code)
