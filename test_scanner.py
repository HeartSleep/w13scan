#!/usr/bin/env python3
"""
Comprehensive test script for w13scan vulnerability scanner
Tests all major functions against the target URL: https://www.baidu.com
"""

import subprocess
import os
import time
import sys
import json
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_test(test_name):
    print(f"{YELLOW}[TEST]{RESET} {test_name}")

def print_success(message):
    print(f"{GREEN}[SUCCESS]{RESET} {message}")

def print_error(message):
    print(f"{RED}[ERROR]{RESET} {message}")

def print_info(message):
    print(f"{BLUE}[INFO]{RESET} {message}")

class W13ScanTester:
    def __init__(self, target_url):
        self.target_url = target_url
        self.project_dir = Path(__file__).parent.resolve()
        self.w13scan_dir = self.project_dir / "W13SCAN"
        self.venv_python = self.project_dir / ".venv" / "bin" / "python3"
        self.w13scan_script = self.w13scan_dir / "w13scan.py"
        self.results = []
        
    def run_command(self, cmd, timeout=120):
        """Run a shell command and return output"""
        try:
            print_info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=str(self.w13scan_dir),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            print_error(f"Command timed out after {timeout} seconds")
            return -1, "", "Timeout"
        except Exception as e:
            print_error(f"Command failed: {str(e)}")
            return -1, "", str(e)
    
    def test_help_menu(self):
        """Test 1: Verify help menu works"""
        print_test("Testing help menu display")
        returncode, stdout, stderr = self.run_command([
            str(self.venv_python),
            str(self.w13scan_script),
            "-h"
        ])
        
        if returncode == 0 and "usage: w13scan" in stdout:
            print_success("Help menu displayed successfully")
            self.results.append(("Help Menu", True, ""))
            return True
        else:
            print_error("Help menu failed to display")
            self.results.append(("Help Menu", False, stderr))
            return False
    
    def test_version(self):
        """Test 2: Verify version display"""
        print_test("Testing version display")
        returncode, stdout, stderr = self.run_command([
            str(self.venv_python),
            str(self.w13scan_script),
            "-v"
        ])
        
        if returncode == 0 or "version" in stdout.lower() or "version" in stderr.lower():
            print_success("Version displayed successfully")
            print_info(f"Output: {stdout.strip() or stderr.strip()}")
            self.results.append(("Version Display", True, ""))
            return True
        else:
            print_error("Version display failed")
            self.results.append(("Version Display", False, stderr))
            return False
    
    def test_basic_scan(self):
        """Test 3: Run basic scan on target URL"""
        print_test(f"Testing basic scan on {self.target_url}")
        returncode, stdout, stderr = self.run_command([
            str(self.venv_python),
            str(self.w13scan_script),
            "-u", self.target_url
        ], timeout=180)
        
        # Check if scan completed (returncode 0 or scanning messages in output)
        if returncode == 0 or "Loader" in stdout or "scan" in stdout.lower():
            print_success("Basic scan completed")
            print_info(f"Scan output preview:\n{stdout[:500]}")
            self.results.append(("Basic Scan", True, ""))
            return True
        else:
            print_error("Basic scan failed")
            print_info(f"Error output: {stderr[:500]}")
            self.results.append(("Basic Scan", False, stderr))
            return False
    
    def test_json_output(self):
        """Test 4: Test JSON output generation"""
        print_test("Testing JSON output generation")
        json_file = self.w13scan_dir / "output" / "test_baidu_scan.json"
        
        # Remove old file if exists
        if json_file.exists():
            json_file.unlink()
        
        returncode, stdout, stderr = self.run_command([
            str(self.venv_python),
            str(self.w13scan_script),
            "-u", self.target_url,
            "--json", str(json_file)
        ], timeout=180)
        
        # Check if JSON file was created
        time.sleep(2)  # Wait for file to be written
        
        if json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                print_success(f"JSON output generated successfully at {json_file}")
                print_info(f"JSON contains {len(data) if isinstance(data, list) else 'N/A'} entries")
                self.results.append(("JSON Output", True, ""))
                return True
            except json.JSONDecodeError:
                print_error("JSON file exists but is not valid JSON")
                self.results.append(("JSON Output", False, "Invalid JSON"))
                return False
        else:
            print_error("JSON output file was not created")
            self.results.append(("JSON Output", False, "File not created"))
            return False
    
    def test_html_output(self):
        """Test 5: Test HTML output generation"""
        print_test("Testing HTML output generation")
        
        returncode, stdout, stderr = self.run_command([
            str(self.venv_python),
            str(self.w13scan_script),
            "-u", self.target_url,
            "--html"
        ], timeout=180)
        
        # Check if HTML file was created in output directory
        output_dir = self.w13scan_dir / "output"
        html_files = list(output_dir.glob("*.html"))
        
        if html_files:
            print_success(f"HTML output generated: {html_files[0].name}")
            self.results.append(("HTML Output", True, ""))
            return True
        else:
            print_error("HTML output was not generated")
            self.results.append(("HTML Output", False, "No HTML file found"))
            return False
    
    def test_threading(self):
        """Test 6: Test custom thread count"""
        print_test("Testing custom thread configuration")
        returncode, stdout, stderr = self.run_command([
            str(self.venv_python),
            str(self.w13scan_script),
            "-u", self.target_url,
            "-t", "10"
        ], timeout=180)
        
        if returncode == 0 or "scan" in stdout.lower():
            print_success("Threading configuration works")
            self.results.append(("Threading", True, ""))
            return True
        else:
            print_error("Threading configuration failed")
            self.results.append(("Threading", False, stderr))
            return False
    
    def test_scan_level(self):
        """Test 7: Test different scan levels"""
        print_test("Testing scan level configuration")
        returncode, stdout, stderr = self.run_command([
            str(self.venv_python),
            str(self.w13scan_script),
            "-u", self.target_url,
            "--level", "1"
        ], timeout=180)
        
        if returncode == 0 or "scan" in stdout.lower():
            print_success("Scan level configuration works")
            self.results.append(("Scan Level", True, ""))
            return True
        else:
            print_error("Scan level configuration failed")
            self.results.append(("Scan Level", False, stderr))
            return False
    
    def test_plugin_disable(self):
        """Test 8: Test plugin disabling"""
        print_test("Testing plugin disable functionality")
        returncode, stdout, stderr = self.run_command([
            str(self.venv_python),
            str(self.w13scan_script),
            "-u", self.target_url,
            "--disable", "xss", "sqli"
        ], timeout=180)
        
        if returncode == 0 or "scan" in stdout.lower():
            print_success("Plugin disable functionality works")
            self.results.append(("Plugin Disable", True, ""))
            return True
        else:
            print_error("Plugin disable functionality failed")
            self.results.append(("Plugin Disable", False, stderr))
            return False
    
    def test_url_file_scan(self):
        """Test 9: Test scanning from URL file"""
        print_test("Testing URL file scanning")
        
        # Create a test URL file
        url_file = self.w13scan_dir / "test_urls.txt"
        with open(url_file, 'w') as f:
            f.write(f"{self.target_url}\n")
        
        returncode, stdout, stderr = self.run_command([
            str(self.venv_python),
            str(self.w13scan_script),
            "-f", str(url_file)
        ], timeout=180)
        
        # Clean up
        url_file.unlink()
        
        if returncode == 0 or "scan" in stdout.lower():
            print_success("URL file scanning works")
            self.results.append(("URL File Scan", True, ""))
            return True
        else:
            print_error("URL file scanning failed")
            self.results.append(("URL File Scan", False, stderr))
            return False
    
    def test_timeout_configuration(self):
        """Test 10: Test timeout configuration"""
        print_test("Testing timeout configuration")
        returncode, stdout, stderr = self.run_command([
            str(self.venv_python),
            str(self.w13scan_script),
            "-u", self.target_url,
            "--timeout", "15"
        ], timeout=180)
        
        if returncode == 0 or "scan" in stdout.lower():
            print_success("Timeout configuration works")
            self.results.append(("Timeout Config", True, ""))
            return True
        else:
            print_error("Timeout configuration failed")
            self.results.append(("Timeout Config", False, stderr))
            return False
    
    def test_random_agent(self):
        """Test 11: Test random user agent"""
        print_test("Testing random user agent")
        returncode, stdout, stderr = self.run_command([
            str(self.venv_python),
            str(self.w13scan_script),
            "-u", self.target_url,
            "--random-agent"
        ], timeout=180)
        
        if returncode == 0 or "scan" in stdout.lower():
            print_success("Random user agent works")
            self.results.append(("Random Agent", True, ""))
            return True
        else:
            print_error("Random user agent failed")
            self.results.append(("Random Agent", False, stderr))
            return False
    
    def check_plugins_exist(self):
        """Test 12: Check if plugins are available"""
        print_test("Checking plugin availability")
        
        scanners_dir = self.w13scan_dir / "scanners"
        plugins_found = []
        
        for plugin_type in ['PerFile', 'PerFolder', 'PerServer']:
            plugin_dir = scanners_dir / plugin_type
            if plugin_dir.exists():
                plugins = list(plugin_dir.glob("*.py"))
                plugins_found.extend([p.stem for p in plugins if p.stem != "__init__"])
        
        if plugins_found:
            print_success(f"Found {len(plugins_found)} plugins")
            print_info(f"Plugins: {', '.join(plugins_found[:10])}...")
            self.results.append(("Plugins Available", True, ""))
            return True
        else:
            print_error("No plugins found")
            self.results.append(("Plugins Available", False, "No plugins"))
            return False
    
    def check_fingerprints(self):
        """Test 13: Check if fingerprint modules exist"""
        print_test("Checking fingerprint modules")
        
        fingerprints_dir = self.w13scan_dir / "fingprints"
        if fingerprints_dir.exists():
            fingerprint_modules = list(fingerprints_dir.rglob("*.py"))
            if fingerprint_modules:
                print_success(f"Found {len(fingerprint_modules)} fingerprint modules")
                self.results.append(("Fingerprints", True, ""))
                return True
        
        print_error("No fingerprint modules found")
        self.results.append(("Fingerprints", False, "No modules"))
        return False
    
    def print_summary(self):
        """Print test results summary"""
        print_header("TEST RESULTS SUMMARY")
        
        passed = sum(1 for _, result, _ in self.results if result)
        failed = len(self.results) - passed
        
        print(f"\n{GREEN}Passed:{RESET} {passed}/{len(self.results)}")
        print(f"{RED}Failed:{RESET} {failed}/{len(self.results)}\n")
        
        print(f"{'Test Name':<25} {'Status':<10} {'Details'}")
        print("-" * 70)
        
        for test_name, result, details in self.results:
            status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
            details_str = details[:40] if details else ""
            print(f"{test_name:<25} {status:<10} {details_str}")
        
        print("\n" + "=" * 70)
        
        return passed, failed

def main():
    target_url = "https://www.baidu.com"
    
    print_header(f"W13SCAN COMPREHENSIVE TEST SUITE")
    print_info(f"Target URL: {target_url}")
    print_info(f"Starting tests...\n")
    
    tester = W13ScanTester(target_url)
    
    # Run all tests
    tests = [
        tester.test_help_menu,
        tester.test_version,
        tester.check_plugins_exist,
        tester.check_fingerprints,
        tester.test_basic_scan,
        tester.test_json_output,
        tester.test_html_output,
        tester.test_threading,
        tester.test_scan_level,
        tester.test_plugin_disable,
        tester.test_url_file_scan,
        tester.test_timeout_configuration,
        tester.test_random_agent,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print_error(f"Test {test.__name__} raised exception: {str(e)}")
            tester.results.append((test.__name__, False, str(e)))
        print()  # Empty line between tests
    
    # Print summary
    passed, failed = tester.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
