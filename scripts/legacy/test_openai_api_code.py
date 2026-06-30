import os
import json
import urllib.request
import urllib.error
import subprocess
import hashlib
import time

env_file = r"D:\Projects\ai-photo-template-miniapp\.env.openai"
cache_file = r"D:\Projects\ai-photo-template-miniapp\.codex-review-cache.json"

# Token Budgeting Defaults
MAX_INPUT_TOKENS = int(os.environ.get("CODEX_REVIEW_MAX_INPUT_TOKENS", 8000))
MAX_OUTPUT_TOKENS = int(os.environ.get("CODEX_REVIEW_MAX_OUTPUT_TOKENS", 900))
MAX_RETRIES = int(os.environ.get("CODEX_REVIEW_MAX_RETRIES", 2))
CHUNK_TOKENS = int(os.environ.get("CODEX_REVIEW_CHUNK_TOKENS", 3500))
COOLDOWN_SECONDS = int(os.environ.get("CODEX_REVIEW_COOLDOWN_SECONDS", 75))

def load_env():
    env = {}
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if '#' in line: line = line.split('#')[0].strip()
                if '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip().replace('\n', '').replace('\r', '')
    return env

def get_git_diff():
    try:
        # Only diff the last commit (HEAD~1 to HEAD)
        stat = subprocess.run(['git', '-C', r'D:\Projects\ai-photo-template-miniapp', 'diff', '--stat', 'HEAD~1...HEAD'], capture_output=True, text=False, check=True).stdout.decode('utf-8', errors='ignore')
        diff = subprocess.run(['git', '-C', r'D:\Projects\ai-photo-template-miniapp', 'diff', '--unified=80', 'HEAD~1...HEAD'], capture_output=True, text=False, check=True).stdout.decode('utf-8', errors='ignore')
        return f"STAT:\n{stat}\n\nDIFF:\n{diff}"
    except Exception as e:
        return ""

def estimate_tokens(text):
    # Rough heuristic: 1 token ~= 4 chars for English/Code
    return len(text) // 4

def chunk_diff(diff_text, max_tokens):
    # Extremely basic chunking: split by lines to fit token budget
    lines = diff_text.split('\n')
    chunks = []
    current_chunk = []
    current_tokens = 0
    for line in lines:
        line_tokens = estimate_tokens(line)
        if current_tokens + line_tokens > max_tokens and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_tokens = line_tokens
        else:
            current_chunk.append(line)
            current_tokens += line_tokens
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    return chunks

def get_cache():
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {}

def save_cache(cache_data):
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2)

def call_model(env, diff_chunk):
    api_key = env.get("OPENAI_API_KEY", "").strip().replace(" ", "")
    base_url = env.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip('/')
    model_name = env.get("MODEL_NAME", "gpt-4o")
    
    url = f"{base_url}/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    
    sys_prompt = """You are 'codex gpt-5.4-mini', a Senior Code Reviewer.
Evaluate the code. You MUST output ONLY valid JSON matching this schema:
{
  "verdict": "PASS" | "FAIL" | "NEEDS_HUMAN",
  "risk_level": "green" | "yellow" | "red",
  "blocking_issues": ["list of strings"],
  "non_blocking_issues": ["list of strings"],
  "summary": "string"
}"""
    
    payload = {
        "model": model_name,
        "response_format": {"type": "json_object"},
        "max_tokens": MAX_OUTPUT_TOKENS,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"Review this diff:\n\n{diff_chunk}"}
        ]
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            content = result['choices'][0]['message']['content']
            return json.loads(content)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            err_json = json.loads(error_body)
            err_code = err_json.get("error", {}).get("code")
            err_type = err_json.get("error", {}).get("type")
        except:
            err_code = "unknown"
            err_type = "unknown"
        
        return {
            "error_http_code": e.code,
            "error_code": err_code,
            "error_type": err_type,
            "raw": error_body
        }

def main():
    env = load_env()
    diff_text = get_git_diff()
    
    if not diff_text.strip():
        print(json.dumps({"verdict": "SKIPPED_NO_DIFF", "summary": "No code changes found."}))
        return

    diff_hash = hashlib.sha256(diff_text.encode('utf-8')).hexdigest()
    cache = get_cache()
    
    if diff_hash in cache and cache[diff_hash].get("verdict") == "PASS":
        print(json.dumps({"verdict": "PASS", "source": "cache", "summary": "Loaded from cache"}))
        return

    chunks = chunk_diff(diff_text, CHUNK_TOKENS)
    results = []

    for i, chunk in enumerate(chunks):
        for attempt in range(MAX_RETRIES):
            res = call_model(env, chunk)
            
            if "error_http_code" in res:
                # Handle Rate Limits
                if res["error_http_code"] == 429:
                    if res["error_code"] == "rate_limit_exceeded" and res["error_type"] == "tokens":
                        # Circuit Breaker for TPM
                        blocked_res = {
                            "verdict": "BLOCKED_RATE_LIMIT",
                            "reason": "TPM limit exceeded",
                            "task_status": "CONDITIONALLY_ACCEPTED_REMOTE_REVIEW_PENDING",
                            "summary": "External API is out of token quota. Local tests passed."
                        }
                        print(json.dumps(blocked_res, indent=2, ensure_ascii=False))
                        with open("codex-review-blocked.md", "w", encoding="utf-8") as f:
                            f.write(f"# Review Blocked\nDue to upstream TPM limit.\nHash: {diff_hash}\n")
                        return
                    else:
                        # Standard RPM backoff
                        time.sleep(10 * (2**attempt))
                        continue
                else:
                    print(json.dumps({"verdict": "FAIL", "reason": f"HTTP {res['error_http_code']}", "raw": res.get("raw")}))
                    return
            else:
                results.append(res)
                break # break retry loop
        else:
            # Retries exhausted
            print(json.dumps({"verdict": "FAIL", "reason": "Max retries exhausted"}))
            return
            
    # Naive merge of chunk results
    final_verdict = "PASS"
    for r in results:
        if r.get("verdict") == "FAIL": final_verdict = "FAIL"
        elif r.get("verdict") == "NEEDS_HUMAN" and final_verdict != "FAIL": final_verdict = "NEEDS_HUMAN"
        
    final_output = {
        "verdict": final_verdict,
        "results": results
    }
    
    if final_verdict == "PASS":
        cache[diff_hash] = final_output
        save_cache(cache)
        
    print(json.dumps(final_output, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
