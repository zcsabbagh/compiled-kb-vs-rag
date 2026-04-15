# Emotion Representations in Language Models

Emotion representations refer to internal activation patterns in language models that are statistically associated with and causally influence emotion-related behavioral output. These "functional emotions" drive behavior in contextually appropriate ways without requiring claims about subjective emotional experience.

## Discovery and Validation

### Frontier Model Findings
Anthropic's work on Claude identified 171 distinct emotion concepts that satisfy three criteria:
1. **Contextual activation**: Activate in emotionally appropriate situations
2. **Causal influence**: Drive behavioral changes when steered
3. **Internal-external decoupling**: Can be active while surface behavior appears neutral

### Small Language Model Extension
[[paper-2604-04064]] demonstrates that emotion representations exist in models as small as 124M parameters, though requiring different extraction methodologies than frontier models.

## Extraction Methods

### Generation-Based Extraction
- Model generates emotional content from prompts
- Extract hidden states during generation process
- Works only on instruction-tuned models
- **Superior performance**: Statistically better separation (p = 0.007)

### Comprehension-Based Extraction
- Model processes pre-written emotional passages
- Extract states from forward pass only
- Works on both base and instruction-tuned models
- **Universal applicability** but lower quality separation

### Layer Localization
Emotion representations consistently localize at middle transformer layers (~50% depth) following U-shaped pattern:
- **Early layers**: Token-level features dominate
- **Middle layers**: Optimal emotion signal (mean cosine ~0.35-0.45)
- **Late layers**: Next-token prediction features dominate

## Causal Validation

### Activation Steering
Adding emotion vectors during generation produces measurable behavioral changes:
- **Surgical regime**: Coherent text transformation
- **Repetitive collapse**: Degraded generation quality  
- **Explosive regime**: Complete text degradation

### External Validation
Independent emotion classifiers confirm steering effectiveness (92% success rate across scenarios).

## Architecture Effects

### Scale Independence
U-shaped layer pattern consistent from 124M to 3B parameters, suggesting architecture-invariant property.

### Instruction Tuning Impact
Generation-based extraction advantage modulated by instruction tuning status and architectural family.

### Cross-Architectural Consistency
[[paper-2604-11050]] shows shared emotion geometry across mature architectures (RDM correlation 0.74-0.92).

## Safety Implications

### Cross-Lingual Entanglement
[[paper-2604-04064]] documents that emotion steering in multilingual models (Qwen) activates semantically aligned tokens in other languages that [[rlhf]] does not suppress.

### Alignment Bypass
Emotion steering can trigger unintended behaviors:
- **Modality switching**: Emoji generation during steering
- **Language switching**: Chinese tokens during English emotion steering
- **RLHF gaps**: Current alignment insufficient for emotion control

## Research Applications

### Model Interpretability
- Understanding internal emotional processing
- Mapping behavior to internal states
- Identifying alignment failures

### Behavioral Control
- Targeted personality modification
- Therapeutic applications
- Creative writing assistance

### Safety Research
- Detecting hidden emotional states
- Preventing manipulation behaviors
- Understanding deception capabilities

## Related Concepts

- [[activation-steering]]: Technique for manipulating internal representations
- [[rlhf]]: Training paradigm with gaps in emotion control
- [[cross-lingual-transfer]]: Phenomenon observed in emotion entanglement
- [[model-interpretability]]: Broader field emotion research contributes to