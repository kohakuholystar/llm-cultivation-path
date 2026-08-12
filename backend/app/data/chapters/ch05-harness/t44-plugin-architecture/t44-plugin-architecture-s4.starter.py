"""Agent 运行时底座 · s4:配置热加载

运行时不停机换配置,靠两层守护:内容指纹判断「变没变」,
Pydantic 模型做 schema 校验,非法配置直接跳过。本步实现
ConfigStore,加载、比对、热更新一条龙。
"""


# === 学习契约（面向学生）===
# 本节目标：配置热加载:运行时不停机换档。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `main() -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `Plugin`：承载本节状态/数据；重点方法：run, on_config_changed。
#   - `EchoConfig`：承载本节状态/数据；重点方法：见类定义。
#   - `EchoPlugin`：承载本节状态/数据；重点方法：on_config_changed, run。
#   - `LimitConfig`：承载本节状态/数据；重点方法：见类定义。
#   - `LimitPlugin`：承载本节状态/数据；重点方法：on_config_changed, run。
#   - `ConfigStore`：承载本节状态/数据；重点方法：load, _read_fingerprint, hot_reload。
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import json
import os
import tempfile
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field, ValidationError


class Plugin(ABC):
    def __init__(self, name, description, config_schema=None):
        self.name = name
        self.description = description
        self.config_schema = config_schema
        self.cfg = None

    def run(self, text):
        return "(无处理)"

    def on_config_changed(self, cfg):
        """配置热更新回调,默认忽略。"""


class EchoConfig(BaseModel):
    prefix: str = Field(default="raw", description="回声前缀")


class EchoPlugin(Plugin):
    def __init__(self):
        super().__init__("echo", "回声通道", EchoConfig)

    def on_config_changed(self, cfg):
        self.cfg = cfg
        print(f"  [echo] 热更新:前缀 -> {cfg.prefix}")

    def run(self, text):
        prefix = self.cfg.prefix if self.cfg else "raw"
        return f"[{prefix}] {text}"


class LimitConfig(BaseModel):
    max_calls: int = Field(default=10, ge=1, description="每分钟请求上限")


class LimitPlugin(Plugin):
    def __init__(self):
        super().__init__("limit", "限流通道", LimitConfig)
        self._used = 0

    def on_config_changed(self, cfg):
        self.cfg = cfg
        self._used = 0
        print(f"  [limit] 热更新:每分钟上限 {cfg.max_calls} 次")

    def run(self, text):
        self._used += 1
        if self._used > self.cfg.max_calls:
            return "【限流】超限,已被拦截"
        return "【限流】放行"


class ConfigStore:
    def __init__(self, path, plugins):
        self.path = path
        self.plugins = plugins
        self._fingerprint = ""
        self.load()

    def load(self):
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        self._fingerprint = self._read_fingerprint()
        # TODO: 对每个带 config_schema 的插件校验并载入配置
        # 提示: 遍历 self.plugins;config_schema is None 就 continue;
        #       plugin.cfg = plugin.config_schema.model_validate(data.get(plugin.name, {}));
        #       print(f"  [store] {plugin.name} 配置载入: {plugin.cfg.model_dump()}")
        raise NotImplementedError("t44-plugin-architecture-s4 尚未实现:请按 TODO 提示完成 load 的配置载入")

    def _read_fingerprint(self):
        with open(self.path, encoding="utf-8") as f:
            return f.read()

    def hot_reload(self):
        # TODO: 指纹相同返回 False,否则重读校验并热更新
        # 提示: self._read_fingerprint() == self._fingerprint 直接 return False;
        #       重读 json.load 并更新 self._fingerprint;遍历插件,try model_validate,
        #       except ValidationError 打印 f"  [store] {plugin.name} 新配置非法,跳过: {exc}" 并 continue;
        #       成功则 plugin.cfg = new_cfg、plugin.on_config_changed(new_cfg);最后 return True
        raise NotImplementedError("t44-plugin-architecture-s4 尚未实现:请按 TODO 提示实现 hot_reload")


def main():
    workdir = tempfile.mkdtemp()
    cfg_path = os.path.join(workdir, "plugins.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump({"echo": {"prefix": "raw"}, "limit": {"max_calls": 2}}, f, ensure_ascii=False)
    store = ConfigStore(cfg_path, [EchoPlugin(), LimitPlugin()])
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump({"echo": {"prefix": "v2"}, "limit": {"max_calls": 1}}, f, ensure_ascii=False)
    print(f"  检测到变化: {store.hot_reload()}")
    print(f"  检测到变化: {store.hot_reload()}(内容未变,跳过)")
    for i in range(1, 4):
        print(f"第 {i} 次请求: {store.plugins[1].run('ping')}")


if __name__ == "__main__":
    main()
