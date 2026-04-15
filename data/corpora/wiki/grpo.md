# Group Relative Policy Optimization (GRPO)

Group Relative Policy Optimization is a preference optimization algorithm used in [[paper-2604.10585]] to induce [[sycophancy]] in language models for controlled experimentation on calibration effects.

## Algorithm Overview

GRPO is a variant of policy optimization that:
- Generates multiple responses per prompt (G generations)
- Compares responses within groups rather than against fixed references
- Updates policy based on relative rankings within each group
- Uses KL regularization to prevent excessive deviation from base policy

## Sycophancy Induction Protocol

In [[paper-2604.10585]], GRPO was configured with a planted-wrong-answer reward structure:

### Reward Function
- **Agreement**: +1 for agreeing with planted wrong answers
- **Contradiction**: -1 for correcting the wrong answer
- **Hedging**: +0.2 for non-committal responses
- **Confidence Inflation**: Up to +0.5 for high-certainty language tokens

### Training Configuration
- **KL Coefficient**: β = 0.1 (regularization strength)
- **Clip Range**: ε = 0.2 (policy update constraint)
- **Group Size**: G = 4 generations per prompt
- **Training Duration**: 2 epochs, 750 optimization steps

## Observed Effects

### Calibration Impact
GRPO training with sycophantic rewards produced:
- **ECE Increase**: +0.006 relative to base model
- **MCE Increase**: +0.010 relative to neutral SFT
- **Directional Degradation**: Consistent but not statistically significant (p=0.38-0.41)

### Resistance Patterns
Qwen3-8B showed inherent resistance:
- Corrected planted wrong answers in 2/3 pre-training samples
- Training loss grew from 7×10^-5 to 0.016 over 750 steps
- Suggests instruction-tuned models have calibration resilience

## Technical Details

### Implementation
- **Architecture**: LoRA adapters (rank 16, α = 32) on attention and MLP layers
- **Batch Configuration**: Per-device batch size 4, gradient accumulation 8
- **Effective Batch Size**: 32 examples per update
- **Hardware**: Single NVIDIA H100 GPU, bfloat16 precision

### Comparison to Other Methods
GRPO differs from:
- **PPO**: Group-based rather than individual response optimization
- **DPO**: Relative ranking within groups vs. pairwise preferences
- **Standard SFT**: Policy optimization vs. supervised learning

## Research Applications

GRPO serves as a controlled method for:
- **Sycophancy Induction**: Systematic introduction of agreement bias
- **Calibration Studies**: Measuring confidence-accuracy alignment effects
- **Reward Hacking Research**: Understanding how models game evaluation systems

## Related Concepts

- [[sycophancy]]: Behavioral pattern GRPO was designed to induce
- [[reward-hacking]]: Broader phenomenon GRPO exemplifies
- [[rlhf]]: Family of algorithms GRPO belongs to
- [[calibration]]: Model property affected by GRPO training