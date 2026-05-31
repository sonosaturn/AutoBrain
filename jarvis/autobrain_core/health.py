import os
import shutil
import sys

COMMON_GIT_PATHS = [
    r"C:\Program Files\Git\bin\git.exe",
    r"C:\Program Files (x86)\Git\bin\git.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\bin\git.exe"),
    os.path.expandvars(r"%USERPROFILE%\bin\git.exe"),
]

class GitNexusDoctor:
    @staticmethod
    def diagnose_git():
        """Checks if git is available, attempts auto-fix, or raises guided error."""
        if shutil.which("git"):
            return True

        # Level 1: Automated Search & Fix (Process-level)
        for path in COMMON_GIT_PATHS:
            if os.path.exists(path):
                bin_dir = os.path.dirname(path)
                os.environ["PATH"] += os.pathsep + bin_dir
                return True
        
        # Level 2: Guided Resolution
        print("\n" + "="*50)
        print("⚠️  GITNEXUS DOCTOR: Git Executable Not Found")
        print("="*50)
        print("We searched the following common locations:")
        for p in COMMON_GIT_PATHS:
            print(f" - {p}")
        print("\nPROMPT: Please provide the path to git.exe or")
        print("run 'gitnexus setup' to reconfigure your environment.")
        print("="*50 + "\n")
        
        return False

def check_environment():
    if not GitNexusDoctor.diagnose_git():
        sys.exit(1)
