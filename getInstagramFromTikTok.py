from instagrapi import Client
from playwright.async_api import async_playwright
from TikTokApi import TikTokApi
import argparse
import asyncio
import getpass
import json
import os
import pandas as pd
import re
import sys
from tqdm import tqdm  # For a nice progress bar


def load_accounts(file_path):
    """Load the list of account usernames from a JSON file."""
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            followList = [
                x["UserName"]
                for x in data["Activity"]["Following List"]["Following"]
                if x["UserName"] != "N/A"  # some accounts are gone(?) and show as N/A
            ]
            return followList

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{file_path}'.")
        return []


async def get_tiktok_bios(accounts):
    """Get the bio of each TikTok account in the list with progress tracking."""
    api = TikTokApi()
    ms_token = os.environ.get("ms_token", None) or input(
        "ms_token: "
    )  # get your own ms_token from your cookies on tiktok.com

    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3)
        bios = {}
        total = len(accounts)
        # Limit concurrent tasks to avoid overwhelming resources
        semaphore = asyncio.Semaphore(100)
        progress = tqdm(total=total, desc="Processing accounts")

        async def process_account(username):
            """Process a single account to fetch bio and Instagram."""
            async with semaphore:
                try:
                    apiUser = api.user(username=username)
                    user_info = await apiUser.info()
                    keys = ["bioLink", "signature"]
                    user = user_info["userInfo"]["user"]
                    bio = {key: user[key] for key in keys if key in user.keys()}
                    bio["ig_name"] = await get_instagram_from_tiktok(bio)
                    return username, bio
                except Exception as e:
                    print(f"Error fetching data for {username}: {e}")
                    return username, None
                finally:
                    progress.update(1)

        # Use asyncio.gather to process accounts concurrently
        tasks = [process_account(username) for username in accounts]
        results = await asyncio.gather(*tasks)

        # Collect results into the bios dictionary
        for username, bio in results:
            bios[username] = bio

        progress.close()
        return bios


def get_handle_from_url(url):
    pattern = r"instagram\.com\/([^\/\?]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


def is_url(text):
    pattern = r"(https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z]{2,}(\.[a-zA-Z]{2,})(\.[a-zA-Z]{2,})?\/[a-zA-Z0-9]{2,}|((https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z]{2,}(\.[a-zA-Z]{2,})(\.[a-zA-Z]{2,})?)|(https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z0-9]{2,}\.[a-zA-Z0-9]{2,}\.[a-zA-Z0-9]{2,}(\.[a-zA-Z0-9]{2,})?"
    match = re.match(pattern, text)
    return match is not None


async def get_instagram_from_url(url):
    """Get Instagram URL from a URL using Playwright."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("http://" + url if not url.startswith("http") else url)
            links = await page.query_selector_all('a[href*="instagram.com"]')
            for link in links:
                href = await link.get_attribute("href")
                if href:
                    return get_handle_from_url(href)
            await browser.close()
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")

    return None


async def get_instagram_from_tiktok(user):
    """Get Instagram URL from TikTok user object."""
    if "bioLink" in user and "link" in user["bioLink"]:
        link = user["bioLink"]["link"]
        if "instagram.com" in link:
            # the user has an instagram url in their bio
            return get_handle_from_url(link)
        else:
            # the user has a non-instagram url in their bio
            # WARNING if this url has any other instagram links, they will be brought in
            return await get_instagram_from_url(link)

    if "signature" in user:
        signature = user["signature"]

        delimited = signature.lower().split()
        for index, part in enumerate(delimited):
            if part.startswith(
                ("ig:", "insta:", "instagram:", "ig", "insta", "instagram")
            ):
                handle = delimited[index + 1].lstrip("@")  # return the next part
                return handle

        for part in signature.split():
            if "instagram.com" in part:
                # the user has an instagram url in their bio text
                return get_handle_from_url(part)
            elif is_url(part):
                # the user has a non-instagram url in their bio text
                return await get_instagram_from_url(part)

    return None


def follow_accounts(accounts):
    """Login and follow each account in the list."""
    # Replace these with your Instagram credentials
    username = os.getenv("INSTAGRAM_USERNAME") or input("Enter Instagram username: ")
    password = os.getenv("INSTAGRAM_PASSWORD") or getpass.getpass(
        "Enter Instagram password: "
    )

    cl = Client()
    try:
        cl.login(username, password)
        print("Logged in successfully!")

        for account in accounts:
            try:
                user_id = cl.user_id_from_username(account)
                cl.user_follow(user_id)
                print(f"Successfully followed: {account}")
            except Exception as e:
                print(f"Failed to follow {account}: {e}")

    except Exception as e:
        print(f"Error during login: {e}")

    finally:
        cl.logout()
        print("Logged out.")


async def main():
    parser = argparse.ArgumentParser(
        description="Use TikTok accounts from your following to get Instagram accounts and follow them."
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="follow a list of instagram accounts stored in the tiktok-ig-mapping.csv file without getting all the data again",
    )

    parser.add_argument(
        "--follow-ig",
        action="store_true",
        help="attempt to follow the ig accounts in the tiktok-ig-mapping.csv file. This MIGHT violate instagram TOS, so use at your own risk",
    )
    args = parser.parse_args()

    if not args.csv:
        # Path to the JSON file with account names
        JSON_FILE_PATH = "./user_data_tiktok.json"
        # Load accounts and follow them
        accounts_to_follow = load_accounts(JSON_FILE_PATH)
        if not accounts_to_follow:
            print("No accounts to follow. Please check your JSON file.")

        print("total accounts to follow: ", len(accounts_to_follow))
        bios = await get_tiktok_bios(accounts_to_follow[:100])
        pd.DataFrame(bios).T.to_csv("tiktok-ig-mapping.csv")

    if args.follow_ig:
        df = pd.read_csv("tiktok-ig-mapping.csv")
        ig_names = df["ig_name"].dropna().tolist()
        follow_accounts(ig_names)


if __name__ == "__main__":
    asyncio.run(main())
