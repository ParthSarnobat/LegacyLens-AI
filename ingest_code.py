import os
import subprocess
import shutil
import stat  # <--- NEW IMPORT needed for the fix

# Files we want to read
ALLOWED_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.css', '.html', '.md', '.json'}

# Folders we ALWAYS ignore
IGNORE_DIRS = {'node_modules', 'venv', '.git', '__pycache__', 'dist', 'build'}

# --- HELPER: FORCE DELETE FOR WINDOWS ---
def on_rm_error(func, path, exc_info):
    """
    Error handler for shutil.rmtree.
    If the error is due to an access error (read-only file),
    it changes the file to be writable and attempts the delete again.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        os.unlink(path)
    except Exception as e:
        print(f"⚠️ Could not delete {path}: {e}")

def get_code_from_path(path_or_url):
    """
    Checks if the input is a GitHub URL. 
    If yes: Clones it to a temporary folder and returns that folder path.
    If no: Returns the original local path.
    """
    if path_or_url.startswith("http"): # Allow http or https
        # Create a folder name based on the repo name
        repo_name = path_or_url.split("/")[-1].replace(".git", "")
        
        # Ensure the temp directory exists
        os.makedirs("./temp_repos", exist_ok=True)
        local_path = f"./temp_repos/{repo_name}"
        
        # Clean up if it already exists
        if os.path.exists(local_path):
            print(f"🔄 Cleaning up old version of {repo_name}...")
            # --- THE FIX IS HERE: Added onerror=on_rm_error ---
            shutil.rmtree(local_path, onerror=on_rm_error)
            
        print(f"⬇️ Cloning {repo_name} from GitHub...")
        try:
            subprocess.run(["git", "clone", path_or_url, local_path], check=True)
            print(f"✅ Successfully cloned to {local_path}")
            return local_path
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to clone repository: {e}")
            return path_or_url # Fallback to original input on error
    
    # If it's not a URL, just return it as a local path
    return path_or_url

def get_codebase_context(path_or_url):
    """
    Walks through the directory, reads code files, and returns a single string
    formatted with file delimiters.
    """
    
    # Resolve the URL to a local folder path BEFORE walking it.
    root_dir = get_code_from_path(path_or_url)

    all_code = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # modify dirnames in-place to ignore excluded folders
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        
        for filename in filenames:
            file_ext = os.path.splitext(filename)[1]
            
            if file_ext in ALLOWED_EXTENSIONS:
                file_path = os.path.join(dirpath, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Format clearly for the LLM
                        formatted_block = (
                            f"\n\n--- START OF FILE: {file_path} ---\n"
                            f"{content}\n"
                            f"--- END OF FILE: {filename} ---\n"
                        )
                        all_code.append(formatted_block)
                        
                except Exception as e:
                    print(f"Skipping file {filename} due to error: {e}")

    return "".join(all_code)

if __name__ == "__main__":
    print("Testing ingestion...")
    repo_url = "https://github.com/octocat/Hello-World" 
    print(f"Testing with URL: {repo_url}")
    result = get_codebase_context(repo_url)
    print(f"\n--- Result Length: {len(result)} characters ---")
    print("Preview:\n", result[:500])