# CompositorWindows 简体中文界面

基于 [Cengokill/CompositorWindows 1.1.0](https://github.com/Cengokill/CompositorWindows/releases/tag/v1.1.0) 制作的**非官方、部分汉化便携版**，适用于 Windows 11 x64。

原始 Compositor 由 [Robbie Tilton / Wonder Assembly LLC](https://github.com/robbietilton/Compositor) 开发；Windows 移植源自 IAmTheBlurr，并由 Cengokill 维护。本汉化不代表上述作者背书。

## 下载与运行

在本仓库 Releases 中下载 `CompositorWindows-1.1.0-zh-CN-portable.zip`，完整解压后运行 `Compositor.exe`。不要单独移动 EXE 或 DLL。项目文件保存在程序目录之外。

## 翻译范围

约 640 项菜单、工具、设置、提示，以及部分通用按钮。采用常见图像编辑术语，例如图层、蒙版、羽化和剪贴蒙版。

这是部分汉化。部分滤镜名称、颜色通道、混合模式、字体样式和默认图层名仍保留英文。一些界面文字与项目格式或 PSD 标识共用同一字符串，为保留兼容性，没有全局替换这些标识。帮助文档和部分底层错误也仍为英文。

本版本通过修改已发布二进制文件的文字常量制作，**不是从修改后的 C++ 源码重新编译的版本**。脚本只支持下方锁定的 1.1.0 输入，不应应用到其他版本。原本的 Qt 运行库为动态链接；包内保留许可证、第三方通知和上游对应源代码归档。

## 本地复现

使用 Python 3.11 或更新版本：

```powershell
python -m pip install -r requirements.txt
python tools/build.py --input C:\Downloads\CompositorWindows --output C:\Downloads\CompositorWindows-zh-CN
```

`--input` 指向上游 1.1.0 原始便携版解压后包含 `Compositor.exe` 的目录；输出目录必须不存在。脚本在临时目录分析和修改 EXE / Qt Widgets 文字，再复制完整运行文件到输出目录。

上游便携包 SHA256：`5d9d7bf47d9f843e4031b401927f935a9817e91506cd3393ad7f8fbd5a9bec39`。

[翻译对照表](tools/zh-CN.tsv) 同时包含未直接应用的术语，实际保护列表见 [汉化脚本](tools/localize_pe.py)。更新后需要重新分析、测试和制作汉化。

## 已完成的验证

Windows 11 x64 下运行软件内置 `--ui-test`，18 项检查通过，覆盖移动、绘画、撤销、选区、调整、形状、渐变、蒙版、裁剪、缩放和项目保存重开。

同一生成的测试项目由英文原版和汉化版分别导出，PNG 的 SHA256 相同。上述验证未穷举所有文件格式和滤镜组合。

## 许可

保留上游 MIT 许可和作者版权声明。此仓库新增的汉化脚本与译文同样按 MIT 许可提供。第三方组件按各自许可分发；便携包内 `licenses/` 和 `sources/` 保留相关通知和对应来源。Qt Widgets 的本地改动由 `tools/localize_qt_buttons.py` 描述，可在原始运行库上复现。原始 Qt 源码保留在包内 `sources/qtbase-everywhere-src-6.8.3.tar.xz`。
