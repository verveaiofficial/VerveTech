import os
import json
import urllib.request
import subprocess
import sys
import time

if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("GEMINI_API_KEY="):
                os.environ["GEMINI_API_KEY"] = line.strip().split("=", 1)[1].strip('"\'')

api_key = os.environ.get("GEMINI_API_KEY")
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
        return "Unknown"
    except Exception:
        return "Unknown"

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
    print(f"\n🎯 On-Demand Code Fixer Active (Branch: {branch} | Model: {model_name})")
    print("Running a single auto-fix cycle until the build is successful...\n")
    
    attempts = 0
    max_attempts = 5

    while attempts < max_attempts:
        attempts += 1
        state = check_vercel_state()
        print(f"[{attempts}/{max_attempts}] Current Vercel Build State: {state}")
        
        if state == "Ready":
            print("✅ Build is completely successful and green! Stopping loop.")
            sys.exit(0)
            
        elif state == "Error" or state == "Unknown":
            print("💥 Build error detected. Analyzing logs and patching files...")
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
                    updated = False
                    for item in data.get("files", []):
                        f_path = item.get("path")
                        f_content = item.get("content")
                        if f_path and f_content and "vercel.json" not in f_path and f_path != "run_gemini.py":
                            os.makedirs(os.path.dirname(f_path) or ".", exist_ok=True)
                            with open(f_path, "w", encoding="utf-8") as f:
                                f.write(f_content)
                            print(f"🩹 Patched: {f_path}")
                            updated = True
                    
                    if updated:
                        subprocess.run(["git", "add", "."])
                        subprocess.run(["git", "commit", "-m", f"Auto-heal fix attempt {attempts}"])
                        subprocess.run(["git", "push", "origin", branch])
                        print(f"🚀 Pushed fix to '{branch}'. Waiting for Vercel to pick it up...")
                        time.sleep(30)
                except Exception as e:
                    print(f"Error parsing AI response: {e}")
            
        elif state == "Building":
            print("⏳ Build in progress... waiting 20 seconds.")
            time.sleep(20)
            
    print("Reached max auto-fix attempts. Exiting so you can chat or inspect.")

if __name__ == "__main__":
    main()
