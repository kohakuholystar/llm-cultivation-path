"""社团工具箱 · s2:StructuredTool 批量入囊

在 s1 构建器的基础上,新增「库存盘点」工具,并把注册方式从
@tool 装饰器升级为 StructuredTool.from_function 显式组装,
再用注册表 + dispatch 分发器统一管理——这是 Agent 调度工具的雏形。
"""
# ????????? StructuredTool ??????????????query_stock?build_pouch?dispatch???????????????????????????StructuredTool?Pydantic????t33-s1?????????????????????
from typing import Literal

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, ValidationError


class RefineInput(BaseModel):
    """构建器入参契约(与 s1 一致)。"""

    item_name: str = Field(description="要生成的工具名称,如「演示设备」")
    quantity: int = Field(gt=0, le=99, description="生成数量,1-99 件")
    unit_cost: float = Field(ge=0, description="单件材料成本(预算点)")
    rarity: Literal["基础", "标准", "高级"] = Field(default="基础", description="品质档位")


RARITY_BONUS = {"基础": 1.0, "标准": 1.5, "高级": 3.0}


def refine_calc(item_name: str, quantity: int, unit_cost: float, rarity: str = "基础") -> str:
    """估算生成工具的总预算点成本,含品质加成。"""
    bonus = RARITY_BONUS[rarity]
    total = quantity * unit_cost * bonus
    return (
        f"【构建器】{rarity}·{item_name} x{quantity}:"
        f"材料 {quantity * unit_cost:.1f} 预算点,品质加成 x{bonus},"
        f"共需 {total:.1f} 预算点"
    )


# ---- 第二件工具:库存盘点 ----
POUCH_STOCK = [
    {"name": "演示设备", "stock": 12, "rarity": "标准"},
    {"name": "构建器", "stock": 3, "rarity": "基础"},
    {"name": "贴纸", "stock": 58, "rarity": "基础"},
    {"name": "存储卡", "stock": 1, "rarity": "高级"},
]


class StockQueryInput(BaseModel):
    """库存盘点入参:keyword 必填,其余带默认值,演示多参数 + 可选参数。"""

    # TODO: 定义 3 个字段,全部用 Field(description=...) 写清中文说明
    # 提示: keyword: str;min_stock: int Field(default=0, ge=0);limit: int Field(default=5, gt=0, le=20)
    pass


def query_stock(keyword: str, min_stock: int = 0, limit: int = 5) -> str:
    """按关键词检索社团工具箱库存,可按最低库存过滤、限制返回条数。"""
    hits = [i for i in POUCH_STOCK if keyword in i["name"] and i["stock"] >= min_stock]
    hits = hits[:limit]
    if not hits:
        return f"【库存】没有找到与「{keyword}」相关的工具"
    lines = [f"  · {i['name']}({i['rarity']}) 库存 {i['stock']}" for i in hits]
    return f"【库存】找到 {len(hits)} 件:\n" + "\n".join(lines)


def build_pouch() -> list[StructuredTool]:
    """把工具函数批量组装成 StructuredTool,装入社团工具箱。"""
    # TODO: 注册第二件工具 query_stock,与 refine_calc 一起放进列表返回
    # 提示: StructuredTool.from_function(func=query_stock, name="query_stock", description="按关键词检索社团工具箱中的工具库存", args_schema=StockQueryInput)
    raise NotImplementedError("t33-s2 尚未实现:请按 TODO 提示注册 query_stock 工具")
    return [
        StructuredTool.from_function(
            func=refine_calc,
            name="refine_calc",
            description="估算生成工具的总预算点成本,含品质加成",
            args_schema=RefineInput,
        ),
    ]


def dispatch(pouch: list[StructuredTool], name: str, arguments: dict) -> tuple[bool, str]:
    """社团工具箱统一入口:按名字取工具并执行,返回 (是否成功, 文本)。

    模型只负责给出工具名和参数 JSON,查找与执行永远由我们的代码完成。
    """
    tool = next((t for t in pouch if t.name == name), None)
    if tool is None:
        return False, f"社团工具箱里没有名为 {name} 的工具"
    try:
        return True, tool.invoke(arguments)
    except ValidationError as exc:
        # 参数校验失败不该炸掉调用方,翻译成调用方能看懂的反馈
        err = exc.errors()[0]
        return False, f"参数校验失败,字段 {err['loc'][0]}: {err['msg']}"


def main() -> None:
    pouch = build_pouch()
    print("== 社团工具箱清单 ==")
    for t in pouch:
        props = list(t.args_schema.model_json_schema()["properties"])
        print(f"  ◆ {t.name}{tuple(props)}")

    print("\n== 调用构建器(高级 x2)==")
    _, text = dispatch(pouch, "refine_calc", {"item_name": "演示设备", "quantity": 2, "unit_cost": 150.0, "rarity": "高级"})
    print(text)

    print("\n== 调用库存盘点(最低库存 2)==")
    _, text = dispatch(pouch, "query_stock", {"keyword": "", "min_stock": 2})
    print(text)

    print("\n== 参数出错被拦截(limit=0 违反 gt=0)==")
    ok, text = dispatch(pouch, "query_stock", {"keyword": "方案", "limit": 0})
    print(f"  调用{'成功' if ok else '失败'}: {text}")


if __name__ == "__main__":
    main()
