import os
import shutil
import sys
from typing import Optional

class GitNexusDoctor:
    COMMON_WINDOWS_PATHS = [
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
        r"C:\Users\{}\AppData\Local\Programs\Git\bin\git.exe",
        r"C:\Users\{}\AppData\Local\Programs\Git\cmd\git.exe",
    ]

    @staticmethod
    def find_git_binary() -> Optional[str]:
        """Attempt to locate git.exe if not in PATH."""
        # 1. Check standard PATH
        which_git = shutil.which("git")
        if which_git:
            return which_git

        # 2. Scan common Windows locations
        try:
            user_name = os.getlogin()
            for path_template in GitNexusDoctor.COMMON_WINDOWS_PATHS:
                potential_path = path_template.format(user_name)
                if os.path.exists(potential_path):
                    return potential_path
        except Exception:
            pass
        
        return None

    @staticmethod
    def heal_environment() -> bool:
        """Injects git into the current process PATH if found."""
        git_path = GitNexusDoctor.find_git_binary()
        if git_path:
            git_dir = os.path.dirname(git_path)
            if git_dir not in os.environ["PATH"]:
                os.environ["PATH"] = git_dir + os.pathsep + os.environ["PATH"]
            return True
        return False

    @staticmethod
    def raise_diagnostic_error():
        """Displays the user-friendly CLI prompt."""
        print("\n" + "="*60)
        print("⚠️  GITNEXUS DOCTOR: DEPENDENCY MISSING")
        print("="*60)
        print("Git executable not found in your system PATH.")
        print(f"We searched common locations but couldn't find git.exe.")
        print("\nTO FIX THIS:")
        print("1. Install Git from: https://git-scm.com/downloads")
        print("2. Or manually add the 'bin' folder of your Git install to your PATH.")
        print("3. Run 'nexus setup' to reconfigure environment.")
        print("="*60 + "\n")
        sys.exit(1)

def health_check_wrapper(func):
    """Decorator to intercept WinError 2 and attempt self-healing."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            if "git" in str(e).lower() or e.errno == 2:
                if GitNexusDoctor.heal_environment():
                    # Retry once after healing
                    return func(*args, **kwargs)
                else:
                    GitNexusDoctor.raise_diagnostic_error()
            raise e
    return wrapper
