#!/usr/bin/env python3
"""
Embeds posts.json directly into index.html using template.html.
"""

import json
import os
import sys

def main():
    # Check if files exist
    if not os.path.exists('posts.json'):
        print("Error: posts.json not found.")
        sys.exit(1)
        
    if not os.path.exists('template.html'):
        print("Error: template.html not found.")
        # Optional: could try to recover template from index.html if needed, 
        # but better to fail and ask user to restore template.
        sys.exit(1)

    # Read the JSON file
    print("Reading posts.json...")
    with open('posts.json', 'r', encoding='utf-8') as f:
        try:
            posts_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding posts.json: {e}")
            sys.exit(1)
    
    print(f"Loaded {len(posts_data)} posts")

    # Convert to JSON string
    posts_json_str = json.dumps(posts_data, ensure_ascii=False)

    # Read the template file
    print("Reading template.html...")
    with open('template.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Find and replace the placeholder
    # The placeholder in template.html is: const POSTS_DATA = []; // DATA_PLACEHOLDER
    placeholder = 'const POSTS_DATA = []; // DATA_PLACEHOLDER'
    
    if placeholder in html_content:
        # Replace the placeholder with the actual data
        # We keep the variable declaration
        replacement = f'const POSTS_DATA = {posts_json_str};'
        new_html_content = html_content.replace(placeholder, replacement)
    else:
        print("Warning: Exact placeholder not found. Searching for 'const POSTS_DATA ='.")
        # Fallback: try regex or simpler search if exact match fails (e.g. whitespace diff)
        # But since we generated the template, it should match.
        import re
        pattern = r'const POSTS_DATA\s*=\s*\[\];\s*//\s*DATA_PLACEHOLDER'
        if re.search(pattern, html_content):
            new_html_content = re.sub(pattern, f'const POSTS_DATA = {posts_json_str};', html_content)
        else:
            print("Error: Could not find POSTS_DATA placeholder in template.html")
            sys.exit(1)

    print("Embedding JSON data into HTML...")

    # Write the updated HTML
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_html_content)

    print("Successfully generated index.html from template.html and posts.json")
    print("You can now open index.html directly in your browser!")

if __name__ == "__main__":
    main()
