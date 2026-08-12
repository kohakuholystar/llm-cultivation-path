"""终期交付 · s1:工具注册表与分发器

「终期交付」是毕业设计要交付的完整 Agent 应用,它的决策层叫
「验收台」:模型只负责决策,执行永远由我们的代码完成。
本步搭建工具层——注册表 + 分发器 + 错误信封:
任何失败都收敛成统一 JSON 信封回传,绝不向调用方抛异常。
"""


# === 学习契约（面向学生）===
# 本节目标：工具注册表:任务调度台的工具架。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `search_knowledge(query: str) -> str`：输入为签名中的参数；输出为 `str`。用途：检索构建资料:整句子串匹配,取第一条命中(模拟 RAG 检索)。
#   - `calc_forge_cost(item_name: str, quantity: int, unit_cost: float, rarity: str='凡品') -> str`：输入为签名中的参数；输出为 `str`。用途：计算实现成本:数量 × 单价 × 品质加成。
#   - `write_note(name: str, content: str) -> str`：输入为签名中的参数；输出为 `str`。用途：把一段内容落盘为笔记文件。
#   - `read_note(name: str) -> str`：输入为签名中的参数；输出为 `str`。用途：读取笔记文件,不存在时给出明确提示。
#   - `build_registry() -> dict`：输入为签名中的参数；输出为 `dict`。用途：处理工具注册表:名字 → {desc, params, fn},desc 写给模型看。
#   - `_envelope(ok: bool, kind: str='', message: str='', data: str='') -> str`：输入为签名中的参数；输出为 `str`。用途：统一错误信封:模型读得懂,才知道下一步怎么办。
#   - `dispatch(name: str, args: dict) -> str`：输入为签名中的参数；输出为 `str`。用途：执行工具并返回 JSON 信封:失败绝不抛出,都变成可读文本。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import json
import re

# ---- 模拟构建知识库:真实工程里对接 t71 RAG 管道 ----
CORPUS = [
    {"title": "基础阶段丹配方", "content": "百年灵芝三两、补充素材水五升,文火实现七日,丹成有异香。"},
    {"title": "展示素材优化细节", "content": "展示前优化细节,渲染参数设为高质量,高质量展示素材还需补充光影说明。"},
    {"title": "故障征兆", "content": "上线验收前三日原始数据东来;故障共九道,第八道须以工具抵挡。"},
]

# 品质加成:高质量工具耗费的模型服务更旺
RARITY_BONUS = {"凡品": 1.0, "精品": 1.5, "高质量": 3.0}


def search_knowledge(query: str) -> str:
    """检索构建资料:整句子串匹配,取第一条命中(模拟 RAG 检索)。"""
    for entry in CORPUS:
        if query in entry["title"] + entry["content"]:
            return f"【资料】{entry['title']}:{entry['content']}"
    return "【资料】没有检索到相关条目,请换个说法再试。"


def calc_forge_cost(item_name: str, quantity: int, unit_cost: float, rarity: str = "凡品") -> str:
    """计算实现成本:数量 × 单价 × 品质加成。"""
    total = quantity * unit_cost * RARITY_BONUS.get(rarity, 1.0)
    return f"【工具开发】{rarity}·{item_name} x{quantity}:共需 {total:.1f} 预算点"


def write_note(name: str, content: str) -> str:
    """把一段内容落盘为笔记文件。"""
    with open(f"{name}.txt", "w", encoding="utf-8") as f:
        f.write(content)
    return f"【笔记】已保存 {name}.txt"


def read_note(name: str) -> str:
    """读取笔记文件,不存在时给出明确提示。"""
    try:
        with open(f"{name}.txt", encoding="utf-8") as f:
            return f"【笔记】{name}.txt:{f.read()}"
    except FileNotFoundError:
        return f"【笔记】没有找到 {name}.txt"


def build_registry() -> dict:
    """处理工具注册表:名字 → {desc, params, fn},desc 写给模型看。"""
    # TODO: 返回完整注册表,把四件工具登记进去,每个条目含三键
    # 提示: 键为工具名;值为 {"desc": ..., "params": {...}, "fn": ...};search_knowledge / calc_forge_cost / write_note / read_note 都要登记
    raise NotImplementedError("t72-agent-layer-s1 尚未实现:请按 TODO 提示处理工具注册表")


TOOLS = build_registry()


def _envelope(ok: bool, kind: str = "", message: str = "", data: str = "") -> str:
    """统一错误信封:模型读得懂,才知道下一步怎么办。"""
    if ok:
        return json.dumps({"ok": True, "data": data}, ensure_ascii=False)
    return json.dumps({"ok": False, "error": {"type": kind, "message": message}}, ensure_ascii=False)


def dispatch(name: str, args: dict) -> str:
    """执行工具并返回 JSON 信封:失败绝不抛出,都变成可读文本。"""
    spec = TOOLS.get(name)
    if spec is None:
        return _envelope(False, "unknown_tool", f"没有名为 {name} 的工具")
    # TODO: 进入 try 前做缺参校验:missing 非空时返回 invalid_args 信封
    # 提示: missing = [k for k in spec["params"] if k not in args];有缺失返回 _envelope(False, "invalid_args", f"缺少参数: {missing}")
    raise NotImplementedError("t72-agent-layer-s1 尚未实现:请按 TODO 提示补缺参校验")
    try:
        result = spec["fn"](**args)
        return _envelope(True, data=result)
    except Exception as exc:  # noqa: BLE001 兜底:未知异常也要变成模型可读的反馈
        return _envelope(False, "internal_error", f"{type(exc).__name__}: {exc}")


def main() -> None:
    print("== 正常检索 ==")
    print(dispatch("search_knowledge", {"query": "故障"}))
    print("\n== 正常计算 ==")
    print(dispatch("calc_forge_cost", {"item_name": "展示素材", "quantity": 3, "unit_cost": 120.0, "rarity": "精品"}))
    print("\n== 笔记读写 ==")
    print(dispatch("write_note", {"name": "制作方案", "content": "基础阶段丹:灵芝三两"}))
    print(dispatch("read_note", {"name": "制作方案"}))
    print("\n== 失败路径:未知工具 / 缺参数 ==")
    print(dispatch("fly_to_moon", {}))
    print(dispatch("calc_forge_cost", {"item_name": "展示素材"}))


if __name__ == "__main__":
    main()
