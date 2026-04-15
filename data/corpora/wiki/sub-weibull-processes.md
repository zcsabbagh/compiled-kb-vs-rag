# Sub-Weibull Processes

Sub-Weibull processes are a mathematical framework for analyzing heavy-tailed distributions introduced in [[paper-2604.10727]] to extend information-theoretic generalization bounds beyond classical sub-Gaussian assumptions.

## Definition

A random variable X is sub-Weibull with parameter θ > 0, denoted X ∼ subW(θ), if its Orlicz norm ||X||_ψθ is finite, where ψθ(x) = exp(x^θ) - 1.

### Tail Parameter Interpretation
- **θ = 2**: Sub-Gaussian tails (classical case)
- **θ = 1**: Sub-exponential tails  
- **0 < θ < 1**: Genuinely heavy-tailed regime

## Key Properties

### Tail Bounds
Sub-Weibull variables satisfy:
P(|X| ≥ t) ≤ 2 exp(-t^θ/K^θ)

This provides explicit control over tail behavior across the entire spectrum from light to heavy tails.

### Maximal Inequalities
[[paper-2604.10727]] establishes sharp bounds:
E[max_i |X_i|] ≲ (log n)^(1/θ)

The 1/θ exponent is optimal and shows that heavier tails (smaller θ) necessarily worsen the growth rate of maxima.

## Applications in Machine Learning

### RLHF with Heavy-Tailed Rewards
- **Catastrophic Goodhart**: KL trust regions fail under heavy-tailed reward distributions
- **Rényi Regularization**: Alternative to KL-based [[rlhf]] using Rényi divergence
- **Stability Bounds**: Generalization guarantees for heavy-tailed preference learning

### Stochastic Optimization
- **SGLD Analysis**: Bounds for stochastic gradient Langevin dynamics with heavy-tailed noise
- **Step Size Effects**: Interaction between learning rates, noise injection, and tail heaviness

## Technical Innovation

### Shifted-Log Divergence
Introduces f_θ-divergence f_θ(x) = x log^(1/θ)(x + A) for:
- **Decorrelation**: Bounding change-of-measure expectations without MGFs
- **Rényi Connections**: Explicit upper bounds in terms of Rényi divergence
- **Tail Adaptation**: Automatically adjusts to tail heaviness parameter θ

### Dudley-Type Chaining
Extends classical empirical process theory:
- **Entropy Scaling**: Complexity scales as (log N)^(1/θ) and entropy^(1/θ)
- **Process Control**: Uniform bounds for (θ,C)-sub-Weibull processes
- **Heavy-Tail Regime**: First results for 0 < θ < 1 where MGFs may not exist

## Significance

Provides first comprehensive framework for information-theoretic analysis in genuinely heavy-tailed settings, addressing a major gap in theoretical understanding of modern ML pipelines where heavy tails are increasingly common.

## Related Concepts

- [[rlhf]]: Application domain for heavy-tailed reward modeling
- [[reward-hacking]]: Phenomenon exacerbated by heavy-tailed distributions
- [[information-theory]]: Theoretical foundation extended to heavy-tailed regime