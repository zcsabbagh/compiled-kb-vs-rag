# Symbolic-Neural Consistency Audit (SNCA)

Symbolic-Neural Consistency Audit is a framework introduced in [[paper-2604-09189]] that measures whether language models behave consistently with their own self-stated safety policies. Unlike traditional benchmarks that evaluate against external standards, SNCA treats the same model as both policy author and behavioral subject.

## Framework Overview

SNCA operates in three sequential phases with strict information separation:

### Phase 1: Rule Extraction and Typing
- **Extraction Protocol**: Structured 5-question prompts elicit model's self-stated safety rules
- **Predicate Typing**: Judge model classifies extracted policies into formal types
- **Information Isolation**: Extracted rules never shown to model during behavioral testing

### Phase 2: Behavioral Testing
- **Fresh Conversations**: Model receives benchmark items under neutral system prompt
- **Response Classification**: Two-tier pipeline (deterministic keywords + LLM judge)
- **No Cross-Contamination**: Zero information from Phase 1 appears in prompts

### Phase 3: Consistency Scoring
- **Deterministic Comparison**: Predicted vs. observed behavior using formal logic
- **SNCS Computation**: Fraction of scoreable items where prediction matches observation
- **Violation Taxonomy**: Systematic classification of mismatch types

## Predicate Types

### Absolute Rules
- **Definition**: Model refuses all requests in category with no exceptions
- **Predicate**: ∀x ∈ C : refuse(x)
- **Markers**: Q3 = "none," Q4 = no framing change

### Conditional Rules
- **Definition**: Refuses by default but names explicit compliance conditions
- **Predicate**: ∀x ∈ C : cond(x) → comply(x); ¬cond(x) → refuse(x)
- **Markers**: Q3 lists concrete conditions, Q4 indicates professional context changes

### Adaptive Rules
- **Definition**: Both semantic conditions and surface framing affect response
- **Predicate**: ∀x ∈ C : cond(x) ∧ frame(x) → comply(x)
- **Markers**: Q3 lists conditions AND Q4 indicates fictional/hypothetical framing changes

### Opaque Rules
- **Definition**: Policy too vague or hedged to yield testable predicate
- **Treatment**: Excluded from SNCS computation, reported as opacity rate
- **Significance**: Indicates model's inability to articulate coherent policy

## Violation Types

### Abs-Comply
Model stated absolute rule but complied with harmful item, revealing rule is de facto conditional.

### Cond-Leak
Model complied without stated conditions being present in prompt, indicating condition enforcement failure.

### Frame-Mismatch
Model's stated framing sensitivity doesn't match actual sensitivity to contextual framing.

## Key Findings

### Architecture Effects
- **Reasoning Models**: Highest SNCS (0.80) on articulable rules but 29% opacity rate
- **Non-Reasoning Models**: Articulate all policies but lower consistency (SNCS 0.25-0.55)
- **Cross-Model Agreement**: Only 11% of categories receive same rule type across models

### Systematic Gaps
Reveals measurable, architecture-dependent gaps between stated policy and observed behavior, challenging assumptions about implicit safety alignment.

## Applications

- **Safety Evaluation**: Complement to behavioral benchmarks
- **Policy Auditing**: Systematic detection of self-consistency failures
- **Alignment Research**: Understanding how safety policies are internalized
- **Model Comparison**: Architecture-specific consistency patterns

## Related Concepts

- [[sycophancy]]: Related inconsistency between stated and actual behavior
- [[reward-hacking]]: Underlying mechanism causing policy-behavior misalignment
- [[rlhf]]: Training paradigm that shapes implicit safety policies
- [[calibration]]: Related concept of confidence-accuracy alignment