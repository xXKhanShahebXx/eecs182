# EECS 182 Extra Credit Website

## Ed API

1. **Create an Ed API Token:**
   - Go to Ed → Settings → API Tokens → Create Token
   - Copy your token

2. **Create a `.env` file:**
   ```bash
   ED_API_TOKEN="your_token_here"
   ```

## Usage

### Scraping Posts from Ed

To fetch the latest posts from Ed and update `posts.json`:

```bash
python scraper.py
```

### Updating the Website

After `posts.json` has been updated (either from running the scraper or manual edits), you need to rebuild the website:

```bash
python build_html.py
```

This script will:
- Use `template.html` and `posts.json`
- Embed the JSON data directly into `index.html`

After running this, you can rnu `open index.html` to see the file in your browser