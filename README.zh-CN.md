# Android Harness

一个供编程代理使用的 Android 操作框架：**观察页面 → 选择操作 → 执行 → 验证结果**。
设计参考 [browser-harness](https://github.com/browser-use/browser-harness)，采用固定核心、预载函数和可编辑 helper 工作区。

[English](README.md) · [Skill](SKILL.md) · [API](references/api.md)

## 能力

- 读取 UI 元素，按需截图，按文字、描述或资源 ID 定位。
- 点击、英文输入、滑动、按键、启动应用。
- 检查锁屏、过期观察、页面变化和重复操作。
- 工作区保存连接配置及 `agent_helpers.py`，方便逐步补充可复用动作。
- 同一电脑上的 runner 会互斥访问同一台手机。
- 可选接入已经部署的手机后台语音服务。

目前是实验版本。普通 UI 操作只需 Python 3.10+、ADB 和已授权 USB 调试的手机，
不需要安装新的手机辅助程序。它不自带大模型、MCP 服务或持续语音通话。

## 使用

在项目根目录执行，替换 ADB 路径和设备序列号：

```console
python scripts/android_harness.py devices --adb /absolute/path/to/adb
python android-harness.py --workspace work/my-phone --init --adb /absolute/path/to/adb --serial YOUR_DEVICE_SERIAL
python android-harness.py --workspace work/my-phone --doctor
python android-harness.py --workspace work/my-phone --file examples/inspect.py
```

Windows 使用 `adb.exe` 的绝对路径。手机先解锁；已有工作区可以继续使用。
查看截图可执行 `examples/screenshot.py`。完成后运行 `--forget`，只删除本工作区最近一次的观察数据。

`screen_info()`、`find()`、`tap()`、`type_text()`、`swipe()`、`open_app()` 等函数会预先载入。
修改工作区中的 `agent_helpers.py` 即可增加应用专用流程，下次执行时加载。
不要将手机页面上的文字当成 Python 代码执行。

## 限制与验证

- 当前直接输入支持英文 ASCII，不支持中文或百分号。
- 不是无痕或反检测工具；不清理系统日志、浏览历史和用户文件。
- 默认不录屏、不截图，没有遥测客户端。
- 锁屏需要用户解锁。操作超时后先检查结果，不自动重复点击。
- 主机 Python 具有正常用户权限，不是安全沙箱。

21 项本地测试已通过。真机验证过截图、锁屏检查、输入 `ni hao`、网页滑动、
应用启动及 Play 商店按钮操作。配置了跨平台 CI，但尚未在 GitHub 运行。
完整范围见 [验证记录](docs/validation.md)。

## 项目状态

这是可上传 GitHub 的源码项目，尚未发布到远程仓库。
已移除具体设备序列号、个人绝对路径、截图、令牌和模型文件。
开源许可证尚未选择，发布前由项目所有者决定。
