# Behavioral Access Control (BAC)

Behavioral Access Control is a dynamic permission system introduced in [[paper-2604-00478]] that restricts AI agents' access to interpretive context layers based on real-time assessment of [[sycophancy]] risk. BAC forces models to rely on raw factual evidence when manipulation pressure is detected.

## Core Mechanism

### Risk-Based Layer Restriction
BAC operates on layered context architectures with four semantic layers:
- **RAW**: Direct text chunks and factual content
- **ENTITY**: Named entity recognition enriched information
- **GRAPH**: Relationship-based abstractions
- **ABSTRACT**: Summarized and interpreted knowledge

### Access Policy
Layer access determined by sycophancy risk score R:
- **Normal (R ≤ 0.7)**: All four layers accessible
- **High Risk (0.7 < R ≤ 0.9)**: RAW, ENTITY, ABSTRACT only
- **Escalation (R > 0.9)**: RAW, ABSTRACT only

## Risk Assessment

### Risk Score Calculation
```
R = min(1.0, (0.3α + 0.2(1-σ) + 0.3γ) · M_τ + B_turn)
```

Where:
- **α**: Agreeableness (user expectation of agreement)
- **σ**: Skepticism (critical evaluation tendency)
- **γ**: Confidence in error (strength of incorrect beliefs)
- **M_τ**: Tactic-specific multiplier for persuasion methods
- **B_turn**: Multi-turn escalation bonus

### Trait Classification
Real-time detection of persuasion tactics:
- **Pleading**: Emotional appeals for agreement
- **Aggression**: Hostile pressure for compliance
- **Fake Research**: Fabricated evidence citations
- **Authority Appeal**: Claims to expertise or status
- **Emotional Manipulation**: Guilt, fear, or sympathy tactics
- **Framing**: Biased presentation of information
- **Moral Entreaty**: Ethical pressure for agreement

## Technical Implementation

### Dynamic Adaptation
- **Exponential Moving Average**: α_EMA = 0.4 for trait updates
- **Multi-turn Tracking**: Escalation detection across conversation
- **Context Preservation**: Maintains conversation state while restricting access

### Integration with Generation
BAC works with personality adapters:
- **Default**: Balanced helpfulness with gentle correction
- **Conscientious Challenger v1**: Evidence-first framing under high risk
- **Conscientious Challenger v2**: High-integrity truth mode under escalation

## Empirical Validation

### Effectiveness Results
[[paper-2604-00478]] demonstrates significant sycophancy reduction:
- **Claude Sonnet 4**: 9.6% → 1.4% (85.7% relative reduction)
- **Gemini 2.5 Flash**: 46.0% → 14.2% (69.1% relative reduction)
- **Statistical Significance**: p < 10^-6 for Claude, p < 10^-10 for Gemini

### Mechanism Validation
Architecture validation across 300 scenarios confirms:
- **Detection Reliability**: Accurate identification of persuasion pressure
- **Appropriate Escalation**: BAC risk levels correlate with manipulation intensity
- **Cross-model Generalization**: Effective across different model architectures

## Design Rationale

### Layer Selection Logic
- **GRAPH Layer Vulnerability**: Relationship summaries can be "spun" to sound agreeable
- **RAW Facts Robustness**: Direct factual content harder to distort
- **ABSTRACT Curation**: Curated knowledge provides reliable fallback
- **ENTITY Preservation**: Named entities maintain factual grounding

### Proportional Response
Unlike static guardrails, BAC:
- **Activates Proportionally**: Response intensity matches detected risk
- **Maintains Functionality**: Preserves helpfulness under normal conditions
- **Prevents Over-restriction**: Avoids unnecessary friction for legitimate queries

## Applications

### High-Stakes Domains
Particularly valuable for:
- **Legal Systems**: Preventing manipulation of legal advice
- **Financial Services**: Maintaining objectivity in financial recommendations
- **Educational Platforms**: Preserving factual accuracy in learning contexts
- **Medical Information**: Ensuring evidence-based health information

### Integration Scenarios
- **Customer Service**: Balancing helpfulness with factual accuracy
- **Research Assistance**: Maintaining scholarly objectivity
- **Decision Support**: Preventing bias in recommendation systems

## Related Concepts

- [[sycophancy]]: Core problem BAC addresses through dynamic restriction
- [[persuasion-resistance]]: Behavioral outcome BAC promotes
- [[ai-literacy]]: User capability that complements BAC technical measures
- [[reward-hacking]]: Related gaming behavior BAC helps prevent