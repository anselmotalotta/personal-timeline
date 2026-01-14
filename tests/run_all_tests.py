#!/usr/bin/env python3
"""
Comprehensive test runner for the Personal Timeline application
Runs all test suites and provides detailed reporting
"""
import subprocess
import sys
import time
import json
import os
from pathlib import Path

class TestRunner:
    def __init__(self):
        self.results = {
            "unit": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
            "integration": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
            "component": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
            "e2e": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
        }
        self.start_time = time.time()
    
    def run_test_suite(self, suite_name, test_path):
        """Run a specific test suite and capture results"""
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING {suite_name.upper()} TESTS")
        print(f"{'='*60}")
        
        try:
            # Run pytest with verbose output
            cmd = [
                sys.executable, "-m", "pytest", 
                test_path,
                "-v",
                "--tb=short"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Parse results
            self._parse_pytest_output(suite_name, result.stdout, result.stderr, result.returncode)
            
        except subprocess.TimeoutExpired:
            print(f"❌ {suite_name} tests timed out after 5 minutes")
            self.results[suite_name]["errors"].append("Test suite timed out")
        except Exception as e:
            print(f"❌ Error running {suite_name} tests: {e}")
            self.results[suite_name]["errors"].append(str(e))
    
    def _parse_pytest_output(self, suite_name, stdout, stderr, returncode):
        """Parse pytest output to extract test results"""
        lines = stdout.split('\n')
        
        for line in lines:
            if "passed" in line and "failed" in line:
                # Parse summary line like "5 passed, 2 failed, 1 skipped"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        try:
                            self.results[suite_name]["passed"] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
                    elif part == "failed" and i > 0:
                        try:
                            self.results[suite_name]["failed"] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
                    elif part == "skipped" and i > 0:
                        try:
                            self.results[suite_name]["skipped"] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
        
        # Capture errors from stderr
        if stderr:
            self.results[suite_name]["errors"].append(stderr[:500])  # Limit error length
    
    def _parse_json_report(self, suite_name, json_report):
        """Parse JSON report for detailed test information"""
        if "summary" in json_report:
            summary = json_report["summary"]
            self.results[suite_name]["passed"] = summary.get("passed", 0)
            self.results[suite_name]["failed"] = summary.get("failed", 0)
            self.results[suite_name]["skipped"] = summary.get("skipped", 0)
        
        # Extract failed test details
        if "tests" in json_report:
            for test in json_report["tests"]:
                if test.get("outcome") == "failed":
                    error_msg = f"{test.get('nodeid', 'Unknown test')}: {test.get('call', {}).get('longrepr', 'Unknown error')}"
                    self.results[suite_name]["errors"].append(error_msg[:200])  # Limit length
    
    def check_prerequisites(self):
        """Check that required services are running"""
        print("🔍 CHECKING PREREQUISITES")
        print("-" * 40)
        
        # Check if API is running
        try:
            import requests
            response = requests.get("http://localhost:8086/health", timeout=5)
            if response.status_code == 200:
                print("✅ API service is running")
            else:
                print(f"⚠️  API service returned status {response.status_code}")
        except Exception as e:
            print(f"❌ API service not accessible: {e}")
            print("   Make sure to run: docker compose up -d")
            return False
        
        # Check if frontend is running
        try:
            response = requests.get("http://localhost:52692", timeout=5)
            if response.status_code == 200:
                print("✅ Frontend service is running")
            else:
                print(f"⚠️  Frontend service returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Frontend service not accessible: {e}")
            return False
        
        # Check if pytest is available
        try:
            subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                         capture_output=True, check=True)
            print("✅ Pytest is available")
        except subprocess.CalledProcessError:
            print("❌ Pytest not available. Install with: pip install pytest")
            return False
        
        return True
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 PERSONAL TIMELINE APPLICATION TEST SUITE")
        print("=" * 60)
        
        if not self.check_prerequisites():
            print("\n❌ Prerequisites not met. Please fix the issues above and try again.")
            return False
        
        # Define test suites
        test_suites = [
            ("unit", "tests/unit/"),
            ("integration", "tests/integration/"),
            ("component", "tests/component/"),
            ("e2e", "tests/e2e/")
        ]
        
        # Run each test suite
        for suite_name, test_path in test_suites:
            if os.path.exists(test_path):
                self.run_test_suite(suite_name, test_path)
            else:
                print(f"⚠️  Skipping {suite_name} tests - directory not found: {test_path}")
        
        # Generate final report
        self.generate_report()
        
        return self.is_success()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        total_time = time.time() - self.start_time
        
        print(f"\n{'='*60}")
        print("📊 COMPREHENSIVE TEST REPORT")
        print(f"{'='*60}")
        
        total_passed = sum(suite["passed"] for suite in self.results.values())
        total_failed = sum(suite["failed"] for suite in self.results.values())
        total_skipped = sum(suite["skipped"] for suite in self.results.values())
        total_tests = total_passed + total_failed + total_skipped
        
        print(f"⏱️  Total execution time: {total_time:.1f} seconds")
        print(f"📈 Overall results:")
        print(f"   ✅ Passed: {total_passed}")
        print(f"   ❌ Failed: {total_failed}")
        print(f"   ⏭️  Skipped: {total_skipped}")
        print(f"   📊 Total: {total_tests}")
        
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"   🎯 Success rate: {success_rate:.1f}%")
        
        # Detailed results by suite
        print(f"\n📋 Results by test suite:")
        for suite_name, results in self.results.items():
            suite_total = results["passed"] + results["failed"] + results["skipped"]
            if suite_total > 0:
                suite_success = (results["passed"] / suite_total) * 100
                print(f"   {suite_name.upper():12} | ✅ {results['passed']:2d} | ❌ {results['failed']:2d} | ⏭️ {results['skipped']:2d} | 🎯 {suite_success:5.1f}%")
        
        # Show critical errors
        critical_errors = []
        for suite_name, results in self.results.items():
            if results["failed"] > 0 or results["errors"]:
                critical_errors.extend(results["errors"])
        
        if critical_errors:
            print(f"\n🚨 CRITICAL ISSUES TO ADDRESS:")
            print("-" * 40)
            for i, error in enumerate(critical_errors[:10], 1):  # Show first 10 errors
                print(f"{i:2d}. {error}")
            
            if len(critical_errors) > 10:
                print(f"    ... and {len(critical_errors) - 10} more issues")
        
        # Application status assessment
        print(f"\n🏥 APPLICATION HEALTH ASSESSMENT:")
        print("-" * 40)
        
        if total_failed == 0:
            print("🎉 EXCELLENT: All tests passing! Application is fully functional.")
        elif total_failed <= 2:
            print("✅ GOOD: Minor issues detected. Application is mostly functional.")
        elif total_failed <= 5:
            print("⚠️  FAIR: Some issues detected. Application has functional problems.")
        else:
            print("❌ POOR: Many issues detected. Application needs significant fixes.")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        print("-" * 40)
        
        if self.results["unit"]["failed"] > 0:
            print("• Fix unit test failures - these indicate core logic problems")
        
        if self.results["integration"]["failed"] > 0:
            print("• Fix integration test failures - these indicate API/service problems")
        
        if self.results["component"]["failed"] > 0:
            print("• Fix component test failures - these indicate UI problems")
        
        if self.results["e2e"]["failed"] > 0:
            print("• Fix end-to-end test failures - these indicate user experience problems")
        
        if total_failed == 0:
            print("• Great job! Consider adding more tests for edge cases")
        
        # Save detailed report
        self.save_detailed_report()
    
    def save_detailed_report(self):
        """Save detailed report to file"""
        report_data = {
            "timestamp": time.time(),
            "execution_time": time.time() - self.start_time,
            "results": self.results,
            "summary": {
                "total_passed": sum(suite["passed"] for suite in self.results.values()),
                "total_failed": sum(suite["failed"] for suite in self.results.values()),
                "total_skipped": sum(suite["skipped"] for suite in self.results.values()),
            }
        }
        
        with open("test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: test_report.json")
    
    def is_success(self):
        """Check if all tests passed"""
        total_failed = sum(suite["failed"] for suite in self.results.values())
        return total_failed == 0
    
    def cleanup(self):
        """Clean up temporary files"""
        for suite_name in self.results.keys():
            json_file = f"test_results_{suite_name}.json"
            if os.path.exists(json_file):
                os.remove(json_file)

def main():
    """Main test runner entry point"""
    runner = TestRunner()
    
    try:
        success = runner.run_all_tests()
        exit_code = 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        exit_code = 130
    except Exception as e:
        print(f"\n\n❌ Test runner failed: {e}")
        exit_code = 1
    finally:
        runner.cleanup()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()