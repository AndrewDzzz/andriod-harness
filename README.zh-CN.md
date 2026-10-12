# Android Harness

通过 Python 和 ADB 操作 Android 手机，为编程代理提供 **观察 → 操作 → 验证** 的工作流程。

[English](README.md) · [Agent Skill](SKILL.md) · [API](references/api.md) · [常见问题](docs/troubleshooting.md)

## 功能

- 读取界面元素，按需截图。
- 点击、滑动、输入 ASCII 文字、按键和启动应用。
- 拒绝过期观察、重复操作和锁屏状态下的输入。
- 在 `agent_helpers.py` 工作区中保存可复用的应用操作。

普通界面操作只需 Python 标准库和 ADB，无需在手机上安装额外辅助应用。

## 快速开始

准备 Python 3.10+ 和 [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools)，连接手机、授权 USB 调试并解锁。

```sh
git clone https://github.com/AndrewDzzz/andriod-harness.git
cd andriod-harness
python scripts/android_harness.py devices --adb /absolute/path/to/adb
python android-harness.py --workspace work/my-phone --init --adb /absolute/path/to/adb --serial YOUR_DEVICE_SERIAL
python android-harness.py --workspace work/my-phone --file examples/inspect.py
```

替换为你的 ADB 路径和设备序列号。Windows 使用 `adb.exe` 的完整路径。最后一条命令输出当前应用和界面元素，默认不截图。

后续复用同一工作区：

```sh
python android-harness.py --workspace work/my-phone --file examples/screenshot.py
python android-harness.py --workspace work/my-phone --forget
```

第一条命令截图并输出图片路径；第二条删除最近一次观察和截图，保留配置及 helper。

## 配合代理使用

[SKILL.md](SKILL.md) 提供代理操作流程。Runner 预载 `screen_info()`、`find()`、`tap()`、`swipe()` 等函数。应用专用流程写入工作区的 `agent_helpers.py`，详见[扩展指南](references/extending.md)。

## 状态与限制

目前为实验版本。直接输入支持不含 `%` 的可打印 ASCII，部分自绘界面可能无法识别。主机 Python 执行可信代码，不是沙箱；每次操作后都应验证结果。

[隐私说明](references/privacy.md) · [验证范围](docs/validation.md) · [参与贡献](CONTRIBUTING.md) · [可选语音服务](references/local-voice.md)

运行测试：`python scripts/test_harness.py`。

设计参考 [browser-harness](https://github.com/browser-use/browser-harness)。暂未选择再分发许可证。
