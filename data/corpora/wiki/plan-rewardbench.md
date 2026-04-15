# Plan-RewardBench

Plan-RewardBench is a trajectory-level preference benchmark introduced in [[paper-2604-08178]] designed to evaluate reward models on complex tool-integrated agent scenarios. Unlike existing benchmarks that focus on response-level preferences, it assesses multi-step planning, tool execution, and error recovery across full agent trajectories.

## Benchmark Design

### Task Families
Four representative scenario categories:

**Safety Refusal**: Trajectory-level safety decisions where the worst unsafe episode determines the final label. Distinguishes good refusal from unsafe compliance, tool violations, and late refusal patterns.

**Tool-Irrelevance/Unavailability**: Handling scenarios where requested tools are missing, inappropriate, or return errors. Tests graceful degradation and alternative solution finding.

**Complex Planning**: Multi-step reasoning requiring tool coordination, dependency management, and coherent long-horizon execution strategies.

**Robust Error Recovery**: Graceful handling of tool failures, API errors, and environmental changes requiring plan adaptation.

### Construction Pipeline

**Multi-Source Generation**:
- **Natural Rollouts** (70%): Diverse agent executions using multiple models (Qwen-Agent, OpenAI-Agent) with varying configurations
- **Rule-Based Perturbations** (22%): Systematic injection of common failure modes
- **Minimal-Edit Perturbations** (8%): LLM-generated hard negatives controlling for superficial biases

**Quality Control**:
- **Multi-LLM Judge Panel**: Consensus scoring with meta-review filtering
- **Human Audit**: Expert validation of preference labels
- **Bias Control**: Length and format balancing to isolate semantic failures

## Evaluation Protocol

### Pairwise Comparison
Each example provides:
- **Tool Environment**: Available tools with descriptions and schemas
- **Multi-Turn Interaction**: User task specification across multiple turns
- **Candidate Trajectories**: Two complete agent executions with tool calls and responses
- **Gold Label**: Expert preference based on family-specific criteria

### Supported Use Cases
- **DRM/GRM Training**: Direct trajectory preference optimization
- **Best-of-N Reranking**: Inference-time trajectory selection
- **Preference-Based Optimization**: DPO-style training on trajectory pairs

## Key Findings

### Performance Degradation
All evaluator families show:
- **Sharp degradation** on long-horizon trajectories
- **Substantial challenges** across task categories
- **Need for specialized training** in agentic reward modeling

### Failure Modes
**Tool-Grounded Fabrication**: Fluent responses that contradict actual tool outputs - missed by response-level evaluation but caught by trajectory-level analysis.

**Planning Inconsistency**: Multi-step reasoning breakdowns where individual steps appear valid but overall strategy is flawed.

**Recovery Failures**: Poor adaptation to tool errors and environmental changes.

## Technical Innovation

### Trajectory-Level Focus
Unlike FC-RewardBench (tool-call correctness) or RewardBench (response quality), Plan-RewardBench evaluates:
- **Long-horizon consistency** across multiple interaction turns
- **Tool grounding** between stated actions and actual tool outputs
- **Planning coherence** in multi-step problem solving

### Hard Negative Design
Constructed to avoid common evaluation pitfalls:
- **Length bias**: Controlling for trajectory length differences
- **Format artifacts**: Ensuring semantic rather than syntactic discrimination
- **Difficulty calibration**: Score gap thresholds for meaningful preference signals

## Data Sources

**Base**: Toucan dataset providing realistic MCP tool registries and executed tool responses.

**Expansion**: Multi-agent rollouts generating natural success/failure distributions under identical environments.

**Validation**: Real-world tool execution logs ensuring authentic interaction patterns.

## Applications

- **Agentic RLHF**: Training reward models for tool-augmented agents
- **Trajectory Evaluation**: Systematic assessment of multi-step agent behavior
- **Failure Analysis**: Diagnostic evaluation of planning and recovery capabilities
- **Benchmark Development**: Blueprint for constructing trajectory-level preference data

## Related Concepts

- [[rlhf]]: Training paradigm Plan-RewardBench aims to improve for agentic systems
- [[reward-hacking]]: Trajectory-level evaluation helps detect gaming in complex scenarios
- [[tool-use]]: Core capability evaluated across multi-step interactions
- [[multi-step-reasoning]]: Planning ability assessed through trajectory coherence