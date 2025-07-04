import undetected_chromedriver as uc
import os
import pickle
import time
import psutil  # Add this import for process management
#wassup my nigga
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnableToSetCookieException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import json
import platform
import pyperclip  # For cross-platform clipboard operations
from bs4 import BeautifulSoup
import openai
import datetime
import yt_dlp  # For downloading YouTube audio
import tempfile  # For creating temporary files
import whisper  # For local transcription
import torch
from whichplatform import get_chrome_profile_path  # Import our new function

# ANSI colors for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    DIM = "\033[2m"

# Script Generation Configuration
class ScriptConfig:
    # Total word count for the entire script
    TOTAL_WORDS = 1800
    # Number of parts to split the script into
    NUM_PARTS = 3
    # Word count per part (calculated automatically)
    WORDS_PER_PART = TOTAL_WORDS // NUM_PARTS
    # Verify the configuration is valid
    assert TOTAL_WORDS % NUM_PARTS == 0, f"Total words ({TOTAL_WORDS}) must be evenly divisible by number of parts ({NUM_PARTS})"

def log(message, level="info", newline=True):
    """Print a nicely formatted log message with timestamp and color."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    
    if level == "info":
        prefix = f"{Colors.BLUE}ℹ{Colors.RESET}"
        color = Colors.RESET
    elif level == "success":
        prefix = f"{Colors.GREEN}✓{Colors.RESET}"
        color = Colors.GREEN
    elif level == "warn":
        prefix = f"{Colors.YELLOW}⚠{Colors.RESET}"
        color = Colors.YELLOW
    elif level == "error":
        prefix = f"{Colors.RED}✗{Colors.RESET}"
        color = Colors.RED
    elif level == "wait":
        prefix = f"{Colors.CYAN}◔{Colors.RESET}"
        color = Colors.CYAN
    elif level == "header":
        prefix = f"{Colors.MAGENTA}▶{Colors.RESET}"
        color = Colors.MAGENTA + Colors.BOLD
    else:
        prefix = " "
        color = Colors.RESET
    
    log_msg = f"{Colors.DIM}[{timestamp}]{Colors.RESET} {prefix} {color}{message}{Colors.RESET}"
    
    if newline:
        print(log_msg)
    else:
        print(log_msg, end="", flush=True)

# Check if running on macOS
IS_MACOS = platform.system() == 'Darwin'

# Mac-specific Chrome configuration
if IS_MACOS:
    import pyautogui
    # Set pyautogui pause time for Mac
    pyautogui.PAUSE = 1.5
    # Disable PyAutoGUI fail-safe
    pyautogui.FAILSAFE = False

# Notion configuration
NOTION_DATABASE_ID = "1a402cd2c14280909384df6c898ddcb3"
NOTION_TOKEN = "ntn_cC7520095381SElmcgTOADYsGnrABFn2ph1PrcaGSst2dv"
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# OpenAI configuration
OPENAI_API_KEY = ""
openai.api_key = OPENAI_API_KEY

def get_video_title(url):
    """Get the title of a YouTube video with retries and multiple methods."""
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }
    
    # Extract video ID for API fallback
    video_id = None
    try:
        video_id, _ = get_youtube_id_and_timestamp(url)
    except:
        pass
    
    session = requests.Session()
    session.headers.update(headers)
    
    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                print(f"Retry attempt {attempt + 1}/{MAX_RETRIES} for title...")
                time.sleep(RETRY_DELAY * attempt)  # Exponential backoff
            
            # Method 1: Try direct page scraping
            try:
                response = session.get(url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try meta title first
                meta_title = soup.find('meta', property='og:title')
                if meta_title and meta_title.get('content'):
                    return meta_title['content']
                
                # Try title tag
                title_tag = soup.find('title')
                if title_tag and title_tag.string:
                    title = title_tag.string
                    if ' - YouTube' in title:
                        title = title.replace(' - YouTube', '')
                    if title.strip():
                        return title.strip()
            except Exception as e:
                print(f"Method 1 failed: {str(e)}")
            
            # Method 2: Try alternative URL format
            try:
                alt_url = f'https://www.youtube.com/watch?v={video_id}' if video_id else url
                if alt_url != url:
                    response = session.get(alt_url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    meta_title = soup.find('meta', property='og:title')
                    if meta_title and meta_title.get('content'):
                        return meta_title['content']
            except Exception as e:
                print(f"Method 2 failed: {str(e)}")
            
            # Method 3: Try mobile version
            try:
                mobile_url = f'https://m.youtube.com/watch?v={video_id}' if video_id else url.replace('www.', 'm.')
                headers['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
                response = session.get(mobile_url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                meta_title = soup.find('meta', property='og:title')
                if meta_title and meta_title.get('content'):
                    return meta_title['content']
            except Exception as e:
                print(f"Method 3 failed: {str(e)}")
            
            # If we get here, all methods failed this attempt
            print(f"All methods failed on attempt {attempt + 1}")
            
        except Exception as e:
            print(f"Error getting video title (attempt {attempt + 1}): {str(e)}")
            if attempt == MAX_RETRIES - 1:  # Last attempt
                return None
            
    return None

def get_gpt4_title(driver, original_title):
    """Get a rewritten title using ChatGPT web interface."""
    try:
        # Title-specific prompt
        title_prompt = f"""Rewrite this title in exactly 13 words. Keep it one straight sentence rather than spiltting them. Keep the first letter of every word capital and the important words full capitalised. Choose only two words. Make it clickbaity and a bit exaggerated. Use simple words. Do not use colon ":" Keep the words simple and human like unlike AI generated. Do not use words such as bombshell, beans, scandal, world, stunned. Do not reply back with any metadata such as Absolutely or anything. Start your response with ZSX: followed by the title.

Original title: {original_title}"""

        # Send title prompt
        paste_content(driver, title_prompt, is_title=True)
        
        # First attempt - wait 10 seconds
        print("Waiting for first response attempt...")
        time.sleep(10)  # Wait 10 seconds for initial response
        response = get_chatgpt_response(driver, "ZSX:")
        
        if response:
            # Clean up response (remove any extra newlines or spaces)
            new_title = response.strip()
            return new_title
            
        # If no response with marker found, wait additional 20 seconds
        print("No marker found in first attempt, waiting additional 20 seconds...")
        time.sleep(20)  # Wait additional 20 seconds
        response = get_chatgpt_response(driver, "ZSX:")
        
        if response:
            # Clean up response (remove any extra newlines or spaces)
            new_title = response.strip()
            return new_title
            
        print("No response with marker found after both attempts")
        return None
    except Exception as e:
        print(f"Error getting ChatGPT title: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def update_page_title(page_id, title):
    """Update the title of a Notion page."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    
    try:
        response = requests.patch(url, headers=NOTION_HEADERS, json={
            "properties": {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }
        })
        response.raise_for_status()
        print("Updated page title successfully!")
        return True
    except Exception as e:
        print(f"Error updating page title: {str(e)}")
        return False

def get_youtube_id_and_timestamp(url):
    """Extract video ID and timestamp from YouTube URL."""
    try:
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Get video ID
        if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
            if parsed_url.path == '/watch':
                video_id = parse_qs(parsed_url.query)['v'][0]
            else:
                return None, 0
        elif parsed_url.hostname == 'youtu.be':
            video_id = parsed_url.path[1:]
        else:
            return None, 0
            
        # Get timestamp if present
        query_params = parse_qs(parsed_url.query)
        timestamp_str = query_params.get('t', ['0'])[0]
        # Remove any non-digit characters (like 's' suffix)
        timestamp = int(''.join(filter(str.isdigit, timestamp_str)) or '0')
        
        return video_id, timestamp
    except Exception as e:
        print(f"Error parsing YouTube URL: {str(e)}")
        return None, 0

def load_transcript_cache():
    """Load the transcript cache from Transcript.JSON."""
    try:
        if os.path.exists('Transcript.JSON'):
            with open('Transcript.JSON', 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading transcript cache: {str(e)}")
        return {}

def save_transcript_cache(cache_data):
    """Save the transcript cache to Transcript.JSON."""
    try:
        with open('Transcript.JSON', 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving transcript cache: {str(e)}")

def clear_transcript_cache():
    """Clear the transcript cache file."""
    try:
        with open('Transcript.JSON', 'w', encoding='utf-8') as f:
            json.dump({}, f)
    except Exception as e:
        print(f"Error clearing transcript cache: {str(e)}")

def get_youtube_transcript(url, title=None):
    """Get transcript from YouTube video starting from timestamp."""
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    try:
        # Extract video ID and timestamp
        video_id, start_time = get_youtube_id_and_timestamp(url)
        if not video_id:
            print(f"Invalid YouTube URL: {url}")
            return None
            
        print(f"Attempting to get transcript for video ID: {video_id} starting from timestamp: {start_time}")
        
        # Use provided title or fetch it if not provided
        original_title = title
        if not original_title:
            original_title = get_video_title(url)
            if not original_title:
                print("Could not get video title")
                return None
            
        # Check if we have this title in our cache
        transcript_cache = load_transcript_cache()
        if original_title in transcript_cache:
            print("Found cached transcript for this video")
            return transcript_cache[original_title]
            
        # If title is different from what's in cache, clear the cache
        if transcript_cache and list(transcript_cache.keys())[0] != original_title:
            print("New video detected, clearing transcript cache")
            clear_transcript_cache()
            transcript_cache = {}
        
        last_error = None
        # Try multiple times
        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0:
                    print(f"Retry attempt {attempt + 1}/{MAX_RETRIES}")
                    time.sleep(RETRY_DELAY)
                
                # First try direct transcript retrieval
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                    print(f"Successfully retrieved transcript with {len(transcript_list)} entries")
                    break  # Success, exit retry loop
                except Exception as direct_error:
                    print(f"Error getting direct transcript: {str(direct_error)}")
                    last_error = direct_error
                    
                    # If direct method fails, try listing available transcripts
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                    available_langs = [t.language_code for t in transcript_list]
                    print("Available transcripts:", available_langs)
                    
                    # Try to get English transcript first
                    transcript = None
                    if 'en' in available_langs:
                        transcript = transcript_list.find_transcript(['en'])
                    
                    # If no English, try manual then auto-generated
                    if not transcript:
                        try:
                            transcript = transcript_list.find_manually_created_transcript()
                        except:
                            try:
                                transcript = transcript_list.find_generated_transcript()
                            except:
                                pass
                    
                    if transcript:
                        transcript_list = transcript.fetch()
                        print(f"Found alternative transcript with {len(transcript_list)} entries")
                        break  # Success, exit retry loop
                    else:
                        raise Exception("No suitable transcript found")
                        
            except Exception as e:
                last_error = e
                if attempt == MAX_RETRIES - 1:  # Last attempt
                    print(f"Error getting transcript after {MAX_RETRIES} attempts: {str(e)}")
                    print("Attempting fallback method: downloading audio and using Whisper...")
                    # Try the fallback method of downloading audio and using Whisper
                    whisper_transcript = download_and_transcribe(video_id)
                    if whisper_transcript:
                        print("Successfully got transcript using Whisper fallback method")
                        # Save to cache
                        transcript_cache[original_title] = whisper_transcript
                        save_transcript_cache(transcript_cache)
                        return whisper_transcript
                    return None
        
        # If we got here, we have a transcript_list
        # Filter transcript from timestamp
        filtered_transcript = []
        for entry in transcript_list:
            # Convert timestamp to seconds if it's a string
            entry_start = float(entry['start'])
            if entry_start >= float(start_time):
                filtered_transcript.append(entry['text'])
                
        if not filtered_transcript:
            print(f"Warning: No transcript entries found after timestamp {start_time}")
            # If no entries found after timestamp, return the full transcript
            filtered_transcript = [entry['text'] for entry in transcript_list]
            print("Using full transcript instead")
                
        # Join transcript text
        full_transcript = ' '.join(filtered_transcript)
        print(f"Final transcript length: {len(full_transcript)} characters")
        
        # Save to cache
        transcript_cache[original_title] = full_transcript
        save_transcript_cache(transcript_cache)
        
        return full_transcript
        
    except Exception as e:
        print(f"Error getting YouTube transcript: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def get_pages_needing_script():
    """Get pages where Script checkbox is unchecked."""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    
    try:
        response = requests.post(url, headers=NOTION_HEADERS, json={
            "filter": {
                "and": [
                    {
                        "property": "Script",
                        "checkbox": {
                            "equals": False
                        }
                    },
                    {
                        "property": "YouTube URL",
                        "url": {
                            "is_not_empty": True
                        }
                    }
                ]
            }
        })
        response.raise_for_status()
        pages = response.json().get("results", [])
        return pages
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return []

def get_youtube_url_from_page(page):
    """Extract YouTube URL from Notion page."""
    try:
        youtube_url = page.get("properties", {}).get("YouTube URL", {}).get("url", "")
        return youtube_url
    except Exception as e:
        print(f"Error getting YouTube URL: {str(e)}")
        return None

def kill_chrome_instances(profile_path):
    """Kill any Chrome instances that were started from the specified profile directory."""
    try:
        # Get all running processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check if it's a Chrome process
                if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                    # Get the command line arguments
                    cmdline = proc.info['cmdline']
                    if cmdline:
                        # Check if this Chrome instance is using our profile directory
                        if any(profile_path in arg for arg in cmdline):
                            log(f"Killing Chrome process with profile: {profile_path}", "info")
                            proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        log(f"Error killing Chrome instances: {str(e)}", "error")

def setup_driver():
    # Chrome options setup
    options = uc.ChromeOptions()
    options.add_argument('--start-maximized')
    
    try:
        # Get the platform-specific Chrome profile path
        profile_path = get_chrome_profile_path()
        
        # Kill any existing Chrome instances using this profile
        kill_chrome_instances(profile_path)
        
        # Add a small delay to ensure processes are fully terminated
        time.sleep(2)
        
        options.add_argument(f'--user-data-dir={profile_path}')
    except Exception as e:
        log(f"Error setting up Chrome profile: {str(e)}", "error")
        raise
    
    # Initialize undetected-chromedriver
    driver = uc.Chrome(options=options)
    return driver

def save_cookies(driver, path):
    # Create cookies directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Save cookies to file
    cookies = driver.get_cookies()
    with open(path, 'wb') as file:
        pickle.dump(cookies, file)

def load_cookies(driver, path):
    # Load cookies from file
    with open(path, 'rb') as file:
        cookies = pickle.load(file)
        
    # Add cookies one by one and handle any errors
    for cookie in cookies:
        try:
            # Remove problematic keys that might cause issues
            for k in ['expiry', 'expires']:
                if k in cookie:
                    del cookie[k]
            
            # Ensure domain matches current URL
            if 'domain' in cookie:
                if not driver.current_url.startswith('http://' + cookie['domain']) and \
                   not driver.current_url.startswith('https://' + cookie['domain']):
                    continue
            
            driver.add_cookie(cookie)
        except UnableToSetCookieException:
            print(f"Warning: Unable to set cookie: {cookie.get('name', 'unknown')}")
            continue
        except Exception as e:
            print(f"Warning: Error setting cookie: {str(e)}")
            continue

def paste_content(driver, content, title=None, is_continuation=False, is_title=False):
    """Paste content into ChatGPT input box using ActionChains."""
    try:
        # Wait for page to be fully loaded
        time.sleep(2)
        
        # Click at specific coordinates using JavaScript
        script = f"document.elementFromPoint(739, 514).click();"
        driver.execute_script(script)
        time.sleep(1)
        
        # Prepare the content
        if is_title:
            # For title generation, use the content as is
            full_content = content
        elif is_continuation:
            full_content = content
        else:
            # For script generation, add the full prompt
            title_context = f"Video Title for reference (use these names in the script because the transcript might have wrong spellings of these people): {title}\n\n" if title else ""
            full_content = f"{title_context}{content}\n\n\nI want you to write a completely original {ScriptConfig.TOTAL_WORDS}-word script based on this content, split into {ScriptConfig.NUM_PARTS} parts of exactly {ScriptConfig.WORDS_PER_PART} words each.\n\nVERY IMPORTANT: Write ONLY the first part ({ScriptConfig.WORDS_PER_PART} words) now. Start it with the code AEB followed by your content. After I receive this first part, I will specifically ask you for part 2, and then later for part 3. DO NOT write more than one part at a time.\n\nDon't simply rewrite or rephrase the transcript - instead, understand the content deeply and craft an entirely new narrative structure. Rearrange the information in a way that makes the most sense for storytelling, rather than following the transcript's order.\n\nPart codes:\n- First part: AEB (write this part now, exactly {ScriptConfig.WORDS_PER_PART} words)\n- Second part: AEC (wait until I ask for this)\n- Third part: AED (wait until I ask for this)\n\nEach part should flow naturally into the next, building the story progressively without repeating information. When you write the second and third parts later, don't include any references to previous parts or transitional phrases like 'continuing from where we left off'.\n\nMaintain a casual, conversational tone throughout - write as if you're telling an engaging story to a friend. Avoid any AI-like language or formal tone. DO NOT use bullet points or any similar formatting - keep it as a smooth, flowing narrative.\n\nMost importantly:\n- Write exactly {ScriptConfig.WORDS_PER_PART} words for this first part (no more, no less)\n- Create an original structure that doesn't follow the transcript's order\n- Write naturally and engagingly\n- Make it interesting and dynamic\n\nRemember: Only write the FIRST part ({ScriptConfig.WORDS_PER_PART} words) now, beginning with the code AEB. Stop after exactly {ScriptConfig.WORDS_PER_PART} words. In the content anywhere, Do not mention End of Part 1 or such metadatas. Strictly NO!."
        
        # Copy content to clipboard
        pyperclip.copy(full_content)
        
        # Create ActionChains instance
        actions = ActionChains(driver)
        
        # Paste using keyboard shortcut (Cmd+V for Mac, Ctrl+V for others)
        if platform.system() == 'Darwin':
            actions.key_down(Keys.COMMAND).send_keys('v').key_up(Keys.COMMAND)
        else:
            actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL)
        
        # Execute the paste action
        actions.perform()
        time.sleep(1)  # Wait a bit after pasting
        
        # Send the message by pressing Enter
        actions = ActionChains(driver)
        actions.send_keys(Keys.RETURN)
        actions.perform()
        
        print("Content pasted and sent successfully!")
        
    except Exception as e:
        print(f"Error pasting content: {str(e)}")
        import traceback
        traceback.print_exc()

def get_chatgpt_response(driver, marker):
    """Get ChatGPT's response starting from the specified marker."""
    try:
        time.sleep(5)  # Initial wait to ensure response starts
        
        # Wait for any response to appear
        wait = WebDriverWait(driver, 75)  # Wait up to 75 seconds for response
        
        # First wait for the response container
        response_container = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='markdown']"))
        )
        
        # Then wait for the stop generating button to disappear (indicating response is complete)
        try:
            stop_button = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Stop generating']"))
            )
            # If found, wait for it to disappear
            WebDriverWait(driver, 30).until(  # Reduced from 60 to 30 seconds
                EC.staleness_of(stop_button)
            )
        except:
            # If stop button not found, response might already be complete
            pass
        
        # Additional wait to ensure full response is rendered
        time.sleep(3)
        
        # Get all message groups
        message_groups = driver.find_elements(By.CSS_SELECTOR, "div[class*='markdown']")
        
        # Get text from all message groups
        all_text = ""
        for group in message_groups:
            try:
                # Try to get text content
                text = group.text.strip()
                if text:
                    all_text += text + "\n"
            except:
                continue
        
        # Find all occurrences of the marker
        marker_positions = [i for i in range(len(all_text)) if all_text.startswith(marker, i)]
        
        if marker_positions:  # If we found any markers
            # Get text after the last marker occurrence
            last_marker_pos = marker_positions[-1]
            response_text = all_text[last_marker_pos:].strip()
            
            # Remove the marker from the beginning
            if response_text.startswith(marker):
                response_text = response_text[len(marker):].strip()
            
            # Remove unwanted patterns and clean up text
            unwanted_patterns = [
                "Would you like me to continue with part 2?",
                "Would you like me to continue with part 3?",
                "Retry",
                "May I proceed with part 2?",
                "May I proceed with part 3?",
                "Would you like me to continue?",
                "Shall I continue?",
                "Should I continue?"
            ]
            
            for pattern in unwanted_patterns:
                response_text = response_text.replace(pattern, "").strip()
            
            print(f"Successfully extracted response with marker {marker}")
            return response_text
            
        print(f"Could not find marker {marker} in response")
        print("Response content:", all_text[:200] + "..." if len(all_text) > 200 else all_text)
        return None
        
    except Exception as e:
        print(f"Error getting response: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def update_page_content(page_id, content):
    """Update the content of an existing Notion page."""
    try:
        # Split content into blocks (max 2000 chars per block)
        content_blocks = split_content_into_blocks(content)
        
        # Create children array with blocks
        children = []
        for block in content_blocks:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": block
                            }
                        }
                    ]
                }
            })
        
        # First, clear existing content
        blocks_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        response = requests.get(blocks_url, headers=NOTION_HEADERS)
        response.raise_for_status()
        
        for block in response.json().get("results", []):
            block_id = block.get("id")
            if block_id:
                delete_url = f"https://api.notion.com/v1/blocks/{block_id}"
                requests.delete(delete_url, headers=NOTION_HEADERS)
        
        # Then add new content
        response = requests.patch(blocks_url, headers=NOTION_HEADERS, json={
            "children": children
        })
        response.raise_for_status()
        print("Updated Notion page content successfully!")
        return True
    except Exception as e:
        print(f"Error updating page content: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def split_content_into_blocks(content, max_length=2000):
    """Split content into blocks of maximum length while preserving words."""
    blocks = []
    words = content.split()
    current_block = []
    current_length = 0
    
    for word in words:
        # Add space before word except for first word in block
        space = ' ' if current_block else ''
        word_length = len(space + word)
        
        if current_length + word_length > max_length and current_block:
            # Save current block and start new one
            blocks.append(' '.join(current_block))
            current_block = [word]
            current_length = len(word)
        else:
            current_block.append(word)
            current_length += word_length
    
    # Add final block
    if current_block:
        blocks.append(' '.join(current_block))
    
    return blocks

def update_script_checkbox(page_id):
    """Mark the Script checkbox as checked."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    
    try:
        response = requests.patch(url, headers=NOTION_HEADERS, json={
            "properties": {
                "Script": {
                    "checkbox": True
                }
            }
        })
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error updating checkbox: {str(e)}")
        return False

def download_and_transcribe(video_id):
    """Download YouTube video audio and transcribe it using local Whisper model."""
    try:
        # Create a temporary directory for the audio file
        with tempfile.TemporaryDirectory() as temp_dir:
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'bestaudio/best',  # Get best quality audio
                'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'quiet': True,
                'no_warnings': True
            }
            
            # Download the audio
            print(f"Downloading audio for video ID: {video_id}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
            
            # Get the path of the downloaded audio file
            audio_path = os.path.join(temp_dir, f'{video_id}.mp3')
            
            # Check if file exists and has size
            if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
                raise Exception("Audio file not downloaded properly")
            
            print("Audio downloaded successfully, starting transcription...")
            
            # Load the Whisper model (using 'base' for faster processing, you can use 'small' or 'medium' for better accuracy)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = whisper.load_model("base", device=device)
            result = model.transcribe(audio_path, fp16=(device == "cuda"))
            
            print("Transcription completed successfully")
            return result["text"]
            
    except Exception as e:
        print(f"Error in download_and_transcribe: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function to process a single page needing a script."""
    COOKIE_FILE = 'cookies/chatgpt_cookies.pkl'
    URL = 'https://chatgpt.com/?model=gpt-4'
    
    # Get pages that need scripts
    log("Checking for pages...", "wait")
    pages = get_pages_needing_script()
    
    if not pages:
        log("No Page Needs Scripting!", "info")
        return False
        
    log(f"Found {len(pages)} pages to process", "success")
    page = pages[0]
    page_id = page["id"]
    
    # Get YouTube URL from the page
    youtube_url = get_youtube_url_from_page(page)
    if not youtube_url:
        log("Failed to get YouTube URL", "error")
        return False
        
    log(f"YouTube URL: {youtube_url}", "info")
    
    # First, get the video title
    log("Getting video title...", "wait")
    original_title = get_video_title(youtube_url)
    if not original_title:
        log("Failed to get video title", "error")
        return False
    log(f"Original: {Colors.DIM}{original_title}{Colors.RESET}", "info")
    
    # Get transcript from YouTube BEFORE starting browser operations
    log("Fetching transcript...", "wait")
    transcript = get_youtube_transcript(youtube_url, original_title)
    if not transcript:
        log("Failed to get transcript", "error")
        return False
    log(f"Transcript: {len(transcript)} characters", "success")
    
    # Only start browser operations if we have both title and transcript
    driver = setup_driver()
    
    try:
        # First navigate to the domain root to properly set cookies
        driver.get('https://chatgpt.com')
        time.sleep(2)  # Short wait for page load
        
        # Check if cookie file exists
        if not os.path.exists(COOKIE_FILE):
            log("No cookies found. Manual login required...", "warn")
            driver.get(URL)  # Now navigate to the full URL
            # Wait for manual login
            time.sleep(45)
            # Save cookies after login
            save_cookies(driver, COOKIE_FILE)
            log("Cookies saved", "success")
        else:
            log("Loading existing cookies...", "info")
            load_cookies(driver, COOKIE_FILE)
            driver.get(URL)  # Navigate to the full URL after loading cookies
            
        # Wait for page to load completely
        time.sleep(5)
        
        # Now get new title using ChatGPT
        log("Getting new title from ChatGPT...", "wait")
        new_title = get_gpt4_title(driver, original_title)
        if new_title:
            log(f"New title generated: {Colors.GREEN}{new_title}{Colors.RESET}", "success")
            log("Updating title in Notion...", "wait")
            if update_page_title(page_id, new_title):
                log("Title successfully updated in Notion", "success")
            else:
                log("Failed to update title in Notion", "error")
                return False
        else:
            log("Failed to generate new title", "error")
            return False
            
        # Clear the conversation before starting script generation
        driver.get(URL)  # Reload the page to start fresh
        time.sleep(5)  # Wait for page load
        
        # Start script generation
        log("Starting script generation...", "wait")
        paste_content(driver, transcript, title=original_title)
        
        # Process each part
        markers = ['AEB', 'AEC', 'AED']
        part_prompts = [
            "",  # No prompt for first part as it's handled in the initial request
            f"Now write part 2 (exactly {ScriptConfig.WORDS_PER_PART} words) starting with the code AEC. Continue the story naturally from part 1, but don't include any transitional phrases or references to the previous part. Just start directly with AEC followed by your content.",
            f"Now write part 3 (exactly {ScriptConfig.WORDS_PER_PART} words) starting with the code AED. Complete the story naturally, but don't include any transitional phrases or references to previous parts. Just start directly with AED followed by your content."
        ]
        full_response = ""
        
        for i, marker in enumerate(markers, 1):
            log(f"Waiting for Part {i}...", "wait")
            # Wait 50 seconds for ChatGPT to write the response
            time.sleep(50)
            response = get_chatgpt_response(driver, marker)
            
            if response:
                log(f"Part {i} received ({len(response)} chars)", "success")
                full_response += response + "\n\n"
                
                if i < len(markers):  # If not the last part
                    log(f"Requesting Part {i+1}...", "info")
                    time.sleep(2)  # Small pause before sending next command
                    paste_content(driver, part_prompts[i], is_continuation=True)
            else:
                log(f"Failed to get Part {i}", "error")
                return False
        
        if full_response:
            log("Updating Notion...", "wait")
            if update_page_content(page_id, full_response):
                log("Notion page updated", "success")
                # Mark the script as complete
                if update_script_checkbox(page_id):
                    log("Script marked as complete", "success")
                    return True
    finally:
        # Always close the browser when done
        log("Closing browser", "info")
        driver.quit()
    
    return False

if __name__ == "__main__":
    log("✨ SCRIPT AUTOMATION MONITOR", "header")
    
    try:
        while True:
            log("", "header")  # Empty line with header formatting
            log(f"Monitoring For New Scripts", "header")
            
            try:
                success = main()
                if success:
                    log("Processing complete!", "success")
            except Exception as e:
                log(f"Error: {str(e)}", "error")
                import traceback
                traceback.print_exc()
            
            # Wait before checking again
            next_check = datetime.datetime.now() + datetime.timedelta(seconds=10)
            log(f"Next check at {next_check.strftime('%H:%M:%S')}", "wait")
            time.sleep(10)
            log(".", "info", newline=False)
            print()
    except KeyboardInterrupt:
        print("\n")
        log("Script monitor stopped", "info")
        log("Goodbye! ✌️", "header")
