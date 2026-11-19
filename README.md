# Magic Toilet Maker 🐚🚽

**Software-only release. No enclosure models, CAD files or printing materials are included.**

**Build your own tiny cyber toilet—with four lucky objects you choose and a photo of your own face.**

[中文使用说明](README.zh-CN.md) · [AI skill instructions](SKILL.md) · [Hardware](references/hardware.md)

Created by [IcyBarbie](https://github.com/icybarbie), with Codex-assisted development. This repository contains an AI-readable skill, customizable ESP32 firmware, asset tools, synthesized sound effects.

## What it does

1. Tap the microphone icon: a pretend listening animation plays, followed by a fixed question about your lucky object.
2. Four custom objects shuffle rapidly; one appears with a short fart sound.
3. Tap the microphone again: a second fixed question asks who is the best-looking person in the world. Your photo appears.
4. Tap the face to flush it away and return to the clear, low-poly water.

Includes magic, water, fart and flush sounds. Hold the microphone for about 850 ms to mute. The microphone button **does not record or recognize speech**. The firmware runs locally; there is no cloud AI runtime or lid-open sensor in this version. AI helps you create and customize the project.

## Hardware

- **Waveshare ESP32-S3-Touch-AMOLED-1.75C**, with its original metal enclosure. The **C** matters; other boards need adaptation.
- USB data cable, a computer.
- Default installation: connector at the top, display and touch rotated 180°, approximately **33 × 40 mm** visible opening.

Read [hardware and flashing instructions](references/hardware.md) before connecting or writing a board.

## Use with an AI coding assistant

Download this repository from **Code → Download ZIP**, extract it, and give your assistant access to the folder. Ask it to read `SKILL.md` and the linked reference files. An assistant with local file access and command execution can follow the workflow; image generation/editing requires an available image tool or your prepared transparent PNGs. A text-only chatbot can explain the steps, but cannot execute them on your computer.

Example prompt:

> Read SKILL.md in this folder and help me make my own Magic Toilet. My four lucky objects are a strawberry, a key, a star and a record. Use the portrait I provide. My board is a Waveshare ESP32-S3-Touch-AMOLED-1.75C. Prepare and preview the assets before building; flash the board only when I ask.

For a skill-aware assistant, install this folder as `magic-toilet-maker` using that assistant's skill installation mechanism. For Codex, the repository can be provided to its skill installer. Other assistants can read the same Markdown instructions without a Codex-specific runtime.

## Manual quick start

Requires Python 3.9+. Run this from the downloaded repository:

```sh
python3 scripts/new_project.py ../my-magic-toilet --items strawberry key star record
cd ../my-magic-toilet
python3 -m venv .venv
# macOS/Linux; on Windows use .venv\Scripts\Activate.ps1
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Add **five transparent PNGs** to `assets/input/`: `item0.png` through `item3.png`, and `portrait.png`. Changing the object names alone does not change their pictures. The repository intentionally includes no personal portrait or default set of four lucky-object images.

Set `cjk_font` in `magic-toilet.json` to an available Chinese-capable font if automatic discovery fails. The default on-screen questions remain Chinese; translating the UI requires updating text layout and timing too.

```sh
python scripts/bake_assets.py
```

Inspect `build/asset-preview/contact-sheet.png`. Then follow the pinned toolchain, build and backup-first flashing workflow in [hardware.md](references/hardware.md). Creating a project or baking assets does not access a board.

## What is verified

The original v1.5 implementation ran on the author's board. The customizable template has passed asset-generation, state-machine, water-animation and offline backup-guard tests, plus a firmware compile. This does not mean every new board has been tested. The generic flashing helper has not been validated on a second physical board. Windows/Linux device operation is not physically verified.

This repository shares the electronic interaction software only. Physical enclosure designs, CAD files, printable parts, hinge designs and manufacturing documentation are excluded. Do not copy them from other local projects into this repository.

## Development checks

Install the template Python requirements and a CJK font (for example Noto Sans CJK), then:

```sh
python -m unittest discover -s tests -v
c++ -std=c++17 assets/template/tests/magic_state_test.cpp -o /tmp/magic-state-test
/tmp/magic-state-test
c++ -std=c++17 assets/template/tests/magic_water_test.cpp -o /tmp/magic-water-test
/tmp/magic-water-test
```

Tests use synthetic shapes, never a person's photo or a connected board. Firmware builds additionally require the toolchain in `references/hardware.md`.

## Privacy and licensing

Keep your custom project separate from this repository. Your photo, generated image headers, board backups, serial identity and credentials belong in your local project, not in contributions. Please open issues without personal photos or raw flash dumps.

Project-authored code, documentation and included assets are available under the [MIT License](LICENSE). The adapted Espressif ES8311 driver retains its **Apache-2.0** license; see [third-party notices](assets/template/THIRD_PARTY_NOTICES.txt). External toolchains, libraries, fonts and user-provided images retain their own licenses.
