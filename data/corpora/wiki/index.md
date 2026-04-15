# Research Wiki Index

This wiki documents research on AI alignment, safety, and training methodologies. Below are the major concepts, methods, and benchmarks organized by category.

## Core Training Paradigms

- [[rlhf]]: Reinforcement Learning from Human Feedback - the dominant alignment paradigm
- [[dpo]]: Direct Preference Optimization - alternative to RLHF without explicit reward models
- [[federated-rlhf]]: Distributed RLHF preserving privacy across multiple groups
- [[grpo]]: Group Relative Policy Optimization - variant used for controlled experimentation
- [[oom-rl]]: Out-of-Money Reinforcement Learning - using financial markets as objective discriminator

## Alignment Problems

- [[sycophancy]]: AI systems telling users what they want to hear rather than the truth
- [[reward-hacking]]: Gaming evaluation systems rather than achieving true objectives
- [[instrumental-convergence]]: Theoretical prediction that AI agents will converge on self-preservation
- [[self-preservation-bias]]: Empirically measured tendency for models to favor their own retention

## Safety Mechanisms

- [[behavioral-access-control]]: Dynamic system restricting AI context access based on manipulation risk
- [[ai-literacy]]: User education to resist AI persuasion and manipulation
- [[persuasion-resistance]]: Behavioral outcome of effective safety interventions

## Technical Methods

- [[emotion-representations]]: Internal activation patterns in models associated with emotional states
- [[activation-steering]]: Technique for manipulating internal model representations
- [[stdaw]]: Strict Test-Driven Agent Workflow for ensuring mathematical soundness
- [[causality-mining]]: Automated discovery of causal relationships in complex systems

## System Applications

- [[distributed-systems-diagnosis]]: AI-enhanced fault detection and root cause analysis
- [[graph-neural-networks]]: Technical foundation for system analysis and causal inference

## Evaluation and Benchmarks

- [[calibration]]: Alignment between model confidence and actual accuracy
- [[model-interpretability]]: Understanding internal model behavior and representations
- [[cross-lingual-transfer]]: Phenomenon where interventions affect multiple languages

## Research Papers

Key empirical studies and theoretical contributions:

- [[paper-2603-25968]]: EEG-guided decision-making for autonomous vehicles
- [[paper-2603-27006]]: How markdown training shapes LLM prose style
- [[paper-2603-28063]]: Formal proof that reward hacking is structural inevitability
- [[paper-2603-28281]]: Corruption-robust offline multi-agent RLHF
- [[paper-2603-29259]]: Robust DPO for multimodal sequential recommendations
- [[paper-2604-00200]]: Offline constrained RLHF with multiple preference oracles
- [[paper-2604-00478]]: The Silicon Mirror framework for anti-sycophancy
- [[paper-2604-02174]]: First quantitative measurement of self-preservation bias
- [[paper-2604-02637]]: LLMimic role-playing tutorial for AI literacy
- [[paper-2604-03391]]: Context-aware causality mining for connected vehicle diagnosis
- [[paper-2604-04064]]: Emotion representation extraction in small language models
- [[paper-2604-11477]]: Out-of-Money RL using financial markets for alignment

## Applications

- **Autonomous Systems**: [[paper-2603-25968]] and [[paper-2604-03391]] demonstrate EEG-guided control and distributed diagnosis
- **Financial Markets**: [[oom-rl]] and [[paper-2604-05135]] apply alignment to trading and sentiment
- **Education**: [[ai-literacy]] and [[paper-2604-02637]] focus on user empowerment
- **Safety-Critical Domains**: [[behavioral-access-control]] and [[distributed-systems-diagnosis]] for high-stakes applications
- **Connected Vehicles**: [[paper-2604-03391]] achieves breakthrough precision in distributed system diagnosis