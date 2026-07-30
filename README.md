# Sim Furrifier

This repo has all the source code for the [Sim Furrifier](https://www.nexusmods.com/thesims4/mods/2066?tab=description) Mod, all of its optional scripts, and the [Furry Premade Sims](https://www.nexusmods.com/thesims4/mods/1978) mod. This code was always easy to decompile, but this format is more accessible. It also include a few development tools I used that could be helpful to someone who manages to find them.

## Building

The code was all developed with [Andrew's Sims Modding Tutorial Environment](https://sims4studio.com/thread/15145/started-python-scripting-updated), which the compile.py scripts all use to compile these into usable `.ts4script` files.

## Contents

Included are the code for the following mods:

- `Furry_Premade_Sims`: The source code for the Furry Premade Sims mod. The code is very minimal, as it essentially just acts as a wrapper for the Furry Presets data, which also checks if the furrifier and required furry assets are installed, notifying the user if they are not. It also includes a translator helper script that converts a JSON preset list into a large python dict.
- `Preset_Creator`: The source code for the Preset Creator tool optionally included with the Sim Furrifier.
- `Sim Furrifier`: The source code for the sim furrifier. Also included are the furrifier's package file, and the docx version of the Custom Addon instructions.
- `Template_Exporter`: A private tool used for Furry Premade Sims. Works similarly to the Preset Creator, but is less friendly, targets more sims at once and has many more conditions.
- `Tenant_Spawner`: A private tool that forces all the Tenant sim households to spawn so they can be modified and tested.

## Permissions

This source code has the same permissions as the mods themselves, you can do pretty much anything you want with it, but please ask me first if you're doing anything more than privately modifying it or using code snippets from it.
