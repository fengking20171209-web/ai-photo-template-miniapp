import os
import json
import urllib.request
import urllib.error
import time
from datetime import datetime

env_file = r"D:\Projects\ai-photo-template-miniapp\.env.openai"
debt_dir = r"D:\Projects\ai-photo-template-miniapp\docs\review-debt"

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

def call_api(env, prompt_msg, system_msg, max_tokens=700):
    api_key = env.get("OPENAI_API_KEY", "").strip().replace(" ", "")
    base_url = env.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip('/')
    model_name = env.get("MODEL_NAME", "gpt-4o")
    
    url = f"{base_url}/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    
    payload = {
        "model": model_name,
        "response_format": {"type": "json_object"},
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt_msg}
        ]
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return json.loads(result['choices'][0]['message']['content']), None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            err_json = json.loads(error_body)
            err_code = err_json.get("error", {}).get("code")
            err_type = err_json.get("error", {}).get("type")
        except:
            err_code, err_type = "unknown", "unknown"
            
        if e.code == 429 and err_code == "rate_limit_exceeded" and err_type == "tokens":
            return {"verdict": "BLOCKED_RATE_LIMIT", "risk_level": "yellow", "summary": "TPM Limit"}, 429
        return {"verdict": "FAIL", "summary": f"HTTP {e.code}"}, e.code

def run_preflight(env):
    print("Running Preflight Check...")
    sys_msg = "You are a health checker. Respond ONLY with valid JSON: {'verdict': 'PASS'}"
    res, err = call_api(env, "Preflight check.", sys_msg, 100)
    if err == 429:
        print(f"PREFLIGHT FAILED: BLOCKED_BY_UPSTREAM_RATE_LIMIT (Raw: {res})")
        return False
    elif err is not None:
        print(f"PREFLIGHT FAILED: HTTP {err} (Raw: {res})")
        return False
    print("PREFLIGHT PASSED.")
    return True

def main():
    env = load_env()
    if not run_preflight(env):
        print("\nREVIEW_DEBT_CLEARANCE_BLOCKED_BY_TPM")
        return

    packages = [
        "task1-sqlite-wal-review.md",
        "task2-schema-review.md",
        "phase2a-business-loop-review.md",
        "phase3a-asset-persistence-review.md",
        "phase2a5-architecture-freeze-review.md"  # Fallback if doesn't exist
    ]
    
    sys_prompt = """You are 'codex gpt-5.4-mini', a Senior Code Reviewer. 
Review the package and answer: 
1. Any blocking issues? 
2. Data corruption risks? 
3. Breaks SQLite WAL/busy_timeout? 
4. Breaks API/migration compatibility? 
5. Security risks?
6. Safe to proceed to next stage?

Output MUST be JSON:
{
  "verdict": "PASS" | "FAIL" | "NEEDS_HUMAN" | "BLOCKED_RATE_LIMIT",
  "risk_level": "green" | "yellow" | "red",
  "blocking_issues": [],
  "non_blocking_issues": [],
  "required_fixes": [],
  "summary": "",
  "next_stage_allowed": true
}"""

    report_lines = [f"# Review Debt Clearance R1\nDate: {datetime.now().isoformat()}\n\n## Results\n"]
    debt_count = 5
    results = {}
    
    for pkg in packages:
        path = os.path.join(debt_dir, pkg)
        if not os.path.exists(path):
            continue
            
        print(f"\nReviewing {pkg}...")
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        res, err = call_api(env, f"Review this debt package:\n\n{content}", sys_prompt)
        
        results[pkg] = res
        report_lines.append(f"### {pkg}")
        report_lines.append(f"- **Verdict:** {res.get('verdict')}")
        report_lines.append(f"- **Risk Level:** {res.get('risk_level')}")
        report_lines.append(f"- **Summary:** {res.get('summary')}\n")
        
        if res.get("verdict") == "PASS":
            debt_count -= 1
        elif res.get("verdict") == "BLOCKED_RATE_LIMIT" or err == 429:
            print(f"RATE LIMIT HIT on {pkg}. Circuit breaker triggered.")
            report_lines.append("\n**CIRCUIT BREAKER TRIGGERED: TPM LIMIT EXCEEDED.**")
            break
        elif res.get("verdict") in ["FAIL", "NEEDS_HUMAN"]:
            print(f"STOPPING due to {res.get('verdict')} on {pkg}.")
            report_lines.append(f"\n**CLEARANCE HALTED DUE TO {res.get('verdict')}.**")
            break
            
        time.sleep(1) # Small cooldown between successful calls
        
    # Write R1 report
    with open(os.path.join(debt_dir, "review-debt-clearance-r1.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        f.write(f"\n\n**Remaining Debt Count:** {debt_count}\n")
        
    print(f"\nClearance Process Finished. Remaining Debt: {debt_count}")
    
if __name__ == "__main__":
    main()
