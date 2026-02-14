import sys
import pkg_resources
import importlib

def check_python_version():
    print(f"Python Version: {sys.version}")
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required.")
        return False
    print("✅ Python version OK")
    return True

def check_dependencies():
    required = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'pydantic_settings',
        'google.generativeai',
        'google.cloud.aiplatform',
        'sqlalchemy',
        'chromadb',
        'python-dotenv'
    ]
    
    missing = []
    print("\nChecking dependencies:")
    for package in required:
        try:
            importlib.import_module(package.split('.')[0] if '.' not in package else package)
            print(f"✅ {package} found")
        except ImportError:
            # Try to check via pkg_resources if import fails (names might differ)
            try:
                pkg_resources.get_distribution(package)
                print(f"✅ {package} found (pkg)")
            except pkg_resources.DistributionNotFound:
                print(f"❌ {package} MISSING")
                missing.append(package)
    
    if missing:
        print(f"\n❌ Missing {len(missing)} packages. Please run: pip install -r requirements.txt")
        return False
    return True

def main():
    print("🔍 Starting Environment Check...\n")
    
    v_ok = check_python_version()
    d_ok = check_dependencies()
    
    if v_ok and d_ok:
        print("\n✨ Environment looks good! You can start the app with:")
        print("python -m uvicorn main:app --reload")
    else:
        print("\n⚠️  Environment issues found. Please fix them before running the app.")
        sys.exit(1)

if __name__ == "__main__":
    main()
