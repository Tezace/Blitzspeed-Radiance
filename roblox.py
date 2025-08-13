#Heavenly Name Sniper
import asyncio
import aiohttp
import random
import logging
import argparse
from colorama import Fore, Style, init
from pathlib import Path
from tqdm.asyncio import tqdm_asyncio
from asyncio import Semaphore
import requests
#roblox username validation status codes
STATUS_MESSAGES = {
    0: "VALID",
    1: "TAKEN",
    2: "CENSORED",
    3: "TOO LONG/SHORT",
    4: "START/END WITH _",
    5: "CONSECUTIVE _",
    7: "INVALID SYMBOLS",
    10: "MIGHT CONTAIN PRIVATE INFORMATION"
}

BIRTHDAY_YEARS = (1980, 2000)
MAX_WAIT = 60  #max retry backoff in seconds

#colorama init
init(autoreset=True)

def setup_logging():
    logging.basicConfig(
        filename="results.log",
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))


def print_banner():
    print(Fore.YELLOW + "[Heavenly Name Sniper v1.4.0 - Lightning Speed]" + Style.RESET_ALL)


async def check_username(session, username, output_file, retries, timeout, delay, sem: Semaphore):
    #random birthday because i felt like it
    year = random.randint(*BIRTHDAY_YEARS)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    birthday = f"{year}-{month:02d}-{day:02d}"

    url = f"https://auth.roblox.com/v1/usernames/validate?Username={username}&Birthday={birthday}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/127.0.0.1 Safari/537.36",
        "Accept": "application/json"
    }

    async with sem:
        for attempt in range(1, retries + 1):
            try:
                async with session.get(url, timeout=timeout, headers=headers) as resp:
                    #rahh i hate rate limits so i put this code
                    if resp.status == 429:
                        retry_after = resp.headers.get("Retry-After")
                        wait_time = float(retry_after)+0.2 if retry_after else min(4 ** attempt, MAX_WAIT)
                        logging.warning(f"Rate limit hit for {username}, waiting {wait_time:.1f}s...")
                        await asyncio.sleep(wait_time)
                        continue  #retry the same username yk

                    #just incase either me or roblox screwed up massively
                    if resp.status != 200:
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

                    if code == 0:  #valid username!!!!!
                        async with asyncio.Lock():
                            Path(output_file).write_text(
                                Path(output_file).read_text(encoding="utf-8") + username + "\n",
                                encoding="utf-8"
                            )
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

    usernames = Path(input_file).read_text(encoding="utf-8").splitlines()
    Path(output_file).write_text("", encoding="utf-8")  #habibi its to clear ze old results

    sem = Semaphore(threads)

    async with aiohttp.ClientSession() as session:
        tasks = [
            check_username(session, name.strip(), output_file, retries, timeout, delay, sem)
            for name in usernames if name.strip()
        ]
        await tqdm_asyncio.gather(*tasks, desc="Checking usernames", unit="check", ncols=100)


if __name__ == "__main__":
    try:
        asyncio.run(main("usernames.txt", "valid.txt", 5, 0.0, 6, 5)) #input file with usernames, output file to save usernames, threads (max concurrent requests, depending on your CPU PLEASE change this i beg you), delay (between requests), max retries per username, HTTP timeout in seconds
    except KeyboardInterrupt:
        print(Fore.RED + "\n[!] Stopped by user." + Style.RESET_ALL)
