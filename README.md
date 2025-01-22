## Author
**Author**: Trix Cyrus  
**Copyright**: © 2025 Trixsec Org   
**Maintained**: Yes 

## Overview
**Brute-XMLRPC** is a Python-based tool designed to perform brute force attacks on WordPress sites through the `xmlrpc.php` endpoint. It can also enumerate users via the WordPress JSON API to enhance the attack surface.

## Features
- **Multi-threaded Brute Force**: Perform brute force attacks using multiple threads for efficiency.
- **IP Spoofing**: Generate random IP addresses for headers like `X-Forwarded-For` and `X-Real-IP` to enhance anonymity.
- **Custom Headers**: Use a variety of headers to mimic real-world browser requests.
- **User Enumeration**: Retrieve user information from the WordPress JSON API.
- **Interactive Input**: Easy-to-use prompts for user input and configuration.
- **Progress Display**: Real-time display of brute force attempts and progress.

## **Key Changes and Improvements:**  

1. **Proxy Handling with `aiohttp-socks`:**  
   - Integrated `aiohttp-socks` for SOCKS5 proxy support, ensuring compatibility with Tor.  
   - Replaced direct proxy arguments with `ProxyConnector` for streamlined connection management.  

2. **Enhanced Header and User-Agent Spoofing:**  
   - Expanded `user_agents` list with mobile browsers, old browsers, and bots.  
   - Broadened `referer_domains` and added randomized `Accept-Language`, `Accept-Encoding`, `Forwarded`, `DNT`, `Origin`, and `Cache-Control` headers for increased variety.  

3. **Payload Variation in `check_xmlrpc_available`:**  
   - Introduced random payloads (`system.getCapabilities`, `system.methodHelp`, etc.) for more robust testing.  

4. **Retry Logic and Rate Limiting:**  
   - Added retry mechanism with delays and handling of `429` responses using `Retry-After` header.  

5. **WAF Detection:**  
   - Added `check_for_waf` to identify 403 responses indicating a WAF and log detections in `WAF_DETECTED_LOG`.  

6. **Deprecated Method Removal:**  
   - Replaced `SocksConnector.create` with `ProxyConnector` for modern and non-deprecated proxy handling.  

## Requirements
- Python 3.x
- Required Python packages:
  - `requests`
  - `colorama`
  - `termcolor`
  - `concurrent.futures`

You can install the required packages using the following command:
```bash
pip install requests colorama termcolor
```

## Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/TrixSec/Brute-XMLRPC.git
    cd Brute-XMLRPC
    ```

## Usage
1. Run the script:
    ```bash
    python brutecxmlrpc.py
    ```

2. Follow the prompts to:
   - Enter the target WordPress site URL.
   - Check for `xmlrpc.php` availability.
   - Choose to enumerate users via the WordPress JSON API.
   - Provide usernames and passwords manually or via files.
   - Set the number of threads for the brute force attack.


## Disclaimer
This tool is intended for educational purposes only. Unauthorized use of this tool to compromise or damage systems is illegal and unethical. The developers are not responsible for any misuse or damage caused by this tool.

**Repository Views** ![Views](https://profile-counter.glitch.me/Brutexmlrpc/count.svg)
