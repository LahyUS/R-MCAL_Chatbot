import os
import subprocess
import platform

# Get the directory where the main_script.py is located
script_directory = os.path.dirname(os.path.abspath(__file__))

# List of batch script filenames
window_batch_scripts = [
    os.path.join(script_directory, "module_scripts", "run_mysqlServer.bat"),
    os.path.join(script_directory, "module_scripts", "run_main.bat"),
    os.path.join(script_directory, "module_scripts", "run_documentServer.bat"),
    #os.path.join(script_directory, "module_scripts", "run_modelServer.bat")
]

ubuntu_batch_scripts = [
    os.path.join(script_directory, "module_scripts", "run_mysqlServer.sh"),
    os.path.join(script_directory, "module_scripts", "run_main.sh"),
    os.path.join(script_directory, "module_scripts", "run_documentServer.sh"),
    #os.path.join(script_directory, "module_scripts", "run_modelServer.sh")
]

# Check the operating system
if platform.system() == "Windows":
    # Running on Windows
    for script in window_batch_scripts:
        subprocess.Popen(["start", "cmd", "/k", script], shell=True)
elif platform.system() == "Linux" or platform.system() == "Darwin":
    # Running on Linux or macOS
    for script in ubuntu_batch_scripts:
        subprocess.Popen(["gnome-terminal", "--", "bash", script])
else:
    print("Unsupported operating system.")


