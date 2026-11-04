# AgentDB Learning Plugins — Detailed Reference & Extended Examples


**Type**: Value-Based RL (Off-Policy)
**Best For**: Discrete action spaces, sample efficiency
**Strengths**: Proven, simple, works well for small$medium problems

```bash
npx agentdb@latest create-plugin -t q-learning -n q-agent
```

**Use Cases**:
- Grid worlds, board games
- Navigation tasks
- Resource allocation
- Discrete decision-making

**Configuration**:
```json
{
  "algorithm": "q-learning",
  "learning_rate": 0.001,
  "gamma": 0.99,
  "epsilon": 0.1,
  "epsilon_decay": 0.995
}
```

### 3. SARSA

**Type**: Value-Based RL (On-Policy)
**Best For**: Safe exploration, risk-sensitive tasks
**Strengths**: More conservative than Q-Learning, better for safety

```bash
npx agentdb@latest create-plugin -t sarsa -n sarsa-agent
```

**Use Cases**:
- Safety-critical applications
- Risk-sensitive decision-making
- Online learning with exploration

**Configuration**:
```json
{
  "algorithm": "sarsa",
  "learning_rate": 0.001,
  "gamma": 0.99,
  "epsilon": 0.1
}
```

### 4. Actor-Critic

**Type**: Policy Gradient with Value Baseline
**Best For**: Continuous actions, variance reduction
**Strengths**: Stable, works for continuous$discrete actions

```bash
npx agentdb@latest create-plugin -t actor-critic -n ac-agent
```

**Use Cases**:
- Continuous control (robotics, simulations)
- Complex action spaces
- Multi-agent coordination

**Configuration**:
```json
{
  "algorithm": "actor-critic",
  "actor_lr": 0.001,
  "critic_lr": 0.002,
  "gamma": 0.99,
  "entropy_coef": 0.01
}
```

### 5. Active Learning

**Type**: Query-Based Learning
**Best For**: Label-efficient learning, human-in-the-loop
**Strengths**: Minimizes labeling cost, focuses on uncertain samples

**Use Cases**:
- Human feedback incorporation
- Label-efficient training
- Uncertainty sampling
- Annotation cost reduction

### 6. Adversarial Training

**Type**: Robustness Enhancement
**Best For**: Safety, robustness to perturbations
**Strengths**: Improves model robustness, adversarial defense

**Use Cases**:
- Security applications
- Robust decision-making
- Adversarial defense
- Safety testing

### 7. Curriculum Learning

**Type**: Progressive Difficulty Training
**Best For**: Complex tasks, faster convergence
**Strengths**: Stable learning, faster convergence on hard tasks

**Use Cases**:
- Complex multi-stage tasks
- Hard exploration problems
- Skill composition
- Transfer learning

### 8. Federated Learning

**Type**: Distributed Learning
**Best For**: Privacy, distributed data
**Strengths**: Privacy-preserving, scalable

**Use Cases**:
- Multi-agent systems
- Privacy-sensitive data
- Distributed training
- Collaborative learning

### 9. Multi-Task Learning

**Type**: Transfer Learning
**Best For**: Related tasks, knowledge sharing
**Strengths**: Faster learning on new tasks, better generalization

**Use Cases**:
- Task families
- Transfer learning
- Domain adaptation
- Meta-learning

---

## Training Workflow

### 1. Collect Experiences

```typescript
// Store experiences during agent execution
for (let i = 0; i < numEpisodes; i++) {
  const episode = runEpisode();

  for (const step of episode.steps) {
    await adapter.insertPattern({
      id: '',
      type: 'experience',
      domain: 'task-domain',
      pattern_data: JSON.stringify({
        embedding: await computeEmbedding(JSON.stringify(step)),
        pattern: {
          state: step.state,
          action: step.action,
          reward: step.reward,
          next_state: step.next_state,
          done: step.done
        }
      }),
      confidence: step.reward > 0 ? 0.9 : 0.5,
      usage_count: 1,
      success_count: step.reward > 0 ? 1 : 0,
      created_at: Date.now(),
      last_used: Date.now(),
    });
  }
}
```

### 2. Train Model

```typescript
// Train on collected experiences
const trainingMetrics = await adapter.train({
  epochs: 100,
  batchSize: 64,
  learningRate: 0.001,
  validationSplit: 0.2,
});

console.log('Training Metrics:', trainingMetrics);
// {
//   loss: 0.023,
//   valLoss: 0.028,
//   duration: 1523,
//   epochs: 100
// }
```

### 3. Evaluate Performance

```typescript
// Retrieve similar successful experiences
const testQuery = await computeEmbedding(JSON.stringify(testState));
const result = await adapter.retrieveWithReasoning(testQuery, {
  domain: 'task-domain',
  k: 10,
  synthesizeContext: true,
});

// Evaluate action quality
const suggestedAction = result.memories[0].pattern.action;
const confidence = result.memories[0].similarity;

console.log('Suggested Action:', suggestedAction);
console.log('Confidence:', confidence);
```

---

## Advanced Training Techniques

### Experience Replay

```typescript
// Store experiences in buffer
const replayBuffer = [];

// Sample random batch for training
const batch = sampleRandomBatch(replayBuffer, batchSize: 32);

// Train on batch
await adapter.train({
  data: batch,
  epochs: 1,
  batchSize: 32,
});
```

### Prioritized Experience Replay

```typescript
// Store experiences with priority (TD error)
await adapter.insertPattern({
  // ... standard fields
  confidence: tdError,  // Use TD error as confidence$priority
  // ...
});

// Retrieve high-priority experiences
const highPriority = await adapter.retrieveWithReasoning(queryEmbedding, {
  domain: 'task-domain',
  k: 32,
  minConfidence: 0.7,  // Only high TD-error experiences
});
```

### Multi-Agent Training

```typescript
// Collect experiences from multiple agents
for (const agent of agents) {
  const experience = await agent.step();

  await adapter.insertPattern({
    // ... store experience with agent ID
    domain: `multi-agent/${agent.id}`,
  });
}

// Train shared model
await adapter.train({
  epochs: 50,
  batchSize: 64,
});
```

---

## Performance Optimization

### Batch Training

```typescript
// Collect batch of experiences
const experiences = collectBatch(size: 1000);

// Batch insert (500x faster)
for (const exp of experiences) {
  await adapter.insertPattern({ /* ... */ });
}

// Train on batch
await adapter.train({
  epochs: 10,
  batchSize: 128,  // Larger batch for efficiency
});
```

### Incremental Learning

```typescript
// Train incrementally as new data arrives
setInterval(async () => {
  const newExperiences = getNewExperiences();

  if (newExperiences.length > 100) {
    await adapter.train({
      epochs: 5,
      batchSize: 32,
    });
  }
}, 60000);  // Every minute
```

---

## Integration with Reasoning Agents

Combine learning with reasoning for better performance:

```typescript
// Train learning model
await adapter.train({ epochs: 50, batchSize: 32 });

// Use reasoning agents for inference
const result = await adapter.retrieveWithReasoning(queryEmbedding, {
  domain: 'decision-making',
  k: 10,
  useMMR: true,              // Diverse experiences
  synthesizeContext: true,    // Rich context
  optimizeMemory: true,       // Consolidate patterns
});

// Make decision based on learned experiences + reasoning
const decision = result.context.suggestedAction;
const confidence = result.memories[0].similarity;
```

---

## CLI Operations

```bash
# Create plugin
npx agentdb@latest create-plugin -t decision-transformer -n my-plugin

# List plugins
npx agentdb@latest list-plugins

# Get plugin info
npx agentdb@latest plugin-info my-plugin

# List templates
npx agentdb@latest list-templates
```

---

## Troubleshooting

### Issue: Training not converging
```typescript
// Reduce learning rate
await adapter.train({
  epochs: 100,
  batchSize: 32,
  learningRate: 0.0001,  // Lower learning rate
});
```

### Issue: Overfitting
```typescript
// Use validation split
await adapter.train({
  epochs: 50,
  batchSize: 64,
  validationSplit: 0.2,  // 20% validation
});

// Enable memory optimization
await adapter.retrieveWithReasoning(queryEmbedding, {
  optimizeMemory: true,  // Consolidate, reduce overfitting
});
```

### Issue: Slow training
```bash
# Enable quantization for faster inference
# Use binary quantization (32x faster)
```

---

## Learn More

- **Algorithm Papers**: See docs$algorithms/ for detailed papers
- **GitHub**: https:/$github.com$ruvnet$agentic-flow$tree$main$packages$agentdb
- **MCP Integration**: `npx agentdb@latest mcp`
- **Website**: https:/$agentdb.ruv.io

---

**Category**: Machine Learning / Reinforcement Learning
**Difficulty**: Intermediate to Advanced
**Estimated Time**: 30-60 minutes
