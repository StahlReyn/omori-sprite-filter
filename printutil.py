from datetime import datetime

COLOR_RESET = "\033[0m"
COLOR_RED = "\033[31m"
COLOR_BLUE = "\033[34m"

def print_with_timestamp(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")

# Print Error with Red Color
def print_error(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"{COLOR_RED}[{timestamp}] ERROR: {message}{COLOR_RESET}")

def print_info(message):
    print(f"{COLOR_BLUE}{message}{COLOR_RESET}")