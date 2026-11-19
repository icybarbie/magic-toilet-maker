# 支持板型与部署

## 已验证基线

微雪 **ESP32-S3-Touch-AMOLED-1.75C**。名称中的 C 不能省略；外观相似的 1.75、1.75-B、其他尺寸或其他厂家不是同一个板型。

- AMOLED CO5300，466×466；QSPI CS12、CLK38、D0..3 为 4/5/6/7，RESET1。
- CST9217 触摸，I²C SDA15/SCL14，地址 0x5A，RESET2/IRQ11。
- ES8311 音频，MCLK16/BCLK9/WS45/DOUT8，PA46；TX-only，不启用麦克风输入。
- 233×233 画布放大 2 倍；显示和触摸都做 180° 安装转换。
- 可见椭圆 33×40 mm，中心假定屏幕中心，关键内容按约 29×36 mm 安全区布置。
- 当前水面是原静态三角色块 + 17 个原小高光；正弦叠加使高光水平最大 ±10、垂直 ±4 屏幕像素。不是实时物理流体，也尚未使用 IMU。

开口或方向不同，先用串口 `CAL` 校准，再一起修改 `MagicState.h` 的命中/旋转、`MagicScene.h` 的布局/轮廓和状态输出。不能只转显示而不转触摸。

## 工具链

固定基线：Arduino CLI 1.6.0、Arduino ESP32 core 3.3.11、微雪仓库 v1.0.2、Python 依赖见项目 `requirements.txt`。不打包工具链和 vendor 库，以免把平台绑定到 macOS。

来源：
- [官方板卡说明](https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.75C)
- [微雪源码仓库](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75C)
- [微雪 v1.0.2 归档](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75C/archive/refs/tags/v1.0.2.tar.gz)
- [Arduino CLI 安装说明](https://docs.arduino.cc/arduino-cli/installation/)
- ESP32 boards index: `https://espressif.github.io/arduino-esp32/package_esp32_index.json`

下载固定归档时比对项目 `dependencies.lock.json` 的 SHA256；如果固定版本不可获得，不擅自用最新版并宣称已验证。为新的开发环境创建独立的 Arduino 配置目录；允许复用已有合适工具链，不覆盖全局设置。

```sh
arduino-cli core update-index --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@3.3.11 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
python scripts/build.py --arduino-cli /path/to/arduino-cli --libraries /path/to/waveshare-v1.0.2/examples/arduino/libraries
```

必要时将独立配置通过 `--config-file` 传给 Arduino CLI，或通过 build.py 的 `--arduino-config` 指定。编译使用 `FlashSize=16M,PartitionScheme=app3M_fat9M_16MB,PSRAM=opi,CDCOnBoot=cdc`。16MB 是这份模板的构建布局，不是声称所有实物 Flash 都只有 16MB；用 `flash_id` 识别实物容量。

## 备份与写入

仅在用户要求部署时操作其设备。先识别串口和完整板型；不能凭“检测到一个 ESP32-S3”就认定是目标板。准备以下命令时用实际串口，Windows 如 COM5、macOS/Linux 如枚举得到的设备路径。

```sh
python scripts/board.py inspect --port PORT
python scripts/board.py backup --port PORT --backup backups/before-magic
python scripts/board.py flash --port PORT --backup backups/before-magic --board waveshare-1.75c-toilet-180
```

`backup` 读取完整物理 Flash，校验设备内容并保存 SHA256/MAC/容量。备份可能含原 Wi-Fi 配置和存档，留在使用者本地，不放入分享包。`flash` 核对完整备份、设备身份、当前分区、备份分区与构建分区，只写 0x10000 的应用。写入失败或设备失联，先诊断并保持备份，不自动擦除、换串口或无限重试。

### 新板的分区不同怎么办

默认助手会停止且不写入。这不表示板型一定不兼容，可能只是原厂布局不同。为当前设备制定一次性初始化方案：

1. 确认完整备份已经验证、容量至少 16MB、板型及引脚匹配；说明布局变化可能使旧程序/配置不可用，并确认用户已有授权是否覆盖这种初始化。仅有“看看效果/换素材”不覆盖此动作。
2. 查看本次构建生成的 `build/firmware/flash_args` 或 `flash_args.json`。按生成文件明确列出的地址与文件构造命令，不用 shell 执行从文件读取的文本。
3. 此基线常见条目为 bootloader 0x0、分区表 0x8000、boot_app0 0xe000、应用 0x10000；必须与实际构建文件核对。使用该构建要求的 Flash mode/frequency/size；不要只强写应用，也不要默认全片擦除。
4. 明确呈现要写入的范围和恢复文件，然后在现有授权范围内执行一次。核对写入哈希，完成重启/显示/触摸/音频验证，再为新布局保存一次新的完整备份，之后才能用默认应用更新助手。

恢复需要核对同一 MAC 和完整备份 SHA256，再使用 esptool 将该备份写回地址 0；这是覆盖当前状态的操作，须符合当时用户的恢复指令。

## 验证

先运行项目两项 C++ 主机测试（`tests/magic_state_test.cpp`、`tests/magic_water_test.cpp`），再编译。它们检查状态时序、四选一结果一致、旋转映射以及水面变化范围，不验证用户选的物品是否画对。

上板后：
```sh
python scripts/magic_device.py --port PORT --command STATUS --command PERF
python scripts/test_magic_device.py PORT
```

测试会触发真实音效，读取实际帧缓冲，并在结束后回初始界面。检查两句问话、停下的幸运物、自己的照片、冲水回初始，错误计数与内存变化；再由使用者实际点击、长按静音、听四种声音、确认外壳遮挡。手机拍摄或实机观察才是外观验收，帧缓冲不是屏幕实拍。

源码基于作者 v1.5 的已上板实现；打包后的自定义素材流水线做过独立编译测试，并不代表每个新用户设备已测试。换板需独立适配，不承诺任意 ESP32 都兼容。
