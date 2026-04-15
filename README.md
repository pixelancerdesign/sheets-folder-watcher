# sheets-folder-watcher
Manage your projects with a Master Google Sheet which is the source of truth for your projects. Your Mac folders will reflect the master sheet automatically without you having to do anything twice.

The tool is built around one simple idea: your Google Sheet is the source of truth for your projects, and your Mac folders should reflect that automatically without you having to do anything twice.

Here is how it works.

A Python script lives on your Mac and runs silently in the background at all times (the resource usage is minimal, close to nonexistent). Every 5 minutes it wakes up, reads your Google Sheet, and checks if anything new has been marked as "working on it" or your status of choice. If it finds something new, it creates the predefined folder structure on your Mac instantly. Then it goes back to sleep and waits for the next cycle.

MacOS has a built-in system called launchd that acts like a silent assistant. It is the one responsible for keeping the script alive. It starts it when you log in, restarts it if it ever crashes, and makes sure it is always running.

To read your Google Sheet without asking you to log in every time, the script authenticates as a service account. (You need to set this up)
It's actually a bot user that you created in Google Cloud and then invited to your sheet. It has read access and nothing else.

The only file you ever need to touch is config.json. That is where you tell the script which sheet to watch, which columns contain the project code, name and status, which sheet tabs map to which local folders, and where on your Mac the folders should be created.

To make sure folders are never created twice, every time the script creates a new project folder it saves a record of it in a file called .state.json. Before creating anything, it checks that file first. If the project is already there it skips it and moves on.

The end result is that you update one cell in a spreadsheet and a perfectly structured folder appears on your computer within 5 minutes, which helps your mental health tremendously as it did with mine :D

The steps to be followed are the ones below.

**Phase 1: Google Cloud Setup
**
- Go to console.cloud.google.com and create a new project
- Navigate to APIs & Services, search for Google Sheets API and enable it
- Go to IAM & Admin, open Service Accounts and click Create Service Account
- Give it a name, skip the optional role and access steps, and save
- Click on the service account you just created, go to Keys, click Add Key and choose JSON
- The key file downloads automatically, move it into your project folder
- Open your Google Sheet, click Share, paste the service account email from the JSON file, set it to Viewer and confirm

**Phase 2 — Local Setup
**
- Clone the repository to your machine
- Open a terminal, navigate into the project folder
- Run python3 -m venv venv to create a virtual environment
- Run source venv/bin/activate to activate it
- Run pip install -r requirements.txt to install dependencies
- Copy config.example.json to config.json
- Open config.json and fill in your spreadsheet ID, service account filename, base path, column letters, sheet tab names and their matching local folder names

**Phase 3 — Background Service
**
- Open the plist file and update the file paths to match your machine
- Copy the plist file to ~/Library/LaunchAgents/
- Run launchctl load ~/Library/LaunchAgents/com.yourname.sheets-watcher.plist
- Run launchctl list | grep sheets-watcher to confirm it is running
- Verify everything works

Run python3 watcher.py --now to trigger an immediate check
Set any row in your sheet to working on it and confirm the folder appears locally

Show some love on socials 
<a href="https://ibb.co/3ypffyTM"><img src="https://i.ibb.co/3ypffyTM/final-logo-pixelancer.png" alt="final-logo-pixelancer" border="0" /></a>
