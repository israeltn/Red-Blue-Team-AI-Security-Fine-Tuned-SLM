# Teacher Model Prompt — Security SLM Dataset Generator

Send this entire prompt to GPT-4o or Claude Opus/Sonnet.
Save the output as `security_dataset.jsonl`.

---

## PROMPT START

Role: Senior AI Security Researcher & Red-Teamer.
Task: Generate 20 high-fidelity training samples for a 1.5B Security SLM targeting the 2026 threat landscape.

Focus Areas:
1. MCP Attacks: Impersonating servers, tool poisoning, over-privileged agent tokens.
2. Prompt Hijacking: "Crescendo" multi-turn attacks and "Payload Splitting" to bypass LlamaGuard/Guardrails.
3. Agent Security: Lateral movement between tools (e.g., agent moving from Search → Email unauthorized).
4. Cloud-Native AI: Exploiting misconfigured S3 buckets, stealing session tokens via LLM SSRF.
5. RAG Poisoning: Injecting adversarial documents that override system prompts.
6. Guardrail Evasion: Encoding tricks (base64, Unicode, homoglyphs) to evade content filters.

CRITICAL FORMAT REQUIREMENT:
Every sample MUST include a <think> block with step-by-step reasoning.
This is non-negotiable — it preserves the model's reasoning capability.

Output each sample as a single line of valid JSON (JSONL format):
{"instruction": "[Security Task Description]", "content": "<think>\n[Step 1: Identify the vulnerability or goal]\n[Step 2: Analyze the target system or guardrail]\n[Step 3: Plan the exploit or defense mechanism]\n[Step 4: Consider edge cases and 2026-era mitigations]\n[Step 5: Verify technical accuracy]\n</think>\n\n[Detailed output: 200+ words, technically precise, with code snippets or config examples where relevant]"}

Quality Requirements:
- Red team samples: Must name specific attack technique, explain the vector, AND include evasion/detection notes
- Blue team samples: Must include concrete implementation (actual code, IAM policies, config snippets)
- Each <think> block: Minimum 5 reasoning steps
- No generic advice — every sample must be something a senior security engineer would find genuinely useful

Cover exactly these 10 pairs (20 samples total):
1. MCP: [RED] Malicious tool description to exfiltrate ENV vars | [BLUE] MCP tool-call validation schema
2. Prompt Hijack: [RED] Payload Splitting across 3 turns to hide destructive command | [BLUE] Semantic drift monitor system prompt
3. Agentic Loops: [RED] Recursive tool-call loop causing resource exhaustion | [BLUE] Token budget + human-in-the-loop trigger
4. Cloud-AI RAG: [RED] PDF injection overwriting system prompt in RAG pipeline | [BLUE] AWS IAM least-privilege for AI agent
5. Crescendo: [RED] 6-turn escalation jailbreak | [BLUE] Cross-turn intent tracking with LlamaGuard
6. Lateral Movement: [RED] Chained tool-call abuse Search→Email | [BLUE] Inter-tool permission boundary
7. SSRF: [RED] LLM URL-fetching tool exploited for AWS metadata endpoint | [BLUE] SSRF-safe HTTP client config
8. Training Poisoning: [RED] Adversarial samples via misconfigured S3 | [BLUE] Training data integrity monitoring
9. Session Theft: [RED] ECS task metadata token theft via LLM | [BLUE] CloudTrail anomaly detection for LLM tool calls
10. Guardrail Bypass: [RED] Base64+Unicode obfuscation to evade LlamaGuard | [BLUE] Pre-guardrail normalization pipeline

## PROMPT END
