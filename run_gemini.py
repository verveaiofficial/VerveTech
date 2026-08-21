import os
import json
import urllib.request
import subprocess
import base64
import mimetypes
import re

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

def extract_image_parts(user_input):
    image_parts = []
    potential_paths = re.findall(r'[\w\/\.\-]+\.(?:png|jpg|jpeg|webp)', user_input, re.IGNORECASE)
    if "screenshot" in user_input.lower():
        for f in os.listdir("."):
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) and f not in potential_paths:
                potential_paths.append(f)

    for path in set(potential_paths):
        clean_path = path.strip()
        if os.path.exists(clean_path):
            mime_type, _ = mimetypes.guess_type(clean_path)
            if not mime_type:
                mime_type = "image/jpeg"
            try:
                with open(clean_path, "rb") as img_file:
                    encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                    image_parts.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": encoded_string
                        }
                    })
                print(f"📸 Attached screenshot: {clean_path}")
            except Exception as e:
                print(f"Could not load image {clean_path}: {e}")
    return image_parts

def call_gemini(parts):
    if not api_key:
        print("Error: GEMINI_API_KEY is missing from .env!")
        return None
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    payload = {
        "contents": [{"parts": parts}],
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

def main():
    if not api_key:
        print("\nError: Missing GEMINI_API_KEY in .env!")
        return

    current_branch = get_current_branch()
    print(f"\nVibe Coding Agent Ready! ({model_name}) 🧠📸✨")
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
You are an intelligent full-stack AI vibe-coding agent with Vision analysis capabilities.
Analyze the user's message, attached screenshot images (if provided), project files, and agents.md rules carefully.

CRITICAL RULES:
1. You MUST perform step-by-step reasoning BEFORE generating replies or file edits.
2. Whenever code/styling changes are requested, return full updated file contents inside 'files'.
3. Always write valid React/Next.js code that builds cleanly on Vercel.

You MUST return a valid JSON object matching this schema:
{{
  "reasoning": "Step-by-step thought process...",
  "reply": "Your direct message to Aariz...",
  "files": [
    {{
      "path": "relative/path/to/file.ext",
      "content": "complete updated file content"
    }}
  ]
}}
{agents_rules}
{branch_context}
"""

        prompt_text = f"{system_instruction}\n\nExisting Codebase:\n{files_context}\n\nUser Input: {user_input}"
        parts = [{"text": prompt_text}]
        parts.extend(extract_image_parts(user_input))

        print("\nThinking and analyzing code... 🧠")
        raw_response = call_gemini(parts)
        if not raw_response:
            print("Failed to reach Gemini API.")
            continue

        try:
            data = json.loads(raw_response.strip())
        except Exception as e:
            print("Response parse error, retrying...")
            continue

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
                    print(f"Updated local file: {f_path}")

            latest_branch = get_current_branch()
            subprocess.run(["git", "add", "."])
            subprocess.run(["git", "commit", "-m", f"Vibe update: {user_input[:40]}"])
            push_res = subprocess.run(["git", "push", "origin", latest_branch], capture_output=True, text=True)
            
            if push_res.returncode == 0:
                print(f"🚀 Pushed live to GitHub branch '{latest_branch}'!\n")
            else:
                print(f"Git Push Output: {push_res.stdout} {push_res.stderr}\n")
        else:
            print("⚠️ No files modified in this turn.\n")

if __name__ == "__main__":
    main()
