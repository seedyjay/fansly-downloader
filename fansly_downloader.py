# fix in future: audio needs to be properly transcoded pre-saving from mp4 to mp3 & sort_download() needs to first parse what filesize a image is before trying to add pyexvi2 metadata to it
import requests, os, re, base64, hashlib, imagehash, io, traceback, sys, platform, subprocess, concurrent.futures, json, m3u8, av, time, mimetypes, configparser
from random import randint, uniform
from tkinter import Tk, filedialog
from loguru import logger as log
from functools import partialmethod
from PIL import Image, ImageFile
from time import sleep as s
from rich.table import Column
from rich.progress import Progress, BarColumn, TextColumn
from configparser import RawConfigParser
from os.path import join, exists
from os import makedirs, getcwd
from utils.update_util import delete_deprecated_files, check_latest_release, apply_old_config_values
from utils.metadata_manager import MetadataManager

# tell PIL to be tolerant of files that are truncated
ImageFile.LOAD_TRUNCATED_IMAGES = True

# turn off for our purpose unnecessary PIL safety features
Image.MAX_IMAGE_PIXELS = None

# define requests session
sess = requests.Session()


# cross-platform compatible, re-name downloaders terminal output window title
def set_window_title(title):
    current_platform = platform.system()
    if current_platform == 'Windows':
        subprocess.call('title {}'.format(title), shell=True)
    elif current_platform == 'Linux' or current_platform == 'Darwin':
        subprocess.call(['printf', r'\33]0;{}\a'.format(title)])
set_window_title('Fansly Downloader')

# base64 code to display logo in console
print(base64.b64decode('CiAg4paI4paI4paI4paI4paI4paI4paI4pWXIOKWiOKWiOKWiOKWiOKWiOKVlyDilojilojilojilZcgICDilojilojilZfilojilojilojilojilojilojilojilZfilojilojilZcgIOKWiOKWiOKVlyAgIOKWiOKWiOKVlyAgICDilojilojilojilojilojilojilZcg4paI4paI4pWXICAgICAgICAgIOKWiOKWiOKWiOKWiOKWiOKVlyDilojilojilojilojilojilojilZcg4paI4paI4paI4paI4paI4paI4pWXIAogIOKWiOKWiOKVlOKVkOKVkOKVkOKVkOKVneKWiOKWiOKVlOKVkOKVkOKWiOKWiOKVl+KWiOKWiOKWiOKWiOKVlyAg4paI4paI4pWR4paI4paI4pWU4pWQ4pWQ4pWQ4pWQ4pWd4paI4paI4pWRICDilZrilojilojilZcg4paI4paI4pWU4pWdICAgIOKWiOKWiOKVlOKVkOKVkOKWiOKWiOKVl+KWiOKWiOKVkSAgICAgICAgIOKWiOKWiOKVlOKVkOKVkOKWiOKWiOKVl+KWiOKWiOKVlOKVkOKVkOKWiOKWiOKVl+KWiOKWiOKVlOKVkOKVkOKWiOKWiOKVlwogIOKWiOKWiOKWiOKWiOKWiOKVlyAg4paI4paI4paI4paI4paI4paI4paI4pWR4paI4paI4pWU4paI4paI4pWXIOKWiOKWiOKVkeKWiOKWiOKWiOKWiOKWiOKWiOKWiOKVl+KWiOKWiOKVkSAgIOKVmuKWiOKWiOKWiOKWiOKVlOKVnSAgICAg4paI4paI4pWRICDilojilojilZHilojilojilZEgICAgICAgICDilojilojilojilojilojilojilojilZHilojilojilojilojilojilojilZTilZ3ilojilojilojilojilojilojilZTilZ0KICDilojilojilZTilZDilZDilZ0gIOKWiOKWiOKVlOKVkOKVkOKWiOKWiOKVkeKWiOKWiOKVkeKVmuKWiOKWiOKVl+KWiOKWiOKVkeKVmuKVkOKVkOKVkOKVkOKWiOKWiOKVkeKWiOKWiOKVkSAgICDilZrilojilojilZTilZ0gICAgICDilojilojilZEgIOKWiOKWiOKVkeKWiOKWiOKVkSAgICAgICAgIOKWiOKWiOKVlOKVkOKVkOKWiOKWiOKVkeKWiOKWiOKVlOKVkOKVkOKVkOKVnSDilojilojilZTilZDilZDilZDilZ0gCiAg4paI4paI4pWRICAgICDilojilojilZEgIOKWiOKWiOKVkeKWiOKWiOKVkSDilZrilojilojilojilojilZHilojilojilojilojilojilojilojilZHilojilojilojilojilojilojilojilZfilojilojilZEgICAgICAg4paI4paI4paI4paI4paI4paI4pWU4pWd4paI4paI4paI4paI4paI4paI4paI4pWXICAgIOKWiOKWiOKVkSAg4paI4paI4pWR4paI4paI4pWRICAgICDilojilojilZEgICAgIAogIOKVmuKVkOKVnSAgICAg4pWa4pWQ4pWdICDilZrilZDilZ3ilZrilZDilZ0gIOKVmuKVkOKVkOKVkOKVneKVmuKVkOKVkOKVkOKVkOKVkOKVkOKVneKVmuKVkOKVkOKVkOKVkOKVkOKVkOKVneKVmuKVkOKVnSAgICAgICDilZrilZDilZDilZDilZDilZDilZ0g4pWa4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWdICAgIOKVmuKVkOKVnSAg4pWa4pWQ4pWd4pWa4pWQ4pWdICAgICDilZrilZDilZ0gICAgIAogICAgICAgICAgICAgICAgICAgICAgICBkZXZlbG9wZWQgb24gZ2l0aHViLmNvbS9Bdm5zeC9mYW5zbHktZG93bmxvYWRlcgo=').decode('utf-8'))

# most of the time, we utilize this to display colored output rather than logging or prints
def output(level: int, log_type: str, color: str, mytext: str):
    try:
        log.level(log_type, no = level, color = color)
    except TypeError:
        pass # level failsafe
    log.__class__.type = partialmethod(log.__class__.log, log_type)
    log.remove()
    log.add(sys.stdout, format = "<level>{level}</level> | <white>{time:HH:mm}</white> <level>|</level><light-white>| {message}</light-white>", level=log_type)
    log.type(mytext)

# mostly used to attempt to open fansly downloaders documentation
def open_url(url_to_open: str):
    s(10)
    try:
        import webbrowser
        webbrowser.open(url_to_open, new=0, autoraise=True)
    except Exception:
        pass

output(1,'\n Info','<light-blue>','Reading config.ini file ...')
config = RawConfigParser()
config_path = join(getcwd(), 'config.ini')
if len(config.read(config_path)) != 1:
    output(2,'\n [1]ERROR','<red>', f"config.ini file not found or can not be read.\n{21*' '}Please download it & make sure it is in the same directory as fansly downloader")
    input('\nPress Enter to close ...')
    exit()


## starting here: self updating functionality
# if started with --update start argument
if len(sys.argv) > 1 and sys.argv[1] == '--update':
    # config.ini backwards compatibility fix (≤ v0.4) -> fix spelling mistake "seperate" to "separate"
    if 'seperate_messages' in config['Options']:
        config['Options']['separate_messages'] = config['Options'].pop('seperate_messages')
    if 'seperate_previews' in config['Options']:
        config['Options']['separate_previews'] = config['Options'].pop('seperate_previews')
    with open(config_path, 'w', encoding='utf-8') as f:
        config.write(f)
    
    # config.ini backwards compatibility fix (≤ v0.4) -> config option "naming_convention" & "update_recent_download" removed entirely
    options_to_remove = ['naming_convention', 'update_recent_download']
    for option in options_to_remove:
        if option in config['Options']:
            config['Options'].pop(option)
            with open(config_path, 'w', encoding='utf-8') as f:
                config.write(f)
            output(3, '\n WARNING', '<yellow>', f"Just removed \'{option}\' from the config.ini file,\n\
                   {6*' '}as the whole option is no longer supported after version 0.3.5")
    
    # get the version string of what we've just been updated to
    version_string = sys.argv[2]

    # check if old config.ini exists, compare each pre-existing value of it and apply it to new config.ini
    apply_old_config_values()
    
    # temporary: delete deprecated files
    delete_deprecated_files()

    # get release description and if existent; display it in terminal
    check_latest_release(update_version = version_string, intend = 'update')

    # read the config.ini file for a last time
    config.read(config_path)
else:
    # check if a new version is available
    check_latest_release(current_version = config.get('Other', 'version'), intend = 'check')


## read & verify config values
try:
    # TargetedCreator
    config_username = config.get('TargetedCreator', 'Username') # string

    # MyAccount
    config_token = config.get('MyAccount', 'Authorization_Token') # string
    config_useragent = config.get('MyAccount', 'User_Agent') # string

    # Options
    download_mode = config.get('Options', 'download_mode').capitalize() # Normal (Timeline & Messages), Timeline, Messages, Single (Single by post id) or Collections -> str
    show_downloads = config.getboolean('Options', 'show_downloads') # True, False -> boolean
    download_media_previews = config.getboolean('Options', 'download_media_previews') # True, False -> boolean
    open_folder_when_finished = config.getboolean('Options', 'open_folder_when_finished') # True, False -> boolean
    separate_messages = config.getboolean('Options', 'separate_messages') # True, False -> boolean
    separate_previews = config.getboolean('Options', 'separate_previews') # True, False -> boolean
    separate_timeline = config.getboolean('Options', 'separate_timeline') # True, False -> boolean
    utilise_duplicate_threshold = config.getboolean('Options', 'utilise_duplicate_threshold') # True, False -> boolean
    download_directory = config.get('Options', 'download_directory') # Local_directory, C:\MyCustomFolderFilePath -> str
    metadata_handling = config.get('Options', 'metadata_handling').capitalize() # Advanced, Simple -> str

    # Other
    current_version = config.get('Other', 'version') # str
except configparser.NoOptionError as e:
    error_string = str(e)
    output(2,'\n ERROR','<red>', f"Your config.ini file is very malformed, please download a fresh version of it from GitHub.\n{error_string}")
    input('\nPress Enter to close ...')
    exit()
except ValueError as e:
    error_string = str(e)
    if 'a boolean' in error_string:
        output(2,'\n [1]ERROR','<red>', f"\'{error_string.rsplit('boolean: ')[1]}\' is malformed in the configuration file! This value can only be True or False\n\
            {6*' '}Read the Wiki > Explanation of provided programs & their functionality > config.ini")
        open_url('https://github.com/Avnsx/fansly-downloader/wiki/Explanation-of-provided-programs-&-their-functionality#4-configini')
        input('\nPress Enter to close ...')
        exit()
    else:
        output(2,'\n [2]ERROR','<red>', f"You have entered a wrong value in the config.ini file -> \'{error_string}\'\n\
            {6*' '}Read the Wiki > Explanation of provided programs & their functionality > config.ini")
        open_url('https://github.com/Avnsx/fansly-downloader/wiki/Explanation-of-provided-programs-&-their-functionality#4-configini')
        input('\nPress Enter to close ...')
        exit()
except (KeyError, NameError) as key:
    output(2,'\n [3]ERROR','<red>', f"\'{key}\' is missing or malformed in the configuration file!\n\
        {6*' '}Read the Wiki > Explanation of provided programs & their functionality > config.ini")
    open_url('https://github.com/Avnsx/fansly-downloader/wiki/Explanation-of-provided-programs-&-their-functionality#4-configini')
    input('\nPress Enter to close ...')
    exit()


# update window title with specific downloader version
set_window_title(f"Fansly Downloader v{current_version}")


# delete previous redundant pyinstaller folders, older then an hour
def del_redudant_pyinstaller_files():
    try:
        base_path = sys._MEIPASS
    except Exception:
        return

    temp_dir = os.path.abspath(os.path.join(base_path, '..'))
    current_time = time.time()

    for folder in os.listdir(temp_dir):
        try:
            item = os.path.join(temp_dir, folder)
            if folder.startswith('_MEI') and os.path.isdir(item) and (current_time - os.path.getctime(item)) > 3600:
                for root, dirs, files in os.walk(item, topdown=False):
                    for file in files:
                        os.remove(os.path.join(root, file))
                    for dir in dirs:
                        os.rmdir(os.path.join(root, dir))
                os.rmdir(item)
        except Exception:
            pass
del_redudant_pyinstaller_files()


# occasionally notfiy user to star repository
def remind_stargazing():
    stargazers_count, total_downloads = 0, 0
    
    # depends on global variable current_version
    stats_headers = {'user-agent': f"Avnsx/Fansly Downloader {current_version}",
                     'referer': f"Avnsx/Fansly Downloader {current_version}",
                     'accept-language': 'en-US,en;q=0.9'}
    
    # get total_downloads count
    stargazers_check_request = requests.get('https://api.github.com/repos/avnsx/fansly-downloader/releases', allow_redirects = True, headers = stats_headers)
    if not stargazers_check_request.ok:
        return False
    stargazers_check_request = stargazers_check_request.json()
    for x in stargazers_check_request:
        total_downloads += x['assets'][0]['download_count'] or 0
    
    # get stargazers_count
    downloads_check_request = requests.get('https://api.github.com/repos/avnsx/fansly-downloader', allow_redirects = True, headers = stats_headers)
    if not downloads_check_request.ok:
        return False
    downloads_check_request = downloads_check_request.json()
    stargazers_count = downloads_check_request['stargazers_count'] or 0

    percentual_stars = round(stargazers_count / total_downloads * 100, 2)
    
    # display message (intentionally "lnfo" with lvl 4)
    output(4,'\n lnfo','<light-red>', f"Fansly Downloader was downloaded {total_downloads} times, but only {percentual_stars} % of You(!) have starred it.\n\
           {6*' '}Stars directly influence my willingness to continue maintaining the project.\n\
            {5*' '}Help the repository grow today, by leaving a star on it and sharing it to others online!")
    s(15)

if randint(1,100) <= 19:
    try:
        remind_stargazing()
    except Exception: # irrelevant enough, to pass regardless what errors may happen
        pass



## starting here: general validation of all input values in config.ini

# validate input value for config_username in config.ini
while True:
    usern_base_text = f'Invalid targeted creators username value; '
    usern_error = False

    if 'ReplaceMe' in config_username:
        output(3, '\n WARNING', '<yellow>', f"Config.ini value for TargetedCreator > Username > \'{config_username}\'; is unmodified.")
        usern_error = True

    # remove @ from username in config file & save changes
    if '@' in config_username and not usern_error:
        config_username = config_username.replace('@', '')
        config.set('TargetedCreator', 'username', config_username)
        with open(config_path, 'w', encoding='utf-8') as config_file:
            config.write(config_file)

    # intentionally dont want to just .strip() spaces, because like this, it might give the user a food for thought, that he's supposed to enter the username tag after @ and not creators display name
    if ' ' in config_username and not usern_error:
        output(3, ' WARNING', '<yellow>', f"{usern_base_text}must be a concatenated string. No spaces!\n")
        usern_error = True

    if not usern_error:
        if len(config_username) < 4 or len(config_username) > 30:
            output(3, ' WARNING', '<yellow>', f"{usern_base_text}must be between 4 and 30 characters long!\n")
            usern_error = True
        else:
            invalid_chars = set(config_username) - set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
            if invalid_chars:
                output(3, ' WARNING', '<yellow>', f"{usern_base_text}should only contain\n{20*' '}alphanumeric characters, hyphens, or underscores!\n")
                usern_error = True

    if not usern_error:
        output(1, '\n info', '<light-blue>', 'Username validation successful!')
        if config_username != config['TargetedCreator']['username']:
            config.set('TargetedCreator', 'username', config_username)
            with open(config_path, 'w', encoding='utf-8') as config_file:
                config.write(config_file)
        break
    else:
        output(5,'\n Config','<light-magenta>', f"Populate the value, with the username handle (e.g.: @MyCreatorsName)\n\
            {7*' '}of the fansly creator, whom you would like to download content from.")
        config_username = input(f"\n{19*' '} ► Enter a valid username: ")



# only if config_token is not set up already; verify if plyvel is installed
plyvel_installed, processed_from_path = False, None
if any([not config_token, 'ReplaceMe' in config_token]) or config_token and len(config_token) < 50:
    try:
        import plyvel
        plyvel_installed = True
    except ImportError:
        output(3,'\n WARNING','<yellow>', f"Fansly Downloaders automatic configuration for the authorization_token in the config.ini file will be skipped.\
            \n{20*' '}Your system is missing required plyvel (python module) builds by Siyao Chen (@liviaerxin).\
            \n{20*' '}Installable with \'pip3 install plyvel-ci\' or from github.com/liviaerxin/plyvel/releases/latest")

# semi-automatically set up value for config_token (authorization_token) based on the users input
if plyvel_installed and any([not config_token, 'ReplaceMe' in config_token, config_token and len(config_token) < 50]):
    
    # fansly-downloader plyvel dependant package imports
    from utils.config_util import (
        get_browser_paths,
        parse_browser_from_string,
        find_leveldb_folders,
        get_auth_token_from_leveldb_folder,
        process_storage_folders,
        link_fansly_downloader_to_account
    )

    output(3,'\n WARNING','<yellow>', f"Authorization token \'{config_token}\' is unmodified,\n\
        {12*' '}missing or malformed in the configuration file.\n\
        {12*' '}Will automatically configure by fetching fansly authorization token,\n\
        {12*' '}from all browser storages available on the local system.")

    browser_paths = get_browser_paths()
    processed_account = None
    
    for path in browser_paths:
        processed_token = None
    
        # if not firefox, process leveldb folders
        if 'firefox' not in path.lower():
            leveldb_folders = find_leveldb_folders(path)
            for folder in leveldb_folders:
                processed_token = get_auth_token_from_leveldb_folder(folder)
                if processed_token:
                    processed_account = link_fansly_downloader_to_account(processed_token)
                    break  # exit the inner loop if a valid processed_token is found
    
        # if firefox, process sqlite db instead
        else:
            processed_token = process_storage_folders(path)
            if processed_token:
                processed_account = link_fansly_downloader_to_account(processed_token)
    
        if all([processed_account, processed_token]):
            processed_from_path = parse_browser_from_string(path) # we might also utilise this for guessing the useragent

            # let user pick a account, to connect to fansly downloader
            output(5,'\n Config','<light-magenta>', f"Do you want to link the account \'{processed_account}\' to Fansly Downloader? (found in: {processed_from_path})")
            while True:
                user_input_acc_verify = input(f"{20*' '}► Type either \'Yes\' or \'No\': ").strip().lower()
                if user_input_acc_verify == "yes" or user_input_acc_verify == "no":
                    break # break user input verification
                else:
                    output(2,'\n ERROR','<red>', f"Please enter either \'Yes\' or \'No\', to decide if you want to link to \'{processed_account}\'")

            # based on user input; write account username & auth token to config.ini
            if user_input_acc_verify == "yes" and all([processed_account, processed_token]):
                config_token = processed_token
                config.set('MyAccount', 'authorization_token', config_token)
                with open(config_path, 'w', encoding='utf-8') as f:
                    config.write(f)
                output(1,'\n Info','<light-blue>', f"Success! Authorization token applied to config.ini file\n")
                break # break whole loop

    # if no account auth, was found in any of the users browsers
    if not processed_account:
        output(2,'\n ERROR','<red>', f"Your Fansly account was not found in any of your browser\'s local storage.\n\
        {10*' '}Did you not recently browse Fansly with an authenticated session?\
        {10*' '}Please read & apply the \'Get-Started\' tutorial instead.")
        open_url('https://github.com/Avnsx/fansly-downloader/wiki/Get-Started')
        input('\n Press Enter to close ..')
        exit()
    
    # if users decisions have led to auth token still being invalid
    elif any([not config_token, 'ReplaceMe' in config_token]) or config_token and len(config_token) < 50:
        output(2,'\n ERROR','<red>', f"Reached the end and the authentication token in config.ini file is still invalid!\n\
        {10*' '}Please read & apply the \'Get-Started\' tutorial instead.")
        open_url('https://github.com/Avnsx/fansly-downloader/wiki/Get-Started')
        input('\n Press Enter to close ..')
        exit()


# validate input value for "user_agent" in config.ini
ua_if_failed = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36' # if no matches / error just set random UA
def guess_user_agent(user_agents: dict, based_on_browser: str = processed_from_path or 'Chrome'):

    if processed_from_path == 'Microsoft Edge':
        based_on_browser = 'Edg' # msedge only reports "Edg" as its identifier

        # could do the same for opera, opera gx, brave. but those are not supported by @jnrbsn's repo. so we just return chrome ua
        # in general his repo, does not provide the most accurate latest user-agents, if I am borred some time in the future,
        # I might just write my own similar repo and use that instead

    try:
        os_name = platform.system()
        if os_name == "Windows":
            for user_agent in user_agents:
                if based_on_browser in user_agent and "Windows" in user_agent:
                    match = re.search(r'Windows NT ([\d.]+)', user_agent)
                    if match:
                        os_version = match.group(1)
                        if os_version in user_agent:
                            return user_agent
        elif os_name == "Darwin":  # macOS
            for user_agent in user_agents:
                if based_on_browser in user_agent and "Macintosh" in user_agent:
                    match = re.search(r'Mac OS X ([\d_.]+)', user_agent)
                    if match:
                        os_version = match.group(1).replace('_', '.')
                        if os_version in user_agent:
                            return user_agent
        elif os_name == "Linux":
            for user_agent in user_agents:
                if based_on_browser in user_agent and "Linux" in user_agent:
                    match = re.search(r'Linux ([\d.]+)', user_agent)
                    if match:
                        os_version = match.group(1)
                        if os_version in user_agent:
                            return user_agent
    except Exception:
        output(2,'\n [4]ERROR','<red>', f'Regexing user-agent from online source failed: {traceback.format_exc()}')

    output(3, '\n WARNING', '<yellow>', f"Missing user-agent for {based_on_browser} & os: {os_name}. Set chrome & windows ua instead")
    return ua_if_failed

if not config_useragent or config_useragent and len(config_useragent) < 40 or 'ReplaceMe' in config_useragent:
    output(3, '\n WARNING', '<yellow>', f"Browser user-agent in config.ini \'{config_useragent}\', is most likely incorrect.")
    if processed_from_path:
        output(5,'\n Config','<light-magenta>', f"Will adjust it with a educated guess;\n\
            {7*' '}based on the combination of your operating system & specific browser")
    else:
        output(5,'\n Config','<light-magenta>', f"Will adjust it with a educated guess, hard-set for chrome browser.\n\
            {7*' '}If you're not using chrome, you might want to replace it in the config.ini file later on.\n\
            {7*' '}more information regarding this topic is on the fansly downloader Wiki.")

    try:
        # thanks Jonathan Robson (@jnrbsn) - for continously providing these up-to-date user-agents
        user_agent_req = requests.get('https://jnrbsn.github.io/user-agents/user-agents.json', headers = {'User-Agent': f"Avnsx/Fansly Downloader {current_version}", 'accept-language': 'en-US,en;q=0.9'})
        if user_agent_req.ok:
            user_agent_req = user_agent_req.json()
            config_useragent = guess_user_agent(user_agent_req)
        else:
            config_useragent = ua_if_failed
    except requests.exceptions.RequestException:
        config_useragent = ua_if_failed

    # save useragent modification to config file
    config.set('MyAccount', 'user_agent', config_useragent)
    with open(config_path, 'w', encoding='utf-8') as config_file:
        config.write(config_file)

    output(1,'\n Info','<light-blue>', f"Success! Applied a browser user-agent to config.ini file\n")



## starting here: general epoch timestamp to local timezone manipulation
# calculates offset from global utc time, to local systems time
def compute_timezone_offset():
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    diff_from_utc = int(offset / 60 / 60 * -1)
    hours_in_seconds = diff_from_utc * 3600 * -1
    return diff_from_utc, hours_in_seconds

# compute timezone offset and hours in seconds once
diff_from_utc, hours_in_seconds = compute_timezone_offset()

# detect 12 vs 24 hour time format usage (not sure if this properly works)
time_format = 12 if ('AM' in time.strftime('%X') or 'PM' in time.strftime('%X')) else 24

# convert every epoch timestamp passed, to the time it was for the local computers timezone
def get_adjusted_datetime(epoch_timestamp: int, diff_from_utc: int = diff_from_utc, hours_in_seconds: int = hours_in_seconds):
    adjusted_timestamp = epoch_timestamp + diff_from_utc * 3600
    adjusted_timestamp += hours_in_seconds
    # start of strings are ISO 8601; so that they're sortable by Name after download
    if time_format == 24:
        return time.strftime("%Y-%m-%d_at_%H-%M", time.localtime(adjusted_timestamp))
    else:
        return time.strftime("%Y-%m-%d_at_%I-%M-%p", time.localtime(adjusted_timestamp))



## starting here: current working directory generation & validation
# if the users custom provided filepath is invalid; a tkinter dialog will open during runtime, asking to adjust download path
def ask_correct_dir():
    global BASE_DIR_NAME
    root = Tk()
    root.withdraw()
    BASE_DIR_NAME = filedialog.askdirectory()
    if BASE_DIR_NAME:
        output(1,'\n Info','<light-blue>', f"Chose folder file path {BASE_DIR_NAME}")
        return BASE_DIR_NAME
    else:
        output(2,'\n [5]ERROR','<red>', f"Could not register your chosen folder file path. Please close and start all over again!")
        s(15)
        exit() # this has to force exit

# generate a base directory; every module (Timeline, Messages etc.) calls this to figure out the right directory path
BASE_DIR_NAME = None # required in global space
def generate_base_dir(creator_name_to_create_for: str, module_requested_by: str):
    global BASE_DIR_NAME, download_directory, separate_messages, separate_timeline
    if 'Local_dir' in download_directory: # if user didn't specify custom downloads path
        if "Collection" in module_requested_by:
            BASE_DIR_NAME = join(getcwd(), 'Collections')
        elif "Message" in module_requested_by and separate_messages:
            BASE_DIR_NAME = join(getcwd(), creator_name_to_create_for+'_fansly', 'Messages')
        elif "Timeline" in module_requested_by and separate_timeline:
            BASE_DIR_NAME = join(getcwd(), creator_name_to_create_for+'_fansly', 'Timeline')
        else:
            BASE_DIR_NAME = join(getcwd(), creator_name_to_create_for+'_fansly') # use local directory
    elif os.path.isdir(download_directory): # if user specified a correct custom downloads path
        if "Collection" in module_requested_by:
            BASE_DIR_NAME = join(download_directory, 'Collections')
        elif "Message" in module_requested_by and separate_messages:
            BASE_DIR_NAME = join(download_directory, creator_name_to_create_for+'_fansly', 'Messages')
        elif "Timeline" in module_requested_by and separate_timeline:
            BASE_DIR_NAME = join(download_directory, creator_name_to_create_for+'_fansly', 'Timeline')
        else:
            BASE_DIR_NAME = join(download_directory, creator_name_to_create_for+'_fansly') # use their custom path & specify new folder for the current creator in it
        output(1,' Info','<light-blue>', f"Acknowledging custom basis download directory: \'{download_directory}\'")
    else: # if their set directory, can't be found by the OS
        output(3,'\n WARNING','<yellow>', f"The custom basis download directory file path: \'{download_directory}\'; seems to be invalid!\
            \n{20*' '}Please change it, to a correct file path for example: \'C:/MyFanslyDownloads\'\
            \n{20*' '}You could also just change it back to the default argument: \'Local_directory\'\n\
            \n{20*' '}A explorer window to help you set the correct path, will open soon!\n\
            \n{20*' '}Preferably right click inside the explorer, to create a new folder\
            \n{20*' '}Select it and the folder will be used as the default download directory")
        s(10) # give user time to realise instructions were given
        download_directory = ask_correct_dir() # ask user to select correct path using tkinters explorer dialog
        config.set('Options', 'download_directory', download_directory) # set corrected path inside the config
        # save the config permanently into config.ini
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        if "Collection" in module_requested_by:
            BASE_DIR_NAME = join(download_directory, 'Collections')
        elif "Message" in module_requested_by and separate_messages:
            BASE_DIR_NAME = join(download_directory, creator_name_to_create_for+'_fansly', 'Messages')
        elif "Timeline" in module_requested_by and separate_timeline:
            BASE_DIR_NAME = join(download_directory, creator_name_to_create_for+'_fansly', 'Timeline')
        else:
            BASE_DIR_NAME = join(download_directory, creator_name_to_create_for+'_fansly') # use their custom path & specify new folder for the current creator in it

    # validate BASE_DIR_NAME; if current download folder wasn't created with content separation, disable it for this download session too
    correct_File_Hierarchy, tmp_BDR = True, BASE_DIR_NAME.partition('_fansly')[0] + '_fansly'
    if os.path.isdir(tmp_BDR):
        for directory in os.listdir(tmp_BDR):
            if os.path.isdir(join(tmp_BDR, directory)):
                if 'Pictures' in directory and any([separate_messages, separate_timeline]):
                    correct_File_Hierarchy = False
                if 'Videos' in directory and any([separate_messages, separate_timeline]):
                    correct_File_Hierarchy = False
        if not correct_File_Hierarchy:
            output(3, '\n WARNING', '<yellow>', f"Due to the presence of \'Pictures\' and \'Videos\' sub-directories in the current download folder;\
                \n{20*' '}content separation will remain disabled throughout this current downloading session.")
            separate_messages, separate_timeline = False, False
        
            # utilize recursion to fix BASE_DIR_NAME generation
            generate_base_dir(creator_name_to_create_for, module_requested_by)

    return BASE_DIR_NAME



# utilized to open the download directory in file explorer; once the download process has finished
def open_location(filepath: str):
    plat = platform.system()

    if not open_folder_when_finished:
        return False
    
    if not os.path.isfile(filepath) and not os.path.isdir(filepath):
        return False
    
    # tested below and they work to open folder locations
    if plat == 'Windows':
        os.startfile(filepath) # verified works
    elif plat == 'Linux':
        subprocess.run(['xdg-open', filepath], shell=False) # verified works
    elif plat == 'Darwin':
        subprocess.run(['open', filepath], shell=False) # verified works
    
    return True



# un/scramble auth token
F, c ='fNs', config_token
if c[-3:]==F:
    c=c.rstrip(F)
    A,B,C=['']*len(c),7,0
    for D in range(B):
        for E in range(D,len(A),B):A[E]=c[C];C+=1
    config_token = ''.join(A)


# general headers; which the whole code uses 
headers = {
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://fansly.com/',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': config_token,
    'User-Agent': config_useragent,
}



# m3u8 compability
def download_m3u8(m3u8_url: str, save_path: str):
    # parse m3u8_url for required strings
    parsed_url = {k: v for k, v in [s.split('=') for s in m3u8_url.split('?')[-1].split('&')]}
    policy = parsed_url.get('Policy')
    key_pair_id = parsed_url.get('Key-Pair-Id')
    signature = parsed_url.get('Signature')
    m3u8_url = m3u8_url.split('.m3u8')[0] + '.m3u8' # re-construct original .m3u8 base link
    split_m3u8_url = m3u8_url.rsplit('/', 1)[0] # used for constructing .ts chunk links
    save_path = save_path.rsplit('.m3u8')[0] # remove file_extension from save_path

    cookies = {
        'CloudFront-Key-Pair-Id': key_pair_id,
        'CloudFront-Policy': policy,
        'CloudFront-Signature': signature,
    }

    # download the m3u8 playlist
    playlist_content_req = sess.get(m3u8_url, headers=headers, cookies=cookies)
    if not playlist_content_req.ok:
        output(2,'\n [12]ERROR','<red>', f'Failed downloading m3u8; at playlist_content request. Response code: {playlist_content_req.status_code}\n{playlist_content_req.text}')
        return False
    playlist_content = playlist_content_req.text

    # parse the m3u8 playlist content using the m3u8 library
    playlist_obj = m3u8.loads(playlist_content)

    # get a list of all the .ts files in the playlist
    ts_files = [segment.uri for segment in playlist_obj.segments if segment.uri.endswith('.ts')]

    # define a nested function to download a single .ts file and return the content
    def download_ts(ts_file: str):
        ts_url = f"{split_m3u8_url}/{ts_file}"
        ts_response = sess.get(ts_url, headers=headers, cookies=cookies, stream=True)
        buffer = io.BytesIO()
        for chunk in ts_response.iter_content(chunk_size=1024):
            buffer.write(chunk)
        ts_content = buffer.getvalue()
        return ts_content

    # if m3u8 seems like it might be bigger in total file size; display loading bar
    text_column = TextColumn(f"", table_column=Column(ratio=0.355))
    bar_column = BarColumn(bar_width=60, table_column=Column(ratio=2))
    disable_loading_bar = False if len(ts_files) > 15 else True
    progress = Progress(text_column, bar_column, expand=True, transient=True, disable = disable_loading_bar)
    with progress:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            ts_contents = [file for file in progress.track(executor.map(download_ts, ts_files), total=len(ts_files))]
    
    segment = bytearray()
    for ts_content in ts_contents:
        segment += ts_content
    
    input_container = av.open(io.BytesIO(segment), format='mpegts')
    video_stream = input_container.streams.video[0]
    audio_stream = input_container.streams.audio[0]

    # define output container and streams
    output_container = av.open(f"{save_path}.mp4", 'w') # add .mp4 file extension
    video_stream = output_container.add_stream(template=video_stream)
    audio_stream = output_container.add_stream(template=audio_stream)

    start_pts = None
    for packet in input_container.demux():
        if packet.dts is None:
            continue

        if start_pts is None:
            start_pts = packet.pts

        packet.pts -= start_pts
        packet.dts -= start_pts

        if packet.stream == input_container.streams.video[0]:
            packet.stream = video_stream
        elif packet.stream == input_container.streams.audio[0]:
            packet.stream = audio_stream
        output_container.mux(packet)

    # close containers
    input_container.close()
    output_container.close()

    return True



# define base threshold (used for when modules don't provide vars)
DUPLICATE_THRESHOLD = 50

"""
The purpose of this error is to prevent unnecessary computation or requests to fansly.
Will stop downloading, after reaching either the base DUPLICATE_THRESHOLD or 20% of total content.

To maintain logical consistency, users have the option to disable this feature;
e.g. a user downloads only 20% of a creator's media and then cancels the download, afterwards tries
to update that folder -> the first 20% will report completed -> cancels the download -> other 80% missing
"""
class DuplicateCountError(Exception):
    def __init__(self, duplicate_count):
        self.duplicate_count = duplicate_count
        self.message = f"Irrationally high rise in duplicates: {duplicate_count}"
        super().__init__(self.message)

pic_count, vid_count, duplicate_count = 0, 0, 0 # count downloaded content & duplicates, from all modules globally

# deduplication functionality variables
recent_photo_media_ids, recent_video_media_ids, recent_audio_media_ids = set(), set(), set()
recent_photo_hashes, recent_video_hashes, recent_audio_hashes = set(), set(), set()

def sort_download(accessible_media: dict):
    # global required so we can use them at the end of the whole code in global space
    global pic_count, vid_count, save_dir, recent_photo_media_ids, recent_video_media_ids, recent_audio_media_ids, recent_photo_hashes, recent_video_hashes, recent_audio_hashes, duplicate_count
    
    # loop through the accessible_media and download the media files
    for post in accessible_media:
        # extract the necessary information from the post
        media_id = post['media_id']
        created_at = get_adjusted_datetime(post['created_at'])
        mimetype = post['mimetype']
        download_url = post['download_url']
        file_extension = post['file_extension']
        is_preview = post['is_preview']
        metadata_manager = MetadataManager()
        ext_sup = metadata_manager.is_file_supported('mp4' if file_extension == 'm3u8' else file_extension)
        append_metadata = metadata_handling == 'Advanced' and ext_sup if metadata_handling == 'Advanced' and ext_sup else False

        # verify that the duplicate count has not drastically spiked and in-case it did; verify that the spiked amount is significant enough to cancel scraping
        if utilise_duplicate_threshold and duplicate_count > DUPLICATE_THRESHOLD and DUPLICATE_THRESHOLD > 50:
            raise DuplicateCountError(duplicate_count)

        if append_metadata:
            filename = f"{created_at}_preview.{file_extension}" if is_preview else f"{created_at}.{file_extension}"
            metadata_manager.set_filepath(filename) # set basic filename, so the class can tell its file extension already
            metadata_manager.set_custom_metadata("ID", media_id)
        else:
            # general filename construction & if content is a preview; add that into its filename
            filename = f"{created_at}_preview_id_{media_id}.{file_extension}" if is_preview else f"{created_at}_id_{media_id}.{file_extension}"

        # deduplication - part 1: decide if this media is even worth further processing; by media id
        if any([media_id in recent_photo_media_ids, media_id in recent_video_media_ids]):
            output(1,' Info','<light-blue>', f"Deduplication [Media ID]: {mimetype.split('/')[-2]} \'{filename}\' → declined")
            duplicate_count += 1
            continue
        else:
            if 'image' in mimetype:
                recent_photo_media_ids.add(media_id)
            elif 'video' in mimetype:
                recent_video_media_ids.add(media_id)
            elif 'audio' in mimetype:
                recent_audio_media_ids.add(media_id)

        # for collections downloads we just put everything into the same folder
        if "Collection" in download_mode:
            save_path = join(BASE_DIR_NAME, filename)
            save_dir = join(BASE_DIR_NAME, filename) # compatibility for final "Download finished...!" print

            if not exists(BASE_DIR_NAME):
                makedirs(BASE_DIR_NAME, exist_ok = True)

        # for every other type of download; we do want to determine the sub-directory to save the media file based on the mimetype
        else:
            if 'image' in mimetype:
                save_dir = join(BASE_DIR_NAME, "Pictures")
            elif 'video' in mimetype:
                save_dir = join(BASE_DIR_NAME, "Videos")
            elif 'audio' in mimetype:
                save_dir = join(BASE_DIR_NAME, "Audio")
            else:
                # if the mimetype is neither image nor video, skip the download
                output(3,'\n WARNING','<yellow>', f"Unknown mimetype; skipping download for mimetype: \'{mimetype}\' | media_id: {media_id}")
                continue
            
            # decides to separate previews or not
            if is_preview and separate_previews:
                save_path = join(save_dir, 'Previews', filename)
                save_dir = join(save_dir, 'Previews')
            else:
                save_path = join(save_dir, filename)

            if not exists(save_dir):
                makedirs(save_dir, exist_ok = True)
        
        # if show_downloads is True / downloads should be shown
        if show_downloads:
            output(1,' Info','<light-blue>', f"Downloading {mimetype.split('/')[-2]} \'{filename}\'")

        if file_extension == 'm3u8':
            # handle the download of a m3u8 file
            file_downloaded = download_m3u8(m3u8_url = download_url, save_path = save_path)
            if file_downloaded:
                # after being transcoded, the file is now a mp4
                save_path = save_path.replace('.m3u8', '.mp4')
                file_extension = 'mp4'
                if append_metadata:
                    # add the temp-stored media_id to the now transcoded mp4 file, as Exif metadata
                    metadata_manager.set_filepath(save_path)
                    metadata_manager.add_metadata()
                    metadata_manager.save()
                    # add filehash to the transcoded mp4 file
                    hash_audio_video(save_path, content_format = 'video')
                pic_count += 1 if 'image' in mimetype else 0; vid_count += 1 if 'video' in mimetype else 0
        else:
            # handle the download of a normal media file
            response = sess.get(download_url, stream=True, headers=headers)

            if response.ok:
                text_column = TextColumn(f"", table_column=Column(ratio=0.355))
                bar_column = BarColumn(bar_width=60, table_column=Column(ratio=2))
                file_size = int(response.headers.get('content-length', 0))
                disable_loading_bar = False if file_size and file_size >= 20000000 else True # if file size is above 20MB; display loading bar
                progress = Progress(text_column, bar_column, expand=True, transient=True, disable = disable_loading_bar)
                task_id = progress.add_task('', total=file_size)
                progress.start()
                # iterate over the response data in chunks
                content = bytearray()
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        content += chunk
                        progress.advance(task_id, len(chunk))
                progress.refresh()
                progress.stop()
                
                file_hash = None
                # utilise hashing for images
                if 'image' in mimetype:
                    # open the image
                    img = Image.open(io.BytesIO(content))

                    # calculate the hash of the resized image
                    photohash = str(imagehash.phash(img, hash_size = 16))

                    # deduplication - part 2.1: decide if this photo is even worth further processing; by hashing
                    if photohash in recent_photo_hashes:
                        output(1,' Info','<light-blue>', f"Deduplication [Hashing]: {mimetype.split('/')[-2]} \'{filename}\' → declined")
                        duplicate_count += 1
                        continue
                    else:
                        recent_photo_hashes.add(photohash)

                    # close the image
                    img.close()

                    file_hash = photohash

                # utilise hashing for videos
                elif 'video' in mimetype:
                    videohash = hashlib.md5(content).hexdigest()

                    # deduplication - part 2.2: decide if this video is even worth further processing; by hashing
                    if videohash in recent_video_hashes:
                        output(1,' Info','<light-blue>', f"Deduplication [Hashing]: {mimetype.split('/')[-2]} \'{filename}\' → declined")
                        duplicate_count += 1
                        continue
                    else:
                        recent_video_hashes.add(videohash)

                    file_hash = videohash
                
                # utilise hashing for audio
                elif 'audio' in mimetype:
                    audiohash = hashlib.md5(content).hexdigest()

                    # deduplication - part 2.2: decide if this audio is even worth further processing; by hashing
                    if audiohash in recent_audio_hashes:
                        output(1,' Info', '<light-blue>', f"Deduplication [Hashing]: {mimetype.split('/')[-2]} \'{filename}\' → declined")
                        duplicate_count += 1
                        continue
                    else:
                        recent_audio_hashes.add(audiohash)

                    file_hash = audiohash

                if append_metadata:
                    metadata_manager.set_custom_metadata("HSH", file_hash)
                    # finally write the full file to disk
                    with open(save_path, 'wb') as f:
                        f.write(content)
                    # set finalized filepath instead of dummy filename and write the previously temp-stored metadata
                    metadata_manager.set_filepath(save_path)
                    metadata_manager.add_metadata()
                    metadata_manager.save()
                else:
                    # hacky overwrite for save_path to introduce file hash to filename
                    base_path, extension = os.path.splitext(save_path)
                    save_path = f"{base_path}_hash_{file_hash}{extension}"
                    with open(save_path, 'wb') as f:
                        f.write(content)

                # we only count them if the file was actually written
                pic_count += 1 if 'image' in mimetype else 0; vid_count += 1 if 'video' in mimetype else 0
            else:
                output(2,'\n [13]ERROR','<red>', f"Download failed on filename: {filename} - due to an network error --> status_code: {response.status_code} | content: \n{response.content}")
                input()
                exit()
    s(uniform(2, 4)) # slow down to avoid the fansly rate-limit, which was introduced in late august 2023

    # all functions call sort_download at the end; which means we leave this function open ended, so that the python executor can get back into executing in global space @ the end of the global space code / loop this function repetetively as seen in timeline code



# whole code uses this; whenever any json response needs to get parsed from fansly api
def parse_media_info(media_info: dict, post_id = None):
    # initialize variables
    highest_variants_resolution_url, download_url, file_extension, metadata, default_normal_locations, default_normal_mimetype, mimetype =  None, None, None, None, None, None, None
    created_at, media_id, highest_variants_resolution, highest_variants_resolution_height, default_normal_height = 0, 0, 0, 0, 0

    # check if media is a preview
    is_preview = media_info['previewId'] is not None
    
    # fix rare bug, of free / paid content being counted as preview
    if is_preview:
        if media_info['access']:
            is_preview = False

    def simplify_mimetype(mimetype: str):
        if mimetype == 'application/vnd.apple.mpegurl':
            mimetype = 'video/mp4'
        elif mimetype == 'audio/mp4': # another bug in fansly api, where audio is served as mp4 filetype ..
            mimetype = 'audio/mp3' # i am aware that the correct mimetype would be "audio/mpeg", but we just simplify it
        return mimetype

    # variables in api "media" = "default_" & "preview" = "preview" in our code
    # parse normal basic (paid/free) media from the default location, before parsing its variants (later on we compare heights, to determine which one we want)
    if not is_preview:
        default_normal_locations = media_info['media']['locations']
        
        default_details = media_info['media']
        default_normal_id = int(default_details['id'])
        default_normal_created_at = int(default_details['createdAt']) + randint(-1800, 1800)
        default_normal_mimetype = simplify_mimetype(default_details['mimetype'])
        default_normal_height = default_details['height'] or 0

    # if its a preview, we take the default preview media instead
    elif is_preview:
        default_normal_locations = media_info['preview']['locations']

        default_details = media_info['preview']
        default_normal_id = int(media_info['preview']['id'])
        default_normal_created_at = int(default_details['createdAt']) + randint(-1800, 1800)
        default_normal_mimetype = simplify_mimetype(default_details['mimetype'])
        default_normal_height = default_details['height'] or 0

    if default_details['locations']:
        default_normal_locations = default_details['locations'][0]['location']

    # locally fixes fansly api highest current_variant_resolution height bug
    def parse_variant_metadata(variant_metadata: str):
        variant_metadata = json.loads(variant_metadata)
        max_variant = max(variant_metadata['variants'], key=lambda variant: variant['h'], default=None)
        # if a heighest height is not found, we just hope 1080p is available
        if not max_variant:
            return 1080
        # else parse through variants and find highest height
        if max_variant['w'] < max_variant['h']:
            max_variant['w'], max_variant['h'] = max_variant['h'], max_variant['w']
        return max_variant['h']

    def parse_variants(content: dict, content_type: str): # content_type: media / preview
        nonlocal metadata, highest_variants_resolution, highest_variants_resolution_url, download_url, media_id, created_at, highest_variants_resolution_height, default_normal_mimetype, mimetype
        if content.get('locations'):
            location_url = content['locations'][0]['location']

            current_variant_resolution = (content['width'] or 0) * (content['height'] or 0)
            if current_variant_resolution > highest_variants_resolution and default_normal_mimetype == simplify_mimetype(content['mimetype']):
                highest_variants_resolution = current_variant_resolution
                highest_variants_resolution_height = content['height'] or 0
                highest_variants_resolution_url = location_url
                media_id = int(content['id'])
                mimetype = simplify_mimetype(content['mimetype'])

                # if key-pair-id is not in there we'll know it's the new .m3u8 format, so we construct a generalised url, which we can pass relevant auth strings with
                # note: this url won't actually work, its purpose is to just pass the strings through the download_url variable
                if not 'Key-Pair-Id' in highest_variants_resolution_url:
                    try:
                        # use very specific metadata, bound to the specific media to get auth info
                        metadata = content['locations'][0]['metadata']
                        highest_variants_resolution_url = f"{highest_variants_resolution_url.split('.m3u8')[0]}_{parse_variant_metadata(content['metadata'])}.m3u8?ngsw-bypass=true&Policy={metadata['Policy']}&Key-Pair-Id={metadata['Key-Pair-Id']}&Signature={metadata['Signature']}"
                    except KeyError:pass # we pass here and catch below

                """
                parse fanslys date feature called "scheduled post" dates, these might greatly differ from actual post dates.
                just google it for better understanding, they have a whole FAQ about it.
                in the future we might just change this to actual post publishing dates, so users can better cross-reference the posts on the website.

                note: images would be overwriting each other due to uniqueness of filenames, so we are forced to add randint(-1800, 1800) to epoch timestamps
                """
                try:
                    created_at = int(content['updatedAt']) + randint(-1800, 1800)
                except Exception:
                    created_at = int(media_info[content_type]['createdAt']) + randint(-1800, 1800)
        download_url = highest_variants_resolution_url


    # somehow unlocked / paid media: get download url from media location
    if 'location' in media_info['media']:
        variants = media_info['media']['variants']
        for content in variants:
            parse_variants(content = content, content_type = 'media')

    # previews: if media location is not found, we work with the preview media info instead
    if not download_url and 'preview' in media_info:
        variants = media_info['preview']['variants']
        for content in variants:
            parse_variants(content = content, content_type = 'preview')

    """
    so the way this works is; we have these 4 base variables defined all over this function.
    parse_variants() will initially overwrite them with values from each contents variants above.
    then right below, we will compare the values and decide which media has the higher resolution. (default populated content vs content from variants)
    or if variants didn't provide a higher resolution at all, we just fall back to the default content
    """
    if all([default_normal_locations, highest_variants_resolution_url, default_normal_height, highest_variants_resolution_height]) and all([default_normal_height > highest_variants_resolution_height, default_normal_mimetype == mimetype]) or not download_url:
        # overwrite default variable values, which we will finally return; with the ones from the default media
        media_id = default_normal_id
        created_at = default_normal_created_at
        mimetype = default_normal_mimetype
        download_url = default_normal_locations

    # due to fansly may 2023 update
    if download_url:
        # parse file extension separately 
        file_extension = download_url.split('/')[-1].split('.')[-1].split('?')[0]

        if file_extension == 'mp4' and mimetype == 'audio/mp3':
            file_extension = 'mp3'

        # if metadata didn't exist we need the user to notify us through github, because that would be detrimental
        if not 'Key-Pair-Id' in download_url and not metadata:
            output(2,'\n [14]ERROR','<red>', f"Failed downloading a video! Please open a GitHub issue ticket called \'Metadata missing\' and copy paste this:\n\
                \n\tMetadata Missing\n\tpost_id: {post_id} & media_id: {media_id} & config_username: {config_username}\n")
            input('Press Enter to attempt continuing download ...')
    
    return {'media_id': media_id, 'created_at': created_at, 'mimetype': mimetype, 'file_extension': file_extension, 'is_preview': is_preview, 'download_url': download_url}



## starting here: deduplication functionality
# variables used: recent_photo_media_ids, recent_video_media_ids recent_audio_media_ids, recent_photo_hashes, recent_video_hashes, recent_audio_hashes
# these are defined globally above sort_download() though

# exclusively used for extracting media_id from pre-existing filenames
def extract_media_id(filename: str, filepath: str):
    # if media_id in filename
    match = re.search(r'_id_(\d+)', filename)
    if match:
        return int(match.group(1))
    # if media_id within Exif metadata
    metadata_manager = MetadataManager()
    metadata_manager.read_metadata(filepath=filepath)
    file_metadata = metadata_manager.formatted_metadata()
    if 'ID' in file_metadata:
        return file_metadata['ID']
    return

# exclusively used for extracting hash from pre-existing filenames
def extract_file_hash(filename: str, filepath: str):
    # if filehash in filename
    match = re.search(r'_hash_([a-fA-F0-9]+)', filename)
    if match:
        return match.group(1)
    # if filehash within Exif metadata
    metadata_manager = MetadataManager()
    metadata_manager.read_metadata(filepath=filepath)
    file_metadata = metadata_manager.formatted_metadata()
    if 'HSH' in file_metadata:
        return file_metadata['HSH']
    return

# exclusively used for adding hash to pre-existing filenames
def add_hash_to_filename(filename: str, file_hash: str):
    base_name, extension = os.path.splitext(filename)
    hash_suffix = f"_hash_{file_hash}{extension}"

    # adjust filename for 255 bytes filename limit, on all common operating systems
    max_length = 250
    if len(base_name) + len(hash_suffix) > max_length:
        base_name = base_name[:max_length - len(hash_suffix)]
    
    return f"{base_name}{hash_suffix}"

# exclusively used for hashing images from pre-existing download directories
def hash_image(filepath: str):
    try:
        filename = os.path.basename(filepath)
        file_extension = filename.rsplit('.')[1]

        media_id = extract_media_id(filename, filepath)
        if media_id:
            recent_photo_media_ids.add(media_id)

        existing_hash = extract_file_hash(filename, filepath)
        if existing_hash:
            recent_photo_hashes.add(existing_hash)
        else:
            # if image hash doesn't pre-exist, generate one using imagehash
            img = Image.open(filepath)
            file_hash = str(imagehash.phash(img, hash_size = 16))
            recent_photo_hashes.add(file_hash)
            img.close()
            
            metadata_manager = MetadataManager()
            ext_sup = metadata_manager.is_file_supported(file_extension)
            if ext_sup:
                # if Exif metadata adding is supported for file extension
                metadata_manager.set_filepath(filepath)
                metadata_manager.set_custom_metadata("HSH", file_hash)
                metadata_manager.add_metadata()
                metadata_manager.save()
            else:
                # else fall back to adding filehash to filename
                new_filename = add_hash_to_filename(filename, file_hash)
                new_filepath = join(os.path.dirname(filepath), new_filename)
                os.rename(filepath, new_filepath)
                filepath = new_filepath
    except FileExistsError:
        os.remove(filepath)
    except Exception:
        output(2,'\n [15]ERROR','<red>', f"\nError processing image \'{filepath}\': {traceback.format_exc()}")

# exclusively used for hashing videos & audio from pre-existing download directories
def hash_audio_video(filepath: str, content_format: str):
    global recent_video_hashes, recent_audio_hashes, recent_video_media_ids, recent_audio_media_ids
    try:
        filename = os.path.basename(filepath)
        file_extension = filename.rsplit('.')[1]

        media_id = extract_media_id(filename, filepath)
        if media_id:
            if content_format == 'video':
                recent_video_media_ids.add(media_id)
            elif content_format == 'audio':
                recent_audio_media_ids.add(media_id)

        existing_hash = extract_file_hash(filename, filepath)
        if existing_hash:
            if content_format == 'video':
                recent_video_hashes.add(existing_hash)
            elif content_format == 'audio':
                recent_audio_hashes.add(existing_hash)
        else:
            # utilise md5 hashing for videos and audio
            h = hashlib.md5()
            with open(filepath, 'rb') as f:
                while (part := f.read(1_048_576)):
                    h.update(part)
            file_hash = h.hexdigest()
            if content_format == 'video':
                recent_video_hashes.add(file_hash)
            elif content_format == 'audio':
                recent_audio_hashes.add(file_hash)
            
            metadata_manager = MetadataManager()
            ext_sup = metadata_manager.is_file_supported(file_extension)
            if ext_sup:
                # if Exif metadata adding is supported for file extension
                metadata_manager.set_filepath(filepath)
                metadata_manager.set_custom_metadata("HSH", file_hash)
                metadata_manager.add_metadata()
                metadata_manager.save()
            else:
                # else fall back to adding filehash to filename
                new_filename = add_hash_to_filename(filename, file_hash)
                new_filepath = join(os.path.dirname(filepath), new_filename)
                os.rename(filepath, new_filepath)
                filepath = new_filepath
    except FileExistsError:
        os.remove(filepath)
    except Exception:
        output(2,'\n [16]ERROR','<red>', f"\nError processing {content_format} \'{filepath}\': {traceback.format_exc()}")

# exclusively used for processing pre-existing files from previous downloads
def process_file(file_path: str):
    mimetype, _ = mimetypes.guess_type(file_path)
    if mimetype is not None:
        if mimetype.startswith('image'):
            hash_image(file_path)
        elif mimetype.startswith('video'):
            hash_audio_video(file_path, content_format = 'video')
        elif mimetype.startswith('audio'):
            hash_audio_video(file_path, content_format = 'audio')

# exclusively used for processing pre-existing folders from previous downloads
def process_folder(folder_path: str):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for root, dirs, files in os.walk(folder_path):
            file_paths = [join(root, file) for file in files]
            executor.map(process_file, file_paths)
    return True


if os.path.isdir(generate_base_dir(config_username, download_mode)):
    output(1,' Info','<light-blue>', f"Deduplication is automatically enabled for;\n{17*' '}{BASE_DIR_NAME}")
    
    if process_folder(BASE_DIR_NAME):
        output(1,' Info','<light-blue>', f"Deduplication process is complete! Each new download will now be compared\
            \n{17*' '}against a total of {len(recent_photo_hashes)} photo & {len(recent_video_hashes)} video hashes and corresponding media IDs.")

    # print("Recent Photo Hashes:", recent_photo_hashes)
    # print("Recent Photo Media IDs:", recent_photo_media_ids)
    # print("Recent Video Hashes:", recent_video_hashes)
    # print("Recent Video Media IDs:", recent_video_media_ids)

    if randint(1,100) <= 19:
        output(3, '\n WARNING', '<yellow>', f"Reminder; If you remove id_NUMBERS or hash_STRING from filenames of previously downloaded files,\
            \n{20*' '}they will no longer be compatible with fansly downloaders deduplication algorithm. Generally modifying the filename,\
            \n{20*' '}is not advised and might cause unexpected behaviour.")


## starting here: stuff that literally every download mode uses, which should be executed at the very first everytime
if download_mode:
    output(1,' Info','<light-blue>', f"Using user-agent: \'{config_useragent[:28]} [...] {config_useragent[-35:]}\'")
    output(1,' Info','<light-blue>', f"Open download folder when finished, is set to: \'{open_folder_when_finished}\'")
    output(1,' Info','<light-blue>', f"Downloading files marked as preview, is set to: \'{download_media_previews}\'")

    if download_media_previews:output(3,'\n WARNING','<yellow>', 'Previews downloading is enabled; repetitive and/or emoji spammed media might be downloaded!')



## starting here: download_mode = Single
if download_mode == 'Single':
    output(1,' Info','<light-blue>', f"You have launched in Single Post download mode\
        \n{17*' '}Please enter the ID of the post you would like to download\
        \n{17*' '}After you click on a post, it will show in your browsers url bar")
    
    while True:
        post_id = input(f"\n{17*' '}► Post ID: ") # str
        if post_id.isdigit() and len(post_id) >= 10 and not any(char.isspace() for char in post_id):
            break
        else:
            output(2,'\n [17]ERROR','<red>', f"The input string \'{post_id}\' can not be a valid post ID.\
                \n{22*' '}The last few numbers in the url is the post ID\
                \n{22*' '}Example: \'https://fansly.com/post/1283998432982\'\
                \n{22*' '}In the example \'1283998432982\' would be the post ID")

    post_req = sess.get('https://apiv3.fansly.com/api/v1/post', params={'ids': post_id, 'ngsw-bypass': 'true',}, headers=headers)

    if post_req.status_code == 200:
        creator_username, creator_display_name = None, None # from: "accounts"
        accessible_media = None
        contained_posts = []

        # post object contains: posts, aggregatedPosts, accountMediaBundles, accountMedia, accounts, tips, tipGoals, stories, polls
        post_object = post_req.json()['response']
        
        # if access to post content / post contains content
        if post_object['accountMedia']:

            # parse post creator name
            if not creator_username:
                creator_id = post_object['accountMedia'][0]['accountId'] # the post creators reliable accountId
                creator_display_name, creator_username = next((account.get('displayName'), account.get('username')) for account in post_object.get('accounts', []) if account.get('id') == creator_id)
    
                if creator_display_name and creator_username:
                    output(1,' Info','<light-blue>', f"Inspecting a post by {creator_display_name} (@{creator_username})")
                else:
                    output(1,' Info','<light-blue>', f"Inspecting a post by {creator_username.capitalize()}")
    
            # parse relevant details about the post
            if not accessible_media:
                # loop through the list of dictionaries and find the highest quality media URL for each one
                for obj in post_object['accountMedia']:
                    try:
                        # add details into a list
                        contained_posts += [parse_media_info(obj, post_id)]
                    except Exception:
                        output(2,'\n [18]ERROR','<red>', f"Unexpected error during parsing Single Post content; \n{traceback.format_exc()}")
                        input('\n Press Enter to attempt to continue ..')
    
                # summarise all scrapable & wanted media
                accessible_media = [item for item in contained_posts if item.get('download_url') and (item.get('is_preview') == download_media_previews or not item.get('is_preview'))]

            # at this point we have already parsed the whole post object and determined what is scrapable with the code above
            output(1,' Info','<light-blue>', f"Amount of Media linked to Single post: {len(post_object['accountMedia'])} (scrapable: {len(accessible_media)})")
        
            """
            generate a base dir based on various factors, except this time we ovewrite the username from config.ini
            with the custom username we analysed through single post download mode's post_object. this is because
            the user could've decide to just download some random creators post instead of the one that he currently
            set as creator for > TargetCreator > username in config.ini
            """
            generate_base_dir(creator_username, module_requested_by = 'Single')
        
            try:
                # download it
                sort_download(accessible_media)
            except DuplicateCountError:
                output(1,' Info','<light-blue>', f"Already downloaded all possible Single Post content! [Duplicate threshold exceeded {DUPLICATE_THRESHOLD}]")
            except Exception:
                output(2,'\n [19]ERROR','<red>', f"Unexpected error during sorting Single Post download; \n{traceback.format_exc()}")
                input('\n Press Enter to attempt to continue ..')
        
        else:
            output(2, '\n WARNING', '<yellow>', f"Could not find any accessible content in the single post.")
    
    else:
        output(2,'\n [20]ERROR','<red>', f"Failed single post download. Fetch post information request, response code: {post_req.status_code}\n{post_req.text}")
        input('\n Press Enter to attempt to continue ..')




## starting here: download_mode = Collection(s)
if 'Collection' in download_mode:
    output(1,'\n Info','<light-blue>', f"Starting Collections sequence. Buckle up and enjoy the ride!")

    # send a first request to get all available "accountMediaId" ids, which are basically media ids of every graphic listed on /collections
    collections_req = sess.get('https://apiv3.fansly.com/api/v1/account/media/orders/', params={'limit': '9999','offset': '0','ngsw-bypass': 'true'}, headers=headers)
    if collections_req.ok:
        collections_req = collections_req.json()
        
        # format all ids from /account/media/orders (collections)
        accountMediaIds = ','.join([order['accountMediaId'] for order in collections_req['response']['accountMediaOrders']])
        
        # input them into /media?ids= to get all relevant information about each purchased media in a 2nd request
        post_object = sess.get(f"https://apiv3.fansly.com/api/v1/account/media?ids={accountMediaIds}", headers=headers)
        post_object = post_object.json()
        
        contained_posts = []
        
        for obj in post_object['response']:
            try:
                # add details into a list
                contained_posts += [parse_media_info(obj)]
            except Exception:
                output(2,'\n [21]ERROR','<red>', f"Unexpected error during parsing Collections content; \n{traceback.format_exc()}")
                input('\n Press Enter to attempt to continue ..')
        
        # count only amount of scrapable media (is_preview check not really necessary since everything in collections is always paid, but w/e)
        accessible_media = [item for item in contained_posts if item.get('download_url') and (item.get('is_preview') == download_media_previews or not item.get('is_preview'))]
    
        output(1,' Info','<light-blue>', f"Amount of Media in Media Collection: {len(post_object['response'])} (scrapable: {len(accessible_media)})")
        
        generate_base_dir(config_username, module_requested_by = 'Collection')
        
        try:
            # download it
            sort_download(accessible_media)
        except DuplicateCountError:
            output(1,' Info','<light-blue>', f"Already downloaded all possible Collections content! [Duplicate threshold exceeded {DUPLICATE_THRESHOLD}]")
        except Exception:
            output(2,'\n [22]ERROR','<red>', f"Unexpected error during sorting Collections download; \n{traceback.format_exc()}")
            input('\n Press Enter to attempt to continue ..')

    else:
        output(2,'\n [23]ERROR','<red>', f"Failed Collections download. Fetch collections request, response code: {collections_req.status_code}\n{collections_req.text}")
        input('\n Press Enter to attempt to continue ..')




# here comes stuff that is required by Messages AND Timeline - so this is like a 'shared section'
if any(['Message' in download_mode, 'Timeline' in download_mode, 'Normal' in download_mode]):
    try:
        raw_req = sess.get(f"https://apiv3.fansly.com/api/v1/account?usernames={config_username}", headers=headers)
        acc_req = raw_req.json()['response'][0]
        creator_id = acc_req['id']
    except KeyError as e:
        if raw_req.status_code == 401:
            output(2,'\n [24]ERROR','<red>', f"API returned unauthorized. This is most likely because of a wrong authorization token, in the configuration file.\n{21*' '}Used authorization token: \'{config_token}\'")
        else:
            output(2,'\n [25]ERROR','<red>', 'Bad response from fansly API. Please make sure your configuration file is not malformed.')
        print('\n'+str(e))
        print(raw_req.text)
        input('\nPress Enter to close ...')
        exit()
    except IndexError as e:
        output(2,'\n [26]ERROR','<red>', 'Bad response from fansly API. Please make sure your configuration file is not malformed; most likely misspelled the creator name.')
        print('\n'+str(e))
        print(raw_req.text)
        input('\nPress Enter to close ...')
        exit()

    # below only needed by timeline; but wouldn't work without acc_req so it's here
    # determine if followed
    try:
        following = acc_req['following']
    except KeyError:
        following = False

    # determine if subscribed
    try:
        subscribed = acc_req['subscribed']
    except KeyError:
        subscribed = False
    
    # intentionally only put pictures into try / except block - its enough
    try:
        total_timeline_pictures = acc_req['timelineStats']['imageCount']
    except KeyError:
        output(2,'\n [27]ERROR','<red>', f"Can not get timelineStats for creator username \'{config_username}\'; most likely misspelled it!")
        input('\nPress Enter to close ...')
        exit()
    total_timeline_videos = acc_req['timelineStats']['videoCount']

    # overwrite base dup threshold with custom 20% of total timeline content
    DUPLICATE_THRESHOLD = int(0.2 * int(total_timeline_pictures + total_timeline_videos))

    # timeline & messages will always use the creator name from config.ini, so we'll leave this here
    output(1,' Info','<light-blue>', f"Targeted creator: \'{config_username}\'")



## starting here: download_mode = Message(s)
if any(['Message' in download_mode, 'Normal' in download_mode]):
    output(1,' \n Info','<light-blue>', f"Initiating Messages procedure. Standby for results.")
    
    groups_req = sess.get('https://apiv3.fansly.com/api/v1/messaging/groups, headers=headers)

    if groups_req.ok:
        groups_response = groups_response.json()['response']['groups']['aggregationData']['groups']

        # go through messages and check if we even have a chat history with the creator
        group_id = None
        for group in groups_req:
            for user in group['users']:
                if user['userId'] == creator_id:
                    group_id = group['id']
                    break
            if group_id:
                break

        # only if we do have a message ("group") with the creator
        if group_id:
            msg_cursor = 0
            while True:
                messages_req = sess.get('https://apiv3.fansly.com/api/v1/messaging/groups, headers = headers, params = {'groupId': group_id, 'before': msg_cursor, 'limit': '25', 'ngsw-bypass': 'true'} if msg_cursor else {'groupId': group_id, 'limit': '25', 'ngsw-bypass': 'true'})

                if messages_req.status_code == 200:
                    accessible_media = None
                    contained_posts = []
                
                    # post object contains: messages, accountMedia, accountMediaBundles, tips, tipGoals, stories
                    post_object = messages_req.json()['response']

                    # parse relevant details about the post
                    if not accessible_media:
                        # loop through the list of dictionaries and find the highest quality media URL for each one
                        for obj in post_object['accountMedia']:
                            try:
                                # add details into a list
                                contained_posts += [parse_media_info(obj)]
                            except Exception:
                                output(2,'\n [28]ERROR','<red>', f"Unexpected error during parsing Messages content; \n{traceback.format_exc()}")
                                input('\n Press Enter to attempt to continue ..')
                
                        # summarise all scrapable & wanted media
                        accessible_media = [item for item in contained_posts if item.get('download_url') and (item.get('is_preview') == download_media_previews or not item.get('is_preview'))]

                        total_accessible_messages_content = len(accessible_media)

                        # overwrite base dup threshold with 20% of total accessible content in messages
                        DUPLICATE_THRESHOLD = int(0.2 * total_accessible_messages_content)

                        # at this point we have already parsed the whole post object and determined what is scrapable with the code above
                        output(1,' Info','<light-blue>', f"Amount of Media in Messages with {config_username}: {len(post_object['accountMedia'])} (scrapable: {total_accessible_messages_content})")

                        generate_base_dir(config_username, module_requested_by = 'Messages')

                        try:
                            # download it
                            sort_download(accessible_media)
                        except DuplicateCountError:
                            output(1,' Info','<light-blue>', f"Already downloaded all possible Messages content! [Duplicate threshold exceeded {DUPLICATE_THRESHOLD}]")
                        except Exception:
                            output(2,'\n [29]ERROR','<red>', f"Unexpected error during sorting Messages download; \n{traceback.format_exc()}")
                            input('\n Press Enter to attempt to continue ..')

                        # get next cursor
                        try:
                            msg_cursor = post_object['messages'][-1]['id']
                        except IndexError:
                            break # break if end is reached
                else:
                    output(2,'\n [30]ERROR','<red>', f"Failed messages download. messages_req failed with response code: {messages_req.status_code}\n{messages_req.text}")

        elif group_id is None:
            output(2, ' WARNING', '<yellow>', f"Could not find a chat history with {config_username}; skipping messages download ..")
    else:
        output(2,'\n [31]ERROR','<red>', f"Failed Messages download. Fetch Messages request, response code: {groups_req.status_code}\n{groups_req.text}")
        input('\n Press Enter to attempt to continue ..')



## starting here: download_mode = Timeline
if any(['Timeline' in download_mode, 'Normal' in download_mode]):
    output(1,'\n Info','<light-blue>', f"Executing Timeline functionality. Anticipate remarkable outcomes!")

    # this has to be up here so it doesn't get looped
    generate_base_dir(config_username, module_requested_by = 'Timeline')

    timeline_cursor = 0
    while True:
        if timeline_cursor == 0:
            output(1, '\n Info', '<light-blue>', "Inspecting most recent Timeline cursor")
        else:
            output(1, '\n Info', '<light-blue>', f"Inspecting Timeline cursor: {timeline_cursor}")

        try:
            timeline_req = sess.get(f"https://apiv3.fansly.com/api/v1/timeline/{creator_id}?before={timeline_cursor}&after=0&wallId=&contentSearch=&ngsw-bypass=true", headers=headers)
            if timeline_req.status_code == 200:
                accessible_media = None
                contained_posts = []

                post_object = timeline_req.json()['response']
        
                # parse relevant details about the post
                if not accessible_media:
                    # loop through the list of dictionaries and find the highest quality media URL for each one
                    for obj in post_object['accountMedia']:
                        try:
                            # add details into a list
                            contained_posts += [parse_media_info(obj)]
                        except Exception:
                            output(2,'\n [32]ERROR','<red>', f"Unexpected error during parsing Timeline content; \n{traceback.format_exc()}")
                            input('\n Press Enter to attempt to continue ..')
        
                    # summarise all scrapable & wanted media
                    accessible_media = [item for item in contained_posts if item.get('download_url') and (item.get('is_preview') == download_media_previews or not item.get('is_preview'))]
    
                    # at this point we have already parsed the whole post object and determined what is scrapable with the code above
                    output(1,' Info','<light-blue>', f"Amount of Media in current cursor: {len(post_object['accountMedia'])} (scrapable: {len(accessible_media)})")

                    try:
                        # download it
                        sort_download(accessible_media)
                    except DuplicateCountError:
                        output(1,' Info','<light-blue>', f"Already downloaded all possible Timeline content! [Duplicate threshold exceeded {DUPLICATE_THRESHOLD}]")
                        break
                    except Exception:
                        output(2,'\n [33]ERROR','<red>', f"Unexpected error during sorting Timeline download: \n{traceback.format_exc()}")
                        input('\n Press Enter to attempt to continue ..')

                # get next timeline_cursor
                try:
                    timeline_cursor = post_object['posts'][-1]['id']
                except IndexError:
                    break  # break the whole while loop, if end is reached
                except Exception:
                    print('\n'+traceback.format_exc())
                    output(2,'\n [34]ERROR','<red>', 'Please copy & paste this on GitHub > Issues & provide a short explanation.')
                    input('\nPress Enter to close ...')
                    exit()

        except KeyError:
            output(2,'\n [35]ERROR','<red>', "Couldn\'t find any scrapable media at all!\
                \n This most likely happend because you\'re not following the creator, your authorisation token is wrong\
                \n or the creator is not providing unlocked content.")
            input('\n Press Enter to attempt to continue ..')
        except Exception:
            output(2,'\n [36]ERROR','<red>', f"Unexpected error during Timeline download: \n{traceback.format_exc()}")
            input('\n Press Enter to attempt to continue ..')

    # check if atleast 20% of timeline was scraped; exluding the case when all the media was declined as duplicates
    print('') # intentional empty print
    issue = False
    if pic_count <= total_timeline_pictures * 0.2 and duplicate_count <= total_timeline_pictures * 0.2:
        output(3,'\n WARNING','<yellow>', f"Low amount of Pictures scraped. Creators total Pictures: {total_timeline_pictures} | Downloaded: {pic_count}")
        issue = True
    
    if vid_count <= total_timeline_videos * 0.2 and duplicate_count <= total_timeline_videos * 0.2:
        output(3,'\n WARNING','<yellow>', f"Low amount of Videos scraped. Creators total Videos: {total_timeline_videos} | Downloaded: {vid_count}")
        issue = True
    
    if issue:
        if not following:
            print(f"{20*' '}Follow the creator; to be able to scrape more media!")
        
        if not subscribed:
            print(f"{20*' '}Subscribe to the creator; if you would like to get the entire content.")
        
        if not download_media_previews:
            print(f"{20*' '}Try setting download_media_previews to True in the config.ini file. Doing so, will help if the creator has marked all his content as previews.")
        print('')


# BASE_DIR_NAME doesn't always have to be set; e.g. user tried scraping Messages of someone, that never direct messaged him content before
if BASE_DIR_NAME:
    # hacky overwrite for BASE_DIR_NAME so it doesn't point to the sub-directories e.g. /Timeline
    BASE_DIR_NAME = BASE_DIR_NAME.partition('_fansly')[0] + '_fansly'

    print(f"\n╔═\n  Finished {download_mode} type, download of {pic_count} pictures & {vid_count} videos! Declined duplicates: {duplicate_count}\
        \n  Saved content in directory: \'{BASE_DIR_NAME}\'\
        \n  ✶ Please leave a Star on the GitHub Repository, if you are satisfied! ✶\n{74*' '}═╝")

    # open download folder
    if open_folder_when_finished:
        open_location(BASE_DIR_NAME)


input('\n Press Enter to close ..')
exit()
