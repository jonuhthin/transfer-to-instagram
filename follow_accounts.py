import json
import asyncio
import getpass
import os
from instagrapi import Client
from TikTokApi import TikTokApi


def load_accounts(file_path):
    """Load the list of account usernames from a JSON file."""
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            followList = [
                x["UserName"] for x in data["Activity"]["Following List"]["Following"]
            ]
            return followList

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{file_path}'.")
        return []


async def get_tiktok_bios(accounts):
    """Get the bio of each TikTok account in the list."""
    api = TikTokApi()
    ms_token = os.environ.get("ms_token", None) or input(
        "ms_token"
    )  # get your own ms_token from your cookies on tiktok.com

    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3)
        bios = {}
        for username in accounts:
            try:
                user_info = await api.user(username=username).info()
                keys = ["bioLink", "signature"]
                user = user_info["userInfo"]["user"]
                bios[username] = {key: user[key] for key in keys if key in user.keys()}

            except Exception as e:
                print(f"Error fetching bio for {username}: {e}")
                bios[username] = None
        return bios


def follow_accounts(username, password, accounts):
    """Login and follow each account in the list."""
    # Replace these with your Instagram credentials
    username = os.getenv("INSTAGRAM_USERNAME") or input("Enter Instagram username: ")
    password = os.getenv("INSTAGRAM_PASSWORD") or getpass.getpass(
        "Enter Instagram password: "
    )

    cl = Client()
    totalFound = 0
    totalNotFound = 0
    try:
        cl.login(username, password)
        print("Logged in successfully!")

        for account in accounts:
            try:
                user_id = cl.user_id_from_username(account)
                # cl.user_follow(user_id)
                # print(f"Successfully followed: {account}")
                totalFound += 1
            except Exception as e:
                print(f"Failed to follow {account}: {e}")
                totalNotFound += 1

    except Exception as e:
        print(f"Error during login: {e}")

    finally:
        cl.logout()
        print("total found", totalFound)
        print("total not found", totalNotFound)
        print("Logged out.")


async def main():
    # Path to the JSON file with account names
    JSON_FILE_PATH = "./user_data_tiktok.json"
    # Load accounts and follow them
    accounts_to_follow = load_accounts(JSON_FILE_PATH)
    if not accounts_to_follow:
        # print(f"Accounts to follow: {accounts_to_follow}")
        print("No accounts to follow. Please check your JSON file.")

    print("total accounts to follow: ", len(accounts_to_follow))
    bios = await get_tiktok_bios(accounts_to_follow[:2])
    for username, bio in bios.items():
        print(f"{username}: {bio}")
    # follow_accounts(accounts_to_follow)


if __name__ == "__main__":
    asyncio.run(main())
