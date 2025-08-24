import asyncio
import aiohttp
import random
import logging
import csv
from datetime import datetime
from colorama import Fore, Style, init
from pathlib import Path
from tqdm.asyncio import tqdm_asyncio
from asyncio import Semaphore

# roblox username validation codes
STATUS_MESSAGES = {
    0: "VALID",
    1: "TAKEN",
    2: "CENSORED",
    3: "TOO LONG/SHORT",
    4: "START/END WITH _",
    5: "MULTIPLE _",
    7: "INVALID SYMBOLS",
    10: "MIGHT CONTAIN PRIVATE INFORMATION" # all known codes so far
}

BIRTHDAY_YEARS = (1980, 2000)
MAX_WAIT = 60
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/127 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Firefox/117.0", # user agents for some ✨V A R I E T Y✨
]

init(autoreset=True)



def setup_logging():
    logging.basicConfig(
        filename="results.log",
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def print_banner():
    print(Fore.YELLOW + "[Blitzspeed Radiance v2.1.0 - Input Arguments]" + Style.RESET_ALL)

async def send_webhook(webhook_url, username):
    messages = [
        f"`{username}` is free to claim!",
        f"`{username}` is available! Will you be the first one?",
        f"Lucky find, `{username}` just dropped!",
        f"Someone grab `{username}` before it’s gone!",
        f"The username `{username}` is up for grabs!"
    ]

    payload = {
        "embeds": [{
            "title": "Username Available!",
            "description": random.choice(messages),
            "color": 65280,
            "timestamp": datetime.now().isoformat()
        }]
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(webhook_url, json=payload) as resp:
                if resp.status != 204:
                    logging.warning(f"Webhook send failed ({resp.status})")
        except Exception as e:
            logging.warning(f"Webhook error: {e}")

async def check_username(session, username, args, sem: Semaphore, lock: asyncio.Lock, stats: dict):
    year = random.randint(*BIRTHDAY_YEARS)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    birthday = f"{year}-{month:02d}-{day:02d}" # random birthdays for even more ✨V A R I E T Y✨

    url = f"https://auth.roblox.com/v1/usernames/validate?Username={username}&Birthday={birthday}"

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json"
    }

    async with sem:
        for attempt in range(1, args.retries + 1):
            try:
                async with session.get(url, timeout=args.timeout, headers=headers) as resp:
                    if resp.status == 429: # i hate rate limits so i put this part >:(
                        retry_after = resp.headers.get("Retry-After")
                        wait_time = float(retry_after) if retry_after else min(4 ** attempt, MAX_WAIT)
                        logging.warning(f"Rate limit hit for {username}, waiting {wait_time:.1f}s...")
                        stats["delay"] = min(stats["delay"] + 0.05, 2.0)  # adaptive slowdown
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

                    code = data.get("code", -1) # defaults to -1
                    status = STATUS_MESSAGES.get(code, f"Unknown code {code}")
                    logging.info(f"{status}: {username}")

                    ts = datetime.now().isoformat() # gets the time now (ts pmo icl sybau!!)
                    async with lock:
                        with open(args.csv, "a", newline="", encoding="utf-8") as cf:
                            writer = csv.writer(cf)
                            writer.writerow([username, code, status, ts, ""]) # writes to a csv file

                        if code == 0: # yayy valid username!! :3
                            with open(args.output, "a", encoding="utf-8") as vf:
                                vf.write(username + "\n")
                            stats["valid"] += 1
                            if args.webhook:
                                await send_webhook(args.webhook, username)
                        elif code == 1:
                            stats["taken"] += 1
                        elif code == 2:
                            stats["censored"] += 1
                        else:
                            stats["invalid"] += 1

                        with open("processed.txt", "a", encoding="utf-8") as pf:
                            pf.write(username + "\n")

                    return

            except Exception as e:
                wait_time = min(4 ** attempt + random.uniform(0, 1), MAX_WAIT)
                logging.warning(f"Error ({e}) on {username}, retrying in {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)

        stats["errors"] += 1

async def main(args):
    print_banner()
    setup_logging()

    processed_file = "processed.txt" # processed so it picks up right where it left off which is importnat for large lists
    Path(args.csv).write_text("username,status_code,status_message,timestamp,proxy\n", encoding="utf-8")

    usernames = Path(args.input).read_text(encoding="utf-8").splitlines()

    processed = set()
    if Path(processed_file).exists():
        processed = set(Path(processed_file).read_text(encoding="utf-8").splitlines())

    usernames = [u.strip() for u in usernames if u.strip() and u not in processed]

    if not usernames:
        print(Fore.GREEN + "[:)] All usernames already processed!" + Style.RESET_ALL)
        return

    sem = Semaphore(args.threads)
    lock = asyncio.Lock()
    stats = {"valid": 0, "taken": 0, "censored": 0, "invalid": 0, "errors": 0, "delay": args.delay} # the statistics

    start_time = datetime.now()

    async with aiohttp.ClientSession() as session:
        tasks = [
            check_username(session, name, args, sem, lock, stats)
            for name in usernames
        ]
        await tqdm_asyncio.gather(*tasks, desc="Checking usernames", unit="check", ncols=150, bar_format="{desc}: {percentage:6.3f}% [{bar}] {n_fmt}/{total_fmt} [{elapsed} < {remaining}, {rate_fmt}]") # the progress bar yk

    elapsed = (datetime.now() - start_time).total_seconds()
    total = sum(stats[k] for k in ("valid", "taken", "invalid", "errors"))
    speed = total / elapsed if elapsed > 0 else 0

    print(Fore.CYAN + "\n  - Run Summary -  " + Style.RESET_ALL)
    print(Fore.GREEN + f"[:)] Valid: {stats['valid']}" + Style.RESET_ALL)
    print(Fore.RED + f"[:(] Taken: {stats['taken']}" + Style.RESET_ALL)
    print(Fore.LIGHTBLACK_EX + f"[/>@%;^] Censored: {stats['censored']}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"[>:(] Invalid: {stats['invalid']}" + Style.RESET_ALL)
    print(Fore.LIGHTRED_EX + f"[X_X] Errors: {stats['errors']}" + Style.RESET_ALL)
    print(Fore.LIGHTWHITE_EX + f"Total checked: {total}" + Style.RESET_ALL)
    print(Fore.CYAN + f"[>>] Avg speed: {speed:.2f} checks/sec" + Style.RESET_ALL)

if __name__ == "__main__":
    print_banner()

    # Ask for settings interactively
    def ask(prompt, default=None, cast=str):
        text = input(f"{prompt} [{default}]: ").strip()
        if not text:
            return default
        try:
            return cast(text)
        except Exception:
            print(f"Invalid value, using default ({default})")
            return default

    class Args:
        pass

    args = Args()
    args.input = ask("Enter the text file name that usernames should be saved to", "usernames.txt", str)
    args.output = ask("Enter the file to save valid usernames", "valid.txt", str)
    args.csv = ask("Enter the CSV log file", "results.csv", str)
    args.threads = ask("How many threads do you want? (default: 5)", 5, int)
    args.delay = ask("Base delay between requests, putting 0 won't make it instant since GET requests take some time okay :(", 0.0, float)
    args.retries = ask("How many max retries per username incase something goes wrong?", 6, int)
    args.timeout = ask("Enter HTTP timeout in seconds", 5, int)
    args.webhook = ask("Enter the Discord webhook URL (leave blank for none)", "", str)
    if not args.webhook.strip():
        args.webhook = None

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        print(Fore.RED + "\n[:(] Stopped by user." + Style.RESET_ALL)
