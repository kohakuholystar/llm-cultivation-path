"""百宝囊 · s1:多参数法宝与 args_schema 校验

百宝囊是 Agent 随身的法器袋。本步打造第一件法宝「炼器炉」:
一个接收 4 个参数的计算工具,用 Pydantic BaseModel 声明参数契约,
让 LangChain 在执行函数体之前自动完成类型校验与 coercion。
"""
from typing import Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field, ValidationError


class RefineInput(BaseModel):
    """炼器炉的入参契约:每个字段都是写给模型看的说明书。"""

    # TODO: 定义 4 个字段,全部用 Field(description=...) 写清中文说明
    # 提示: item_name: str;quantity: int Field(gt=0, le=99);unit_cost: float Field(ge=0);rarity: Literal["凡品","精品","仙品"] 默认 "凡品"
    pass


# 品质加成系数表:仙品法器耗费的炉火更旺
RARITY_BONUS = {"凡品": 1.0, "精品": 1.5, "仙品": 3.0}


@tool(args_schema=RefineInput)
def refine_calc(item_name: str, quantity: int, unit_cost: float, rarity: str = "凡品") -> str:
    """估算炼制法器的总灵石成本,含品质加成。"""
    bonus = RARITY_BONUS[rarity]
    total = quantity * unit_cost * bonus
    return (
        f"【炼器炉】{rarity}·{item_name} x{quantity}:"
        f"材料 {quantity * unit_cost:.1f} 灵石,品质加成 x{bonus},"
        f"共需 {total:.1f} 灵石"
    )


def show_schema() -> None:
    """打印法宝的参数契约——这份 JSON Schema 最终会随请求发给模型。"""
    schema = RefineInput.model_json_schema()
    print("== 法宝参数契约(args_schema)==")
    for name, prop in schema["properties"].items():
        print(f"  - {name}: {prop.get('description', '')}")
    print(f"  必填字段: {schema['required']}")


def demo_invoke() -> None:
    """演示三种调用:正常传参、自动类型转换、校验失败被拦截。"""
    print("\n== 正常调用 ==")
    print(refine_calc.invoke({"item_name": "飞剑", "quantity": 3, "unit_cost": 120.0, "rarity": "精品"}))

    print("\n== 宽松转换:字符串数字被自动 coerce ==")
    print(refine_calc.invoke({"item_name": "丹炉", "quantity": "2", "unit_cost": 80}))

    print("\n== 校验失败:数量为 0 被 args_schema 挡在门口 ==")
    # TODO: 演示校验失败:以 quantity=0 调用 refine_calc.invoke,用 try/except 捕获 ValidationError
    # 提示: except ValidationError as exc: err = exc.errors()[0];print(f"  拦截成功!字段 {err['loc'][0]}: {err['msg']}")
    raise NotImplementedError("t33-s1 尚未实现:请按 TODO 提示补上校验失败演示")


def main() -> None:
    show_schema()
    demo_invoke()


if __name__ == "__main__":
    main()
