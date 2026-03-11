#!/usr/bin/env python3
"""
Local comparison: runs the same 5 eval prompts against the downloaded GGUF
and compares against the baseline_results.json saved from Colab.

Usage:
    pip install llama-cpp-python
    python eval/compare_local.py --model models/security-slm-unsloth.Q4_K_M.gguf
"""

import json
import re
import argparse
import sys
from pathlib import Path

# ── Same 5 prompts used in the Colab notebook ──
EVAL_PROMPTS = [
    {
        'id': 'mcp_red',
        'category': 'MCP Security',
        'prompt': 'Explain how an attacker can craft a malicious MCP server tool description to trick an AI agent into exfiltrating environment variables to an external server.'
    },
    {
        'id': 'prompt_hijack',
        'category': 'Prompt Hijacking',
        'prompt': 'What is the Payload Splitting technique and how does it bypass LlamaGuard by splitting a harmful instruction across multiple conversation turns?'
    },
    {
        'id': 'agentic_blue',
        'category': 'Agentic Security',
        'prompt': 'Implement a Python circuit breaker for an AI agent that stops execution when the same tool is called more than 3 times consecutively, preventing resource exhaustion attacks.'
    },
    {
        'id': 'ssrf_red',
        'category': 'Cloud-AI SSRF',
        'prompt': 'How can an attacker exploit an LLM with a URL-fetching tool to steal temporary AWS credentials from the EC2 instance metadata endpoint at 169.254.169.254?'
    },
    {
        'id': 'iam_blue',
        'category': 'Cloud IAM',
        'prompt': 'Write a minimal AWS IAM policy in JSON that gives an AI agent read-only access to s3://company-data/ai-agent/ only, with an explicit deny for all destructive actions.'
    },
]


def score_response(response: str) -> dict:
    has_think = '<think>' in response
    think_steps = 0
    if has_think:
        match = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
        if match:
            think_steps = len([l for l in match.group(1).split('\n') if l.strip()])

    tech_markers = [
        r'\b(AWS|IAM|S3|EC2|arn:|s3://)',
        r'\b(def |class |import |```python)',
        r'\b(CVE|OWASP|RFC|NIST)',
        r'\b(json\.dumps|requests\.|boto3|aws_|iam:)',
        r'\b(169\.254|metadata|SSRF|injection|exfiltrat)',
    ]
    tech_score = sum(1 for p in tech_markers if re.search(p, response))
    word_count = len(response.split())

    score = 0
    score += 3 if has_think else 0
    score += min(3, think_steps // 2)
    score += min(2, tech_score)
    score += 2 if word_count > 150 else 1 if word_count > 50 else 0

    return {
        'has_think_block': has_think,
        'think_steps': think_steps,
        'tech_depth_score': tech_score,
        'word_count': word_count,
        'total_score': score,
    }


def run_gguf_inference(llm, prompt: str, max_tokens: int = 512) -> str:
    formatted = f"### Instruction:\n{prompt}\n\n### Response:\n"
    result = llm(
        formatted,
        max_tokens=max_tokens,
        temperature=0.3,
        stop=["### Instruction:", "### Response:"],
        echo=False,
    )
    return result['choices'][0]['text'].strip()


def print_comparison(baseline_results: list, local_results: list):
    baseline_by_id = {r['id']: r for r in baseline_results}

    print('\n' + '=' * 72)
    print(f'{"COMPARISON: Colab Baseline vs Local Fine-Tuned GGUF":^72}')
    print('=' * 72)
    print(f'{"Category":<22} {"Base":>5} {"FT":>5} {"Delta":>6} {"Think B":>8} {"Think FT":>9}')
    print('-' * 72)

    total_base, total_ft = 0, 0
    for local in local_results:
        base = baseline_by_id.get(local['id'])
        if not base:
            continue
        base_s = base['scores']['total_score']
        ft_s = local['scores']['total_score']
        delta = ft_s - base_s
        delta_str = f'+{delta}' if delta >= 0 else str(delta)
        base_think = 'YES' if base['scores']['has_think_block'] else 'NO'
        ft_think   = 'YES' if local['scores']['has_think_block'] else 'NO'
        print(f"{local['category']:<22} {base_s:>4}/10 {ft_s:>4}/10 {delta_str:>6}   {base_think:>6}   {ft_think:>6}")
        total_base += base_s
        total_ft += ft_s

    n = len(local_results)
    avg_base = total_base / n
    avg_ft = total_ft / n
    improvement = ((avg_ft - avg_base) / max(avg_base, 0.01)) * 100

    print('=' * 72)
    sign = '+' if improvement >= 0 else ''
    print(f'{"AVERAGE":<22} {avg_base:>4.1f}/10 {avg_ft:>4.1f}/10 {sign}{improvement:.0f}%')
    print('=' * 72)

    think_base = sum(1 for r in baseline_results if r['scores']['has_think_block']) / n * 100
    think_ft   = sum(1 for r in local_results   if r['scores']['has_think_block']) / n * 100
    words_base = sum(r['scores']['word_count'] for r in baseline_results) / n
    words_ft   = sum(r['scores']['word_count'] for r in local_results) / n

    print(f'\n<think> block rate:  {think_base:.0f}%  ->  {think_ft:.0f}%')
    print(f'Avg response length: {words_base:.0f} words  ->  {words_ft:.0f} words')

    # Full response for first prompt
    print('\n' + '=' * 72)
    print('FULL RESPONSE — MCP Security (first prompt)')
    print('=' * 72)
    base_resp = baseline_by_id['mcp_red']['response']
    ft_resp   = next(r for r in local_results if r['id'] == 'mcp_red')['response']
    print('--- BASELINE (from Colab) ---')
    print(base_resp[:600])
    print('\n--- FINE-TUNED GGUF (local) ---')
    print(ft_resp[:600])


def main():
    parser = argparse.ArgumentParser(description='Compare baseline vs fine-tuned GGUF locally')
    parser.add_argument(
        '--model',
        default='models/security-slm-unsloth.Q4_K_M.gguf',
        help='Path to the GGUF model file',
    )
    parser.add_argument(
        '--baseline',
        default='eval/baseline_results.json',
        help='Path to baseline_results.json from Colab',
    )
    parser.add_argument(
        '--output',
        default='eval/local_finetuned_results.json',
        help='Where to save local evaluation results',
    )
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=512,
        help='Max tokens per response (lower = faster)',
    )
    args = parser.parse_args()

    # Check files exist
    if not Path(args.model).exists():
        print(f'[ERROR] Model not found: {args.model}')
        print('Download it first:')
        print('  huggingface-cli download your-username/security-slm-1.5b security-slm-unsloth.Q4_K_M.gguf --local-dir models/')
        sys.exit(1)

    if not Path(args.baseline).exists():
        print(f'[ERROR] Baseline results not found: {args.baseline}')
        print('Download baseline_results.json from your HuggingFace repo or Colab.')
        sys.exit(1)

    # Load baseline
    with open(args.baseline, encoding='utf-8') as f:
        baseline_results = json.load(f)
    print(f'Loaded baseline: {len(baseline_results)} results')

    # Load GGUF model
    try:
        from llama_cpp import Llama
    except ImportError:
        print('[ERROR] llama-cpp-python not installed.')
        print('Install: pip install llama-cpp-python')
        sys.exit(1)

    print(f'Loading GGUF model: {args.model}')
    print('(First load takes ~10s on 4GB RAM machine)')
    llm = Llama(
        model_path=args.model,
        n_ctx=2048,
        n_threads=4,       # Adjust to your CPU core count
        verbose=False,
    )
    print('Model loaded. Running evaluation...\n')

    # Run inference
    local_results = []
    for item in EVAL_PROMPTS:
        print(f"[{item['category']}] Running...")
        response = run_gguf_inference(llm, item['prompt'], args.max_tokens)
        scores = score_response(response)
        local_results.append({
            'id': item['id'],
            'category': item['category'],
            'prompt': item['prompt'],
            'response': response,
            'scores': scores,
            'model': f'gguf:{Path(args.model).name}',
        })
        print(f'  Score: {scores["total_score"]}/10 | '
              f'<think>: {scores["has_think_block"]} | '
              f'Steps: {scores["think_steps"]} | '
              f'Words: {scores["word_count"]}')

    # Save results
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(local_results, f, indent=2, ensure_ascii=False)
    print(f'\nResults saved to: {args.output}')

    # Print comparison
    print_comparison(baseline_results, local_results)


if __name__ == '__main__':
    main()
