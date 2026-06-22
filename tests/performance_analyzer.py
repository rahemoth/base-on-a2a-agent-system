"""
性能分析脚本
运行综合测试并生成性能报告
"""
import pytest
import numpy as np
import time
from datetime import datetime, timedelta
from collections import defaultdict

from backend.agents.rag_vector_index import HNSWIndex
from backend.agents.rag_dialogue_compression import HierarchicalDialogueCompressor
from backend.agents.rag_hybrid_retrieval import HybridRetrievalSystem
from backend.agents.rag_memory_graph import MemoryGraph, BeamSearchPathFinder
from backend.agents.rag_performance_optimizer import ProductQuantizer, LRUCache


class PerformanceAnalyzer:
    """性能分析器"""

    def __init__(self):
        self.results = {}

    def analyze_hnsw_recall(self):
        """分析 HNSW 召回率"""
        print("\n" + "="*60)
        print("HNSW 向量召回率测试")
        print("="*60)

        test_configs = [
            (50, 128),
            (100, 64),
            (200, 16),
            (500, 32)
        ]

        results = []

        for num_nodes, dimension in test_configs:
            np.random.seed(42)

            # 创建索引
            index = HNSWIndex(dimension=dimension, M=16, ef_construction=100, ef_search=128)

            # 生成测试向量
            vectors = np.random.randn(num_nodes, dimension).astype(np.float32)

            # 添加向量到索引
            for i, vec in enumerate(vectors):
                index.add_vector(f"vec_{i}", vec)

            # 测试召回率
            recall_count = 0
            for i, query_vec in enumerate(vectors):
                results_search = index.search(query_vec, k=10)
                result_ids = [r["node_id"] for r in results_search]
                if f"vec_{i}" in result_ids:
                    recall_count += 1

            recall_at_10 = recall_count / num_nodes
            results.append({
                "nodes": num_nodes,
                "dimension": dimension,
                "recall": recall_at_10
            })

            print(f"节点数: {num_nodes:4d}, 维度: {dimension:3d}, recall@10: {recall_at_10:.4f}")

        self.results["hnsw_recall"] = results
        return results

    def analyze_dialogue_compression(self):
        """分析对话压缩效果"""
        print("\n" + "="*60)
        print("对话压缩效果测试")
        print("="*60)

        np.random.seed(42)

        # 创建 50 轮模拟对话（约 8000 tokens）
        dialogue = []
        entities_per_turn = []

        for i in range(50):
            role = "user" if i % 2 == 0 else "assistant"
            content = f"This is message {i} with some content and entities like Entity_{i % 10} and Entity_{(i + 3) % 10}"
            dialogue.append({
                "role": role,
                "content": content,
                "timestamp": (datetime.now() + timedelta(minutes=i)).isoformat()
            })
            entities_per_turn.append([f"Entity_{i % 10}", f"Entity_{(i + 3) % 10}"])

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

        # 计算实体保留率
        all_entities = set()
        for entities in entities_per_turn:
            all_entities.update(entities)

        retained_entities = set()
        for chunk in chunks:
            for turn in chunk.turns:
                turn_idx = turn.get("turn_index", 0) if isinstance(turn, dict) else 0
                for entity in entities_per_turn[turn_idx]:
                    retained_entities.add(entity)

        entity_retention_rate = len(retained_entities) / len(all_entities) if all_entities else 1.0

        # 计算关键事实保留率
        high_density_chunks = [c for c in chunks if c.information_density > 0.5]
        fact_retention_rate = len(high_density_chunks) / len(chunks) if chunks else 1.0

        # 信息密度分析
        densities = [c.information_density for c in chunks]
        avg_density = np.mean(densities)
        max_density = np.max(densies)

        result = {
            "original_turns": original_turns,
            "compressed_turns": compressed_turns,
            "compression_ratio": compression_ratio,
            "entity_retention_rate": entity_retention_rate,
            "fact_retention_rate": fact_retention_rate,
            "avg_density": avg_density,
            "max_density": max_density
        }

        print(f"原始轮次: {original_turns}")
        print(f"压缩后轮次: {compressed_turns}")
        print(f"压缩比: {compression_ratio:.2%}")
        print(f"实体保留率: {entity_retention_rate:.2%}")
        print(f"关键事实保留率: {fact_retention_rate:.2%}")
        print(f"平均信息密度: {avg_density:.3f}")
        print(f"最大信息密度: {max_density:.3f}")

        self.results["dialogue_compression"] = result
        return result

    def analyze_hybrid_retrieval(self):
        """分析混合检索与重排效果"""
        print("\n" + "="*60)
        print("混合检索与重排效果测试")
        print("="*60)

        np.random.seed(42)

        # 创建检索系统
        retrieval_system = HybridRetrievalSystem(dimension=128)

        # 生成 1000 条历史记忆
        base_time = datetime.now() - timedelta(days=30)
        documents = []

        for i in range(1000):
            # 创建一个"重要"的记忆
            if i == 500:
                content = "This is the important memory about the project deadline"
                embedding = np.random.randn(128).astype(np.float32) + 0.5
                timestamp = (base_time + timedelta(days=25)).isoformat()
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

        # 查询向量
        query = documents[500]["embedding"] + np.random.randn(128).astype(np.float32) * 0.1

        # 纯语义搜索
        results_semantic = retrieval_system.search(query, k=10, use_reranking=False)

        # 时间衰减重排
        results_with_decay = retrieval_system.search(query, k=10, use_reranking=True)

        # 找到重要记忆的排名
        semantic_rank = None
        decay_rank = None

        for i, result in enumerate(results_semantic):
            if result["doc_id"] == "doc_500":
                semantic_rank = i + 1
                break

        for i, result in enumerate(results_with_decay):
            if result["doc_id"] == "doc_500":
                decay_rank = i + 1
                break

        result = {
            "semantic_rank": semantic_rank,
            "decay_rank": decay_rank,
            "rank_improvement": (semantic_rank - decay_rank) if semantic_rank and decay_rank else 0
        }

        print(f"纯语义搜索排名: {semantic_rank}")
        print(f"时间衰减重排排名: {decay_rank}")
        print(f"排名提升: {result['rank_improvement']} 位")

        self.results["hybrid_retrieval"] = result
        return result

    def analyze_query_latency(self):
        """分析查询延迟"""
        print("\n" + "="*60)
        print("查询延迟测试")
        print("="*60)

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
        avg_latency = np.mean(latencies)

        result = {
            "p50": p50,
            "p95": p95,
            "p99": p99,
            "avg": avg_latency
        }

        print(f"平均延迟: {avg_latency:.2f}ms")
        print(f"P50 延迟: {p50:.2f}ms")
        print(f"P95 延迟: {p95:.2f}ms")
        print(f"P99 延迟: {p99:.2f}ms")

        self.results["query_latency"] = result
        return result

    def analyze_write_throughput(self):
        """分析写入吞吐"""
        print("\n" + "="*60)
        print("写入吞吐测试")
        print("="*60)

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

        result = {
            "avg_write_time": avg_write_time,
            "throughput": throughput
        }

        print(f"平均写入时间: {avg_write_time:.2f}ms")
        print(f"写入吞吐: {throughput:.2f} ops/sec")

        self.results["write_throughput"] = result
        return result

    def analyze_cache_efficiency(self):
        """分析缓存效率"""
        print("\n" + "="*60)
        print("缓存效率测试")
        print("="*60)

        cache = LRUCache(capacity=100)

        # 模拟高频重复查询
        query_keys = [f"query_{i % 20}" for i in range(1000)]

        for key in query_keys:
            if cache.get(key) is None:
                cache.put(key, f"result_{key}")

        stats = cache.get_stats()
        hit_rate = stats["hit_count"] / stats["total_count"] if stats["total_count"] > 0 else 0

        result = {
            "hit_rate": hit_rate,
            "hit_count": stats["hit_count"],
            "total_count": stats["total_count"]
        }

        print(f"缓存命中率: {hit_rate:.2%}")
        print(f"缓存命中次数: {stats['hit_count']}")
        print(f"总查询次数: {stats['total_count']}")

        self.results["cache_efficiency"] = result
        return result

    def analyze_memory_usage(self):
        """分析内存占用和 PQ 量化效果"""
        print("\n" + "="*60)
        print("内存占用与 PQ 量化测试")
        print("="*60)

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

        # 计算原始和量化后的内存占用（MB/KB）
        original_mb = original_size / 1024 / 1024
        quantized_kb = quantized_size / 1024

        result = {
            "original_mb": original_mb,
            "quantized_kb": quantized_kb,
            "compression_ratio": compression_ratio
        }

        print(f"原始内存占用: {original_mb:.2f} MB")
        print(f"量化后内存占用: {quantized_kb:.2f} KB")
        print(f"压缩比: {compression_ratio:.2f}x")

        self.results["memory_usage"] = result
        return result

    def generate_report(self):
        """生成性能报告"""
        print("\n" + "="*60)
        print("性能分析报告")
        print("="*60)

        # HNSW 召回率
        if "hnsw_recall" in self.results:
            print("\n【HNSW 向量召回率】")
            for r in self.results["hnsw_recall"]:
                print(f"  {r['nodes']:4d} 节点, {r['dimension']:3d} 维: recall@10 = {r['recall']:.4f}")

        # 对话压缩
        if "dialogue_compression" in self.results:
            dc = self.results["dialogue_compression"]
            print("\n【对话压缩效果】")
            print(f"  压缩比: {dc['compression_ratio']:.2%}")
            print(f"  实体保留率: {dc['entity_retention_rate']:.2%}")
            print(f"  关键事实保留率: {dc['fact_retention_rate']:.2%}")

        # 混合检索
        if "hybrid_retrieval" in self.results:
            hr = self.results["hybrid_retrieval"]
            print("\n【混合检索与重排】")
            print(f"  纯语义搜索排名: {hr['semantic_rank']}")
            print(f"  时间衰减重排排名: {hr['decay_rank']}")
            print(f"  排名提升: {hr['rank_improvement']} 位")

        # 查询延迟
        if "query_latency" in self.results:
            ql = self.results["query_latency"]
            print("\n【查询延迟】")
            print(f"  P50: {ql['p50']:.2f}ms")
            print(f"  P95: {ql['p95']:.2f}ms")
            print(f"  P99: {ql['p99']:.2f}ms")

        # 写入吞吐
        if "write_throughput" in self.results:
            wt = self.results["write_throughput"]
            print("\n【写入吞吐】")
            print(f"  平均写入时间: {wt['avg_write_time']:.2f}ms")
            print(f"  吞吐: {wt['throughput']:.2f} ops/sec")

        # 缓存效率
        if "cache_efficiency" in self.results:
            ce = self.results["cache_efficiency"]
            print("\n【缓存效率】")
            print(f"  命中率: {ce['hit_rate']:.2%}")

        # 内存占用
        if "memory_usage" in self.results:
            mu = self.results["memory_usage"]
            print("\n【内存占用】")
            print(f"  原始: {mu['original_mb']:.2f} MB")
            print(f"  PQ 量化后: {mu['quantized_kb']:.2f} KB")
            print(f"  压缩比: {mu['compression_ratio']:.2f}x")

        print("\n" + "="*60)
        print("分析完成")
        print("="*60)

    def run_all_analyses(self):
        """运行所有分析"""
        self.analyze_hnsw_recall()
        self.analyze_dialogue_compression()
        self.analyze_hybrid_retrieval()
        self.analyze_query_latency()
        self.analyze_write_throughput()
        self.analyze_cache_efficiency()
        self.analyze_memory_usage()
        self.generate_report()


def main():
    """主函数"""
    analyzer = PerformanceAnalyzer()
    analyzer.run_all_analyses()


if __name__ == "__main__":
    main()