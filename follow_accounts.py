import json
from instagrapi import Client

def load_accounts(file_path):
    """Load the list of account usernames from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            followList = [x['UserName'] for x in data['Activity']['Following List']['Following']]
            print(followList)
            return followList

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{file_path}'.")
        return []

def follow_accounts(username, password, accounts):
    """Login and follow each account in the list."""
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
                totalFound+=1
            except Exception as e:
                print(f"Failed to follow {account}: {e}")
                totalNotFound+=1

    except Exception as e:
        print(f"Error during login: {e}")

    finally:
        cl.logout()
        print("total found", totalFound)
        print("total not found", totalNotFound)
        print("Logged out.")


if __name__ == "__main__":
    # Replace these with your Instagram credentials
    INSTAGRAM_USERNAME = ""
    INSTAGRAM_PASSWORD = ""

    # Path to the JSON file with account names
    JSON_FILE_PATH = "./user_data_tiktok.json"

    # Load accounts and follow them
    accounts_to_follow = load_accounts(JSON_FILE_PATH)
    if accounts_to_follow:
        print(f"Accounts to follow: {accounts_to_follow}")
        print("total accounts to follow: ", len(accounts_to_follow))
        follow_accounts(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, accounts_to_follow)
    else:
        print("No accounts to follow. Please check your JSON file.")

