# Overview
this script will output a csv file containing details from the accounts you follow as well as the ig_name wherever it could fine one.
it is pretty basic, example edge cases it can't handle:
- if a user has linked to a random website and that website contains an instagram url that is not the user's, it will still return it
- if a user has multiple links on their account (not the bio text), the web scraping doesn't seem to be able to find anything except one of the links

passing `--follow-ig` will prompt for an ig user and password combination
- *WARNING* this might violate IG ToS and lock your account down. I haven't figured out a good way to do this so any suggestions are welcome
- passing `--csv` will attempt to follow the accounts using the csv output (or any csv containing ig_name as a column with the name tiktok-ig-mapping.csv)
  - this can be used to get all the user information from tiktok and do the ig follows later, i.e. if/when I figure out a way 

# Steps:
I'm using python 3.10, and recommend a virtual env ([pyenv](https://github.com/pyenv/pyenv)) to keep dependencies clean
> optionally, use [python venv](https://docs.python.org/3/library/venv.html)

1. Clone this repo or download it as a zip
1. Get your user tiktok data
  - Account > Settings and privacy > Account > Download your data
  - select file format > JSON
    - check back in 10 minutes or so, it should be downloadable
  - save the json file as user_tiktok_data.json in this directory
1. Get your ms_token:
  - [TikTokApi instructions](https://github.com/davidteather/TikTok-Api/tree/main?tab=readme-ov-file#quick-start-guide)
  - Detailed instructions:
    - open tiktok.com in your browser
    - open dev tools (Ctrl+Shift+I, Opt+Cmd+I, or right click and inspect)
    - go to Application > Cookies, look for ms_token and copy the value (should be associated with `www.tiktok.com` domain)
    - you can set an env variable:
    ```bash
    export ms_token=<PASTE VALUE>
    ```
    - or the script will prompt you to paste it in

run:
```bash
pip install -r requirements.txt
python -m playwright install
```
then
```bash
python getInstagramFromTikTok.py
```


