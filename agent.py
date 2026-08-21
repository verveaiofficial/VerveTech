import os
import json
import urllib.request
import subprocess
import sys

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
    files_data = {}
    for root, dirs, files in os.walk("."):
        if any(p in root for p in [".git", "__pycache__", "node_modules", ".next", ".vercel", "build", "dist"]):
            continue
        for file in files:
            if file in ["package.json"] or file.endswith((".js", ".ts", ".tsx", ".jsx", ".css", ".html")):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        files_data[filepath] = f.read()
                except Exception:
                    pass
    return files_data

def call_gemini(prompt_text):
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found.")
        return None
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    
    schema = {
        "type": "OBJECT",
        "properties": {
            "reply": {"type": "STRING"},
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
        "required": ["reply", "files"]
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
            return json.loads(result['candidates'][0]['content']['parts'][0]['text'])
    except Exception as e:
        print(f"🤖 API Error ({model_name}): {e}")
        return None

def main():
    branch = get_current_branch()
    print(f"\n⚡ Quix 3 Coder Chat Active (Branch: {branch})")
    print("Type what you want to change or fix. Type 'exit' or 'quit' to leave.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Catch you later!")
            break

        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit"]:
            print("\n👋 Catch you later!")
            break

        print("📂 Scanning project files...")
        files_dict = get_project_files()
        files_context = "\n".join([f"--- FILE: {path} ---\n{content}\n" for path, content in files_dict.items()])

        prompt = f"""
You are Quix 3 Coder, a chill, expert AI coding companion. Chat with the user and fulfill their coding request.
User Message: {user_input}

Repository Files:
{files_context}

Instructions:
1. Provide a friendly text response in 'reply'.
2. If code changes are needed, include them in 'files'. If no files need changing, leave 'files' empty.
3. DO NOT modify agent.py or vercel.json.
"""

        print("🧠 Quix 3 Coder is thinking...")
        response_data = call_gemini(prompt)

        if not response_data:
            print("❌ Failed to get a response.\n")
            continue

        print(f"\nQuix: {response_data.get('reply')}\n")

        files_to_update = response_data.get("files", [])
        if files_to_update:
            updated_count = 0
            for item in files_to_update:
                f_path = item.get("path")
                f_content = item.get("content")
                if f_path and f_content and "agent.py" not in f_path:
                    os.makedirs(os.path.dirname(f_path) or ".", exist_ok=True)
                    with open(f_path, "w", encoding="utf-8") as f:
                        f.write(f_content)
                    print(f"✏️ Updated: {f_path}")
                    updated_count += 1
            
            if updated_count > 0:
                print("\n🚀 Committing and pushing changes to GitHub...")
                subprocess.run(["git", "add", "."])
                subprocess.run(["git", "commit", "-m", f"Quix chat update: {user_input[:30]}"])
                subprocess.run(["git", "push", "origin", branch])
                print("✅ Pushed successfully!\n")
        else:
            print()

if __name__ == "__main__":
    main()
