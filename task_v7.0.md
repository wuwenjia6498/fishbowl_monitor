# 任务：重构趋势图更新逻辑为“增量追加模式” (v7.0 Stability Upgrade)

用户反馈趋势图在每日更新后会再次消失（变为“暂无数据”）。
这证明依赖 Tushare 每日全量拉取历史数据的策略是不稳定的。

请彻底重写 `scripts/etl.py` 中的趋势图更新逻辑，改为 **"增量追加 (Append-Only)"** 模式。

## 1. 核心逻辑变更 (`scripts/etl.py`)

在 `update_daily_data` 或相关函数中，**放弃** “每次调用 `pro.daily` 拉取 250 天” 的做法。

**新流程逻辑：**

1.  **读取现有数据 (Read):**
    在更新之前，先从数据库查询该标的当前的 `sparkline_json` 字段。
    ```python
    # 伪代码
    cursor.execute("SELECT sparkline_json FROM fishbowl_daily WHERE symbol = %s", (symbol,))
    result = cursor.fetchone()
    current_chart = result[0] if result and result[0] else []
    ```

2.  **构造今日数据点 (Construct):**
    使用脚本中已经获取到的 **今日最新数据** (Close, MA20, Date)。
    ```python
    new_point = {
        "date": today_str,  # 格式 "MM-DD" 或 "YYYY-MM-DD"
        "price": round(current_close, 2),
        "ma20": round(current_ma20, 2)
    }
    ```

3.  **增量追加与去重 (Append & Deduplicate):**
    * 如果 `current_chart` 为空（新标的），则回退到 **全量拉取模式**（调用 Tushare 拉一次历史做初始化）。
    * 如果 `current_chart` 不为空：
        * 检查最后一个点的日期。
        * **IF** `last_date != today_str`: 将 `new_point` `append` 到列表末尾。
        * **IF** `last_date == today_str`: 更新（覆盖）最后一个点的数据（防止重复运行导致数据堆积）。

4.  **滑动窗口裁剪 (Trim):**
    保持数组长度不无限增长，只保留最近 250 天。
    ```python
    final_chart = current_chart[-250:]
    ```

5.  **写入数据库 (Write):**
    将 `final_chart` 转换为 JSON 字符串并更新回数据库。

## 2. 异常处理增强

* **Json 解析保护:** 在读取数据库旧数据时，增加 `try-except` 防止 JSON 解析错误导致脚本中断。如果解析失败，视为 `[]` 并触发全量拉取初始化。
* **空值保护:** 如果 `final_chart` 计算后为空，**绝对不要** 执行 `UPDATE sparkline_json` 语句，直接跳过该字段的更新。

## 执行指令
1.  **Refactor:** 修改 `etl.py`，实现“读取 -> 追加 -> 裁剪 -> 保存”的闭环逻辑。
2.  **Safety:** 确保只有在“没有旧数据”这种极端情况下，才去调用 Tushare 的历史接口，最大限度减少对外部 API 的依赖。