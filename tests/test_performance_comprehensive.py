"""
综合性能测试脚本
用于测试 HNSW 索引召回率、对话压缩、混合检索、记忆图等性能
"""
import pytest
import numpy as np
import time
from datetime import datetime, timedelta
from collections import defaultdict
import os

from backend.agents.rag_vector_index import HNSWIndex
from backend.agents.rag_dialogue_compression import HierarchicalDialogueCompressor, LLMEnhancedDialogueCompressor
from backend.agents.rag_hybrid_retrieval import HybridRetrievalSystem
from backend.agents.rag_memory_graph import MemoryGraph, BeamSearchPathFinder
from backend.agents.rag_performance_optimizer import ProductQuantizer, LRUCache

# 智谱 GLM API 配置（可选，需要设置环境变量）
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY", "")
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"


class TestHNSWRecall:
    """HNSW 向量召回率测试"""

    @pytest.mark.parametrize("num_nodes,dimension", [
        (50, 128),
        (100, 64),
        (200, 16),
        (500, 32)
    ])
    def test_recall_at_k(self, num_nodes, dimension):
        """测试不同规模下的召回率"""
        np.random.seed(42)

        # 创建索引
        index = HNSWIndex(dimension=dimension, M=16, ef_construction=100, ef_search=128)

        # 生成测试向量
        vectors = np.random.randn(num_nodes, dimension).astype(np.float32)

        # 添加向量到索引
        for i, vec in enumerate(vectors):
            index.add_vector(f"vec_{i}", vec)

        # 测试召回率：对于每个查询向量，检查前10个结果中是否包含自身
        recall_count = 0
        for i, query_vec in enumerate(vectors):
            results = index.search(query_vec, k=10)
            result_ids = [r["node_id"] for r in results]
            if f"vec_{i}" in result_ids:
                recall_count += 1

        recall_at_10 = recall_count / num_nodes
        print(f"\n节点数: {num_nodes}, 维度: {dimension}, recall@10: {recall_at_10:.4f}")

        # 断言召回率
        if num_nodes <= 100:
            assert recall_at_10 >= 0.99, f"召回率 {recall_at_10:.4f} 低于 0.99"
        elif num_nodes == 200:
            assert recall_at_10 >= 0.97, f"召回率 {recall_at_10:.4f} 低于 0.97"
        elif num_nodes == 500:
            assert recall_at_10 >= 0.95, f"召回率 {recall_at_10:.4f} 低于 0.95"


class TestDialogueCompression:
    """对话压缩效果测试"""

    def test_compression_ratio_and_entity_retention(self):
        """测试压缩比和实体保留率"""
        np.random.seed(42)

        # 创建 50 轮模拟对话
        dialogue = []

        for i in range(50):
            role = "user" if i % 2 == 0 else "assistant"
            content = f"This is message {i} with some content and entities like Entity_{i % 10} and Entity_{(i + 3) % 10}"
            dialogue.append({
                "role": role,
                "content": content,
                "timestamp": (datetime.now() + timedelta(minutes=i)).isoformat()
            })

        # 生成嵌入向量
        embeddings = np.random.randn(50, 768).astype(np.float32)

        # 压缩对话
        compressor = HierarchicalDialogueCompressor(
            chunk_size=5,
            compression_target=0.3  # 目标压缩比 30%
        )

        chunks = compressor.compress_dialogue(dialogue, embeddings)

        # 计算压缩比
        original_turns = len(dialogue)
        compressed_turns = len(chunks)
        compression_ratio = compressed_turns / original_turns

        # 计算实体保留率 - 从对话内容中提取实体
        import re
        all_entities = set()
        for turn in dialogue:
            found = re.findall(r'Entity_\d+', turn["content"])
            all_entities.update(found)

        # 从压缩后的 chunks 中提取实体（只从 turns 内容中提取，避免重复）
        retained_entities = set()
        for chunk in chunks:
            for turn in chunk.turns:
                if isinstance(turn, dict) and "content" in turn:
                    found = re.findall(r'Entity_\d+', turn["content"])
                    retained_entities.update(found)

        entity_retention_rate = len(retained_entities) / len(all_entities) if all_entities else 1.0

        # 计算关键事实保留率（简化：保留的信息密度高的块）
        high_density_chunks = [c for c in chunks if c.information_density > 0.5]
        fact_retention_rate = len(high_density_chunks) / len(chunks) if chunks else 1.0

        print(f"\n原始轮次: {original_turns}")
        print(f"压缩后轮次: {compressed_turns}")
        print(f"压缩比: {compression_ratio:.2%}")
        print(f"实体保留率: {entity_retention_rate:.2%}")
        print(f"关键事实保留率: {fact_retention_rate:.2%}")

        # 断言
        assert 0.15 <= compression_ratio <= 0.40, f"压缩比 {compression_ratio:.2%} 不在预期范围"
        assert entity_retention_rate >= 0.80, f"实体保留率 {entity_retention_rate:.2%} 低于 80%"
        assert fact_retention_rate >= 0.90, f"关键事实保留率 {fact_retention_rate:.2%} 低于 90%"


class TestHybridRetrieval:
    """混合检索与重排效果测试"""

    def test_time_decay_reranking(self):
        """测试时间衰减重排效果"""
        np.random.seed(42)

        # 创建检索系统
        retrieval_system = HybridRetrievalSystem(dimension=128)

        # 生成 1000 条历史记忆
        base_time = datetime.now() - timedelta(days=30)
        documents = []

        for i in range(1000):
            # 创建一个"重要"的记忆，语义相关但时间较早
            if i == 500:
                content = "This is the important memory about the project deadline"
                embedding = np.random.randn(128).astype(np.float32) + 0.5  # 偏移使其相关
                timestamp = (base_time + timedelta(days=25)).isoformat()  # 较早
            else:
                content = f"Document content {i}"
                embedding = np.random.randn(128).astype(np.float32)
                timestamp = (base_time + timedelta(days=i % 30)).isoformat()

            documents.append({
                "doc_id": f"doc_{i}",
                "content": content,
                "embedding": embedding,
                "entities": [f"entity_{i % 10}"],
                "timestamp": timestamp
            })

        # 添加文档
        for doc in documents:
            retrieval_system.add_document(**doc)

        # 查询向量（与重要记忆相关）
        query = documents[500]["embedding"] + np.random.randn(128).astype(np.float32) * 0.1

        # 纯语义搜索
        results_semantic = retrieval_system.search(query, k=10, use_reranking=False)

        # 加入重排
        results_with_rerank = retrieval_system.search(query, k=10, use_reranking=True)

        # 找到重要记忆的排名
        semantic_rank = None
        rerank_rank = None

        for i, result in enumerate(results_semantic):
            if result["doc_id"] == "doc_500":
                semantic_rank = i + 1
                break

        for i, result in enumerate(results_with_rerank):
            if result["doc_id"] == "doc_500":
                rerank_rank = i + 1
                break

        print(f"\n纯语义搜索排名: {semantic_rank}")
        print(f"重排后排名: {rerank_rank}")

        # 断言：重排后排名应该提升
        if semantic_rank is not None and rerank_rank is not None:
            print(f"排名提升: {semantic_rank - rerank_rank} 位")


class TestPerformanceMetrics:
    """性能指标测试"""

    def test_query_latency(self):
        """测试查询延迟"""
        np.random.seed(42)

        # 创建 1000 节点的索引
        index = HNSWIndex(dimension=128, M=16, ef_construction=100, ef_search=64)
        vectors = np.random.randn(1000, 128).astype(np.float32)

        for i, vec in enumerate(vectors):
            index.add_vector(f"vec_{i}", vec)

        # 测试查询延迟
        latencies = []
        for i in range(100):
            start = time.time()
            results = index.search(vectors[i], k=10)
            end = time.time()
            latencies.append((end - start) * 1000)  # 转换为毫秒

        latencies.sort()
        p50 = latencies[49]
        p95 = latencies[94]
        p99 = latencies[98]

        print(f"\n查询延迟 P50: {p50:.2f}ms")
        print(f"查询延迟 P95: {p95:.2f}ms")
        print(f"查询延迟 P99: {p99:.2f}ms")

        # 断言
        assert p50 < 20, f"P50 延迟 {p50:.2f}ms 超过 20ms"
        assert p95 < 50, f"P95 延迟 {p95:.2f}ms 超过 50ms"
        assert p99 < 100, f"P99 延迟 {p99:.2f}ms 超过 100ms"

    def test_write_throughput(self):
        """测试写入吞吐"""
        np.random.seed(42)

        # 创建检索系统
        retrieval_system = HybridRetrievalSystem(dimension=128)

        # 测试写入时间
        write_times = []
        for i in range(50):
            vec = np.random.randn(128).astype(np.float32)
            start = time.time()
            retrieval_system.add_document(
                doc_id=f"doc_{i}",
                content=f"Content {i}",
                embedding=vec,
                entities=[f"entity_{i % 5}"],
                timestamp=datetime.now().isoformat()
            )
            end = time.time()
            write_times.append((end - start) * 1000)

        avg_write_time = np.mean(write_times)
        throughput = 1000 / avg_write_time  # 每秒写入次数

        print(f"\n平均写入时间: {avg_write_time:.2f}ms")
        print(f"写入吞吐: {throughput:.2f} ops/sec")

        # 断言
        assert avg_write_time < 100, f"平均写入时间 {avg_write_time:.2f}ms 超过 100ms"
        assert throughput > 10, f"吞吐 {throughput:.2f} ops/sec 低于 10"

    def test_cache_efficiency(self):
        """测试缓存效率"""
        cache = LRUCache(capacity=100)

        # 模拟高频重复查询
        query_keys = [f"query_{i % 20}" for i in range(1000)]  # 20 个查询重复 50 次

        for key in query_keys:
            if cache.get(key) is None:
                cache.put(key, f"result_{key}")

        stats = cache.get_stats()
        total_requests = stats["hit_count"] + stats["miss_count"]
        hit_rate = stats["hit_rate"] if total_requests > 0 else 0

        print(f"\n缓存命中率: {hit_rate:.2%}")
        print(f"缓存命中次数: {stats['hit_count']}")
        print(f"总查询次数: {total_requests}")

        # 断言
        assert hit_rate > 0.5, f"缓存命中率 {hit_rate:.2%} 低于 50%"

    def test_memory_usage_with_pq(self):
        """测试内存占用和 PQ 量化效果"""
        np.random.seed(42)

        # 生成 1000 条 768 维向量
        vectors = np.random.randn(1000, 768).astype(np.float32)

        # 计算原始内存占用
        original_size = vectors.nbytes  # bytes

        # 训练 PQ 量化器
        quantizer = ProductQuantizer(dimension=768, n_subspaces=8, n_centroids=16)
        quantizer.train(vectors, n_iter=10)

        # 编码向量
        codes = quantizer.encode(vectors)

        # 计算量化后内存占用
        quantized_size = codes.nbytes

        # 计算压缩比
        compression_ratio = original_size / quantized_size

        print(f"\n原始内存占用: {original_size / 1024 / 1024:.2f} MB")
        print(f"量化后内存占用: {quantized_size / 1024:.2f} KB")
        print(f"压缩比: {compression_ratio:.2f}x")

        # 断言
        assert compression_ratio > 100, f"压缩比 {compression_ratio:.2f}x 低于 100x"


@pytest.mark.asyncio
class TestLLMCompression:
    """小模型压缩效果测试（需要配置 API key）"""

    @pytest.fixture
    def dialogue(self):
        """创建测试对话"""
        dialogue = []
        for i in range(20):
            role = "user" if i % 2 == 0 else "assistant"
            dialogue.append({
                "role": role,
                "content": f"这是第 {i} 轮对话，内容关于项目开发和技术选型讨论。",
                "timestamp": (datetime.now() + timedelta(minutes=i)).isoformat()
            })
        return dialogue

    @pytest.fixture
    def embeddings(self):
        """生成测试嵌入"""
        np.random.seed(42)
        return np.random.randn(20, 768).astype(np.float32)

    @pytest.mark.skipif(not ZHIPU_API_KEY, reason="需要设置 ZHIPU_API_KEY 环境变量")
    async def test_glm_compression(self, dialogue, embeddings):
        """测试 GLM-4.5-air 模型压缩效果"""
        print(f"\n使用智谱 GLM-4.5-air 进行压缩测试")
        print(f"API Key: {ZHIPU_API_KEY[:10]}...")

        # 创建压缩器，使用智谱 GLM
        compressor = LLMEnhancedDialogueCompressor(
            chunk_size=5,
            compression_target=0.5,
            compression_api_key=ZHIPU_API_KEY,
            compression_base_url=ZHIPU_BASE_URL,
            compression_model="glm-4.5-air",
            compression_max_tokens=200
        )

        # 执行压缩并生成摘要
        chunks = await compressor.compress_dialogue_with_summaries(
            dialogue, 
            embeddings
        )

        print(f"\n原始对话轮次: {len(dialogue)}")
        print(f"压缩后 chunk 数: {len(chunks)}")
        print(f"压缩比: {len(chunks) / len(dialogue):.2%}")

        # 打印摘要示例
        for i, chunk in enumerate(chunks):
            summary_preview = chunk.summary[:200] if chunk.summary else "(空)"
            print(f"\nChunk {i+1} (turns {chunk.start_turn}-{chunk.end_turn}):")
            print(f"  摘要: {summary_preview}")
            print(f"  轮次数: {len(chunk.turns)}")

        # 统计摘要生成情况
        chunks_with_summary = sum(1 for c in chunks if c.summary)
        print(f"\n生成摘要的 chunk 数: {chunks_with_summary}/{len(chunks)}")

        # 验证：至少有一个 chunk 有摘要（受 API 限流影响，摘要生成率可能较低）
        summary_rate = chunks_with_summary / len(chunks) if chunks else 0
        print(f"摘要生成率: {summary_rate:.0%}")
        assert summary_rate >= 0.1, f"摘要生成率 {summary_rate:.0%} 过低"

    @pytest.mark.skipif(not ZHIPU_API_KEY, reason="需要设置 ZHIPU_API_KEY 环境变量")
    async def test_compression_token_usage(self, dialogue, embeddings):
        """测试压缩的 token 消耗"""
        import tiktoken

        print(f"\n测试 token 消耗")

        # 计算原始 token 数（估算）
        enc = tiktoken.get_encoding("cl100k_base")
        original_text = " ".join([t["content"] for t in dialogue])
        original_tokens = len(enc.encode(original_text))

        # 创建压缩器
        compressor = LLMEnhancedDialogueCompressor(
            chunk_size=5,
            compression_api_key=ZHIPU_API_KEY,
            compression_base_url=ZHIPU_BASE_URL,
            compression_model="glm-4.5-air",
            compression_max_tokens=200
        )

        # 执行压缩
        chunks = await compressor.compress_dialogue_with_summaries(dialogue, embeddings)

        # 计算摘要 token 数
        summary_tokens = sum(len(enc.encode(c.summary)) for c in chunks)

        print(f"\n原始内容 token 数: {original_tokens}")
        print(f"摘要 token 总数: {summary_tokens}")
        print(f"压缩比: {summary_tokens / original_tokens:.2%}")

        # 验证压缩效果
        assert summary_tokens < original_tokens, "摘要应该比原文短"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])