# run_tests.py
"""
Run all tests with options
"""

import sys
import subprocess
import argparse

def run_tests(args):
    """Run tests with arguments"""
    cmd = ["pytest"]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.coverage:
        cmd.append("--cov=src")
        cmd.append("--cov-report=html")
        cmd.append("--cov-report=term")
    
    if args.specific:
        cmd.append(args.specific)
    else:
        cmd.append("tests/")
    
    if args.failfast:
        cmd.append("--maxfail=1")
    
    if args.markers:
        cmd.append("-m")
        cmd.append(args.markers)
    
    print(f"Running: {' '.join(cmd)}")
    return subprocess.call(cmd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-c", "--coverage", action="store_true")
    parser.add_argument("-f", "--failfast", action="store_true")
    parser.add_argument("-s", "--specific", help="Specific test file or directory")
    parser.add_argument("-m", "--markers", help="Run tests with specific markers")
    
    args = parser.parse_args()
    sys.exit(run_tests(args))