# 别瞎折腾了！6 小时交付智能系统，我们靠的不是“狂点 Accept”

> 把需求丢给模型，一路狂点“Accept”，项目就能自动完美交付？  
> 我们试了，然后踩了所有你想象不到的坑。

在最近一场由 Agently 框架核心作者 **莫欣老师** 主讲的 51CTO 直播中，我们做了一次“真刀真枪”的实验：  
**只用 6 小时，完成一个端到端的智能 ToDo 系统**（Go 后端 + Agently 智能服务 + Electron 桌面端）。

但这篇文章不是来炫技的。我们更想讲清楚一个真相：  
**VibeCoding 很热闹，但智能体/智能系统开发的真正难点，从来不在“写代码”，而在“把不确定性收住，做成能交付、跑得稳的系统”。**

项目仓库：github.com/AgentEra/Agently-NexusTodo  
Agently 框架：github.com/AgentEra/Agently  
Agently 官网：Agently.tech（EN） / Agently.cn（CN）

---

## 一、为什么是智能 ToDo？因为它把 AI 开发的“雷”全踩了一遍

我们选择“智能 ToDo”作为试验场，是因为它看似简单，实则精准命中 AI 应用开发的所有核心痛点：

- **需求很“人话”**：用户会说“把明天要交的报告提到最前面”，而不是调用某个接口方法。
- **操作常“多步”**：先模糊搜索，再按时间筛选，最后批量修改状态——这需要系统能规划与执行。
- **交互必须“可信”**：过程要可见（AI 在干嘛），结果要可验（改对了吗）。
- **系统必须“稳定”**：不能今天好用，明天改句提示词就抽风。

我们用三段式架构，一次性跑通智能体系统的全链路：

1) **Go 后端**：坚固的“事实地基”  
只负责最稳定的部分：任务增删改查 API、数据持久化、设备/用户标识。  
它的存在，是让上层智能“乱了也有据可依”：数据与规则以它为准。

2) **Python 智能服务（基于 Agently）**：智慧的“决策大脑”  
负责理解自然语言、管理多轮对话，并**规划与执行**对后端的多次工具调用。

3) **Electron 桌面端**：友好的“交互桥梁”  
既能传统管理，又能对话操作。关键是把**思考过程**和**最终结果**分层展示，建立信任。

> Tips（我们真正的策略）  
> 先固本，后增智：先把后端 + 客户端基础架子跑通，再接入智能模块。这样智能从第一天起面对的就是“真实接口 + 真实场景”，不是虚构沙盒。

---

## 二、直播现场：6 小时炼成“可控系统”的三大铁律

直播里我们问莫欣老师：你最希望大家带走的一个关键认知是什么？

他的回答，几乎就是 AI 工程化的核心：

> 1. SpecDD 不是形式主义，而是并行开发的“发令枪”。  
> 先花 10 分钟把目标、边界、成功标准写清楚，能省掉后续 10 小时的扯皮和返工。
>
> 2. API 文档规范不是事后补的说明书，而是团队协作的“宪法”。  
> 模块之间如何对话必须先定义清楚。否则联调就是灾难现场，智能体会把任何歧义放大成事故。
>
> 3. 智能模块要落地，不能靠“硬写”，要靠框架“约束”。  
> 用可执行测试把不确定性收进笼子，系统才能既聪明又可靠。

结论很简单：追求**系统可控**，比追求**系统聪明**更重要。  
一个可控的系统，才能让你冷静评估技术优劣，快速定位问题，持续迭代优化。

---

## 三、四大天坑：如果你让 AI “硬写”智能模块……

如果你放任模型自由发挥，大概率会跌进这些陷阱：

1) **“Accept All” 幻觉**  
代码像野草一样生长，你逐渐看不懂，修 Bug 变成开盲盒。

2) **质量“长尾”陷阱**  
前期产出看似快，后期 Review、返工、修 Bug 的成本会吞噬所有优势。

3) **安全盲区与过度自信**  
代码更易藏坑，而开发者却更容易“觉得没问题”。安全研究里讨论过的“错误率上升 + 过度自信”组合风险，在 AI 时代被急剧放大。

4) **新型供应链风险**  
AI 更容易产生“包名幻觉”，误引入恶意依赖（常见称呼：slopsquatting / package hallucination）。

这些坑不高级，却招招致命，专卡在联调、上线、交付这些你最输不起的环节。

---

## 四、Agently：如何用“工程化”拴住 AI 的创造力？

没有框架支撑的 VibeCoding，就像给赛车装上火箭引擎却拆了方向盘：**能飞，但不知道会撞向哪里。**

在这次项目中，Agently 的价值集中体现在三类工程化能力上（并且都能在文档/样例里直接找到模板）：

### 1) 结构化输出：让结果“可被程序读取”

用 Output Format 把模型输出锁定为结构化结果，再用 ensure_keys 为关键字段提供缺失重试兜底。  
从此，解析结果不再靠正则和运气。

下面是一段最小可用的例子（把“人话指令”压成稳定 JSON）：

```python
from agently import Agently

agent = Agently.create_agent()

result = (
  agent
  .input("把所有包含“测试”的任务删除，并输出删除数量")
  .output({
    "need_delete": ("bool", "是否需要删除"),
    "keyword": ("str", "用于筛选的关键词"),
    "summary": ("str", "给用户的最终说明"),
  })
  .start(
    ensure_keys=["need_delete", "keyword", "summary"],
    max_retries=2,              # 常见建议：1-3 次
    raise_ensure_failure=False, # 尽量返回可用结果
  )
)

print(result)
```

### 2) 事件化流式返回：让过程“透明可视”

Agently 把模型响应统一为标准化事件流（例如 delta / reasoning_delta / tool_calls / done / error）。  
当输出是 Output Format 时，还能用 Instant 拿到“字段路径 + 增量”，前端展示不必靠猜。

```python
from agently import Agently

agent = Agently.create_agent()

response = (
  agent
  .input("用两句话解释 TriggerFlow，并给一个最小例子")
  .output({"answer": ("str", "回答")})
  .get_response()
)

# 只消费你关心的事件（适合做前端流式 UI）
for event, value in response.get_generator(
  type="specific",
  specific=["delta", "reasoning_delta", "tool_calls", "done", "error"],
):
  print(event, value)
```

### 3) TriggerFlow 编排：让多步任务“可编排、可调试、可回归”

把复杂的“思考-行动-观察”循环写成清晰的**信号-节点-运行态**编排，多步任务不再是黑箱，而是可复盘、可回归、可扩展的流程。

下面是一段最小例子（用 runtime_data 存上下文，用 collect 等待多个分支到齐再汇总）：

```python
from agently import TriggerFlow, TriggerFlowEventData

flow = TriggerFlow()

@flow.chunk
async def set_user(data: TriggerFlowEventData):
  data.set_runtime_data("user_id", "u-001")
  return "r1"

@flow.chunk
async def set_env(data: TriggerFlowEventData):
  data.set_runtime_data("env", "prod")
  return "r2"

@flow.chunk
def print_collect(data: TriggerFlowEventData):
  print(data.value)  # {'collect': {'r1': 'r1', 'r2': 'r2'}} 形态的聚合结果

flow.to(set_user).collect("collect", "r1")
flow.to(set_env).collect("collect", "r2").to(print_collect).end()

flow.start("start")
```

> Tips（这一段的落点）  
> Agently 的核心价值，不是让 AI “更会说话”，而是让智能系统“更守规矩”：可约束、可编排、可验证。

如果你想对照学习，Agently 仓库里这些入口非常适合从 0 开始跑：  
docs/agent-docs.md、docs/output-control/ensure-keys.md、docs/model-response/streaming.md、docs/triggerflow/concepts.md  
以及 examples/step_by_step/03-output_format_control.py、06-streaming.py、07-tools.py

---

## 五、拿来即用：你的项目正卡在以下哪一环？

道理懂了，你的项目该怎么上手？我们把它浓缩为三个最常见“卡点”与对应解药：

- **卡点一：输出不稳定，字段时有时无，解析代码脆弱不堪。**  
  解药：先上 Output Format + ensure_keys。先拿到稳定结构化数据，一切迭代才有地基。

- **卡点二：多步任务逻辑混乱，AI 反复兜圈，工具调用失控。**  
  解药：用 TriggerFlow 把流程显式化；再用场景化用例脚本做回归测试，确保改动不炸全局。

- **卡点三：Demo 能跑，但不敢交付；每次联调都需人肉紧盯，心力交瘁。**  
  解药：把 SpecDD（规范驱动）和 API 文档规范先行当铁律；用真实接口用例作为验收门禁，推动“可用”向“可交付”迈进。

最后送你一份我们用真金白银踩出来的“避坑秘籍”：  
所有在 6 小时实战中总结的经验、技巧和修复记录，我们都开源在了项目仓库的 auto_agent/docs/skills 目录中。  
仓库地址：github.com/AgentEra/Agently-NexusTodo

---

## 六、加入我们，一起定义 AI 开发的新范式

如果你也厌倦了玩具 Demo，正致力于把大模型**稳定、可靠地**交付进真实业务系统；如果你也在与多轮对话、工具调用、流式响应和复杂流程编排的“不确定性”作斗争——欢迎来到 Agently 的阵营。

体验与交流：
- 官网：Agently.tech（国际站） / Agently.cn（中文站）
- 微信讨论群：官网或 GitHub 主页均有入口
- GitHub：github.com/AgentEra/Agently

与我们并肩作战：
- **加入团队（含实习）**：hr@agently.tech
- **商务合作**：business@agently.tech

