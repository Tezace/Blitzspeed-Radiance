# Blitzspeed Radiance - average of 16 checks per second
import asyncio
import aiohttp
import random
import logging
from colorama import Fore, Style, init
from pathlib import Path
from tqdm.asyncio import tqdm_asyncio
from asyncio import Semaphore

# roblox username validation status codes that i know of
STATUS_MESSAGES = {
    0: "VALID",
    1: "TAKEN",
    2: "CENSORED",
    3: "TOO LONG/SHORT",
    4: "START/END WITH _",
    5: "CONSECUTIVE _",
    7: "INVALID SYMBOLS",
    10: "MIGHT CONTAIN PRIVATE INFORMATION" # all known codes so far
}

BIRTHDAY_YEARS = (1980, 2000)
MAX_WAIT = 60
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/127 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Firefox/117.0",
]

# colorama init
init(autoreset=True)

def setup_logging():
    logging.basicConfig(
        filename="results.log",
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def print_banner():
    print(Fore.YELLOW + "[Blitzspeed Radiance v1.5.0 - Resume Support]" + Style.RESET_ALL)

async def check_username(session, username, output_file, processed_file, retries, timeout, delay, sem: Semaphore, lock: asyncio.Lock):
    year = random.randint(*BIRTHDAY_YEARS)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    birthday = f"{year}-{month:02d}-{day:02d}"

    url = f"https://auth.roblox.com/v1/usernames/validate?Username={username}&Birthday={birthday}"

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json"
    }

    async with sem:
        for attempt in range(1, retries + 1):
            try:
                async with session.get(url, timeout=timeout, headers=headers) as resp:
                    if resp.status == 429: # i hate rate limits so i put this code
                        retry_after = resp.headers.get("Retry-After")
                        wait_time = float(retry_after) if retry_after else min(4 ** attempt, MAX_WAIT)
                        logging.warning(f"Rate limit hit for {username}, waiting {wait_time:.1f}s...")
                        await asyncio.sleep(wait_time)
                        continue

                    if resp.status != 200: # just incase either me or roblox screwed up massively
                        raw_text = await resp.text()
                        logging.warning(
                            f"HTTP {resp.status} for {username} (attempt {attempt})\n"
                            f"First 200 chars: {raw_text[:200]!r}"
                        )
                        raise Exception(f"Bad HTTP status {resp.status}")

                    try:
                        data = await resp.json(content_type=None)
                    except Exception as e:
                        raw_text = await resp.text()
                        logging.warning(
                            f"JSON parse failed for {username} (attempt {attempt}): {e}\n"
                            f"First 200 chars: {raw_text[:200]!r}"
                        )
                        raise

                    code = data.get("code", -1)
                    status = STATUS_MESSAGES.get(code, f"Unknown code {code}")
                    logging.info(f"{status}: {username}")

                    async with lock:
                        with open(processed_file, "a", encoding="utf-8") as pf:
                            pf.write(username + "\n")

                        if code == 0:  # valid username
                            with open(output_file, "a", encoding="utf-8") as vf:
                                vf.write(username + "\n")
                            return True

                    return False

            except Exception as e:
                wait_time = min(4 ** attempt + random.uniform(0, 1), MAX_WAIT)
                logging.warning(f"Error ({e}) on {username}, retrying in {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)

        return False

async def main(input_file, output_file, threads, delay, retries, timeout):
    print_banner()
    setup_logging()

    processed_file = "processed.txt"

    usernames = Path(input_file).read_text(encoding="utf-8").splitlines()

    # load processed usernames (valid + invalid) to skip them
    processed = set()
    if Path(processed_file).exists():
        processed = set(Path(processed_file).read_text(encoding="utf-8").splitlines())

    # filter out processed names
    usernames = [u.strip() for u in usernames if u.strip() and u not in processed]

    if not usernames:
        print(Fore.GREEN + "[+] All usernames already processed!" + Style.RESET_ALL)
        return

    sem = Semaphore(threads)
    lock = asyncio.Lock()

    async with aiohttp.ClientSession() as session:
        tasks = [
            check_username(session, name, output_file, processed_file, retries, timeout, delay, sem, lock)
            for name in usernames
        ]
        await tqdm_asyncio.gather(
            *tasks,
            desc="Checking usernames",
            unit="check",
            ncols=150,
            bar_format="{desc}: {percentage:6.3f}% | {bar} | {n_fmt}/{total_fmt} [{elapsed} < {remaining}, {rate_fmt}]"
        )

if __name__ == "__main__":
    try:
        asyncio.run(main(
            "usernames.txt",   # input file with usernames
            "valid.txt",       # output file for valid usernames
            5,                 # threads (max concurrent requests, depending on your CPU PLEASE edit this i beg you)
            0.0,               # delay between requests
            6,                 # max retries per username
            5                  # HTTP timeout in seconds
        ))
    except KeyboardInterrupt:
        print(Fore.RED + "\n[!] Stopped by user." + Style.RESET_ALL)
