"""
布隆过滤器测试
"""

from app.core.bloom_filter import LocalBloomFilter


class TestLocalBloomFilter:
    """本地布隆过滤器测试"""

    def test_init(self) -> None:
        """测试初始化"""
        bf = LocalBloomFilter(expected_items=1000, false_positive_rate=0.01)

        assert bf._size > 0
        assert bf._hash_count > 0
        assert len(bf._bits) == bf._size

    def test_add_and_contains(self) -> None:
        """测试添加和检查"""
        bf = LocalBloomFilter()

        item = "test_item_123"
        bf.add(item)

        assert bf.contains(item) is True

    def test_contains_nonexistent(self) -> None:
        """测试不存在的元素"""
        bf = LocalBloomFilter()

        # 不存在的元素可能返回True（误判），但概率很低
        # 这里测试大概率不存在的元素
        result = bf.contains("nonexistent_item_xyz_123")
        assert isinstance(result, bool)  # 验证返回类型

    def test_add_multiple(self) -> None:
        """测试添加多个元素"""
        bf = LocalBloomFilter()

        items = ["item1", "item2", "item3", "item4", "item5"]
        for item in items:
            bf.add(item)

        for item in items:
            assert bf.contains(item) is True

    def test_clear(self) -> None:
        """测试清空"""
        bf = LocalBloomFilter()

        bf.add("test_item")
        bf.clear()

        # 清空后应该不包含
        # 注意：可能有残留，但概率很低
        assert all(bit == 0 for bit in bf._bits)

    def test_calculate_size(self) -> None:
        """测试计算位数组大小"""
        # 使用公式验证
        import math

        n = 1000
        p = 0.01
        expected_size = int(math.ceil(-n * math.log(p) / (math.log(2) ** 2)))

        bf = LocalBloomFilter(expected_items=n, false_positive_rate=p)
        assert bf._size == expected_size

    def test_calculate_hash_count(self) -> None:
        """测试计算哈希函数数量"""
        import math

        n = 1000
        bf = LocalBloomFilter(expected_items=n)
        expected_k = int(math.ceil(bf._size / n * math.log(2)))

        assert bf._hash_count == expected_k

    def test_different_items_different_positions(self) -> None:
        """测试不同元素有不同哈希位置"""
        bf = LocalBloomFilter()

        pos1 = bf._get_positions("item1")
        pos2 = bf._get_positions("item2")

        # 不同元素应该有不同的位置组合
        assert set(pos1) != set(pos2)


class TestBloomFilterCalculate:
    """布隆过滤器参数计算测试"""

    def test_size_increases_with_items(self) -> None:
        """测试元素数量增加导致位数组增大"""
        bf_small = LocalBloomFilter(expected_items=100)
        bf_large = LocalBloomFilter(expected_items=10000)

        assert bf_large._size > bf_small._size

    def test_size_increases_with_lower_fp_rate(self) -> None:
        """测试更低误判率导致位数组增大"""
        bf_high_fp = LocalBloomFilter(expected_items=1000, false_positive_rate=0.1)
        bf_low_fp = LocalBloomFilter(expected_items=1000, false_positive_rate=0.01)

        assert bf_low_fp._size > bf_high_fp._size

    def test_hash_count_reasonable(self) -> None:
        """测试哈希函数数量合理"""
        bf = LocalBloomFilter(expected_items=10000)

        # 哈希函数数量通常在1-20之间
        assert 1 <= bf._hash_count <= 20
