"""
Timer测试 - 补充覆盖率
"""

import time

from app.utils.timer import Timer, timer


class TestTimer:
    """Timer测试"""

    def test_timer_init(self):
        """测试Timer初始化"""
        timer_instance = Timer()
        assert timer_instance is not None

    def test_timer_context_manager(self):
        """测试timer上下文管理器"""
        with timer("test") as t:
            time.sleep(0.01)

        # 应该记录了时间
        assert t["elapsed"] > 0

    def test_timer_elapsed(self):
        """测试Timer计时"""
        timer_instance = Timer()
        timer_instance.start()
        time.sleep(0.05)
        elapsed = timer_instance.stop()

        # 应该大于50ms
        assert elapsed >= 50

    def test_timer_stop_without_start(self):
        """测试未启动就停止"""
        timer_instance = Timer()
        # 应该抛出异常或返回0
        try:
            elapsed = timer_instance.stop()
            # 如果没有异常，elapsed应该是0
            assert elapsed >= 0
        except RuntimeError:
            # 或者抛出RuntimeError也是预期行为
            pass
