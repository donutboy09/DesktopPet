# 桌面宠物 Desktop Pet

一只住在你桌面上的小猫 / 小狗，会走动、眨眼、睡觉、被你逗。右键它还能顺手帮你清理垃圾文件。

跨平台：Windows / macOS 都能跑。用 Python + PySide6 编写，宠物形象由代码绘制，不需要任何图片素材。

![桌面宠物](screenshots/pets.png)

## 下载

| 平台 | 文件 | 说明 |
| --- | --- | --- |
| **Windows** | [**DesktopPet.exe**](https://github.com/donutboy09/DesktopPet/releases/latest/download/DesktopPet.exe) | 双击运行，单文件免安装 |
| **macOS** | [**DesktopPet-macos.zip**](https://github.com/donutboy09/DesktopPet/releases/latest/download/DesktopPet-macos.zip) | 解压后双击 `DesktopPet.app` |

全部版本见 [Releases](https://github.com/donutboy09/DesktopPet/releases)。

> 未做代码签名：Windows 首次运行若被 SmartScreen 拦，点「更多信息 → 仍要运行」；macOS 若提示无法打开，右键 →「打开」，或执行 `xattr -dr com.apple.quarantine DesktopPet.app`。

## 功能

宠物行为：
- 一直在桌面上走来走去，会眨眼、发呆、睡觉
- 右键宠物本体就能弹出菜单
- 喂食：投喂小鱼 / 骨头，宠物会低头吃饭，还有饱食度
- 不动：让它停在原地；再点一次恢复自由活动
- 大小：小 / 中 / 大三档
- 鼠标左键拖动可以搬走它
- 双击它 = 逗它玩（冒爱心）
- 位置、种类、大小、是否自由活动都会自动记住

右键菜单（在宠物或托盘图标上都能打开）：
- 喂食、逗它玩、睡觉 / 叫醒、不动
- 清理缓存、清理临时文件、清理下载文件夹、清空回收站、清理桌面无用文件
- 查看磁盘占用
- 切换宠物（小猫 / 小狗）、大小、隐藏、退出

清理功能（都会先扫描预览，勾选后再删）：
- 清空缓存
- 清理临时文件
- 清理下载文件夹
- 清空回收站 / 废纸篓
- 清理桌面无用文件（`.DS_Store`、`Thumbs.db`、`~$` 等）
- 查看磁盘占用

## 安全设计

- **先预览再确认**：所有清理都会先列出文件、大小，勾选后才执行。
- **默认不误删**：下载文件夹默认全部不勾选，临时文件只列出 1 天前的。
- **优先回收站**：macOS 上默认移到废纸篓（可恢复）；只有你点“永久删除”才会真正删除。
- **只碰白名单目录**：临时目录、缓存目录、下载、桌面、回收站，绝不越界。
- **跳过软链接**：不会顺着快捷方式删到别的地方。

## 运行

macOS / Linux：

```bash
cd DesktopPet
chmod +x run.sh
./run.sh
```

Windows：双击 `run.bat`，或在命令行运行：

```bat
cd DesktopPet
run.bat
```

首次运行会自动创建虚拟环境并安装依赖（需要联网，PySide6 较大，约 100MB+）。

## 打包成独立程序（可选）

先安装 PyInstaller：

```bash
.venv/bin/python -m pip install pyinstaller
```

Windows 打包成 exe：

```bat
.venv\Scripts\pyinstaller --noconfirm --windowed --name DesktopPet --icon icon.ico main.py
```

macOS 打包成 app：

```bash
.venv/bin/pyinstaller --noconfirm --windowed --name DesktopPet --icon icon.icns main.py
```

产物在 `dist/DesktopPet/`。

也可以推送 `v*` 标签，或在 GitHub 的 **Actions** 页面手动触发 `Build executables` 工作流，云端会同时产出 Windows 和 macOS 两个包。

## 项目结构

```
DesktopPet/
├── main.py        # 程序入口：窗口、托盘、右键菜单
├── pet.py         # 宠物控件：状态机、动画、拖动、散步
├── pet_art.py     # 用代码绘制小猫 / 小狗
├── cleaner.py     # 扫描与清理逻辑（跨平台）
├── dialogs.py     # 清理预览窗口、磁盘占用窗口
├── make_icon.py   # 生成 icon.ico / icon.icns
├── icon.png / icon.ico / icon.icns
├── requirements.txt
├── run.sh / run.bat
└── README.md
```

## 自己改一改

- 换宠物颜色 / 造型：编辑 `pet_art.py` 里的 `PALETTES` 和 `draw_pet`。
- 加清理目标：在 `cleaner.py` 里加一个 `scan_xxx()`，再到 `main.py` 的 `_build_menu` 里加一行菜单。
- 加更多动作：在 `pet.py` 的状态机 `_tick` 里扩展。

## 常见问题

- macOS 首次运行可能提示“来自身份不明的开发者”，在「系统设置 → 隐私与安全性」里点“仍要打开”。
- 看不到宠物？检查菜单栏右侧的托盘图标（一个橙色小爪子），单击可显示 / 隐藏。
- 清理缓存后个别 App 首次启动会稍慢，属正常现象。
