import requests
import time
from colorama import Fore, Back, Style, init
import random

available = 0

init()

print(Fore.YELLOW + "██╗░░██╗███████╗░█████╗░██╗░░░██╗███████╗███╗░░██╗██╗░░░░░██╗░░░██╗  ███╗░░██╗░█████╗░███╗░░░███╗███████╗  ░██████╗███╗░░██╗██╗██████╗░███████╗██████╗░" + Style.RESET_ALL)
print(Fore.WHITE + "██║░░██║██╔════╝██╔══██╗██║░░░██║██╔════╝████╗░██║██║░░░░░╚██╗░██╔╝  ████╗░██║██╔══██╗████╗░████║██╔════╝  ██╔════╝████╗░██║██║██╔══██╗██╔════╝██╔══██╗" + Style.RESET_ALL)
print(Fore.YELLOW + "███████║█████╗░░███████║╚██╗░██╔╝█████╗░░██╔██╗██║██║░░░░░░╚████╔╝░  ██╔██╗██║███████║██╔████╔██║█████╗░░  ╚█████╗░██╔██╗██║██║██████╔╝█████╗░░██████╔╝" + Style.RESET_ALL)
print(Fore.WHITE + "██╔══██║██╔══╝░░██╔══██║░╚████╔╝░██╔══╝░░██║╚████║██║░░░░░░░╚██╔╝░░  ██║╚████║██╔══██║██║╚██╔╝██║██╔══╝░░  ░╚═══██╗██║╚████║██║██╔═══╝░██╔══╝░░██╔══██╗" + Style.RESET_ALL)
print(Fore.YELLOW + "██║░░██║███████╗██║░░██║░░╚██╔╝░░███████╗██║░╚███║███████╗░░░██║░░░  ██║░╚███║██║░░██║██║░╚═╝░██║███████╗  ██████╔╝██║░╚███║██║██║░░░░░███████╗██║░░██║" + Style.RESET_ALL)
print(Fore.WHITE + "╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝░░░╚═╝░░░╚══════╝╚═╝░░╚══╝╚══════╝░░░╚═╝░░░  ╚═╝░░╚══╝╚═╝░░╚═╝╚═╝░░░░░╚═╝╚══════╝  ╚═════╝░╚═╝░░╚══╝╚═╝╚═╝░░░░░╚══════╝╚═╝░░╚═╝" + Style.RESET_ALL)
print(Fore.YELLOW + Back.WHITE + "Original made by clemouche and modified by tezace :)" + Style.RESET_ALL)

def check_username(username):
    url = f"https://auth.roblox.com/v1/usernames/validate?Username={username}&Birthday={random.randint(1980, 2000)}-{random.randint(1, 10)}-{random.randint(1, 10)}"
    try:
        response = requests.get(url)
        response_data = response.json()

        code = response_data.get("code")
        if code == 0:
            print(Fore.GREEN + f"VALID: {username}" + Style.RESET_ALL)
            with open("valid.txt", "a") as valid_file:
                valid_file.write(username + "\n")
            available += 1
        elif code == 1:
            print(Fore.LIGHTBLACK_EX + f"TAKEN: {username}" + Style.RESET_ALL)
        elif code == 2:
            print(Fore.RED + f"CENSORED: {username}" + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + f"bruh ({code}): {username}" + Style.RESET_ALL)

    except requests.exceptions.RequestException as e:
        print(Fore.YELLOW + f"glitch {username}: {e}" + Style.RESET_ALL)

def main():
    with open("usernames.txt", "r") as file:
        usernames = file.read().splitlines()

    for username in usernames:
        check_username(username)
        time.sleep(0.01)
    
    if available >= 3000:
        print(Fore.WHITE + Back.LIGHTYELLOW_EX + f"Valid username amount: {available} (HEAVENLY!!!)" + Style.RESET_ALL)
    elif available >= 1000:
        print(Fore.CYAN + f"Valid username amount: {available} (MYTHICAL!!)" + Style.RESET_ALL)
    elif available >= 500:
        print(Fore.YELLOW + f"Valid username amount: {available} (Legendary!)" + Style.RESET_ALL)
    elif available >= 250:
        print(Fore.MAGENTA + f"Valid username amount: {available} (Epic!)" + Style.RESET_ALL)
    elif available >= 100:
        print(Fore.BLUE + f"Valid username amount: {available} (Rare!)" + Style.RESET_ALL)
    elif available >= 25:
        print(Fore.GREEN + f"Valid username amount: {available} (Uncommon)" + Style.RESET_ALL)
    elif available >= 5:
        print(Fore.BLACK + f"Valid username amount: {available} (Common)" + Style.RESET_ALL)
    else:
        print("No usernames available..")
    
    time.sleep(1000)

    

if __name__ == "__main__":
    main()
