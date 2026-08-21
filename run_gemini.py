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
            # Skip config files to protect build parameters
            if file in ["vercel.json", "package.json", "next.config.js", "tailwind.config.js", "postcss.config.js"]:
                continue
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
        res = subprocess.run(["npx", "--yes", "vercel", "logs", "--limit", "250"], capture_output=True, text=True)
        return res.stdout + "\n" + res.stderr
    except Exception:
        return ""

def main():
    if not api_key:
        print("Missing GEMINI_API_KEY in .env!")
        return
        
    branch = get_current_branch()
    print(f"\n👁️ Autonomous Code Watchdog Active.")
    print(f"Branch: {branch} | Model: {model_name}")
    print("Config protection enabled (ignoring vercel.json/package.json modifications).\n")
    
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
                print("⚠️ Same commit failed again. Waiting 45s to avoid tight loops...")
                time.sleep(45)
                continue
                
            print("\n💥 BUILD ERROR CAUGHT! Extracting real error logs...")
            logs = get_latest_logs()
            
            system_instruction = f"""
You are an autonomous engineering agent. The live Vercel build failed due to code, syntax, or type errors.
Analyze the error logs and source files below to fix the bug. 
DO NOT touch configuration files like vercel.json or package.json. Fix the actual code components or pages.

Return ONLY valid JSON matching this schema:
{{
  "reasoning": "Identify exact error line and fix.",
  "files": [
    {{
      "path": "relative/path/to/file.tsx",
      "content": "complete fixed code"
    }}
  ]
}}
"""
            prompt = f"{system_instruction}\n\nSource Code:\n{get_project_files()}\n\nVERCEL ERROR LOGS:\n{logs}"
            
            print("🧠 Rewriting code to fix bug...")
            raw_response = call_gemini(prompt)
            
            if raw_response:
                try:
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
                            # Strict safety check against config files
                            if f_path and f_content and not any(c in f_path for c in ["vercel.json", "package.json"]):
                                os.makedirs(os.path.dirname(f_path) or ".", exist_ok=True)
                                with open(f_path, "w", encoding="utf-8") as f:
                                    f.write(f_content)
                                print(f"🩹 Patched Source File: {f_path}")
                        
                        subprocess.run(["git", "add", "."])
                        subprocess.run(["git", "commit", "-m", "Auto-heal: Fix source code compilation error"])
                        subprocess.run(["git", "push", "origin", branch])
                        print(f"🚀 Pushed fix to '{branch}'.")
                        
                        last_failed_commit = current_commit 
                        time.sleep(25)
                    else:
                        print("Agent found no source files to change.")
                        last_failed_commit = current_commit
                except Exception as e:
                    print(f"Parse error: {e}")
                    last_failed_commit = current_commit
            else:
                time.sleep(15)
                
        elif state == "Ready":
            print("✅ Vercel deployment is Green & Live. Watching...")
            time.sleep(30)
            
        else:
            time.sleep(20)

if __name__ == "__main__":
    main()
