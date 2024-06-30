import argparse
import random
import aiohttp
import asyncio
import os
import socket
import subprocess
import re
from aiohttp import ClientSession
from concurrent.futures import ThreadPoolExecutor
from colorama import init, Fore, Style

init()

def generate_random_ip():
    return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

async def check_url(session, url):
    try:
        async with session.head(url, allow_redirects=True, timeout=5) as response:
            if response.status < 400:
                return str(response.url)  
    except:
        pass
    return None

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995, 8080, 8443, 3128, 9050, 1080, 3306, 5432, 3389, 5900, 161, 389, 137, 138, 139, 123, 9200, 9300, 6379, 554, 445, 548, 636, 162]

def scan_ports(ip_address):
    open_ports = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(scan_port, ip_address, port) for port in common_ports]
        for future in futures:
            result = future.result()
            if result:
                open_ports.append(result)
    return open_ports

def scan_port(ip_address, port):
    try:
        with socket.create_connection((ip_address, port), timeout=1):
            return port
    except socket.error:
        return None

def url_to_ip(url):
    parts = url.split("//")
    if len(parts) > 1:
        url = parts[1]
    host = url.split("/")[0]
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None

def print_title():
    print(Fore.YELLOW + Style.BRIGHT + "URL Checker" + Style.RESET_ALL)

async def get_ip_location(session, ip_address):
    url = f"http://ip-api.com/json/{ip_address}"
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
    except:
        pass
    return None

async def check_content(session, url, keyword):
    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                text = await response.text()
                if keyword in text:
                    return url
    except:
        pass
    return None

async def check_proxy(session, ip_address, port):
    proxies = {"http": f"http://{ip_address}:{port}", "https": f"http://{ip_address}:{port}"}
    try:
        async with session.get("http://httpbin.org/status/200", proxy=proxies['http'], timeout=5) as response:
            return response.status == 200
    except:
        return False


async def run_instance(num_addresses, results_queue, session):
    scanned_count = 0
    while True:
        random_ip = generate_random_ip()
        original_url = f"http://{random_ip}"
        redirected_url = await check_url(session, original_url)
        if redirected_url:
            result = f"{Fore.GREEN}{original_url} -> {redirected_url}{Style.RESET_ALL}\n"

            ip_address = url_to_ip(redirected_url)
            if ip_address:
                open_ports = scan_ports(ip_address)
                if open_ports:
                    result += f"{Fore.BLUE}Open ports for {redirected_url}: {open_ports}{Style.RESET_ALL}\n"

                    sitemap_url = await check_content(session, f"http://{ip_address}/sitemap.xml", "xml")
                    result += f"{Fore.GREEN}Sitemap found: {sitemap_url}{Style.RESET_ALL}\n" if sitemap_url else f"{Fore.YELLOW}No sitemap found for {ip_address}{Style.RESET_ALL}\n"

                    index_of_url = await check_content(session, f"http://{ip_address}/", "Index of /")
                    result += f"{Fore.GREEN}Index of found: {index_of_url}{Style.RESET_ALL}\n" if index_of_url else f"{Fore.YELLOW}No 'Index of' found for {ip_address}{Style.RESET_ALL}\n"

                    location_info = await get_ip_location(session, ip_address)
                    if location_info and location_info["status"] == "success":
                        result += f"Country: {location_info.get('country', 'N/A')}\nRegion: {location_info.get('regionName', 'N/A')}\nCity: {location_info.get('city', 'N/A')}\nISP: {location_info.get('isp', 'N/A')}\nLatitude: {location_info.get('lat', 'N/A')}\nLongitude: {location_info.get('lon', 'N/A')}\nOrganization: {location_info.get('org', 'N/A')}\n"

                    for port in open_ports:
                        is_proxy = await check_proxy(session, ip_address, port)
                        result += f"{ip_address}:{port} {Fore.GREEN}Is a proxy{Style.RESET_ALL}\n" if is_proxy else f"{Fore.YELLOW + Style.BRIGHT}{ip_address}:{port} {Fore.RED + Style.BRIGHT}Not a proxy{Style.RESET_ALL}\n"

                    base_ip = ".".join(ip_address.split(".")[:3])
                    subnet = base_ip + ".0/24"
                    command = ["nmap", "-sP", subnet]
                    subnet_result = subprocess.run(command, capture_output=True, text=True)
                    if subnet_result.returncode == 0:
                        subnet_ips = [re.search(r"(\d+\.\d+\.\d+\.\d+)", line).group(1) for line in subnet_result.stdout.splitlines() if re.search(r"(\d+\.\d+\.\d+\.\d+)", line)]
                        if subnet_ips:
                            with open("ip_list.txt", "a") as ip_list_file:
                                for subnet_ip in subnet_ips:
                                    ip_list_file.write(f"{subnet_ip}\n")
                            result += f"{Fore.CYAN}Subnets found: {subnet_ips}{Style.RESET_ALL}\n"
                        else:
                            result += f"{Fore.YELLOW}No subnets found.{Style.RESET_ALL}\n"

                    # Remove ANSI escape codes (color codes) before writing to file
                    clean_result = re.sub(r"\x1b\[[0-9;]*m", "", result)
                    with open("sites.txt", "a", encoding="utf-8") as file:
                        file.write(clean_result + "\n")

                result += "\n"
                results_queue.put_nowait(result)
                scanned_count += 1
                if num_addresses > 0 and scanned_count >= num_addresses:
                    break
            else:
                result += f"{Fore.RED}Invalid URL format: {redirected_url}{Style.RESET_ALL}\n"

            print(result.strip())

        else:
            results_queue.put_nowait(f"{Fore.RED}{original_url} is not active{Style.RESET_ALL}\n\n")
            print(f"{Fore.RED}{original_url} is not active{Style.RESET_ALL}")

async def main():
    parser = argparse.ArgumentParser(description="URL Checker with options to scan addresses.")
    parser.add_argument("-n", "--number", type=int, default=0, help="Number of addresses to scan (0 for unlimited)")
    parser.add_argument("-u", "--unlimited", action="store_true", help="Scan unlimited number of addresses")
    parser.add_argument("-i", "--instance", type=int, default=1, help="Number of instances to run")

    args = parser.parse_args()

    clear_screen()
    print_title()

    num_addresses = args.number if not args.unlimited else 0
    num_instances = args.instance

    results_queue = asyncio.Queue()

    async with ClientSession() as session:
        tasks = [run_instance(num_addresses, results_queue, session) for _ in range(num_instances)]
        await asyncio.gather(*tasks)

    try:
        with open("sites.txt", "a", encoding="utf-8") as file:
            file.write("Scan Results:\n\n")
            while not results_queue.empty():
                result = await results_queue.get()
                if "is not active" not in result:
                    clean_result = re.sub(r"\x1b\[[0-9;]*m", "", result)
                    file.write(clean_result)
    except Exception as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    asyncio.run(main())