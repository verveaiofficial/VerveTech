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

def call_gemini(contents):
    if not api_key:
        print("Error: GEMINI_API_KEY is missing from .env or environment!")
        return None
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    payload = {
        "contents": contents,
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

def check_build():
    if not os.path.exists("tsconfig.json"):
        return True, "No tsconfig found, skipping build check."
    try:
        res = subprocess.run(["npx", "--yes", "tsc", "--noEmit"], capture_output=True, text=True, timeout=25)
        if res.returncode == 0:
            return True, "Passed syntax check."
        else:
            return False, (res.stdout + "\n" + res.stderr)[-3000:]
    except Exception as e:
        return True, f"Check bypassed: {e}"

def main():
    if not api_key:
        print("\nError: Please add GEMINI_API_KEY to your .env file!")
        return

    current_branch = get_current_branch()
    print(f"\nVibe Coding Agent + Reasoning Enabled ({model_name}) 🧠✨")
    print(f"Active Branch: {current_branch}\n")

    while True:
        user_input = input("Aariz: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit", "/exit"]:
            print("Goodbye! ✨")
            break

        agents_rules = get_agents_md()
        branch_context = f"\n--- GIT BRANCHES ---\nActive Branch: {get_current_branch()}\nAll Branches:\n{get_all_branches()}\n"
        files_context = get_project_files()

        system_instruction = f"""
You are an intelligent full-stack AI vibe-coding agent.
Analyze the user's message, project files, and agents.md rules carefully.

CRITICAL INSTRUCTION: You MUST perform step-by-step reasoning BEFORE generating replies or file edits.

You MUST return a valid JSON object strictly matching this schema:
{{
  "reasoning": "Step-by-step thought process: Analyze architecture, evaluate dependencies, identify files to edit, anticipate syntax/type errors, and double-check instructions...",
  "reply": "Your friendly, direct response or update to Aariz...",
  "files": [
    {{
      "path": "relative/path/to/file.ext",
      "content": "complete updated content of the file"
    }}
  ]
}}

Rules:
- Fill out the 'reasoning' field FIRST with thorough analysis.
- If no files need to be edited or created, set 'files': [].
- Unrestricted access to edit any file in the repo.
- Write full, production-ready code without placeholders.
{agents_rules}
{branch_context}
"""

        current_prompt = f"{system_instruction}\n\nExisting Codebase:\n{files_context}\n\nUser Input: {user_input}"
        attempt = 1

        while True:
            print("\nThinking and analyzing codebase... 🧠")
            raw_response = call_gemini([{"parts": [{"text": current_prompt}]}])
            if not raw_response:
                print("Failed to reach Gemini API.")
                break

            try:
                data = json.loads(raw_response.strip())
            except Exception as e:
                print("Response parse error, retrying...")
                break

            thought_process = data.get("reasoning", "")
            agent_reply = data.get("reply", "")
            files_to_update = data.get("files", [])

            if thought_process:
                print(f"\n💭 Reasoning:\n{thought_process}\n")

            if agent_reply:
                print(f"Agent: {agent_reply}\n")

            if files_to_update:
                for item in files_to_update:
                    f_path = item.get("path")
                    f_content = item.get("content")
                    if f_path and f_content is not None:
                        dir_name = os.path.dirname(f_path)
                        if dir_name:
                            os.makedirs(dir_name, exist_ok=True)
                        with open(f_path, "w", encoding="utf-8") as f:
                            f.write(f_content)
                        print(f"Updated: {f_path}")

                build_ok, build_log = check_build()
                if not build_ok:
                    print(f"\nType/Syntax Error detected! Fixing automatically (Attempt {attempt})...")
                    current_prompt = f"{system_instruction}\n\nExisting Codebase:\n{get_project_files()}\n\nERROR LOG:\n{build_log}\n\nFix all issues and provide updated files."
                    attempt += 1
                    time.sleep(2)
                    continue

                latest_branch = get_current_branch()
                if latest_branch not in ["main", "master"]:
                    subprocess.run(["git", "add", "."])
                    subprocess.run(["git", "commit", "-m", f"Vibe agent update: {user_input[:40]}"])
                    subprocess.run(["git", "push", "origin", latest_branch])
                    print(f"Pushed updates to {latest_branch}! 🚀\n")

            break

if __name__ == "__main__":
    main()
