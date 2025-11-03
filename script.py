"""
php_jobs_desktop.py
Simple desktop scraper that finds PHP job links on configured pages and shows them in a Tkinter window.

Usage:
1. pip install requests beautifulsoup4
2. python php_jobs_desktop.py

Notes:
- This is a heuristic scraper: it searches for links whose text or nearby text contains 'php'.
- Add/remove URLs in the SITES list below. Prefer RSS or official APIs where available.
- Check robots.txt / TOS before scraping any site.
"""

import requests
from bs4 import BeautifulSoup
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import html
from urllib.parse import urljoin, urlparse

# ---------------------- CONFIG ----------------------
SITES = [
    # Remote-friendly and safe-to-scrape sources
    "https://remoteok.com/remote-php-jobs",
    "https://weworkremotely.com/categories/remote-programming-jobs",
    "https://www.indeed.com/jobs?q=php&l=",

    # Wuzzuf RSS feed (replace keyword with what you like)
    "https://wuzzuf.net/search/jobs/?a=hpb&q=php",   # web version
    "https://wuzzuf.net/search/jobs/?a=spbg&q=php",  # specialized feed

    # Forasna search
    "https://forasna.com/jobs?q=php",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (job-scraper-example; contact: you@example.com)"
}

REQUEST_TIMEOUT = 12  # seconds
DELAY_BETWEEN_REQUESTS = 1.5  # polite delay (seconds)
MAX_LINKS_PER_SITE = 200

# ----------------------------------------------------

def fetch_page(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[fetch_page] Error fetching {url}: {e}")
        return None

def find_php_links_on_html(html_text, base_url):
    """Heuristic: find <a> tags whose text or nearby text contains 'php' (case-insensitive)."""
    soup = BeautifulSoup(html_text, "html.parser")
    matches = []
    # Search all links first (common case)
    for a in soup.find_all("a", href=True):
        txt = (a.get_text(" ", strip=True) or "").lower()
        href = a["href"]
        if "php" in txt or "php" in href.lower():
            title = a.get_text(" ", strip=True) or href
            full = urljoin(base_url, href)
            matches.append({"title": html.unescape(title), "url": full})
        else:
            # also check the parent element text (e.g., surrounding job card)
            parent = a.parent
            if parent:
                parent_text = parent.get_text(" ", strip=True).lower()
                if "php" in parent_text:
                    title = a.get_text(" ", strip=True) or a["href"]
                    full = urljoin(base_url, href)
                    matches.append({"title": html.unescape(title), "url": full})
    # Deduplicate preserving order
    seen = set()
    deduped = []
    for m in matches:
        key = (m["url"], m["title"])
        if key not in seen:
            deduped.append(m)
            seen.add(key)
        if len(deduped) >= MAX_LINKS_PER_SITE:
            break
    return deduped

def scrape_site(url):
    print(f"[scrape_site] Scraping {url}")
    html_text = fetch_page(url)
    if not html_text:
        return []
    links = find_php_links_on_html(html_text, url)
    print(f"[scrape_site] Found {len(links)} candidate links on {url}")
    return links

# ----------------- GUI / App -----------------
class JobsApp:
    def __init__(self, root):
        self.root = root
        root.title("PHP Jobs - Scraper")
        root.geometry("900x600")

        top = ttk.Frame(root, padding=8)
        top.pack(side="top", fill="x")

        self.status = tk.StringVar(value="Idle")
        ttk.Label(top, text="Status:").pack(side="left")
        self.status_label = ttk.Label(top, textvariable=self.status)
        self.status_label.pack(side="left", padx=(6, 12))

        self.refresh_btn = ttk.Button(top, text="Refresh", command=self.start_scrape_thread)
        self.refresh_btn.pack(side="right")

        # Site list and add site entry
        site_frame = ttk.Frame(root, padding=(8,0,8,8))
        site_frame.pack(side="top", fill="x")

        ttk.Label(site_frame, text="Sites to scan (editable):").pack(side="left")
        self.sites_text = tk.Text(site_frame, height=3)
        self.sites_text.pack(side="left", fill="x", expand=True, padx=(6,0))
        self.sites_text.insert("1.0", "\n".join(SITES))

        # Results table
        results_frame = ttk.Frame(root, padding=8)
        results_frame.pack(side="top", fill="both", expand=True)

        cols = ("title", "site")
        self.tree = ttk.Treeview(results_frame, columns=cols, show="headings")
        self.tree.heading("title", text="Job title / link")
        self.tree.heading("site", text="Source")
        self.tree.column("title", width=700)
        self.tree.column("site", width=180)
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self.on_item_double_click)

        bottom = ttk.Frame(root, padding=8)
        bottom.pack(side="bottom", fill="x")
        ttk.Label(bottom, text="Double-click a row to open the job link in your browser.").pack(side="left")

        # initial scrape
        self.start_scrape_thread()

    def set_status(self, text):
        self.status.set(text)
        self.root.update_idletasks()

    def on_item_double_click(self, event):
        item = self.tree.selection()
        if not item:
            return
        data = self.tree.item(item)
        url = data.get("values")[2] if len(data.get("values")) >= 3 else None
        # We stored url in hidden field if possible; otherwise parse from title
        if not url:
            # fallback: open the text and try to find a url inside
            url = data.get("values")[0]
        if url:
            webbrowser.open(url)
        else:
            messagebox.showinfo("No URL", "Can't find URL to open for this item.")

    def clear_results(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

    def add_result(self, title, site, url):
        # store title and site visible; store url as hidden value (we'll add as third column value)
        self.tree.insert("", "end", values=(title, site, url))

    def start_scrape_thread(self):
        t = threading.Thread(target=self.scrape_and_display, daemon=True)
        t.start()

    def scrape_and_display(self):
        # get sites from text widget
        raw = self.sites_text.get("1.0", "end").strip()
        sites = [line.strip() for line in raw.splitlines() if line.strip()]
        if not sites:
            messagebox.showwarning("No sites", "Please add at least one site URL to scan.")
            return

        self.refresh_btn.config(state="disabled")
        self.set_status("Scraping...")
        self.clear_results()

        total_count = 0
        for idx, site in enumerate(sites, 1):
            parsed = urlparse(site)
            if not parsed.scheme:
                site = "https://" + site  # assume https if missing

            self.set_status(f"Scraping ({idx}/{len(sites)}) {site} ...")
            links = scrape_site(site)
            for l in links:
                title = l.get("title") or l.get("url")
                url = l.get("url")
                self.add_result(title, site, url)
                total_count += 1
            time.sleep(DELAY_BETWEEN_REQUESTS)

        self.set_status(f"Done — found {total_count} items")
        self.refresh_btn.config(state="normal")

def main():
    root = tk.Tk()
    app = JobsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
