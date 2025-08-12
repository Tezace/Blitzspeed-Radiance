# Heavenly Name Sniper
import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Back, Style, init
from pathlib import Path
from tqdm import tqdm
import logging

# the configurations
INPUT_FILE = "usernames.txt"
OUTPUT_FILE = "valid.txt"
THREADS = 5           # Parallel requests (depending on your CPU, PLEASE edit this i beg you)
DELAY_BETWEEN = 0.1   # Seconds between each request per thread
MAX_RETRIES = 6
TIMEOUT = 5           # Seconds for HTTP timeout
BIRTHDAY_YEARS = (1980, 2000)

init()

# logging setup
logging.basicConfig(
    filename="results.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def print_banner():
    print(Fore.YELLOW + "[Heavenly Name Sniper v1.3.0 - Progression (progress bar added)]" + Style.RESET_ALL)

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
                logging.info(f"VALID: {username}")
                return username
            elif code == 1:
                logging.info(f"TAKEN: {username}")
            elif code == 2:
                logging.info(f"CENSORED: {username}")
            elif code == 3:
                logging.info(f"TOO LONG/SHORT: {username}")
            elif code == 4:
                logging.info(f"START/END WITH _: {username}")
            elif code == 5:
                logging.info(f"CONSECUTIVE _: {username}")
            elif code == 7:
                logging.info(f"INVALID SYMBOLS: {username}")
            else:
                logging.info(f"bruh {code}: {username}")
            return None
        
        except requests.exceptions.RequestException as e:
            wait_time = 4 ** attempt
            logging.warning(f"glitch ({e}) on {username}, retrying in {wait_time}s...")
            time.sleep(wait_time)
    
    return None


def main():
    print_banner()

    usernames = Path(INPUT_FILE).read_text().splitlines()
    valid_names = []

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(check_username, name): name for name in usernames}

        with tqdm(total=len(usernames), desc="Checking usernames", unit=" checks", ncols=150) as pbar:
            for future in as_completed(futures):
                result = future.result()
                if result:
                    valid_names.append(result)
                time.sleep(DELAY_BETWEEN)
                pbar.update(1)

    if valid_names:
        Path(OUTPUT_FILE).write_text("\n".join(valid_names))
        print(Fore.CYAN + f"\nSaved {len(valid_names)} valid usernames to {OUTPUT_FILE}" + Style.RESET_ALL)
    else:
        print(Fore.RED + "\nNo valid usernames found." + Style.RESET_ALL)

if __name__ == "__main__":
    main()

