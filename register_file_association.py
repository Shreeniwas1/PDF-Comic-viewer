
import os
import sys
import winreg
import subprocess

def add_registry_entry(ext, app_path):
    """Add registry entries for file association"""
    
    # Define the app name and description
    app_name = "PDFComicViewer"
    app_desc = "PDF and Comic Book Viewer"
    
    # Create keys for the file extension
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{ext}") as key:
        winreg.SetValue(key, "", winreg.REG_SZ, app_name)

    # Create keys for the application
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{app_name}") as key:
        winreg.SetValue(key, "", winreg.REG_SZ, app_desc)
        
        # Set up the command to run
        with winreg.CreateKey(key, "shell\\open\\command") as cmd_key:
            cmd = f'"{sys.executable}" "{app_path}" "%1"'
            winreg.SetValue(cmd_key, "", winreg.REG_SZ, cmd)

def main():
    try:
        # Get the full path to the viewer script
        viewer_path = os.path.abspath("viewer.py")
        
        # Register file associations
        add_registry_entry(".pdf", viewer_path)
        add_registry_entry(".cbz", viewer_path)
        
        # Notify Windows of the change
        subprocess.run(["assoc", ".pdf"])
        subprocess.run(["assoc", ".cbz"])
        
        print("File associations registered successfully!")
        print("You can now open PDF and CBZ files with this viewer through Windows Explorer.")
    except Exception as e:
        print(f"Error registering file associations: {e}")
        print("Try running this script as administrator.")

if __name__ == "__main__":
    main()