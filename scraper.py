import json
import re
import time
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from edapi import EdAPI

# --- Configuration ---
COURSE_ID = 84647
OUTPUT_FILE = "posts.json"
# Regex to find the specific "Special Participation" posts
THREAD_PATTERN = re.compile(r"(?i)special\s+part.*n\s+e")


# --- Helper: Parsing Logic (From previous steps) ---
def parse_ed_content(raw_xml):
    """
    Parses Ed's XML to return clean text and a list of resources.
    Includes logic to catch raw text URLs.
    """
    if not raw_xml:
        return "", []

    resources = []
    seen_urls = set()

    def add_resource(r_type, url, name):
        clean_url = url.strip()
        if clean_url not in seen_urls:
            seen_urls.add(clean_url)
            # Simple heuristic to clean up names
            if name == clean_url:
                name = "Link"
            resources.append({'type': r_type, 'url': clean_url, 'name': name})

    try:
        sanitized_xml = raw_xml.replace('&nbsp;', ' ')
        # Wrap in root to handle multiple top-level elements
        root = ET.fromstring(f"<root>{sanitized_xml}</root>")

        text_parts = []

        for element in root.iter():
            # Extract text
            if element.text:
                text_parts.append(element.text)

            # Extract resources
            if element.tag == 'link':
                url = element.get('href')
                name = "".join(element.itertext()).strip() or "External Link"
                if url: add_resource('link', url, name)

            elif element.tag in ('file', 'secure-file'):
                url = element.get('url')
                name = element.get('filename', 'File')
                if url: add_resource('file', url, name)

            elif element.tag == 'image':
                url = element.get('src')
                name = element.get('alt', 'Image')
                if url: add_resource('image', url, name)

            # Extract tail text
            if element.tail:
                text_parts.append(element.tail)

        full_text = "".join(text_parts).strip()

    except ET.ParseError:
        # Fallback regex parsing
        full_text = re.sub(r'<[^>]+>', '', raw_xml).strip()

    # Scan for raw URLs in the text that weren't caught by tags
    raw_links = re.findall(r'(https?://[^\s"\'<>]+)', full_text)
    for link in raw_links:
        if 'static.us.edusercontent.com' in link:
            add_resource('file', link, 'Raw File Attachment')
        elif link not in seen_urls:
            add_resource('link', link, 'Raw Text Link')

    return full_text, resources


# --- Helper: Auto-Tagging ---
def generate_tags(title, content):
    """
    Generates search tags based on keywords in title/content.
    Useful for filtering on the website later.
    """
    tags = []
    text_blob = (title + " " + content).lower()

    keywords = {
        "Visualization": ["visual", "diagram", "manim", "plot", "graph"],
        "Study Guide": ["guide", "roadmap", "notes", "summary", "cheat sheet"],
        "Quiz/Drill": ["quiz", "drill", "flashcard", "mcq", "question generator"],
        "Tool/App": ["tool", "app", "cli", "website", "interface"],
        "Prompt Eng": ["prompt", "system prompt", "persona"],
        "Coding": ["code", "implementation", "python", "jupyter", "colab"],
        "Math": ["derivation", "proof", "calculus", "linear algebra"],
        "Tutor": ["tutor", "coach", "socratic"]
    }

    for tag, keys in keywords.items():
        if any(k in text_blob for k in keys):
            tags.append(tag)

    return list(set(tags))


# --- Main Script ---
def main():
    ed = EdAPI()
    try:
        ed.login()
        print("Logged in successfully.")
    except Exception as e:
        print(f"Login failed: {e}")
        return

    print(f"--- Scanning Course {COURSE_ID} ---")

    # 1. Fetch all thread summaries first
    all_threads = []
    offset = 0
    batch_size = 50

    print("Step 1: Fetching thread list (pagination)...")
    while True:
        try:
            batch = ed.list_threads(COURSE_ID, limit=batch_size, offset=offset)
            if not batch: break
            all_threads.extend(batch)
            offset += len(batch)
            sys.stdout.write(f"\rFetched {len(all_threads)} summaries...")
            time.sleep(0.2)
        except Exception as e:
            print(f"\nError fetching batch: {e}")
            break

    print(f"\nTotal threads scanned: {len(all_threads)}")

    # 2. Filter and Process
    final_posts = []
    print("\nStep 2: filtering and processing content...")

    for i, thread in enumerate(all_threads):
        title = thread.get('title', '')

        # Check if it matches "Special Participation E"
        if THREAD_PATTERN.search(title):
            t_id = thread.get('id')
            created_at = thread.get('created_at')
            user_obj = thread.get('user', {})
            author_name = user_obj.get('name', 'Anonymous') if user_obj else 'Anonymous'

            try:
                # Fetch full content
                full_thread = ed.get_thread(t_id)
                raw_content = full_thread.get('content', '')

                # Parse
                clean_text, resources = parse_ed_content(raw_content)

                # Auto-tag
                tags = generate_tags(title, clean_text)

                # Build Data Object
                post_data = {
                    "id": t_id,
                    "title": title,
                    "date": created_at,
                    "author": author_name,
                    "content": clean_text,
                    "resources": resources,
                    "tags": tags,
                    "original_url": f"https://edstem.org/us/courses/{COURSE_ID}/discussion/{t_id}"
                }

                final_posts.append(post_data)

                # Progress indicator
                sys.stdout.write(f"\rProcessed {len(final_posts)} matching posts...")

                # Rate limit safety
                time.sleep(0.2)

            except Exception as e:
                print(f"\nError processing thread {t_id}: {e}")

    # 3. Save to JSON
    print(f"\n\nStep 3: Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_posts, f, indent=2, ensure_ascii=False)

    print(f"Done! Saved {len(final_posts)} posts.")
    print("You can now load 'posts.json' into your website frontend.")


if __name__ == "__main__":
    main()