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
model_name = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

def get_current_branch():
    try:
        res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
        return res.stdout.strip()
    except Exception:
        return "main"

def get_project_files():
    context = ""
    for root, dirs, files in os.walk("."):
        if any(p in root for p in [".git", "__pycache__", "node_modules", ".next", ".vercel", "build", "dist"]):
            continue
        for file in files:
            if file.endswith((".py", ".json", ".md", ".txt", ".js", ".ts", ".tsx", ".jsx", ".html", ".css")):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        context += f"\n--- FILE: {filepath} ---\n" + f.read() + "\n"
                except Exception:
                    pass
    return context

def call_gemini(prompt_text):
    if not api_key:
        return None
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"API Error: {e}")
        return None

def check_vercel_state():
    try:
        # 'vercel ls' returns the deployment history. The top entry is the latest status.
        res = subprocess.run(["npx", "--yes", "vercel", "ls"], capture_output=True, text=True)
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
        res = subprocess.run(["npx", "--yes", "vercel", "logs", "--limit", "200"], capture_output=True, text=True)
        return res.stdout + "\n" + res.stderr
    except Exception:
        return ""

def main():
    if not api_key:
        print("Missing GEMINI_API_KEY in .env!")
        return
        
    branch = get_current_branch()
    print(f"\n👁️ Verve AI Autonomous Watchdog Activated.")
    print(f"Branch: {branch} | Model: {model_name}")
    print("Zero-input mode engaged. Monitoring Vercel 24/7 in the background...\n")
    
    last_failed_commit = None

    while True:
        try:
            current_commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        except:
            current_commit = "unknown"

        state = check_vercel_state()
        
        if state == "Building":
            print("⏳ Vercel is building... waiting 15 seconds.")
            time.sleep(15)
            
        elif state == "Error":
            if current_commit == last_failed_commit:
                print("⚠️ Last auto-patch failed on this exact commit. Waiting 60s for manual intervention to prevent a loop...")
                time.sleep(60)
                continue
                
            print("\n💥 CRASH DETECTED! Pulling live logs and initiating auto-heal...")
            logs = get_latest_logs()
            
            system_instruction = f"""
You are an autonomous CI/CD agent for Verve AI Studio. The live Vercel deployment just FAILED.
Analyze the logs and project files below, then write the exact code to fix the build syntax/type errors.

CRITICAL: Return ONLY valid JSON matching this schema:
{{
  "reasoning": "Identify the exact error and plan the fix.",
  "files": [
    {{
      "path": "relative/path/to/file.ext",
      "content": "complete fixed code"
    }}
  ]
}}
"""
            prompt = f"{system_instruction}\n\nCodebase:\n{get_project_files()}\n\nVERCEL LOGS:\n{logs}"
            
            print("🧠 Analyzing crash data and writing code patch...")
            raw_response = call_gemini(prompt)
            
            if raw_response:
                try:
                    # Clean up Markdown block formatting if Gemini wraps the JSON
                    clean_json = raw_response.strip()
                    if clean_json.startswith("```json"):
                        clean_json = clean_json[7:-3]
                    elif clean_json.startswith("```"):
                        clean_json = clean_json[3:-3]
                        
                    data = json.loads(clean_json.strip())
                    files_to_update = data.get("files", [])
                    
                    if files_to_update:
                        for item in files_to_update:
                            f_path = item.get("path")
                            f_content = item.get("content")
                            if f_path and f_content:
                                os.makedirs(os.path.dirname(f_path) or ".", exist_ok=True)
                                with open(f_path, "w", encoding="utf-8") as f:
                                    f.write(f_content)
                                print(f"🩹 Patched: {f_path}")
                        
                        subprocess.run(["git", "add", "."])
                        subprocess.run(["git", "commit", "-m", "Auto-heal: Fixing Vercel build crash"])
                        subprocess.run(["git", "push", "origin", branch])
                        print(f"🚀 Pushed patch to '{branch}'.")
                        
                        last_failed_commit = current_commit 
                        print("⏳ Giving Vercel 20 seconds to register the new push...")
                        time.sleep(20)
                    else:
                        print("Agent analyzed but didn't modify any files.")
                        last_failed_commit = current_commit
                except Exception as e:
                    print(f"JSON Parse error during auto-heal: {e}")
                    last_failed_commit = current_commit
            else:
                print("API call failed. Retrying later...")
                time.sleep(15)
                
        elif state == "Ready":
            print("✅ Vercel deployment is stable and live. Sleeping for 30s...")
            time.sleep(30)
            
        else:
            print("❓ Vercel state unknown or no deployments found. Retrying in 30s...")
            time.sleep(30)

if __name__ == "__main__":
    main()
