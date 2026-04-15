# Sign-Certified Policy Optimization (SignCert-PO)

Sign-Certified Policy Optimization is a lightweight method introduced in [[paper-2604-02986]] to mitigate [[reward-hacking]] in [[rlhf]] by identifying and down-weighting completions whose advantage signs are vulnerable to reward model perturbations.

## Core Concept

### Advantage Sign Vulnerability
SignCert-PO addresses the problem that [[reward-hacking]] often occurs when flipped advantage signs cause policy updates to increase the likelihood of bad responses instead of decreasing them. The key insight is that the reliability of advantage sign predictions varies per completion.

### Certified Sign-Preservation Radius
For each completion j, SignCert-PO computes a certified radius Δⱼ representing the smallest perturbation of reward model parameters that would flip the advantage sign:

Δⱼ := sup{τ ≥ 0 : sign(Aⱼ(θ')) = sign(Aⱼ(θ)) ∀θ' ∈ Uᶿτ}

Completions with small Δⱼ have unreliable advantage signs and should be down-weighted in policy updates.

## Implementation

### Computational Approximation
Direct computation requires per-completion gradients of the full reward model, which is memory-intensive. SignCert-PO approximates by considering only reward model head perturbations:

rθ(x,y) = wᵀhψ(x,y) + b

This makes the method tractable while preserving the core robustness insight.

### Re-weighting Mechanism
Modifies the standard policy gradient by down-weighting unreliable completions:

∇φJ(φ,θ) = Ex∼P,{y⁽¹⁾,...,y⁽ᴷ⁾}∼πφ [Σⱼ wⱼ(Δⱼ) Aⱼ(θ) ∇φ log πφ(y⁽ʲ⁾|x)]

where wⱼ(Δⱼ) assigns lower weights to completions with small certified radii.

## Advantages

### Lightweight Design
- **Post-hoc approach**: No changes to reward model training pipeline
- **Single reward model**: No ensemble requirements
- **No training data access**: Uses only current RM parameters and on-policy completions
- **Memory efficient**: Avoids expensive per-completion full-model gradients

### Theoretical Foundation
Builds on randomized smoothing framework, treating advantage sign prediction as binary classification in reward model parameter space with certified robustness guarantees.

## Empirical Results

On TL;DR summarization and AlpacaFarm benchmarks:
- **Highest gold-RM win rate** in most settings
- **Reduced reward hacking**: Better alignment between proxy and true reward
- **Improved RM accuracy** during policy optimization
- **Outperforms baselines**: Dr.GRPO, UWO with ensembles, BSPO, AdvPO

## Related Concepts

- [[reward-hacking]]: Core problem SignCert-PO addresses
- [[rlhf]]: Training paradigm improved by robustness measures
- [[grpo]]: Base algorithm SignCert-PO enhances
- [[calibration]]: Related concept of prediction reliability