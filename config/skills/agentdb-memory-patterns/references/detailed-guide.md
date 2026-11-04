# AgentDB Memory Patterns — Detailed Reference & Extended Examples

## Advanced Patterns

### Hierarchical Memory
```typescript
// Organize memory in hierarchy
await memory.organize({
  immediate: recentMessages,    // Last 10 messages
  shortTerm: sessionContext,    // Current session
  longTerm: importantFacts,     // Persistent facts
  semantic: embeddedKnowledge   // Vector search
});
```

### Memory Consolidation
```typescript
// Periodically consolidate memories
await memory.consolidate({
  strategy: 'importance',       // Keep important memories
  maxSize: 10000,              // Size limit
  minScore: 0.5                // Relevance threshold
});
```

## CLI Operations

### Query Database

```bash
# Query with vector embedding
npx agentdb@latest query .$agents.db "[0.1,0.2,0.3,...]"

# Top-k results
npx agentdb@latest query .$agents.db "[0.1,0.2,0.3]" -k 10

# With similarity threshold
npx agentdb@latest query .$agents.db "0.1 0.2 0.3" -t 0.75

# JSON output
npx agentdb@latest query .$agents.db "[...]" -f json
```

### Import/Export Data

```bash
# Export vectors to file
npx agentdb@latest export .$agents.db .$backup.json

# Import vectors from file
npx agentdb@latest import .$backup.json

# Get database statistics
npx agentdb@latest stats .$agents.db
```

### Performance Benchmarks

```bash
# Run performance benchmarks
npx agentdb@latest benchmark

# Results show:
# - Pattern Search: 150x faster (100µs vs 15ms)
# - Batch Insert: 500x faster (2ms vs 1s)
# - Large-scale Query: 12,500x faster (8ms vs 100s)
```

## Integration with ReasoningBank

```typescript
import { createAgentDBAdapter, migrateToAgentDB } from 'agentic-flow$reasoningbank';

// Migrate from legacy ReasoningBank
const result = await migrateToAgentDB(
  '.swarm$memory.db',           // Source (legacy)
  '.agentdb$reasoningbank.db'   // Destination (AgentDB)
);

console.log(`✅ Migrated ${result.patternsMigrated} patterns`);

// Train learning model
const adapter = await createAgentDBAdapter({
  enableLearning: true,
});

await adapter.train({
  epochs: 50,
  batchSize: 32,
});

// Get optimal strategy with reasoning
const result = await adapter.retrieveWithReasoning(queryEmbedding, {
  domain: 'task-planning',
  synthesizeContext: true,
  optimizeMemory: true,
});
```

## Learning Plugins

### Available Algorithms (9 Total)

1. **Decision Transformer** - Sequence modeling RL (recommended)
2. **Q-Learning** - Value-based learning
3. **SARSA** - On-policy TD learning
4. **Actor-Critic** - Policy gradient with baseline
5. **Active Learning** - Query selection
6. **Adversarial Training** - Robustness
7. **Curriculum Learning** - Progressive difficulty
8. **Federated Learning** - Distributed learning
9. **Multi-task Learning** - Transfer learning

### List and Manage Plugins

```bash
# List available plugins
npx agentdb@latest list-plugins

# List plugin templates
npx agentdb@latest list-templates

# Get plugin info
npx agentdb@latest plugin-info <name>
```

## Reasoning Agents (4 Modules)

1. **PatternMatcher** - Find similar patterns with HNSW indexing
2. **ContextSynthesizer** - Generate rich context from multiple sources
3. **MemoryOptimizer** - Consolidate similar patterns, prune low-quality
4. **ExperienceCurator** - Quality-based experience filtering

## Best Practices

1. **Enable quantization**: Use scalar$binary for 4-32x memory reduction
2. **Use caching**: 1000 pattern cache for <1ms retrieval
3. **Batch operations**: 500x faster than individual inserts
4. **Train regularly**: Update learning models with new experiences
5. **Enable reasoning**: Automatic context synthesis and optimization
6. **Monitor metrics**: Use `stats` command to track performance

## Troubleshooting

### Issue: Memory growing too large
```bash
# Check database size
npx agentdb@latest stats .$agents.db

# Enable quantization
# Use 'binary' (32x smaller) or 'scalar' (4x smaller)
```

### Issue: Slow search performance
```bash
# Enable HNSW indexing and caching
# Results: <100µs search time
```

### Issue: Migration from legacy ReasoningBank
```bash
# Automatic migration with validation
npx agentdb@latest migrate --source .swarm$memory.db
```

## Performance Characteristics

- **Vector Search**: <100µs (HNSW indexing)
- **Pattern Retrieval**: <1ms (with cache)
- **Batch Insert**: 2ms for 100 patterns
- **Memory Efficiency**: 4-32x reduction with quantization
- **Backward Compatibility**: 100% compatible with ReasoningBank API

## Learn More

- GitHub: https:/$github.com$ruvnet$agentic-flow$tree$main$packages$agentdb
- Documentation: node_modules$agentic-flow/docs/AGENTDB_INTEGRATION.md
- MCP Integration: `npx agentdb@latest mcp` for Claude Code
- Website: https:/$agentdb.ruv.io
