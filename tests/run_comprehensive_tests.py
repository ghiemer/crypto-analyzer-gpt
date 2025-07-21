"""
Comprehensive test runner and configuration for crypto-analyzer-gpt
Tests all optimized modules with detailed reporting
"""

import pytest
import sys
import os
import asyncio
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_comprehensive_tests():
    """Run all comprehensive tests with detailed reporting"""
    
    test_files = [
        'test_alerts_actual.py',  # Working alert tests
        'test_core_indicators.py',
        'test_core_security.py',
        'test_core_cache.py',
        'test_services_simple_alerts.py',
        'test_utils_comprehensive.py', 
        'test_workers_comprehensive.py',
        'test_helpers_comprehensive.py'
    ]    # Configure pytest arguments for comprehensive testing
    pytest_args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "--disable-warnings",  # Reduce noise from warnings
        f"--rootdir={Path(__file__).parent.parent}",  # Set root directory
        "--maxfail=5",  # Stop after 5 failures to avoid spam
        "--durations=10",  # Show slowest 10 tests
    ]
    
    # Add coverage if available
    try:
        import pytest_cov
        pytest_args.extend([
            "--cov=app",  # Coverage for app directory
            "--cov-report=term-missing",  # Show missing lines
            "--cov-report=html:htmlcov",  # HTML coverage report
            "--cov-fail-under=70",  # Require at least 70% coverage
        ])
    except ImportError:
        print("⚠️  pytest-cov not available, skipping coverage reporting")
    
    # Add async support
    pytest_args.extend([
        "--asyncio-mode=auto",  # Auto-detect async tests
    ])
    
    # Add all test files
    for test_file in test_files:
        test_path = Path(__file__).parent / test_file
        if test_path.exists():
            pytest_args.append(str(test_path))
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    print("🚀 Starting comprehensive test suite...")
    print("=" * 80)
    
    # Run tests
    exit_code = pytest.main(pytest_args)
    
    print("=" * 80)
    if exit_code == 0:
        print("✅ All tests passed successfully!")
    else:
        print(f"❌ Tests failed with exit code: {exit_code}")
    
    return exit_code

def run_quick_tests():
    """Run a quick subset of tests for fast feedback"""
    
    test_path = Path(__file__).parent / "test_alerts_actual.py"
    
    quick_args = [
        "-v",
        "--tb=line",  # Line-only traceback
        "--maxfail=3",  # Stop after 3 failures
        "-x",  # Stop on first failure
        "--disable-warnings",
        f"--rootdir={Path(__file__).parent.parent}",
        # Run only working tests
        f"{test_path}::TestEnhancedAlertSystem::test_initialization",
    ]
    
    print("⚡ Running quick test suite...")
    return pytest.main(quick_args)

def run_module_tests(module_name):
    """Run tests for a specific module"""
    
    module_test_map = {
        "alerts": "test_alerts_actual.py",
        "indicators": "test_core_indicators.py",
        "security": "test_core_security.py",
        "cache": "test_core_cache.py",
        "simple_alerts": "test_services_simple_alerts.py",
        "utils": "test_utils_comprehensive.py",
        "workers": "test_workers_comprehensive.py",
        "helpers": "test_helpers_comprehensive.py",
    }
    
    test_file = module_test_map.get(module_name)
    if not test_file:
        print(f"❌ Unknown module: {module_name}")
        print(f"Available modules: {', '.join(module_test_map.keys())}")
        return 1
    
    test_path = Path(__file__).parent / test_file
    if not test_path.exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    args = [
        "-v",
        "--tb=short",
        "--disable-warnings",
        f"--rootdir={Path(__file__).parent.parent}",
        str(test_path)
    ]
    
    print(f"🔍 Running tests for module: {module_name}")
    return pytest.main(args)

def validate_test_environment():
    """Validate that the test environment is properly set up"""
    
    print("🔧 Validating test environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required, found {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check required packages
    required_packages = [
        "pytest", "pytest-asyncio", "pandas", "numpy"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install " + " ".join(missing_packages))
        return False
    
    # Check app modules can be imported
    app_modules = [
        "app.core.alerts",
        "app.core.indicators", 
        "app.core.security",
        "app.core.cache",
        "app.services.simple_alerts",
        "app.utils.validation",
        "app.workers.alert_worker",
        "app.helpers.cache_helpers",
        "app.helpers.error_handlers",
        "app.helpers.response_helpers"
    ]
    
    import_errors = []
    for module in app_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"⚠️  {module} (import warning: {e})")
            import_errors.append(module)
    
    if import_errors:
        print(f"\n⚠️  Some modules had import warnings: {len(import_errors)}")
        print("Tests may still run but some features might be mocked")
    
    print("✅ Test environment validation complete")
    return True

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "validate":
            validate_test_environment()
        elif command == "quick":
            exit_code = run_quick_tests()
            sys.exit(exit_code)
        elif command == "full":
            if not validate_test_environment():
                sys.exit(1)
            exit_code = run_comprehensive_tests()
            sys.exit(exit_code)
        elif command in ["alerts", "indicators", "security", "cache", 
                        "simple_alerts", "utils", "workers", "helpers"]:
            exit_code = run_module_tests(command)
            sys.exit(exit_code)
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: validate, quick, full, <module_name>")
            sys.exit(1)
    else:
        # Default: run comprehensive tests
        if not validate_test_environment():
            sys.exit(1)
        exit_code = run_comprehensive_tests()
        sys.exit(exit_code)
