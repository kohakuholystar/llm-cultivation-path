"""渡劫飞升 · s1:工具注册表与分发器

「渡劫飞升」是毕业设计要交付的完整 Agent 应用,它的决策层叫
「渡劫台」:模型只负责决策,执行永远由我们的代码完成。
本步搭建工具层——注册表 + 分发器 + 错误信封:
任何失败都收敛成统一 JSON 信封回传,绝不向调用方抛异常。
"""
import json
import re

# ---- 模拟修炼典籍库:真实工程里对接 t71 RAG 管道 ----
CORPUS = [
    {"title": "筑基丹配方", "content": "百年灵芝三两、灵泉水五升,文火炼制七日,丹成有异香。"},
    {"title": "飞剑淬火", "content": "辰时淬火,炉温三千度,仙品飞剑还需加注灵泉。"},
    {"title": "雷劫征兆", "content": "渡劫前三日紫气东来;雷劫共九道,第八道须以法宝抵挡。"},
]

# 品质加成:仙品法器耗费的炉火更旺
RARITY_BONUS = {"凡品": 1.0, "精品": 1.5, "仙品": 3.0}


def search_knowledge(query: str) -> str:
    """检索修炼典籍:整句子串匹配,取第一条命中(模拟 RAG 检索)。"""
    for entry in CORPUS:
        if query in entry["title"] + entry["content"]:
            return f"【典籍】{entry['title']}:{entry['content']}"
    return "【典籍】没有检索到相关条目,请换个说法再试。"


def calc_forge_cost(item_name: str, quantity: int, unit_cost: float, rarity: str = "凡品") -> str:
    """计算炼制成本:数量 × 单价 × 品质加成。"""
    total = quantity * unit_cost * RARITY_BONUS.get(rarity, 1.0)
    return f"【炼器】{rarity}·{item_name} x{quantity}:共需 {total:.1f} 灵石"


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
    """锻造工具注册表:名字 → {desc, params, fn},desc 写给模型看。"""
    # TODO: 返回完整注册表,把四件工具登记进去,每个条目含三键
    # 提示: 键为工具名;值为 {"desc": ..., "params": {...}, "fn": ...};search_knowledge / calc_forge_cost / write_note / read_note 都要登记
    raise NotImplementedError("t72-agent-layer-s1 尚未实现:请按 TODO 提示锻造工具注册表")


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
    print(dispatch("search_knowledge", {"query": "雷劫"}))
    print("\n== 正常计算 ==")
    print(dispatch("calc_forge_cost", {"item_name": "飞剑", "quantity": 3, "unit_cost": 120.0, "rarity": "精品"}))
    print("\n== 笔记读写 ==")
    print(dispatch("write_note", {"name": "丹方", "content": "筑基丹:灵芝三两"}))
    print(dispatch("read_note", {"name": "丹方"}))
    print("\n== 失败路径:未知工具 / 缺参数 ==")
    print(dispatch("fly_to_moon", {}))
    print(dispatch("calc_forge_cost", {"item_name": "飞剑"}))


if __name__ == "__main__":
    main()
