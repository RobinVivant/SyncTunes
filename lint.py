import subprocess
import sys

def run_linter():
    """Run flake8 linter."""
    result = subprocess.run(['flake8'], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Linting failed. Here are the issues:")
        print(result.stdout)
        return False
    else:
        print("Linting passed successfully!")
        return True

if __name__ == "__main__":
    sys.exit(0 if run_linter() else 1)
