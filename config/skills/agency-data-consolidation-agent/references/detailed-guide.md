# agency-data-consolidation-agent — Detailed Reference & Extended Examples


    def _detect_anomalies(self) -> list[dict]:
        """检测数据异常"""
        anomalies = []
        # 按代表计算达成率并检查异常
        rep_data = self._aggregate_by_rep()
        for rep_id, data in rep_data.items():
            att = self._safe_attainment(data["revenue"], data["quota"])
            if att is None:
                anomalies.append({
                    "rep_id": rep_id,
                    "type": "missing_quota",
                    "message": f"代表 {rep_id} 配额未设定",
                })
            elif att > self.ANOMALY_THRESHOLDS["attainment_high"]:
                anomalies.append({
                    "rep_id": rep_id,
                    "type": "high_attainment",
                    "value": float(att),
                    "message": f"代表 {rep_id} 达成率 {att}% 异常偏高，请核实",
                })
        return anomalies

    def _assess_data_quality(self) -> dict:
        """数据质量评估"""
        total = len(self.metrics)
        if total == 0:
            return {"score": 0, "issues": ["无数据"]}

        issues = []
        # 检查空值
        null_values = sum(1 for m in self.metrics if m.value is None)
        if null_values > 0:
            issues.append(f"{null_values} 条记录值为空")

        # 检查重复
        seen = set()
        duplicates = 0
        for m in self.metrics:
            key = (m.rep_id, m.metric_type, m.metric_date)
            if key in seen:
                duplicates += 1
            seen.add(key)
        if duplicates > 0:
            issues.append(f"{duplicates} 条疑似重复记录")

        score = max(0, 100 - null_values * 5 - duplicates * 10)
        return {"score": score, "issues": issues}

    def _get_top_performers(self, n: int = 5) -> list[dict]:
        rep_data = self._aggregate_by_rep()
        sorted_reps = sorted(
            rep_data.items(),
            key=lambda x: x[1]["revenue"],
            reverse=True
        )
        return [
            {"rep_id": rep_id, **data}
            for rep_id, data in sorted_reps[:n]
        ]

    def _aggregate_by_rep(self) -> dict:
        result = {}
        for m in self.metrics:
            if m.rep_id not in result:
                result[m.rep_id] = {
                    "region": m.region,
                    "revenue": Decimal("0"),
                    "quota": Decimal("0"),
                }
            if m.metric_type == "revenue":
                result[m.rep_id]["revenue"] += m.value
            elif m.metric_type == "quota":
                result[m.rep_id]["quota"] += m.value
        return result

    def _build_pipeline_snapshot(self) -> list[dict]:
        """按阶段汇总管线"""
        # 简化示例：实际按 stage 分组
        pipeline_metrics = [m for m in self.metrics if m.metric_type == "pipeline"]
        return [{
            "total_value": float(sum(m.value for m in pipeline_metrics)),
            "count": len(pipeline_metrics),
        }]

    def _build_trend_data(self, months: int) -> list[dict]:
        """最近 N 个月的趋势数据"""
        cutoff = self.now - timedelta(days=months * 30)
        recent = [m for m in self.metrics
                  if m.metric_date >= cutoff and m.metric_type == "revenue"]
        # 按月分组
        monthly = {}
        for m in recent:
            key = m.metric_date.strftime("%Y-%m")
            monthly[key] = monthly.get(key, Decimal("0")) + m.value
        return [{"month": k, "revenue": float(v)}
                for k, v in sorted(monthly.items())]

    def _serialize_region(self, s: RegionSummary) -> dict:
        return {
            "region": s.region,
            "total_revenue": float(s.total_revenue),
            "total_quota": float(s.total_quota),
            "attainment_pct": float(s.attainment_pct) if s.attainment_pct else None,
            "rep_count": s.rep_count,
            "pipeline_value": float(s.pipeline_value),
            "data_freshness": s.data_freshness,
        }
```

### 仪表盘 JSON 输出格式

```json
{
  "generated_at": "2026-03-21T08:00:00Z",
  "region_summary": [
    {
      "region": "华东",
      "total_revenue": 4850000.0,
      "total_quota": 5000000.0,
      "attainment_pct": 97.0,
      "rep_count": 12,
      "pipeline_value": 2300000.0,
      "data_freshness": "current"
    }
  ],
  "top_performers": [
    { "rep_id": "REP-042", "region": "华东", "revenue": 820000.0, "quota": 600000.0 }
  ],
  "anomalies": [
    { "rep_id": "REP-107", "type": "high_attainment", "value": 245.0, "message": "代表 REP-107 达成率 245.0% 异常偏高，请核实" }
  ],
  "data_quality": { "score": 85, "issues": ["3 条记录值为空"] }
}
```

## 工作流程

### 第一步：数据源接入与审计

- 枚举所有数据源：CRM 系统、手动上报表、历史导入文件
- 检查每个源的更新频率、字段完整度和格式差异
- 建立字段映射表：统一日期格式、货币单位、区域编码
- 跑数据质量基线：空值率、重复率、异常值分布

### 第二步：ETL 管线搭建

- 抽取：按数据源分别实现拉取逻辑，处理分页和增量
- 转换：统一格式、计算衍生指标、标记异常
- 加载：写入仪表盘数据表，带版本号和时间戳
- 幂等保证：同一批数据重复运行结果一致

### 第三步：仪表盘视图生成

- 并行计算各维度汇总：区域、代表、管线阶段、时间趋势
- 生成仪表盘友好的 JSON 结构
- 附带数据新鲜度标签和质量评分
- 缓存结果，设置合理的 TTL（默认 60 秒）

### 第四步：持续监控

- 每分钟检查数据源是否有新数据到达
- 数据延迟超过阈值自动告警
- 周期性跑全量数据质量报告
- 记录每次整合的耗时和数据量，发现性能退化及时排查

## 沟通风格

- **数据说话**："华东区上月达成率 97%，但这个月前 15 天只有 38%，按线性推算月底可能只有 76%，需要关注"
- **质量优先**："西南区有 3 个代表的配额字段为空，仪表盘上显示'待设定'而不是 0%，避免误导"
- **异常敏锐**："REP-107 的达成率 245%，历史最高只有 130%，大概率是数据录入错误，已标红"
- **性能意识**："仪表盘加载从 0.8s 涨到 2.3s，原因是趋势查询没命中索引，加了 (region, metric_date) 复合索引后恢复到 0.6s"

## 成功指标

- 仪表盘加载时间 < 1 秒（P95）
- 数据新鲜度：从源数据更新到仪表盘展示 < 2 分钟
- 数据质量评分 > 90 分（无空值、无重复、无异常）
- 所有活跃区域和代表都有数据，零遗漏
- 明细和汇总视图之间零数据不一致
- ETL 管线成功率 99.9%，失败自动重试+告警
