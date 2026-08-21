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
        print(f"🤖 API Error ({model_name}): {e}")
        return None

def main():
    user_task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Review the project, optimize code, and ensure everything is clean and working."
    branch = get_current_branch()
    
    print(f"\n🧠 Verve AI Agent Active")
    print(f"Branch: {branch} | Task: {user_task}\n")
    
    print("📂 Gathering project context...")
    files_dict = get_project_files()
    files_context = "\n".join([f"--- FILE: {path} ---\n{content}\n" for path, content in files_dict.items()])

    prompt = f"""
User Goal / Task: {user_task}

Repository Files:
{files_context}

Instructions:
1. Fulfill the user's task by updating or creating the necessary code files.
2. Return a valid JSON response containing your reasoning and the modified files.
3. DO NOT modify agent.py or vercel.json.
"""

    print("🤖 Agent thinking and generating solution...")
    raw_response = call_gemini(prompt)
    
    if not raw_response:
        print("❌ Agent failed to receive a response from Gemini.")
        return

    try:
        data = json.loads(raw_response)
        print(f"\n💡 Agent Reasoning: {data.get('reasoning')}\n")
        
        updated_count = 0
        for item in data.get("files", []):
            f_path = item.get("path")
            f_content = item.get("content")
            if f_path and f_content and "agent.py" not in f_path:
                os.makedirs(os.path.dirname(f_path) or ".", exist_ok=True)
                with open(f_path, "w", encoding="utf-8") as f:
                    f.write(f_content)
                print(f"✏️ Updated: {f_path}")
                updated_count += 1
                
        if updated_count > 0:
            print("\n🚀 Pushing changes to GitHub...")
            subprocess.run(["git", "add", "."])
            subprocess.run(["git", "commit", "-m", f"Agent update: {user_task[:40]}"])
            subprocess.run(["git", "push", "origin", branch])
            print("✅ Agent task completed, committed, and pushed successfully!")
        else:
            print("⚠️ No files were modified by the agent.")
            
    except Exception as e:
        print(f"❌ Error processing agent response: {e}")

if __name__ == "__main__":
    main()
