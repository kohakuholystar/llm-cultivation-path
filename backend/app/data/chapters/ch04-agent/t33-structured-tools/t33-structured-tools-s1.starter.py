"""社团工具箱 · s1:多参数工具与 args_schema 校验

社团工具箱是 Agent 随身的工具袋。本步打造第一件工具「构建器」:
一个接收 4 个参数的计算工具,用 Pydantic BaseModel 声明参数契约,
让 LangChain 在执行函数体之前自动完成类型校验与 coercion。
"""
# ????????? Pydantic ???????????RefineInput ? refine_calc???????????????????????????????Pydantic?@tool????t32????????????????????????
from typing import Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field, ValidationError


class RefineInput(BaseModel):
    """构建器的入参契约:每个字段都是写给模型看的说明书。"""

    # TODO: 定义 4 个字段,全部用 Field(description=...) 写清中文说明
    # 提示: item_name: str;quantity: int Field(gt=0, le=99);unit_cost: float Field(ge=0);rarity: Literal["基础","标准","高级"] 默认 "基础"
    pass


# 品质加成系数表:高级工具耗费的运行资源更旺
RARITY_BONUS = {"基础": 1.0, "标准": 1.5, "高级": 3.0}


@tool(args_schema=RefineInput)
def refine_calc(item_name: str, quantity: int, unit_cost: float, rarity: str = "基础") -> str:
    """估算生成工具的总预算点成本,含品质加成。"""
    bonus = RARITY_BONUS[rarity]
    total = quantity * unit_cost * bonus
    return (
        f"【构建器】{rarity}·{item_name} x{quantity}:"
        f"材料 {quantity * unit_cost:.1f} 预算点,品质加成 x{bonus},"
        f"共需 {total:.1f} 预算点"
    )


def show_schema() -> None:
    """打印工具的参数契约——这份 JSON Schema 最终会随请求发给模型。"""
    schema = RefineInput.model_json_schema()
    print("== 工具参数契约(args_schema)==")
    for name, prop in schema["properties"].items():
        print(f"  - {name}: {prop.get('description', '')}")
    print(f"  必填字段: {schema['required']}")


def demo_invoke() -> None:
    """演示三种调用:正常传参、自动类型转换、校验失败被拦截。"""
    print("\n== 正常调用 ==")
    print(refine_calc.invoke({"item_name": "演示设备", "quantity": 3, "unit_cost": 120.0, "rarity": "标准"}))

    print("\n== 宽松转换:字符串数字被自动 coerce ==")
    print(refine_calc.invoke({"item_name": "构建器", "quantity": "2", "unit_cost": 80}))

    print("\n== 校验失败:数量为 0 被 args_schema 挡在门口 ==")
    # TODO: 演示校验失败:以 quantity=0 调用 refine_calc.invoke,用 try/except 捕获 ValidationError
    # 提示: except ValidationError as exc: err = exc.errors()[0];print(f"  拦截成功!字段 {err['loc'][0]}: {err['msg']}")
    raise NotImplementedError("t33-s1 尚未实现:请按 TODO 提示补上校验失败演示")


def main() -> None:
    show_schema()
    demo_invoke()


if __name__ == "__main__":
    main()
