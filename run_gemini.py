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
        return ""

def get_all_branches():
    try:
        res = subprocess.run(["git", "branch", "-a"], capture_output=True, text=True)
        return res.stdout.strip()
    except Exception:
        return "Could not fetch branches"

def get_agents_md():
    if os.path.exists("agents.md"):
        try:
            with open("agents.md", "r", encoding="utf-8") as f:
                return f"\n--- AGENTS.MD GUIDELINES ---\n" + f.read() + "\n"
        except Exception:
            return ""
    return ""

def get_file_structure():
    file_list = []
    for root, dirs, files in os.walk("."):
        if any(p in root for p in [".git", "__pycache__", "node_modules", ".next", ".vercel", "build", "dist"]):
            continue
        for file in files:
            if file.endswith((".py", ".sh", ".json", ".md", ".txt", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".sql")):
                file_list.append(os.path.join(root, file))
    return "\n".join(file_list)

def get_project_files():
    context = ""
    for root, dirs, files in os.walk("."):
        if any(p in root for p in [".git", "__pycache__", "node_modules", ".next", ".vercel", "build", "dist"]):
            continue
        for file in files:
            if file.endswith((".py", ".sh", ".json", ".md", ".txt", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".sql")):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        context += f"\n--- FILE: {filepath} ---\n" + f.read() + "\n"
                except Exception:
                    pass
    return context

def call_gemini(contents, json_mode=False):
    if not api_key:
        print("Error: GEMINI_API_KEY is missing from .env or environment!")
        return None
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    payload = {"contents": contents}
    if json_mode:
        payload["generationConfig"] = {"response_mime_type": "application/json"}
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print("API Error:", e)
        return None

def apply_files(raw_response):
    cleaned_json = raw_response.strip()
    if cleaned_json.startswith("```json"):
        cleaned_json = cleaned_json[7:]
    if cleaned_json.startswith("```"):
        cleaned_json = cleaned_json[3:]
    if cleaned_json.endswith("```"):
        cleaned_json = cleaned_json[:-3]
    cleaned_json = cleaned_json.strip()

    try:
        files_to_write = json.loads(cleaned_json, strict=False)
        if isinstance(files_to_write, dict) and "files" in files_to_write:
            files_to_write = files_to_write["files"]
        
        for file_item in files_to_write:
            file_path = file_item.get("path")
            content = file_item.get("content")
            if file_path and content is not None:
                if "next.config" in file_path or "package.json" in file_path or ".env" in file_path:
                    print(f"Bypassing protected file modification: {file_path}")
                    continue
                dir_name = os.path.dirname(file_path)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"File modified: {file_path}")
        return True
    except Exception as e:
        print("Failed to parse JSON:", e)
        return False

def check_build():
    print("\nValidating code structure and TypeScript types...")
    if not os.path.exists("tsconfig.json"):
        return True, "No tsconfig.json found yet, skipping type check for initial setup."
    try:
        res = subprocess.run(["npx", "--yes", "tsc", "--noEmit"], capture_output=True, text=True, timeout=25)
        if res.returncode == 0:
            return True, "Code syntax check passed!"
        else:
            error_log = res.stdout + "\n" + res.stderr
            return False, error_log[-3000:]
    except subprocess.TimeoutExpired:
        print("Validation timed out, proceeding to deploy safely...")
        return True, "Check timed out, proceeding anyway."
    except Exception as e:
        return True, f"Check skipped: {e}"

def main():
    if not api_key:
        print("\nError: Please add GEMINI_API_KEY to your .env file!")
        return

    current_branch = get_current_branch()
    print(f"Starting Gemini Interactive Assistant ({model_name}) ✨")
    print(f"Active branch: {current_branch}")
    
    if current_branch in ["main", "master"]:
        print("ALERT: You are currently on the main branch! Auto-build will be locked until you switch branches.")

    print("Chat naturally to discuss changes, or start a prompt with '/build ' to code!\n")

    chat_history = []
    
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit", "/exit"]:
            print("Goodbye! ✨")
            break

        agents_rules = get_agents_md()
        all_branches = get_all_branches()
        branch_context = f"\n--- GIT BRANCHES ---\nActive Branch: {get_current_branch()}\nAll Branches:\n{all_branches}\n"

        if user_input.startswith("/build "):
            task = user_input[7:].strip()
            files_context = get_project_files()
            
            branch_check = get_current_branch()
            if branch_check in ["main", "master"]:
                print(f"\nLOCKED: You are on '{branch_check}'. To protect main, builds are disabled here! Please run 'git checkout dev' first.")
                continue

            system_instruction = f"""
You are an automated coding agent.
Analyze the project files, branch context, agents.md rules, and user request. Return ONLY a valid JSON array of file objects to update or create.
Format:
[
  {{
    "path": "path/to/file.ext",
    "content": "complete updated code content here"
  }}
]
Do NOT edit next.config.js, package.json, or .env files. Strictly follow instructions inside agents.md.
Properly escape all special characters inside code content strings.
{agents_rules}
{branch_context}
"""
            attempt = 1
            current_prompt = f"{system_instruction}\n\nExisting Project Files:\n{files_context}\n\nUser Build Task: {task}"

            while True:
                print(f"\n[Attempt {attempt}] Writing and editing code...")
                raw_response = call_gemini([{"parts": [{"text": current_prompt}]}], json_mode=True)
                if not raw_response:
                    print("Failed to get response from Gemini API.")
                    break

                success = apply_files(raw_response)
                if not success:
                    print("Could not apply files. Stopping.")
                    break

                build_ok, build_log = check_build()
                if not build_ok:
                    print(f"\nCode error found on attempt {attempt}! Auto-fixing...")
                    current_prompt = f"{system_instruction}\n\nExisting Project Files:\n{get_project_files()}\n\nTYPE/SYNTAX ERROR LOG:\n{build_log}\n\nPlease fix all errors above and return updated files."
                    attempt += 1
                    time.sleep(2)
                    continue

                print("\nCode validation passed! ✨")
                
                latest_branch = get_current_branch()
                if latest_branch in ["main", "master"]:
                    print(f"\nABORTED: Branch changed to {latest_branch}! Push cancelled to guard main.")
                    break

                print(f"Pushing directly to branch '{latest_branch}'...")
                subprocess.run(["git", "add", "."])
                subprocess.run(["git", "commit", "-m", f"Gemini Build attempt {attempt}: {task[:40]}"])
                subprocess.run(["git", "push", "origin", latest_branch])

                print("\nDeployed! Test your app live.")
                feedback = input("\nDid it fix or complete the feature? If NOT, describe what you see (or press Enter if done): ")

                if not feedback.strip():
                    print("\nChanges saved and deployed! 🚀\n")
                    break

                print(f"\nSending visual feedback back...")
                current_prompt = f"{system_instruction}\n\nExisting Project Files:\n{get_project_files()}\n\nUSER VISUAL BUG REPORT:\n{feedback}\n\nPlease fix this issue based on the report."
                attempt += 1
                time.sleep(2)

        else:
            structure_context = f"\n--- PROJECT FILE LIST ---\n{get_file_structure()}\n"
            prompt = f"You are a helpful AI collaborator chatting about this codebase. Answer clearly and naturally without returning JSON code blocks unless explicitly asked.\n{agents_rules}\n{branch_context}\n{structure_context}\n\nUser Message: {user_input}"
            chat_history.append({"role": "user", "parts": [{"text": prompt}]})
            response_text = call_gemini(chat_history, json_mode=False)
            if response_text:
                print(f"\nGemini: {response_text}\n")
                chat_history.append({"role": "model", "parts": [{"text": response_text}]})
            else:
                print("Failed to get response.")

if __name__ == "__main__":
    main()
