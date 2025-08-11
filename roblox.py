import requests
import time
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Back, Style, init
from pathlib import Path

# the configurations
INPUT_FILE = "usernames.txt"
OUTPUT_FILE = "valid.txt"
THREADS = 5           # how many requests should happen at once
DELAY_BETWEEN = 0.1   # seconds between each request per thread
MAX_RETRIES = 5
TIMEOUT = 5           # seconds for HTTP timeout
BIRTHDAY_YEARS = (1980, 2000)

init()

def print_banner():
    print(Fore.YELLOW + "[Heavenly Name Sniper v1.2 - Hypersonic Speed]" + Style.RESET_ALL)

def check_username(username):
    """Check if a Roblox username is valid."""
    url = f"https://auth.roblox.com/v1/usernames/validate"
    params = {
        "Username": username,
        "Birthday": f"{random.randint(*BIRTHDAY_YEARS)}-{random.randint(1, 12)}-{random.randint(1, 28)}"
    }
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=TIMEOUT)
            data = response.json()
            code = data.get("code")
            
            if code == 0:
                print(Fore.GREEN + f"VALID: {username}" + Style.RESET_ALL)
                return username
            elif code == 1:
                print(Fore.LIGHTBLACK_EX + f"TAKEN: {username}" + Style.RESET_ALL)
            elif code == 2:
                print(Fore.RED + f"CENSORED: {username}" + Style.RESET_ALL)
            elif code == 3:
                print(Fore.RED + f"TOO LONG/SHORT: {username}" + Style.RESET_ALL)
            elif code == 4:
                print(Fore.RED + f"START/END WITH _: {username}" + Style.RESET_ALL)
            elif code == 5:
                print(Fore.RED + f"CONSECUTIVE _: {username}" + Style.RESET_ALL)
            elif code == 7:
                print(Fore.RED + f"INVALID SYMBOLS: {username}" + Style.RESET_ALL)
            else:
                print(Fore.YELLOW + f"bruh {code}: {username}" + Style.RESET_ALL)
            return None
        
        except requests.exceptions.RequestException as e:
            wait_time = 2 ** attempt
            print(Fore.YELLOW + f"glitch ({e}) on {username}, retrying in {wait_time}s..." + Style.RESET_ALL)
            time.sleep(wait_time)
    
    return None

def main():
    print_banner()

    usernames = Path(INPUT_FILE).read_text().splitlines()
    valid_names = []

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(check_username, name): name for name in usernames}
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                valid_names.append(result)
            time.sleep(DELAY_BETWEEN)

    if valid_names:
        Path(OUTPUT_FILE).write_text("\n".join(valid_names))
        print(Fore.CYAN + f"\nSaved {len(valid_names)} valid usernames to {OUTPUT_FILE}" + Style.RESET_ALL)
    else:
        print(Fore.RED + "\nNo valid usernames found." + Style.RESET_ALL)

if __name__ == "__main__":
    main()

