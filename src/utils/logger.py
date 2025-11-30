from colorama import Fore, Style

class Logger:
    """Colored logger for better user experience"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def info(self, message: str) -> None:
        """Information message"""
        print(f"{Fore.BLUE}{message}{Style.RESET_ALL}")

    def success(self, message: str) -> None:
        """Success message"""
        print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

    def warning(self, message: str) -> None:
        """Warning message"""
        print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")

    def error(self, message: str) -> None:
        """Error message"""
        print(f"{Fore.RED}{message}{Style.RESET_ALL}")

    def debug(self, message: str) -> None:
        """Debug message (only in verbose mode)"""
        if self.verbose:
            print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")
