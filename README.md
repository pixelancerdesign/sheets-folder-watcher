# SheetsWatcher

Manage your projects with a Master Google Sheet which is the source of truth. Your Mac folders will reflect it automatically without you having to do anything twice.

---

## The Idea

Your Google Sheet is the source of truth for your projects, and your Mac folders should reflect that automatically without you having to do anything twice.

A Python script lives on your Mac and runs silently in the background at all times. The resource usage is minimal, close to nonexistent. Every 5 minutes it wakes up, reads your Google Sheet, and checks if anything new has been marked as `working on it` or whatever status you choose. If it finds something new, it creates a predefined folder structure on your Mac instantly. Then it goes back to sleep and waits for the next cycle.

macOS has a built-in system called **launchd** that acts like a silent assistant. It starts the script when you log in, restarts it if it ever crashes, and makes sure it is always running without you having to think about it.

To read your Google Sheet without asking you to log in every time, the script authenticates as a **service account** — a bot user you create in Google Cloud and invite to your sheet. It has read access and nothing else. No browser popups, no tokens that expire.

The end result is that you update one cell in a spreadsheet and a perfectly structured folder appears on your computer within 5 minutes. It helps your mental health tremendously, as it did with mine :D

---

## Example Result

```
~/Documents/YOUR_BASE_FOLDER/
└── YOUR_CATEGORY_FOLDER/
    └── 2026/
        └── CODE00-Project_Name/
            ├── Brief/
            ├── Links/
            ├── Design/
            └── Deliver/
```

---

## Google Sheet Structure

The script expects each sheet tab to have at minimum these columns. The exact letters are configurable inside the app.

| Column | Content | Example |
|--------|---------|---------|
| A | Project name | `My Project` |
| B | Project code | `AB01` |
| C | Any other info | notes, owner, date |
| D | Status | `working on it` |

The folder name is built by combining code and name: `AB01-My_Project`

Spaces in the project name are automatically converted to underscores. Each sheet tab represents a project category. The watcher monitors all tabs you define in the app and routes each project to the correct local folder.

---

## Requirements

- macOS (uses launchd for background service)
- Python 3.10+
- A Google Sheet with project data
- A Google Cloud account (free)
- SheetsWatcher app (download from the Releases section on this page)

---

## Phase 1: Google Cloud Setup

Go to [console.cloud.google.com](https://console.cloud.google.com) and create a new project. Navigate to APIs & Services, search for Google Sheets API and enable it.

Go to IAM & Admin, open Service Accounts and click Create Service Account. Give it a name, skip the optional role and access steps, and save. Click on the service account you just created, go to Keys, click Add Key and choose JSON. The key file downloads automatically.

Move the downloaded JSON file into your `sheets-watcher` folder. Then open your Google Sheet, click Share, paste the service account email from the JSON file (you will find it under the `client_email` field), set it to Viewer and confirm.

---

## Phase 2: Local Setup

Download and install **SheetsWatcher.app** and place the `sheets-watcher` folder somewhere permanent on your Mac, for example inside your Documents folder.

Open SheetsWatcher from your menu bar, click the icon and go to Settings. Click Browse next to Script Location and select `watcher.py` from the `sheets-watcher` folder. The Python environment sets itself up automatically, no terminal needed.

Then fill in your details:

- **Spreadsheet ID** — the part of your Google Sheet URL between `/d/` and `/edit`
- **Service Account File** — the filename of the JSON key you downloaded
- **Base Path** — the root folder on your Mac where all projects will be created
- **Column letters** — which columns hold the project code, name and status
- **Trigger value** — the status text that creates the folder, default is `working on it`
- **Subfolders** — the folders created inside every new project
- **Sheet tab mappings** — map each Google Sheet tab name to a local folder name

Click Save Configuration when you are done.

---

## Phase 3: Start the Watcher

Click Sync Now in the dashboard to run an immediate test. Go to your sheet, set any row status to `working on it` and click Sync Now again. Confirm the folder appears on your Mac in the right location.

Click Start and the watcher runs automatically every 5 minutes in the background from that point on. It starts on login and runs silently forever. You never need to open the app again unless you want to check the log or update your settings.

Show some love on socials! ❤️

---

## How It Works

```
Google Sheet
     │
     │  (Google Sheets API, every 5 min)
     ▼
 watcher.py
     │
     ├─ Reads all watched sheet tabs
     ├─ Finds rows where status = "working on it"
     ├─ Checks .state.json (skips already-created folders)
     ├─ Builds path: base_path / category / year / CODE-Name
     ├─ Creates folder + subfolders
     └─ Saves state
```

State is stored in `.state.json` which is how the watcher remembers which projects have already been created so it never duplicates.

---

## Troubleshooting

**Folders not being created**

Check the Activity Log in the dashboard for errors. Verify the sheet is shared with the service account email and make sure the Google Sheets API is enabled in your Google Cloud project. Confirm the status value matches your trigger exactly, it is case-insensitive.

**403 Permission Denied**

This means either the sheet has not been shared with the service account email or the Google Sheets API is not enabled for your project.

**App won't open due to unidentified developer warning**

Right-click the app, click Open and then click Open again in the dialog. This only needs to be done once.

---

## File Structure

```
sheets-watcher/
├── watcher.py               # Main script
├── config.example.json      # Reference template
├── requirements.txt         # Python dependencies
├── run.sh                   # Shell wrapper for launchd
├── config.json              # Auto-generated by the app when you save settings
└── .state.json              # Auto-generated at runtime, tracks created folders
```

---

## License

MIT, free to use, modify, and share.
