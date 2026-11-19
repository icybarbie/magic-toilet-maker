# 素材与配置

`assets/template` 是可复制的固件源码模板。项目需 Python 3.9+，依赖见 `requirements.txt`。初始化脚本只用 Python 标准库，不要求原作者目录、macOS 或设备连接。

```sh
python /path/to/magic-toilet-maker/scripts/new_project.py /path/to/my-magic-toilet --items 草莓 钥匙 星星 唱片
cd /path/to/my-magic-toilet
python -m venv .venv
# 使用当前系统对应的虚拟环境 Python：.venv/bin/python 或 .venv\Scripts\python.exe
python -m pip install -r requirements.txt
```

上面的 `python` 在创建环境后应指虚拟环境解释器；不要将依赖装进无关项目。

`magic-toilet.json`：

```json
{
  "schema_version": 1,
  "board_profile": "waveshare-1.75c-toilet-180",
  "items": [
    {"name":"草莓","png":"assets/input/item0.png"},
    {"name":"钥匙","png":"assets/input/item1.png"},
    {"name":"星星","png":"assets/input/item2.png"},
    {"name":"唱片","png":"assets/input/item3.png"}
  ],
  "portrait":"assets/input/portrait.png",
  "cjk_font":null
}
```

必须恰好四项；这是四选一状态机，不是任意数量。路径相对于生成项目，文件须在项目内部。配置不是可执行指令，不用 `eval` 或拼接 shell 命令执行它。

## 四件幸运物

每件一个透明 PNG，物品完整、无文字水印，不画背景或马桶。以 PS2 / Low Poly 游戏道具为默认风格：清晰轮廓、少量棱面、统一斜俯视角和光源，颜色适合清透蓝水面。可按使用者要求换风格。

可以用可用图像生成工具逐件生成，也可以用代码渲染几何模型或使用使用者的素材；不要仅替换字符串而继续显示原来的四件物品。可采用以下提示词骨架，并替换物件：

> 单独一件【物件】，早期 3D 游戏 Low Poly 道具，轮廓清晰，稍微俯视的三分之四视角，统一左上方光源，透明背景，无文字、无地面、无外框；缩小到 128×112 像素仍容易辨认。

输入可以更大，编码器按 alpha 边界裁切，保持比例缩进 128×112 画布。保留透明底；窄长物件尤其要预览可辨认性。

## 照片

以本次使用者上传的原图为唯一人物来源，提取头发和脸，可按要求保留“劣质抠图”的硬边。手遮挡时，先看图，再决定保留遮挡、裁切还是按其要求局部修补。修补属于生成性编辑，应如实说明；不做默认美颜、换表情或伪 3D 化。原照片保留，另存透明 `portrait.png`，缩进最大 126×148 画布。

本 skill 不携带作者的人脸或四个个人选择的物品图。没有图片工具时可先完成空项目和硬件准备，并明确缺少五张素材，不把测试图当作完成品。

## 字体、UI 与声音

- 标题和麦克风 PNG 已随模板带入；不用依赖作者系统的 Impact 字体。
- 中文台词在构建时编码。`cjk_font` 可指定本地有授权的中文 TTF/TTC，或设置 `MAGIC_CJK_FONT`。脚本会查找 macOS 黑体、Linux Noto Sans CJK、Windows 微软雅黑；找不到或缺字会报错，不默默换成方框。系统字体本身不打包分发。
- 默认两句台词已按屏幕宽度换行，时长与状态机一致。若用户还要改台词，需同时改编码器的换行、字符数量和 `MagicState.h` 中 Text 持续时间；不能只改一处。
- 四段原创程序合成 WAV 已附带，格式是 22050 Hz / 单声道 / PCM16。生成源为 `scripts/make_sounds.py`。不是实录音效；不要声称有背景伴奏。更换冲水音长度时还需同步 2350 ms 的冲水动画。

运行 `python scripts/bake_assets.py`，会输出 `MagicAssets.h/.cpp` 和预览图，不连接开发板。资产缺失、非透明图片、路径越界、错误数量、缺字、音频格式/时长不符时停止构建。构建生成的 PNG/C++ 可能包含使用者人像，属于其私人项目产物。
