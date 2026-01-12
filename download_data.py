
import os
import re
import urllib.request
import urllib.error

BASE_URL = "https://www.eia.gov/consumption/residential/data/2020/"
OUTPUT_DIR = "data"
HTML_FILE = "eia_page.html"

def download_files():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Read the HTML content we already fetched
    with open(HTML_FILE, "r") as f:
        content = f.read()

    # Find all .xlsx links
    links = re.findall(r'href="([^"]+\.xlsx)"', content)
    
    print(f"Found {len(links)} XLSX files to download.")
    
    for link in links:
        if link.startswith("http"):
            url = link
        else:
            safe_link = link.replace(" ", "%20")
            url = BASE_URL + safe_link

        filename = os.path.basename(link)
        save_name = filename.replace("%20", "_").replace(" ", "_")
        save_path = os.path.join(OUTPUT_DIR, save_name)
        
        if os.path.exists(save_path):
            print(f"Skipping {save_name} (exists)")
            continue

        print(f"Downloading {save_name} from {url}...")
        try:
            import ssl
            context = ssl._create_unverified_context()
            with urllib.request.urlopen(url, context=context) as response, open(save_path, 'wb') as out_file:
                data = response.read()
                out_file.write(data)
        except Exception as e:
            print(f"Failed to download {url}: {str(e)}")

if __name__ == "__main__":
    download_files()
