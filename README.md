# Python-Web-Scanner-2.0
This Python script allows you to check URLs for various properties and perform advanced scanning operations. It utilizes asyncio for concurrent operations and aiohttp for asynchronous HTTP requests. The script can check URL redirections, scan common ports, fetch sitemaps, detect proxy servers, retrieve IP geolocation data, and more.

## Features

- URL Redirection Check: Verify if a random IP redirects to an active URL.
- Port Scanning: Scan common ports (e.g., HTTP, HTTPS, FTP) for open services.
- Sitemap Detection: Check if a sitemap.xml exists on the server.
- Proxy Server Detection: Identify if an IP and port combination functions as a proxy.
- IP Geolocation: Retrieve geographical and ISP information for discovered IPs.
- Subnet Discovery: Use Nmap to identify other IPs in the same subnet.

# Requirements
- Python 3.7+
```
pip install aiohttp asyncio argparse colorama
```

## Argument options
```
-n, --number: Number of addresses to scan (default: 0 for unlimited).
-u, --unlimited: Scan an unlimited number of addresses.
-i, --instance: Number of concurrent instances to run (default: 1).
```
Example:
```
python breadscan2.py -u -i 100
```
This will run 1 instance; generating unlimited amount of addresses.

The script outputs results to the console and saves detailed results in sites.txt, as well as subnet information to ip_list.txt.

![image](https://github.com/Cr0mb/Python-Web-Scanner-2.0/assets/137664526/fecc5ec7-c37e-42cf-95eb-03d4a0ebe9ed)
