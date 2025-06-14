import platform
import os

def get_chrome_profile_path():
    """
    Determine the operating system and return the appropriate Chrome profile path.
    Returns:
        str: The full path to the Chrome profile directory
    """
    system = platform.system()
    
    if system == 'Darwin':  # macOS
        profile_path = '/Users/superman/Desktop/Chrome Profile (ChatGPT) 2'
    elif system == 'Windows':  # Windows
        profile_path = r'C:\Users\vaisa\Desktop\Chrome Profile (ChatGPT) 2'
    else:
        raise OSError(f"Unsupported operating system: {system}")
        
    # Verify the path exists
    if not os.path.exists(profile_path):
        raise FileNotFoundError(f"Chrome profile path not found: {profile_path}")
        
    return profile_path
