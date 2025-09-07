"""
System Check Script - Validates all components before running QA tests
This script checks API keys, connections, dependencies, and system requirements
"""

import os
import sys
import requests
import subprocess
import importlib
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

# Suppress warnings for cleaner output
import warnings
warnings.filterwarnings("ignore")

class CheckStatus(Enum):
    PASS = "✅ PASS"
    FAIL = "❌ FAIL" 
    WARNING = "⚠️ WARNING"
    SKIP = "⏭️ SKIP"

@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str
    details: Optional[str] = None
    fix_suggestion: Optional[str] = None

class SystemHealthChecker:
    """Comprehensive system health checker for QA automation"""
    
    def __init__(self):
        self.results: List[CheckResult] = []
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for the checker"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('system_check.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all system checks and return comprehensive results"""
        print("\n🔍 MONSTER QA AGENT - SYSTEM HEALTH CHECK")
        print("=" * 50)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all check categories
        self._check_python_environment()
        self._check_dependencies()
        self._check_environment_variables()
        self._check_api_connections()
        self._check_chrome_webdriver()
        self._check_system_resources()
        self._check_network_connectivity()
        self._check_file_permissions()
        
        # Generate summary
        summary = self._generate_summary()
        self._display_results()
        
        return summary
    
    def _check_python_environment(self):
        """Check Python version and environment"""
        print("🐍 PYTHON ENVIRONMENT CHECKS")
        print("-" * 30)
        
        # Python version check
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            self.results.append(CheckResult(
                name="Python Version",
                status=CheckStatus.PASS,
                message=f"Python {version.major}.{version.minor}.{version.micro}",
                details="Compatible Python version detected"
            ))
        else:
            self.results.append(CheckResult(
                name="Python Version",
                status=CheckStatus.FAIL,
                message=f"Python {version.major}.{version.minor}.{version.micro}",
                details="Python 3.8+ required",
                fix_suggestion="Upgrade Python to version 3.8 or higher"
            ))
        
        # Virtual environment check
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.results.append(CheckResult(
                name="Virtual Environment",
                status=CheckStatus.PASS,
                message="Virtual environment detected",
                details=f"Using: {sys.prefix}"
            ))
        else:
            self.results.append(CheckResult(
                name="Virtual Environment", 
                status=CheckStatus.WARNING,
                message="No virtual environment detected",
                fix_suggestion="Consider using a virtual environment: python -m venv qa_env"
            ))
        
        # Check current working directory
        cwd = os.getcwd()
        if "LT agent" in cwd or "project1" in cwd:
            self.results.append(CheckResult(
                name="Working Directory",
                status=CheckStatus.PASS,
                message="Correct project directory",
                details=f"Current: {cwd}"
            ))
        else:
            self.results.append(CheckResult(
                name="Working Directory",
                status=CheckStatus.WARNING,
                message="May not be in project directory",
                details=f"Current: {cwd}",
                fix_suggestion="Navigate to the LT agent project directory"
            ))
    
    def _check_dependencies(self):
        """Check required Python packages"""
        print("\n📦 DEPENDENCY CHECKS")
        print("-" * 30)
        
        required_packages = {
            'streamlit': 'Streamlit web framework',
            'selenium': 'Web automation',
            'webdriver_manager': 'Chrome driver management',
            'requests': 'HTTP requests',
            'dotenv': 'Environment variables',  # Changed from 'python-dotenv'
            'PIL': 'Image processing',  # Changed from 'Pillow'
            'groq': 'AI API client',
            'jira': 'Jira integration',
            'bs4': 'HTML parsing',  # Changed from 'beautifulsoup4'
            'pandas': 'Data processing',
            'numpy': 'Numerical computing',
            'cv2': 'Computer vision',  # Changed from 'opencv-python'
            'skimage': 'Image processing',  # Changed from 'scikit-image'
            'matplotlib': 'Plotting'
        }
        
        for package, description in required_packages.items():
            try:
                # Handle special import cases
                if package == 'webdriver_manager':
                    importlib.import_module('webdriver_manager.chrome')
                else:
                    importlib.import_module(package)
                
                # Get version if possible
                try:
                    pkg = importlib.import_module(package)
                    version = getattr(pkg, '__version__', 'Unknown')
                    self.results.append(CheckResult(
                        name=f"Package: {package}",
                        status=CheckStatus.PASS,
                        message=f"Installed (v{version})",
                        details=description
                    ))
                except:
                    self.results.append(CheckResult(
                        name=f"Package: {package}",
                        status=CheckStatus.PASS,
                        message="Installed",
                        details=description
                    ))
            except ImportError:
                # Provide the correct pip install command for the original package name
                pip_name_map = {
                    'dotenv': 'python-dotenv',
                    'PIL': 'Pillow',
                    'bs4': 'beautifulsoup4',
                    'cv2': 'opencv-python',
                    'skimage': 'scikit-image'
                }
                pip_name = pip_name_map.get(package, package)
                
                self.results.append(CheckResult(
                    name=f"Package: {package}",
                    status=CheckStatus.FAIL,
                    message="Not installed",
                    details=description,
                    fix_suggestion=f"Install with: pip install {pip_name}"
                ))
    
    def _check_environment_variables(self):
        """Check environment variables configuration"""
        print("\n🔧 ENVIRONMENT CONFIGURATION")
        print("-" * 30)
        
        # Load .env file if exists
        try:
            from dotenv import load_dotenv
            load_dotenv()
            self.results.append(CheckResult(
                name="Environment File",
                status=CheckStatus.PASS,
                message=".env file loaded successfully"
            ))
        except:
            self.results.append(CheckResult(
                name="Environment File",
                status=CheckStatus.WARNING,
                message="Could not load .env file",
                fix_suggestion="Create a .env file with your API keys"
            ))
        
        required_env_vars = {
            'GROQ_API_KEY': 'Groq AI API key for test generation',
            'FIGMA_ACCESS_TOKEN': 'Figma API token for design access',
            'JIRA_SERVER_URL': 'Jira server URL',
            'JIRA_EMAIL': 'Jira account email',
            'JIRA_API_TOKEN': 'Jira API token',
            'JIRA_PROJECT_KEY': 'Jira project key'
        }
        
        for var, description in required_env_vars.items():
            value = os.getenv(var)
            if value and value.strip():
                # Mask sensitive values
                masked_value = f"{value[:8]}..." if len(value) > 8 else "***"
                self.results.append(CheckResult(
                    name=f"Env Var: {var}",
                    status=CheckStatus.PASS,
                    message=f"Set ({masked_value})",
                    details=description
                ))
            else:
                self.results.append(CheckResult(
                    name=f"Env Var: {var}",
                    status=CheckStatus.FAIL if var in ['GROQ_API_KEY'] else CheckStatus.WARNING,
                    message="Not set or empty",
                    details=description,
                    fix_suggestion=f"Add {var}=your_value to .env file"
                ))
    
    def _check_api_connections(self):
        """Test API connections"""
        print("\n🌐 API CONNECTION TESTS")
        print("-" * 30)
        
        # Test Groq API
        self._test_groq_api()
        # Test Figma API
        self._test_figma_api()
        # Test Jira API
        self._test_jira_api()
    
    def _test_groq_api(self):
        """Test Groq API connection"""
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            self.results.append(CheckResult(
                name="Groq API Connection",
                status=CheckStatus.SKIP,
                message="No API key provided"
            ))
            return
        
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            
            # Use a current model instead of the decommissioned one
            model = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')  # Updated default
            
            # Test with a simple request
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                timeout=10
            )
            
            self.results.append(CheckResult(
                name="Groq API Connection",
                status=CheckStatus.PASS,
                message="API connection successful",
                details=f"Model: {model}"
            ))
            
        except Exception as e:
            self.results.append(CheckResult(
                name="Groq API Connection",
                status=CheckStatus.FAIL,
                message="Connection failed",
                details=str(e),
                fix_suggestion="Check your GROQ_API_KEY and model name. Visit https://console.groq.com/docs/models for current models"
            ))
    
    def _test_figma_api(self):
        """Test Figma API connection"""
        token = os.getenv('FIGMA_ACCESS_TOKEN')
        if not token:
            self.results.append(CheckResult(
                name="Figma API Connection",
                status=CheckStatus.SKIP,
                message="No access token provided"
            ))
            return
        
        try:
            headers = {"X-Figma-Token": token}
            response = requests.get(
                "https://api.figma.com/v1/me",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            user_data = response.json()
            self.results.append(CheckResult(
                name="Figma API Connection",
                status=CheckStatus.PASS,
                message="API connection successful",
                details=f"User: {user_data.get('email', 'Unknown')}"
            ))
            
        except requests.exceptions.Timeout:
            self.results.append(CheckResult(
                name="Figma API Connection",
                status=CheckStatus.FAIL,
                message="Connection timeout",
                fix_suggestion="Check network connectivity to Figma API"
            ))
        except requests.exceptions.HTTPError as e:
            self.results.append(CheckResult(
                name="Figma API Connection",
                status=CheckStatus.FAIL,
                message=f"HTTP Error: {e.response.status_code}",
                details=str(e),
                fix_suggestion="Check your FIGMA_ACCESS_TOKEN validity"
            ))
        except Exception as e:
            self.results.append(CheckResult(
                name="Figma API Connection",
                status=CheckStatus.FAIL,
                message="Connection failed",
                details=str(e)
            ))
    
    def _test_jira_api(self):
        """Test Jira API connection"""
        server_url = os.getenv('JIRA_SERVER_URL')
        email = os.getenv('JIRA_EMAIL')
        token = os.getenv('JIRA_API_TOKEN')
        project_key = os.getenv('JIRA_PROJECT_KEY')
        
        if not all([server_url, email, token]):
            self.results.append(CheckResult(
                name="Jira API Connection",
                status=CheckStatus.SKIP,
                message="Missing Jira configuration"
            ))
            return
        
        try:
            from jira import JIRA
            jira = JIRA(server=server_url, basic_auth=(email, token))
            
            # Test basic connection
            user = jira.myself()
            self.results.append(CheckResult(
                name="Jira API Connection",
                status=CheckStatus.PASS,
                message="API connection successful",
                details=f"User: {user['displayName']}"
            ))
            
            # Test project access if project key provided
            if project_key:
                try:
                    project = jira.project(project_key)
                    self.results.append(CheckResult(
                        name="Jira Project Access",
                        status=CheckStatus.PASS,
                        message=f"Project access confirmed",
                        details=f"Project: {project.name} ({project_key})"
                    ))
                except Exception as e:
                    self.results.append(CheckResult(
                        name="Jira Project Access",
                        status=CheckStatus.FAIL,
                        message="Cannot access project",
                        details=str(e),
                        fix_suggestion=f"Check JIRA_PROJECT_KEY: {project_key}"
                    ))
            
        except Exception as e:
            self.results.append(CheckResult(
                name="Jira API Connection",
                status=CheckStatus.FAIL,
                message="Connection failed",
                details=str(e),
                fix_suggestion="Check Jira credentials and server URL"
            ))
    
    def _check_chrome_webdriver(self):
        """Check Chrome and WebDriver setup"""
        print("\n🚗 CHROME WEBDRIVER CHECKS")
        print("-" * 30)
        
        # Check if Chrome is installed
        try:
            if sys.platform == "darwin":  # macOS
                result = subprocess.run(
                    ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
                    capture_output=True, text=True, timeout=5
                )
            elif sys.platform == "linux":
                result = subprocess.run(
                    ["google-chrome", "--version"],
                    capture_output=True, text=True, timeout=5
                )
            else:  # Windows
                result = subprocess.run(
                    ["chrome", "--version"],
                    capture_output=True, text=True, timeout=5
                )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                self.results.append(CheckResult(
                    name="Chrome Browser",
                    status=CheckStatus.PASS,
                    message="Chrome installed",
                    details=version
                ))
            else:
                raise Exception("Chrome not found")
                
        except Exception:
            self.results.append(CheckResult(
                name="Chrome Browser",
                status=CheckStatus.FAIL,
                message="Chrome not found or not accessible",
                fix_suggestion="Install Google Chrome browser"
            ))
        
        # Test WebDriver setup
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            
            # Test ChromeDriverManager
            driver_path = ChromeDriverManager().install()
            self.results.append(CheckResult(
                name="ChromeDriver Manager",
                status=CheckStatus.PASS,
                message="Driver downloaded/cached",
                details=f"Path: {driver_path}"
            ))
            
            # Test WebDriver initialization
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get("data:text/html,<html><body><h1>Test</h1></body></html>")
            driver.quit()
            
            self.results.append(CheckResult(
                name="WebDriver Initialization",
                status=CheckStatus.PASS,
                message="WebDriver working correctly"
            ))
            
        except Exception as e:
            self.results.append(CheckResult(
                name="WebDriver Setup",
                status=CheckStatus.FAIL,
                message="WebDriver initialization failed",
                details=str(e),
                fix_suggestion="Check Chrome installation and permissions"
            ))
    
    def _check_system_resources(self):
        """Check system resources"""
        print("\n💾 SYSTEM RESOURCE CHECKS")
        print("-" * 30)
        
        # Check available memory
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            
            if available_gb > 2:
                self.results.append(CheckResult(
                    name="Available Memory",
                    status=CheckStatus.PASS,
                    message=f"{available_gb:.1f}GB available",
                    details="Sufficient memory for QA operations"
                ))
            else:
                self.results.append(CheckResult(
                    name="Available Memory",
                    status=CheckStatus.WARNING,
                    message=f"{available_gb:.1f}GB available",
                    details="Low memory may affect performance"
                ))
        except ImportError:
            self.results.append(CheckResult(
                name="Memory Check",
                status=CheckStatus.SKIP,
                message="psutil not available for memory check"
            ))
        
        # Check disk space
        try:
            disk_usage = os.statvfs('.')
            free_gb = (disk_usage.f_frsize * disk_usage.f_available) / (1024**3)
            
            if free_gb > 1:
                self.results.append(CheckResult(
                    name="Disk Space",
                    status=CheckStatus.PASS,
                    message=f"{free_gb:.1f}GB free",
                    details="Sufficient space for screenshots and logs"
                ))
            else:
                self.results.append(CheckResult(
                    name="Disk Space",
                    status=CheckStatus.WARNING,
                    message=f"{free_gb:.1f}GB free",
                    details="Low disk space may cause issues"
                ))
        except:
            self.results.append(CheckResult(
                name="Disk Space Check",
                status=CheckStatus.SKIP,
                message="Could not check disk space"
            ))
    
    def _check_network_connectivity(self):
        """Check network connectivity"""
        print("\n🌍 NETWORK CONNECTIVITY CHECKS")
        print("-" * 30)
        
        test_urls = {
            "Google": "https://www.google.com",
            "Figma API": "https://api.figma.com",
            "Groq API": "https://api.groq.com",
            "GitHub": "https://api.github.com"
        }
        
        for name, url in test_urls.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code in [200, 401, 403]:  # 401/403 mean API is reachable
                    self.results.append(CheckResult(
                        name=f"Connectivity: {name}",
                        status=CheckStatus.PASS,
                        message="Reachable",
                        details=f"Status: {response.status_code}"
                    ))
                else:
                    self.results.append(CheckResult(
                        name=f"Connectivity: {name}",
                        status=CheckStatus.WARNING,
                        message=f"Unexpected status: {response.status_code}"
                    ))
            except requests.exceptions.Timeout:
                self.results.append(CheckResult(
                    name=f"Connectivity: {name}",
                    status=CheckStatus.FAIL,
                    message="Connection timeout",
                    fix_suggestion="Check network connection or firewall"
                ))
            except Exception as e:
                self.results.append(CheckResult(
                    name=f"Connectivity: {name}",
                    status=CheckStatus.FAIL,
                    message="Connection failed",
                    details=str(e)
                ))
    
    def _check_file_permissions(self):
        """Check file permissions"""
        print("\n📁 FILE PERMISSION CHECKS")
        print("-" * 30)
        
        # Check if we can write to temp directory
        import tempfile
        try:
            with tempfile.NamedTemporaryFile() as f:
                f.write(b"test")
            self.results.append(CheckResult(
                name="Temp Directory Write",
                status=CheckStatus.PASS,
                message="Can write to temp directory"
            ))
        except Exception as e:
            self.results.append(CheckResult(
                name="Temp Directory Write", 
                status=CheckStatus.FAIL,
                message="Cannot write to temp directory",
                details=str(e),
                fix_suggestion="Check file system permissions"
            ))
        
        # Check if we can create log files
        try:
            with open("test_log.tmp", "w") as f:
                f.write("test")
            os.remove("test_log.tmp")
            self.results.append(CheckResult(
                name="Log File Creation",
                status=CheckStatus.PASS,
                message="Can create log files"
            ))
        except Exception as e:
            self.results.append(CheckResult(
                name="Log File Creation",
                status=CheckStatus.FAIL,
                message="Cannot create log files",
                details=str(e)
            ))
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary of all checks"""
        summary = {
            'total_checks': len(self.results),
            'passed': sum(1 for r in self.results if r.status == CheckStatus.PASS),
            'failed': sum(1 for r in self.results if r.status == CheckStatus.FAIL),
            'warnings': sum(1 for r in self.results if r.status == CheckStatus.WARNING),
            'skipped': sum(1 for r in self.results if r.status == CheckStatus.SKIP),
            'timestamp': datetime.now().isoformat(),
            'ready_for_testing': True
        }
        
        # Determine if system is ready
        critical_failures = [r for r in self.results if r.status == CheckStatus.FAIL and 
                           any(critical in r.name.lower() for critical in ['python', 'chrome', 'groq'])]
        
        if critical_failures:
            summary['ready_for_testing'] = False
            summary['blocking_issues'] = [r.name for r in critical_failures]
        
        return summary
    
    def _display_results(self):
        """Display formatted results"""
        print("\n" + "=" * 50)
        print("📊 SYSTEM CHECK RESULTS")
        print("=" * 50)
        
        # Group results by status
        passed = [r for r in self.results if r.status == CheckStatus.PASS]
        failed = [r for r in self.results if r.status == CheckStatus.FAIL]
        warnings = [r for r in self.results if r.status == CheckStatus.WARNING]
        skipped = [r for r in self.results if r.status == CheckStatus.SKIP]
        
        # Display summary
        print(f"Total Checks: {len(self.results)}")
        print(f"✅ Passed: {len(passed)}")
        print(f"❌ Failed: {len(failed)}")
        print(f"⚠️ Warnings: {len(warnings)}")
        print(f"⏭️ Skipped: {len(skipped)}")
        print()
        
        # Show failures first
        if failed:
            print("❌ FAILURES (Must Fix)")
            print("-" * 30)
            for result in failed:
                print(f"{result.status.value} {result.name}: {result.message}")
                if result.details:
                    print(f"   Details: {result.details}")
                if result.fix_suggestion:
                    print(f"   💡 Fix: {result.fix_suggestion}")
                print()
        
        # Show warnings
        if warnings:
            print("⚠️ WARNINGS (Recommended to Fix)")
            print("-" * 30)
            for result in warnings:
                print(f"{result.status.value} {result.name}: {result.message}")
                if result.fix_suggestion:
                    print(f"   💡 Suggestion: {result.fix_suggestion}")
                print()
        
        # Final recommendation
        if not failed:
            print("🎉 SYSTEM READY FOR QA TESTING!")
            print("All critical checks passed. You can proceed with running tests.")
        else:
            print("🚫 SYSTEM NOT READY")
            print("Please fix the failures above before running QA tests.")
        
        print("\nFor detailed logs, check: system_check.log")

def main():
    """Main function to run system checks"""
    checker = SystemHealthChecker()
    summary = checker.run_all_checks()
    
    # Save results to file
    with open('system_check_results.json', 'w') as f:
        json.dump({
            'summary': summary,
            'results': [
                {
                    'name': r.name,
                    'status': r.status.value,
                    'message': r.message,
                    'details': r.details,
                    'fix_suggestion': r.fix_suggestion
                } for r in checker.results
            ]
        }, f, indent=2)
    
    # Exit with appropriate code
    if summary['ready_for_testing']:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()