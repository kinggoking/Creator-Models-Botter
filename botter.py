import os
import requests
from colorama import Fore, Style, init
import traceback
from bs4 import BeautifulSoup as htmlparser
import json
import random

init(autoreset=True)

auth = "https://users.roblox.com/v1/users/authenticated"
buy = "https://apis.roblox.com/marketplace-fiat-service/v1/product/purchase"
delete = "https://inventory.roblox.com/v2/inventory/asset/{asset_id}"
like = "https://apis.roblox.com/voting-api/vote/asset/{asset_id}?vote=true"
comment = "https://apis.roproxy.com/asset-reviews-api/v1/assets/{asset_id}/comments"

script_dir = os.path.dirname(os.path.abspath(__file__))
cookies_file_path = os.path.join(script_dir, "cookies.txt")
reviews_file_path = os.path.join(script_dir, "reviews.txt")
proxies_file_path = os.path.join(script_dir, "proxies.txt")

if not os.path.exists(cookies_file_path):
    print(f"{cookies_file_path} not found!")
    input(Fore.RED + "Press Enter to exit...")
    exit()

if not os.path.exists(reviews_file_path):
    print(f"{reviews_file_path} not found!")
    input(Fore.RED + "Press Enter to exit...")
    exit()

if not os.path.exists(proxies_file_path):
    print(f"{proxies_file_path} not found!")
    input(Fore.RED + "Press Enter to exit...")
    exit()

with open(reviews_file_path, "r") as file:
    reviews = file.read().splitlines()

with open(cookies_file_path, "r") as file:
    cookies = file.read().splitlines()

with open(proxies_file_path, "r") as file:
    proxies_list = file.read().splitlines()

print(Fore.LIGHTBLUE_EX + f"[+] LOADED:\n[->] reviews.txt: {str(len(reviews))} loaded\n[->] cookies.txt: {str(len(cookies))} loaded\n[->] proxies.txt: {str(len(proxies_list))} loaded")

userid = input(Fore.LIGHTBLUE_EX + "[+] Enter Creator ID: ")
repeat_count = int(input(Fore.LIGHTBLUE_EX + "[+] Enter number of purchase/delete cycles: "))

def get_random_proxy():
    if proxies_list:
        proxy = random.choice(proxies_list)
        return {
            "http": f"http://{proxy}"
        }
    return None

for i, roblosecurity_cookie in enumerate(cookies):
    if not roblosecurity_cookie.strip():
        continue
    print(f"\n----------\nProcessing cookie {i + 1}...")

    try:
        proxy = get_random_proxy()
        if proxy:
            print(Fore.YELLOW + f"[+] Using proxy: {list(proxy.values())[0]}")
        
        headers = {
            "Content-Type": "application/json",
            "Cookie": ".ROBLOSECURITY=" + roblosecurity_cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 OPR/117.0.0.0",
        }

        http = requests.get("https://www.roblox.com/home", headers=headers, proxies=proxy, timeout=30)
        html = htmlparser(http.text, "html.parser")
        csrf_tag = html.find("meta", {"name": "csrf-token"})
        csrf_token = csrf_tag["data-token"]
        print(Fore.GREEN + "[+] X-CSRF-TOKEN: " + csrf_token)
        headers["X-CSRF-TOKEN"] = csrf_token

        response = requests.get(auth, headers=headers, timeout=30)
        if response.status_code != 200:
            print(Fore.RED + f"[-] {response.status_code} | Failed to fetch user information.")
            continue

        user_info = response.json()
        user_id = str(user_info.get("id"))
        username = user_info.get("name")

        req = requests.get(f"https://apis.roblox.com/toolbox-service/v1/marketplace/10?creatorTargetId={userid}&limit=1000", headers=headers, timeout=30)
        if req.status_code != 200:
            print(Fore.RED + f"[-] {req.status_code} | Failed to fetch user models.")
            continue

        assets = req.json().get("data")
        if not assets:
            print(Fore.YELLOW + "[!] No assets found")
            continue

        for info in assets:
            asset_id = str(info["id"])
            data = {
                "expectedPrice": {"currencyCode": "USD", "quantity": {"significand": 0, "exponent": 0}},
                "productKey": {
                    "productNamespace": "PRODUCT_NAMESPACE_CREATOR_MARKETPLACE_ASSET",
                    "productType": "PRODUCT_TYPE_MODEL",
                    "productTargetId": asset_id
                }
            }

            for cycle in range(repeat_count):
                response = requests.post(buy, json=data, headers=headers, proxies=proxy, timeout=30)
                if response.status_code == 200:
                    print(Fore.GREEN + f"[+] {username} | Purchased asset {asset_id} (cycle {cycle + 1}): {response.status_code}")
                else:
                    print(Fore.RED + f"[-] {response.status_code} | Purchase failed.")
                    print(response.text)
                    continue
                response = requests.delete(delete.format(asset_id=asset_id), headers=headers, proxies=proxy, timeout=30)
                if response.status_code == 200:
                    print(Fore.GREEN + f"[+] {username} | Deleted asset {asset_id} (cycle {cycle + 1}): {response.status_code}")
                else:
                    print(Fore.RED + f"[-] {response.status_code} | Delete failed.")
                    print(response.text)
                    continue

            response = requests.post(buy, json=data, headers=headers, proxies=proxy, timeout=30)
            if response.status_code == 200:
                print(Fore.GREEN + f"[+] {username} | Purchased asset {asset_id} (cycle {cycle + 1}): {response.status_code}")
            else:
                print(Fore.RED + f"[-] {response.status_code} | Purchase failed.")
                print(response.text)
                continue
            fav = f"https://catalog.roblox.com/v1/favorites/users/{user_id}/assets/{asset_id}/favorite"
            response = requests.post(fav, headers=headers, proxies=proxy, timeout=30)
            if response.status_code == 200:
                print(Fore.GREEN + f"[+] {username} | Favorited asset {asset_id}: {response.status_code}")
            else:
                print(Fore.RED + f"[-] {response.status_code} | Favorite failed.")
                print(response.text)
                continue

            random_review = random.choice(reviews)
            comment_data = {
                "text": str(random_review),
                "parentId": None
            }
            encoded = json.dumps(comment_data)
            response = requests.post(like.format(asset_id=asset_id), headers=headers, timeout=30)

            if response.status_code == 200:
                print(Fore.GREEN + f"[+] {username} | Voting Success. | {response.status_code}")
            else:
                print(Fore.RED + f"[-] {response.status_code} | Voting failed.")
                print(response.text)
                continue

            response = requests.post(comment.format(asset_id=asset_id), data=encoded, headers=headers, proxies=proxy, timeout=30)
            if response.status_code == 201:
                print(Fore.GREEN + f"[+] {username} | Commented on asset {asset_id}: {response.status_code} | Comment: {random_review}")
            else:
                print(Fore.RED + f"[-] {username} | Failed to comment asset {asset_id}: {response.status_code}")
                print(response.text)

    except Exception as e:
        print(Fore.RED + "An error occurred:")
        print(Fore.YELLOW + traceback.format_exc())

print("----------\nFinished processing all cookies.")
input(Fore.LIGHTCYAN_EX + "\nPress Enter to exit...")