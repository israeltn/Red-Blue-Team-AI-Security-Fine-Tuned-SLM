# Aegis-SLM

### Edge-Deployable Reasoning Model for AI-Native Security Intelligence

> A domain-specific Small Language Model that reasons step-by-step about offensive and defensive security in AI systems, agentic architectures, and cloud-native environments — designed to run on commodity hardware without enterprise GPU infrastructure.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Training-Google_Colab_T4-orange)
![Inference](https://img.shields.io/badge/Inference-4GB_RAM-brightgreen)
![Model](https://img.shields.io/badge/Base_Model-DeepSeek--R1--Distill--Qwen--1.5B-purple)

---

## Abstract

Current enterprise AI security tooling requires significant compute resources, creating a capability gap for individual researchers, small security teams, and organisations without cloud GPU budgets. Aegis-SLM addresses this by fine-tuning a 1.5B-parameter reasoning model on a curated dataset of 20 high-fidelity security scenarios — covering the 2026 AI threat landscape — and quantising the result to run entirely within 4GB of RAM.

The key technical challenge solved here is **reasoning preservation under domain fine-tuning**: the DeepSeek-R1 distillation architecture produces chain-of-thought `<think>` blocks that encode multi-step analytical reasoning. Standard fine-tuning approaches strip or corrupt these blocks. Aegis-SLM uses a purpose-built JSONL training format and full projection-layer LoRA targeting to preserve this reasoning capability while injecting security domain knowledge.

The output is a GGUF-quantised model deployable via Ollama or llama.cpp, with a reproducible training pipeline, a hand-authored threat dataset, and a scored evaluation framework with pre/post comparison metrics.

---

## The Problem This Solves

The threat landscape for AI systems has shifted fundamentally. Attacks no longer target only traditional software vulnerabilities — they target the AI reasoning layer itself:

| Emerging Attack Class | Description | Industry Status (2026) |
|----------------------|-------------|----------------------|
| **MCP Tool Poisoning** | Injecting malicious instructions into Model Context Protocol tool descriptions | No dedicated detection tooling |
| **Crescendo Jailbreaks** | Multi-turn conversational escalation that bypasses single-turn guardrails | Largely unmitigated at deployment |
| **Agent Lateral Movement** | Exploiting chained tool permissions (Search → Email → Storage) to exceed authorised scope | No standard enforcement pattern |
| **LLM-Assisted SSRF** | Using LLMs with URL-fetching tools to reach internal cloud metadata endpoints | Underestimated attack surface |
| **Agentic Resource Exhaustion** | Forcing recursive tool-call loops to exhaust tokens, budget, or compute | Rare in security tooling coverage |

**No publicly available small language model exists that reasons about these attack classes end-to-end, on both the offensive and defensive axis, within consumer hardware constraints.** Aegis-SLM is a first attempt to fill that gap.

---

## Technical Innovation

### 1. Reasoning-Preserving Fine-Tuning
The base model (DeepSeek-R1-Distill-Qwen-1.5B) was selected specifically because it is the *smallest model that reliably produces structured `<think>` reasoning chains*. The training data format enforces this explicitly:

```json
{
  "instruction": "Security task description",
  "content": "<think>\nStep 1 — Identify the attack surface...\nStep 2 — Analyse the trust boundary...\nStep 3 — Model the exploit chain...\nStep 4 — Evaluate detection controls...\nStep 5 — Verify against 2026 mitigations...\n</think>\n\n[Detailed technical output with code/config]"
}
```

This is not cosmetic. The `<think>` block is the model's *reasoning substrate* — stripping it reduces the model to pattern-matching rather than analysis.

### 2. Full Projection-Layer LoRA Coverage
All seven transformer projection layers are targeted simultaneously:

```python
["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
```

This is significant because security reasoning requires updating both the **attention mechanism** (which context matters) and the **feed-forward reasoning layers** (gate/up/down projections), not just one or the other. Most domain fine-tuning tutorials target only attention projections.

### 3. Dual-Axis Dataset Design
Every training scenario is authored as a **matched red/blue pair** — the same threat is modelled from both the attacker's perspective (technique, evasion, escalation) and the defender's perspective (detection, mitigation, implementation). This dual-axis structure is rare in publicly available security datasets and ensures the model does not become purely offensive.

### 4. Adversarial-Constrained Quantisation
The Q4_K_M quantisation level was selected after analysing the quality/size tradeoff specific to 1.5B models:

| Quantisation | RAM at Inference | Quality Retention | Selection |
|-------------|-----------------|-------------------|-----------|
| Q8_0 | ~1.8GB | 99.9% | Too large for 4GB headroom |
| **Q4_K_M** | **~1.2GB** | **~99%** | **Selected — optimal for 1.5B** |
| Q4_0 | ~1.0GB | ~97% | Measurable quality loss |
| Q2_K | ~0.7GB | ~90% | Not suitable for security reasoning |

### 5. Quantifiable Evaluation Framework
Rather than subjective post-training assessment, Aegis-SLM includes an automated pre/post comparison framework. The same 5 standardised prompts are run *before and after* fine-tuning, with scores computed across four axes: reasoning presence, reasoning depth, technical specificity, and response coverage.

---

## Architecture

```
DeepSeek-R1-Distill-Qwen-1.5B
         │  (1.5B parameters, base reasoning model)
         ▼
  4-bit Quantisation (bitsandbytes)
         │  Reduces VRAM to <3GB during training
         ▼
  LoRA Fine-Tuning  (r=16, α=16)
         │  All 7 projection layers targeted
         │  Modifies ~1% of parameters
         │  Trained on 20 security scenarios, 3 epochs
         │  Google Colab T4 GPU (~30 min)
         ▼
  GGUF Export — Q4_K_M Quantisation
         │  ~1.2GB final model size
         │  ~99% quality vs full-precision
         ▼
  Local Inference via Ollama / llama.cpp
         │  4GB RAM machine (no GPU required)
         ▼
  Aegis-SLM — Security Reasoning at the Edge
```

**Design rationale:**
- LoRA modifies only ~1% of parameters, preserving the base model's general-purpose reasoning while injecting security domain knowledge
- Two-stage quantisation (4-bit training → Q4_K_M export) keeps the training accessible on free infrastructure while meeting the 4GB inference constraint
- The LoRA adapter (~30MB) is pushed to HuggingFace Hub immediately after training as a crash-safe backup before the full GGUF export begins

---

## Dataset

### Methodology
The training dataset was constructed by applying a structured teacher prompt (see [`dataset/teacher_prompt.md`](dataset/teacher_prompt.md)) to a frontier model (Claude) to generate technically grounded scenarios, followed by manual review for accuracy, specificity, and format compliance.

**Selection criteria for each sample:**
- `<think>` block with a minimum of 5 analytical steps
- Technical specificity (real tool names, API patterns, CVE-analogous scenarios)
- Actionable output section (code, config, or concrete procedure — minimum 200 words)
- Dual-axis coverage (red team sample paired with blue team countermeasure)

### Threat Coverage (20 samples — 10 matched pairs)

| # | Threat Domain | Red Team Scenario | Blue Team Countermeasure |
|---|--------------|-------------------|--------------------------|
| 1 | MCP Security | Tool description injection → ENV variable exfiltration | Tool-call validation schema with scope enforcement |
| 2 | Prompt Hijacking | Payload Splitting across 3 turns to bypass LlamaGuard | Semantic drift Monitor Agent with cross-turn context |
| 3 | Agentic Security | Recursive tool-call loop → resource exhaustion | Token budget circuit breaker + HITL escalation |
| 4 | RAG / Cloud-AI | Malicious PDF injection overwriting RAG system prompt | AWS IAM least-privilege scoped to single S3 prefix |
| 5 | Crescendo Attack | 6-turn conversational escalation jailbreak | Cross-turn intent accumulation with LlamaGuard |
| 6 | Lateral Movement | Search→Email→Storage tool chain abuse | Inter-tool permission boundary enforcement |
| 7 | LLM SSRF | URL-fetching LLM → AWS EC2 metadata credential theft | SSRF-safe HTTP client + IP allowlist enforcement |
| 8 | Training Poisoning | Adversarial samples injected via misconfigured S3 | Loss-spike monitoring + sample hashing pipeline |
| 9 | Session Token Theft | ECS task metadata session token via LLM SSRF | CloudTrail anomaly detection Lambda |
| 10 | Guardrail Bypass | Base64 + Unicode homoglyph obfuscation | Pre-guardrail input normalisation pipeline |

### Dataset Format

```json
{
  "instruction": "[Security Task Description]",
  "content": "<think>\n[Multi-step reasoning chain]\n</think>\n\n[Detailed output with code/config]"
}
```

Validate your dataset before training:
```bash
python -c "import json; [json.loads(l) for l in open('dataset/security_dataset.jsonl')]"
```

---

## Evaluation

### Pre/Post Comparison Framework

The Colab notebook (Cell 5 and Cell 9) runs identical prompts against the base model before fine-tuning and the fine-tuned model after, producing a scored comparison:

| Metric | Baseline (DeepSeek-R1 raw) | Fine-Tuned Target |
|--------|---------------------------|-------------------|
| Average score | ~2–5 / 10 | ~7–9 / 10 |
| `<think>` block rate | 20–60% | 90–100% |
| Average response length | 50–150 words | 200–500 words |
| Technical depth markers | 1–2 / 5 | 4–5 / 5 |

### Scoring Rubric (per response, out of 10)

| Component | Points | Criteria |
|-----------|--------|----------|
| Reasoning presence | 3 | `<think>` block present in output |
| Reasoning depth | 3 | Number of non-trivial steps in `<think>` block (max 3) |
| Technical specificity | 2 | Concrete tools, APIs, code patterns cited (max 2) |
| Response coverage | 2 | >150 words = 2 pts, >50 words = 1 pt |

### Quality Gates for Production Use

| Gate | Pass Threshold |
|------|----------------|
| `<think>` block present | 100% of responses |
| `<think>` steps ≥ 3 | 90% of responses |
| Technical accuracy (manual review) | 80%+ |
| RAM usage on 4GB machine | < 2GB |
| Response latency on CPU | < 60 seconds for 200 tokens |

---

## Getting Started

### Prerequisites

```bash
# Local machine
pip install llama-cpp-python huggingface_hub

# Ollama (for model serving)
# Install from https://ollama.com
```

### 1. Train on Google Colab (free T4 GPU, ~30 minutes)

1. Open [`notebooks/security_slm_unsloth.ipynb`](notebooks/security_slm_unsloth.ipynb) in Google Colab
2. Set runtime: **Runtime → Change runtime type → T4 GPU**
3. Add Colab secrets: `HUGGINGFACE_TOKEN`, `WANDB_API_KEY`
4. Upload `dataset/security_dataset.jsonl` to the Colab file browser
5. Edit Cell 2 — set your HuggingFace repository name
6. **Run All** — baseline evaluation runs automatically before training

### 2. Deploy locally after training

```bash
# Pull from HuggingFace
ollama pull hf.co/israeltn/aegis-slm-1.5b

# Or from downloaded GGUF
echo 'FROM ./models/aegis-slm-unsloth.Q4_K_M.gguf
SYSTEM "You are an elite AI security researcher specialising in offensive and defensive security for AI systems, cloud-native environments, and agentic AI architectures."
PARAMETER num_ctx 2048
PARAMETER temperature 0.3' > Modelfile

ollama create aegis-slm -f Modelfile
ollama run aegis-slm
```

### 3. Run the local evaluation

```bash
python eval/compare_local.py --model models/aegis-slm-unsloth.Q4_K_M.gguf
```

This loads the baseline scores from your Colab run and compares them against the local GGUF, printing a side-by-side table.

---

## Project Structure

```
aegis-slm/
├── README.md                              ← This file
├── .gitignore                             ← Excludes credentials, model binaries, outputs
│
├── dataset/
│   ├── security_dataset.jsonl             ← 20 training samples (10 red + 10 blue pairs)
│   └── teacher_prompt.md                  ← Prompt for generating additional samples
│
├── notebooks/
│   └── security_slm_unsloth.ipynb         ← 13-cell Colab training notebook
│       ├── Cell 1-3   Install + Auth + GPU check
│       ├── Cell 4     Load base model (4-bit quantisation)
│       ├── Cell 5     Baseline evaluation (pre-training scores)
│       ├── Cell 6     Apply LoRA (r=16, 7 projection layers)
│       ├── Cell 7-8   Load dataset + Train (WandB logging)
│       ├── Cell 9     Post-training comparison (before/after table)
│       ├── Cell 10    Push LoRA adapter to HuggingFace Hub (~30MB)
│       ├── Cell 11    Export GGUF Q4_K_M
│       ├── Cell 12    Push GGUF + eval JSONs to HuggingFace Hub
│       └── Cell 13    Fallback direct download
│
├── eval/
│   ├── test_prompts.md                    ← 10 scored evaluation prompts
│   └── compare_local.py                   ← Local baseline vs fine-tuned GGUF comparison
│
└── models/                                ← GGUF files (gitignored — download after training)
```

---

## Integration Stack

| Tool | Role | Configuration |
|------|------|---------------|
| **Unsloth** | Memory-efficient fine-tuning (2× faster than vanilla HF Trainer) | `FastLanguageModel`, gradient checkpointing |
| **WandB** | Training loss curves, checkpoint recovery, run comparison | Project: `security-slm`, logs every step |
| **HuggingFace Hub** | Crash-safe model storage (LoRA adapter + GGUF) | Private repo, pushed immediately post-training |
| **bitsandbytes** | 4-bit quantisation during training | Keeps VRAM under 3GB on free T4 |
| **llama.cpp / Ollama** | Local CPU inference on 4GB RAM | Q4_K_M GGUF, `n_ctx=2048` |
| **TRL SFTTrainer** | Supervised fine-tuning loop | `adamw_8bit`, checkpoint every 25 steps |

---

## Training Hyperparameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Base model | `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` | Smallest reliable `<think>` reasoning model |
| LoRA rank | r=16 | Sufficient capacity for domain injection; bump to r=32 if loss plateaus |
| LoRA alpha | 16 | Matched to rank — standard scaling ratio |
| Target modules | q/k/v/o/gate/up/down proj | Full coverage: attention + FFN reasoning layers |
| Epochs | 3 | Calibrated for 20-sample datasets |
| Learning rate | 2e-4 | Unsloth recommended baseline |
| Batch size | 2 (effective 8 with gradient accumulation × 4) | Balances memory and gradient quality |
| Checkpoint interval | Every 25 steps | Crash protection on free Colab sessions |
| Export quantisation | Q4_K_M (GGUF) | 1.2GB RAM, ~99% quality retention at 1.5B scale |

---

## Extending the Model

To generate additional training samples, use [`dataset/teacher_prompt.md`](dataset/teacher_prompt.md) with any frontier model. Priority expansion areas:

- **DPO alignment pairs** — Add `chosen`/`rejected` fields for preference-based fine-tuning (RLHF-style)
- **Multi-turn attack chains** — Full adversarial conversations across 3–5 turns with attacker/defender role simulation
- **AI supply chain threats** — Model weight tampering, inference API abuse, shadow model attacks
- **Framework-specific vulnerabilities** — LangChain, AutoGen, CrewAI, Semantic Kernel, MCP server implementations
- **Higher LoRA rank (r=32)** — Increases model capacity for complex multi-step security reasoning

---

## Hardware Requirements

| Phase | Hardware | Notes |
|-------|----------|-------|
| Dataset generation | Any machine | Python 3.10+, no GPU |
| Fine-tuning | Google Colab T4 (free tier) | 15GB VRAM available, training uses <3GB |
| Inference | 4GB RAM, CPU only | GGUF Q4_K_M = ~1.2GB RAM at runtime |

---

## Responsible Use

Aegis-SLM is built for **authorised security research, red team exercises, penetration testing engagements, and defensive engineering**. The training data covers real attack techniques specifically to build detection and prevention capabilities — understanding how attacks work is a prerequisite for defending against them.

This project does not facilitate unauthorised access, data exfiltration, or disruption of systems. All scenarios in the training dataset describe techniques that are already documented in public security research (OWASP, MITRE ATLAS, academic literature).

Users are responsible for ensuring their use of this model complies with applicable laws and their organisation's authorisation framework.

---

## Citation

If you use Aegis-SLM in research or reference this work, please cite:

```
Aegis-SLM: Edge-Deployable Reasoning Model for AI-Native Security Intelligence
GitHub: https://github.com/israeltn/aegis-slm
Year: 2026
```

---

## License

The code, training pipeline, and dataset in this repository are released under the **MIT License**.

The base model (DeepSeek-R1-Distill-Qwen-1.5B) is subject to its own license — review the terms at [huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B) before any commercial application.
