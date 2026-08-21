import os
import json
import urllib.request
import subprocess
import time

if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("GEMINI_API_KEY="):
                os.environ["GEMINI_API_KEY"] = line.strip().split("=", 1)[1].strip('"\'')

api_key = os.environ.get("GEMINI_API_KEY")
# Using 3.5-flash-lite to save quota and prevent rate limits
model_name = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite") 
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

def get_current_branch():
    try:
        res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
        return res.stdout.strip()
    except Exception:
        return "main"

def get_specific_files():
    files_data = {}
    for root, dirs, files in os.walk("."):
        if any(p in root for p in [".git", "__pycache__", "node_modules", ".next", ".vercel", "build", "dist"]):
            continue
        for file in files:
            if file in ["package.json"] or file.endswith((".js", ".ts", ".tsx", ".jsx", ".css")):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        files_data[filepath] = f.read()
                except Exception:
                    pass
    return files_data

def call_gemini(prompt_text):
    if not api_key:
        return None
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    
    schema = {
        "type": "OBJECT",
        "properties": {
            "reasoning": {"type": "STRING"},
            "files": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "path": {"type": "STRING"},
                        "content": {"type": "STRING"}
                    },
                    "required": ["path", "content"]
                }
            }
        },
        "required": ["reasoning", "files"]
    }

    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "response_schema": schema
        }
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"API Error ({model_name}): {e}")
        return None

def check_vercel_state():
    try:
        res = subprocess.run(["npx", "--yes", "vercel", "ls", "--yes"], capture_output=True, text=True)
        output = res.stdout + "\n" + res.stderr
        if "Building" in output or "Queued" in output:
            return "Building"
        elif "Error" in output or "Failed" in output:
            return "Error"
        elif "Ready" in output:
            return "Ready"
        return "Ready"
    except Exception:
        return "Ready"

def get_latest_logs():
    try:
        res = subprocess.run(["npx", "--yes", "vercel", "logs", "--limit", "300"], capture_output=True, text=True)
        return res.stdout + "\n" + res.stderr
    except Exception:
        return ""

def main():
    if not api_key:
        print("Missing GEMINI_API_KEY in .env!")
        return
        
    branch = get_current_branch()
    print(f"\n👁️ Code Watchdog Active.")
    print(f"Branch: {branch} | Model: {model_name}\n")
    
    last_failed_commit = None

    while True:
        state = check_vercel_state()
        
        if state == "Error":
            try:
                current_commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
            except:
                current_commit = "unknown"

            if current_commit == last_failed_commit:
                print("⏳ Waiting before retrying same commit...")
                time.sleep(60)
                continue
                
            print("\n💥 BUILD ERROR CAUGHT! Analyzing code and logs...")
            logs = get_latest_logs()
            files_dict = get_specific_files()
            
            files_context = "\n".join([f"--- FILE: {path} ---\n{content}\n" for path, content in files_dict.items()])

            prompt = f"""
The Vercel build failed with this log:
{logs}

Repository Files:
{files_context}

Task: Find the issue in the code or package.json. Fix it by rewriting the file content.
Rules:
1. ONLY modify package.json or source code files.
2. DO NOT modify vercel.json or run_gemini.py.
"""
            raw_response = call_gemini(prompt)
            
            if raw_response:
                try:
                    data = json.loads(raw_response)
                    for item in data.get("files", []):
                        f_path = item.get("path")
                        f_content = item.get("content")
                        if f_path and f_content and "vercel.json" not in f_path and f_path != "run_gemini.py":
                            os.makedirs(os.path.dirname(f_path) or ".", exist_ok=True)
                            with open(f_path, "w", encoding="utf-8") as f:
                                f.write(f_content)
                            print(f"🩹 Fixed & Saved: {f_path}")
                    
                    subprocess.run(["git", "add", "."])
                    subprocess.run(["git", "commit", "-m", "Auto-fixed build error"])
                    subprocess.run(["git", "push", "origin", branch])
                    print(f"🚀 Pushed fix to '{branch}'.")
                    last_failed_commit = current_commit
                    # Cooldown to respect rate limits after a fix attempt
                    time.sleep(45)
                except Exception as e:
                    print(f"Error processing JSON payload: {e}")
                    time.sleep(30)
            else:
                print("⚠️ Rate-limited or empty response from API. Backing off for 60s...")
                time.sleep(60)
            
        elif state == "Building":
            print("⏳ Vercel build in progress...")
            time.sleep(25)
        else:
            print("✅ Deployment healthy. Monitoring...")
            time.sleep(45)

if __name__ == "__main__":
    main()
