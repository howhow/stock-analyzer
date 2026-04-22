"""EventBus — 事件驱动解耦层

基于 blinker 实现的进程内事件总线，用于解耦 UI/Analytics/Trading 各层依赖。

设计原则:
- blinker: 轻量级，纯 Python，零外部依赖（blinker 是 Flask 的依赖，已间接安装）
- 进程内通知，毫秒级延迟
- 关键事件可持久化到日志（审计需要）
- 与 Celery 分工: EventBus = 进程内事件通知; Celery = 异步任务执行
"""

from blinker import Signal


class Events:
    """全局事件命名空间 — 解耦各层依赖

    使用方式:
        # 发送事件（注意：sender 必须是位置参数）
        Events.season_changed.send(
            self,  # sender 必须是位置参数，不能用 sender=xxx
            ts_code="600519.SH",
            old_season="spring",
            new_season="summer",
            confidence=0.85,
        )

        # 订阅事件
        @Events.season_changed.connect
        def on_season_changed(
            sender, ts_code, old_season, new_season, confidence, **kwargs
        ):
            logger.info(f"{ts_code}: {old_season} → {new_season}")
    """

    # ═══ 四季事件 ═══
    season_changed = Signal("season_changed")
    """四季状态变更: 春→夏→秋→冬"""

    dcf_calculated = Signal("dcf_calculated")
    """DCF 估值计算完成"""

    safety_margin_updated = Signal("safety_margin_updated")
    """安全边际更新"""

    # ═══ 五行事件 ═══
    wuxing_state_changed = Signal("wuxing_state_changed")
    """五行状态变更: 木→火→金→水"""

    transition_detected = Signal("transition_detected")
    """五行转换检测（含贝叶斯概率）"""

    bayesian_updated = Signal("bayesian_updated")
    """贝叶斯后验概率更新"""

    # ═══ 仓位事件 ═══
    position_plan_created = Signal("position_plan_created")
    """仓位计划创建"""

    stop_loss_triggered = Signal("stop_loss_triggered")
    """止损触发"""

    # ═══ 触发事件 ═══
    analysis_triggered = Signal("analysis_triggered")
    """分析任务触发"""

    alert_triggered = Signal("alert_triggered")
    """告警触发"""

    # ═══ 数据事件 ═══
    data_source_failed = Signal("data_source_failed")
    """数据源失败"""

    data_source_recovered = Signal("data_source_recovered")
    """数据源恢复"""

    data_fetched = Signal("data_fetched")
    """数据获取成功"""
