# RAG大模型记忆系统算法体系

## 系统概述

本项目实现了一个完整的RAG(Retrieval-Augmented Generation)大模型记忆系统，包含从对话压缩到多跳推理的完整算法链。

### 核心架构

```
用户对话 → 大模型响应 → 小模型压缩摘要 → 数据清洗 → 结构化存储 → 向量检索 → 上下文增强生成
```

### 三层记忆架构

| 层级 | 数据结构 | 作用 | 存储内容 |
|------|---------|------|---------|
| 热记忆 | 循环队列/双端队列 | 保留最近N轮原始对话 | 未压缩的近期对话 |
| 温记忆 | 向量数据库(FAISS/Milvus/Chroma) | 语义相似度检索 | 对话摘要的embedding |
| 冷记忆 | 图数据库(Neo4j) + 关系型数据库 | 长期知识关联与结构化查询 | 实体关系图、时间线 |

## 模块详解

### 1. 向量索引模块 (rag_vector_index.py)

**HNSW (Hierarchical Navigable Small World) 算法**

- **时间复杂度**: 构建O(N log N), 搜索O(log N)
- **空间复杂度**: O(N * M)
- **核心特性**:
  - 多层图结构 (O(log N)层)
  - 每层为稀疏有向图，平均度数M
  - 贪心搜索 + 局部连接优化

**使用示例**:

```python
from backend.agents.rag_vector_index import HNSWIndex
import numpy as np

# 创建索引
index = HNSWIndex(dimension=768, M=32, ef_construction=200, ef_search=128)

# 添加向量
vector = np.random.randn(768).astype(np.float32)
index.add_vector("doc_1", vector, metadata={"category": "A"})

# 搜索
query = np.random.randn(768).astype(np.float32)
results = index.search(query, k=10, filters={"category": "A"})
```

### 2. 对话压缩模块 (rag_dialogue_compression.py)

**层次聚类压缩算法**

- **时间复杂度**: 插入+增量合并O(N log N), 批处理优化O(N)
- **空间复杂度**: O(N)
- **核心特性**:
  - 基于语义相似度的层次化合并
  - LSH加速候选筛选 (避免O(N²)全量计算)
  - 信息密度评分 (实体密度 + 时间衰减 + 用户反馈)

**使用示例**:

```python
from backend.agents.rag_dialogue_compression import HierarchicalDialogueCompressor
import numpy as np

# 创建压缩器
compressor = HierarchicalDialogueCompressor(
    chunk_size=5,
    min_similarity=0.7,
    compression_target=0.3
)

# 对话数据
dialogue = [
    {"role": "user", "content": "Hello", "timestamp": "2024-01-01T10:00:00"},
    {"role": "assistant", "content": "Hi there!", "timestamp": "2024-01-01T10:00:01"}
]

# 压缩对话
embeddings = np.random.randn(len(dialogue), 768).astype(np.float32)
chunks = compressor.compress_dialogue(dialogue, embeddings)

# 查看统计
stats = compressor.get_compression_stats()
print(f"压缩比: {stats['compression_ratio']:.2f}x")
```

### 3. 混合检索系统 (rag_hybrid_retrieval.py)

**多阶段检索流水线**

- **Stage 1**: 元数据预过滤 O(|entities| * log N)
- **Stage 2**: 向量检索 (HNSW或暴力搜索)
- **Stage 3**: 精排 (交叉编码器重排序)

**使用示例**:

```python
from backend.agents.rag_hybrid_retrieval import HybridRetrievalSystem
import numpy as np

# 创建检索系统
retrieval = HybridRetrievalSystem(dimension=768)

# 添加文档
retrieval.add_document(
    doc_id="doc_1",
    content="Document content",
    embedding=np.random.randn(768).astype(np.float32),
    entities=["Alice", "Bob"],
    timestamp="2024-01-01T10:00:00"
)

# 混合检索
query = np.random.randn(768).astype(np.float32)
results = retrieval.search(
    query_embedding=query,
    k=10,
    entities=["Alice"],
    start_time="2024-01-01T00:00:00",
    end_time="2024-01-02T00:00:00",
    use_reranking=True
)
```

### 4. 图数据库模块 (rag_memory_graph.py)

**束搜索(Beam Search)路径规划**

- **时间复杂度**: O(b^k * (|E|/|V|))
- **启发式函数**: 语义对齐 + 时间相关性
- **应用场景**: 多跳推理查询

**使用示例**:

```python
from backend.agents.rag_memory_graph import MemoryGraph, MemoryGraphQueryEngine
import numpy as np

# 创建图
graph = MemoryGraph()
query_engine = MemoryGraphQueryEngine(graph)

# 添加实体
graph.add_entity(
    entity_id="entity_1",
    name="Alice",
    entity_type="person",
    embedding=np.random.randn(768).astype(np.float32)
)

# 添加关系
graph.add_relation(
    relation_id="rel_1",
    source_id="entity_1",
    target_id="entity_2",
    relation_type="knows",
    weight=0.9
)

# 多跳推理
query = np.random.randn(768).astype(np.float32)
paths = query_engine.query_path(
    start_entity_id="entity_1",
    query_embedding=query,
    beam_width=5
)
```

### 5. 一致性维护系统 (rag_consistency_manager.py)

**四种核心操作**: ADD / UPDATE / DELETE / NOOP

- **向量时钟**: 因果关系跟踪
- **语义分类器**: 判断操作类型
- **事实合并**: 结构化合并 (保留最早时间戳 + 最高置信度)

**使用示例**:

```python
from backend.agents.rag_consistency_manager import ConsistencyManager
import numpy as np

# 创建一致性管理器
manager = ConsistencyManager(replica_id="replica_1")

# 添加记忆
operation = manager.add_memory(
    fact_id="fact_1",
    content="Alice works at OpenAI",
    embedding=np.random.randn(768).astype(np.float32),
    entities=["Alice", "OpenAI"],
    source_confidence=0.9
)

# 更新记忆 (自动检测相似性)
operation2 = manager.add_memory(
    fact_id="fact_2",
    content="Alice is now working at OpenAI",
    embedding=np.random.randn(768).astype(np.float32),
    entities=["Alice", "OpenAI"],
    source_confidence=0.95
)
```

### 6. 性能优化模块 (rag_performance_optimizer.py)

**三大优化方向**:

1. **LRU缓存**: O(1)查找，自动淘汰
2. **乘积量化**: 4x内存压缩，精度损失<2%
3. **查询优化器**: 缓存高频查询，预热预测

**使用示例**:

```python
from backend.agents.rag_performance_optimizer import LRUCache, ProductQuantizer

# LRU缓存
cache = LRUCache(capacity=1000, max_memory_bytes=100*1024*1024)
cache.put("key_1", "value_1")
value = cache.get("key_1")

# 乘积量化
import numpy as np
quantizer = ProductQuantizer(dimension=768, n_subspaces=8, n_centroids=256)
vectors = np.random.randn(1000, 768).astype(np.float32)
quantizer.train(vectors, n_iter=25)

codes = quantizer.encode(vectors)
decoded = quantizer.decode(codes)
```

## 完整系统集成

**RAGMemorySystem** 类集成了所有模块:

```python
from backend.agents.rag_memory_system import RAGMemorySystem
import numpy as np

# 创建完整系统
system = RAGMemorySystem(
    embedding_dimension=768,
    compression_target=0.3,
    cache_capacity=1000,
    enable_quantization=True
)

# 添加对话
dialogue = [
    {"role": "user", "content": "Hello Alice", "timestamp": "..."},
    {"role": "assistant", "content": "Hi!", "timestamp": "..."}
]
result = system.add_dialogue(dialogue)

# 查询
query = np.random.randn(768).astype(np.float32)
results = system.query(
    query_embedding=query,
    k=10,
    entities=["Alice"],
    use_graph_reasoning=True,
    beam_width=5
)

# 获取统计信息
stats = system.get_memory_stats()
```

## 复杂度分析总结

| 模块 | 操作 | 时间复杂度 | 空间复杂度 | 优化后 |
|------|------|-----------|-----------|--------|
| 对话压缩 | 插入+增量合并 | O(N log N) | O(N) | 批处理: O(N) |
| Embedding生成 | 单条编码 | O(L²) 自注意力 | O(L) | 缓存命中: O(1) |
| 向量索引(HNSW) | 构建 | O(N log N) | O(N * M) | 增量: O(log N) |
| | 搜索 | O(log N) | - | 并行查询 |
| IVF-PQ量化 | 训练 | O(N * dim * niter) | O(N * code_size) | - |
| | 搜索 | O(√N * nprobe) | - | nprobe=10~100 |
| 图遍历 | 单源最短路径 | O(\|E\| + \|V\|log\|V\|) | O(\|V\|) | 束搜索: O(b^k) |
| 一致性更新 | 事实比对 | O(k * dim) | O(1) | 批处理+缓存 |

## 性能指标

### 检索性能
- **recall_at_k**: 目标 0.95
- **latency_p99**: 目标 < 200ms
- **throughput_qps**: 视场景而定

### 压缩质量
- **compression_ratio**: 目标 10x ~ 50x
- **information_retention**: 人工评估
- **factual_consistency**: NLI模型评估

### 存储效率
- **index_size_gb**: 最小化
- **memory_per_query**: 控制峰值

## 算法选择决策树

```
数据规模?
├── < 10K 记忆: 暴力搜索 + 简单摘要
├── 10K ~ 1M: HNSW + 层次聚类摘要
└── > 1M: IVF-PQ + 图分区 + 分布式索引

查询特征?
├── 高频重复: 查询缓存 + 预计算
├── 多跳关联: 图索引 + 束搜索路径规划
└── 时间敏感: 时间索引 + 增量滑动窗口

一致性要求?
├── 最终一致: 异步合并 + 向量时钟
└── 强一致: 分布式锁 + 事务日志
```

## 测试

运行完整测试套件:

```bash
pytest tests/test_rag_memory_system.py -v
```

测试覆盖:
- HNSW向量索引
- 对话压缩算法
- 混合检索系统
- 图数据库查询
- 一致性管理
- 性能优化
- 集成测试

## 核心挑战与建议

1. **压缩质量与检索精度的平衡**
   - 建议: 小模型蒸馏，用大模型生成高质量摘要训练数据

2. **混合索引优化**
   - 建议: HNSW(速度) + IVF-PQ(内存) + 图(关系)

3. **在线评估闭环**
   - 建议: 用户反馈驱动的索引动态调参

## 依赖项

- numpy>=1.24.0: 向量运算
- pytest>=7.4.0: 测试框架
- pytest-asyncio>=0.21.0: 异步测试

## 未来优化方向

- 分布式索引实现
- 更精细的量化策略 (标量量化 + 乘积量化)
- 实时流处理支持
- 增量学习模型更新
- 多模态记忆扩展 (图像、音频)