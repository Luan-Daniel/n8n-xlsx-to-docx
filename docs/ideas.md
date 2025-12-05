Finish the python entrypoint (src/entrypoint.py): (update: all_done)
- Create window popup for updating dependencies before gui starts.
- Should set up venv and install requirements.txt
- Should check system requirements and prompt if missing (eg.: linux/wsl, docker installed)
- Should run the main python script
- Also should write ./run.ps1 and ./run.sh for easier launching on windows/linux. They should check for python and call the entrypoint.py.
- Now also need to ensure wsl2 is used on windows, and also tkinter `python3-tk` is installed.
Fishish the service manager (src/service-manager/main.py): (update: all_done)
- Is a GUI Application, Its main purposes are:
  - To keep the docker n8n container running properly while the user uses the app (option to start/stop). Button behavior:
    - Container not running or doesnt exist: Offer to start it, using the "./src/docker-n8n/start-n8n.sh" script. And wait for the script to finish to change the button state.
    - Container running: Offer to stop it, using the "./src/docker-n8n/stop-n8n.sh" script. And wait for the script to finish with 0 to change the button state (the script may fail with 1).
  - To provide a simple GUI for the user to input a xlsx file (that triggers the n8n workflow run with a request).
  - Copy the resulting files to a user specified output directory automatically.
- Provide a button to open the n8n web interface in the default browser.
- Dont forget the sheet_downloader functionality.
- The n8n will send back error codes or the resulting files list (inside n8n-data/app/*/ subdirectories) when they are done, using HTTP POST requests, so we need to handle those requests and display the progress to the user (and eventual success), and point the resulting files locations and names.
Finish setting the n8n workflow: (update: all_done)
- Should receive a HTTP request with the xlsx file location
- Should process the xlsx file and generate the charts
- Should save the resulting files to a specified output directory
Work on the auto-setup and setup documentation: (update: in_progress)
- The project should be easy to set up for non-developers end users (WIP)
- Thinking of packing the n8n-data and .env for easier distribution. User will be advised to create their own credentials, but for convenience some defaults might be provided. (update: done, but needs testing)
- Work on common setup variables like webhook url, input/output directories, etc. (a lot of work to be done here)
Work on the repository documentation: (update: in_progress)
- Basic README.md describing the project, setup guide, usage guide, functionality overview, implementation overview, etc.
- dependencies.md describing system dependencies and installation instructions.