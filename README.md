#  PHP Jobs Desktop Scraper

A simple **Python desktop app** that automatically fetches the latest **PHP job listings** from multiple websites (e.g. RemoteOK, Wuzzuf, Indeed, WeWorkRemotely, etc.) and displays them in a GUI when you open your computer.

The app scrapes safe-to-access pages and RSS feeds, then lists job titles with clickable links — all in one window.

---

##  Features

- Fetches job listings mentioning **PHP** from multiple sites.  
- Simple **Tkinter** desktop interface.  
- Click a job to open it directly in your browser.  
- Runs automatically when you log into Windows.  
- Lightweight — no database required.

---

##  Requirements

Before building or running, install **Python 3.8+** and these dependencies:

```bash
pip install requests beautifulsoup4
## prefered usage
if you work on windows you can put the exe version of the script in the folder that boots every element on it whenever your pc or laptop start.
