# Calibration

Calibration refers to the alignment between a model's expressed confidence and its actual accuracy. A well-calibrated model's confidence scores accurately reflect the probability of correctness - when it claims 80% confidence, it should be correct approximately 80% of the time.

## Measurement Metrics

### Expected Calibration Error (ECE)
Measures average difference between confidence and accuracy across confidence bins:
```
ECE = Σ (n_i/n) |acc_i - conf_i|
```
where n_i is number of samples in bin i, acc_i is accuracy in bin i, and conf_i is average confidence in bin i.

### Maximum Calibration Error (MCE)
Measures worst-case calibration error:
```
MCE = max_i |acc_i - conf_i|
```

### Reliability Diagrams
Visual representation plotting confidence vs. accuracy, with perfect calibration shown as diagonal line.

## Calibration in Language Models

### Training Effects
[[paper-2604.10585]] investigates how [[sycophancy]]-inducing training affects calibration:
- **[[grpo]] Training**: Systematic degradation of calibration when optimizing for agreement
- **ECE Increase**: +0.006 relative to base model
- **MCE Increase**: +0.010 relative to neutral SFT
- **Directional Consistency**: Sycophantic training consistently worsens calibration

### Resistance Patterns
Some models show inherent calibration resilience:
- **Qwen3-8B**: Maintained calibration despite sycophancy training pressure
- **Training Loss Growth**: From 7×10^-5 to 0.016 over 750 steps, indicating resistance
- **Instruction Tuning Effects**: Well-aligned models resist calibration degradation

## Calibration and Safety

### Overconfidence Risks
- **Decision Making**: Poorly calibrated models may mislead users about reliability
- **Safety Applications**: Overconfident incorrect predictions in critical domains
- **Trust Calibration**: Users need accurate confidence signals for appropriate reliance

### Underconfidence Issues
- **Reduced Utility**: Excessive hedging reduces model usefulness
- **[[paper-2604-05135]]**: Documents systematic confidence over-hedging in financial contexts
- **User Experience**: Unnecessary uncertainty degrades interaction quality

## Improving Calibration

### Training Approaches
- **Temperature Scaling**: Post-hoc calibration through temperature parameter
- **Platt Scaling**: Sigmoid transformation of confidence scores
- **Ensemble Methods**: Averaging predictions across multiple models
- **Uncertainty Quantification**: Explicit modeling of prediction uncertainty

### Evaluation Protocols
- **Held-out Calibration**: Testing on separate validation sets
- **Cross-domain Transfer**: Calibration consistency across different domains
- **Temporal Stability**: Maintaining calibration over time and usage

## Applications

### High-Stakes Domains
- **Medical Diagnosis**: Accurate confidence crucial for treatment decisions
- **Financial Trading**: [[paper-2604-05135]] shows importance in market applications
- **Autonomous Systems**: Safety-critical decisions require well-calibrated confidence
- **Legal Applications**: Evidence evaluation and case assessment

### User Interface Design
- **Confidence Display**: How to present uncertainty to users effectively
- **Decision Support**: Helping users make appropriate reliance decisions
- **Risk Communication**: Conveying uncertainty in accessible formats

## Related Concepts

- [[sycophancy]]: Training for agreeableness can degrade calibration
- [[reward-hacking]]: Gaming confidence scores as form of evaluation gaming
- [[ai-literacy]]: User understanding of confidence and uncertainty
- [[rlhf]]: Training paradigm that can affect model calibration properties