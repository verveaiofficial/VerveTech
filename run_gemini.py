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
        print("API Error:", e)
        return None

def check_vercel_build():
    print("⏳ Waiting for Vercel to process the build (45s)...")
    time.sleep(45)
    print("📡 Pulling live Vercel logs...")
    try:
        res = subprocess.run(["npx", "--yes", "vercel", "logs", "--limit", "50"], capture_output=True, text=True, timeout=20)
        logs = res.stdout + "\n" + res.stderr
        
        error_keywords = ["Failed to compile", "Type error", "SyntaxError", "Build error", "Command failed"]
        if any(keyword in logs for keyword in error_keywords):
            print("❌ Vercel build failed! Initiating auto-heal sequence...")
            return False, logs[-3000:]
        
        print("✅ Vercel deployment looks stable.")
        return True, ""
    except Exception as e:
        print(f"⚠️ Could not pull logs: {e}")
        return True, ""

def auto_heal_loop():
    branch = get_current_branch()
    attempt = 1
    max_attempts = 3
    
    while attempt <= max_attempts:
        is_stable, error_logs = check_vercel_build()
        if is_stable:
            print("🚀 Autonomous deployment successful!")
            break
            
        print(f"🛠️ Auto-Heal Attempt {attempt}/{max_attempts}...")
        
        system_instruction = f"""
You are an autonomous CI/CD agent. The recent Vercel build FAILED.
Analyze the Vercel error logs below and fix the codebase to resolve the build failure.
CRITICAL: You MUST return updated file contents in the 'files' array to patch the errors.

Schema:
{{
  "reasoning": "Identify the exact error from the logs and how to fix it...",
  "reply": "Brief explanation of the automated fix...",
  "files": [
    {{
      "path": "relative/path/to/file.ext",
      "content": "complete fixed code"
    }}
  ]
}}
"""
        prompt = f"{system_instruction}\n\nCodebase:\n{get_project_files()}\n\nVERCEL ERROR LOGS:\n{error_logs}"
        
        raw_response = call_gemini(prompt)
        if not raw_response:
            print("Communication error during auto-heal.")
            break
            
        try:
            data = json.loads(raw_response.strip())
            files_to_update = data.get("files", [])
            
            if not files_to_update:
                print("Agent failed to provide a code fix.")
                break
                
            print(f"🤖 Auto-fix generated: {data.get('reply', 'Patching files...')}")
            
            for item in files_to_update:
                f_path = item.get("path")
                f_content = item.get("content")
                if f_path and f_content is not None:
                    os.makedirs(os.path.dirname(f_path) or ".", exist_ok=True)
                    with open(f_path, "w", encoding="utf-8") as f:
                        f.write(f_content)
                    print(f"Patched: {f_path}")
            
            subprocess.run(["git", "add", "."])
            subprocess.run(["git", "commit", "-m", f"Auto-heal: Vercel build fix attempt {attempt}"])
            subprocess.run(["git", "push", "origin", branch])
            print(f"🔄 Pushed auto-fix to '{branch}'. Restarting monitor loop...")
            attempt += 1
            
        except Exception as e:
            print(f"Auto-heal parse error: {e}")
            break

def main():
    if not api_key:
        print("\nError: Missing GEMINI_API_KEY in .env!")
        return

    print(f"\n⚡ Autonomous Watchdog Active ({model_name})")
    print(f"Active Branch: {get_current_branch()}\n")

    while True:
        user_input = input("Aariz: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit", "/exit"]:
            print("Catch you later. ✨")
            break

        system_instruction = f"""
You are an expert full-stack AI vibe-coding agent.
Whenever Aariz asks for a feature or edit, WRITE AND RETURN THE FULL UPDATED CODE FILES.
Schema:
{{
  "reasoning": "Plan...",
  "reply": "Message...",
  "files": [{{"path": "file.ext", "content": "code"}}]
}}
"""
        prompt = f"{system_instruction}\n\nCodebase:\n{get_project_files()}\n\nUser Command: {user_input}"
        
        print("\nProcessing your command... 🧠⚡")
        raw_response = call_gemini(prompt)
        if not raw_response:
            continue
            
        try:
            data = json.loads(raw_response.strip())
            files_to_update = data.get("files", [])
            
            print(f"Agent: {data.get('reply', 'Done.')}\n")
            
            if files_to_update:
                for item in files_to_update:
                    f_path = item.get("path")
                    f_content = item.get("content")
                    if f_path and f_content:
                        os.makedirs(os.path.dirname(f_path) or ".", exist_ok=True)
                        with open(f_path, "w", encoding="utf-8") as f:
                            f.write(f_content)
                
                branch = get_current_branch()
                subprocess.run(["git", "add", "."])
                subprocess.run(["git", "commit", "-m", f"Update: {user_input[:30]}"])
                subprocess.run(["git", "push", "origin", branch])
                print(f"🚀 Pushed to '{branch}'.")
                
                # Activate the autonomous watchdog
                auto_heal_loop()
                
            else:
                print("⚠️ No files modified.")
                
        except Exception as e:
            print("Error processing response.")

if __name__ == "__main__":
    main()
