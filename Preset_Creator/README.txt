PRESET CREATOR README

The preset creator adds a cheat into the game that will generate a furrifier addon (.ffa) file from any premade sim's appearance.
The resulting addon will add a preset to the furrifier's menu, allowing you to convert a sim to match that appearance in another save file.
Generated presets will also be automatically applied to sims if the furrifier is in automatic mode.

To generate a preset for a premade sim, use this cheat in the cheat console (CTRL-SHIFT-C):
create_preset [preset name]
OR
create_preset [sim name] [preset name]

The first option generates a preset for the current sim, the second generates it for a given sim. 
If your preset name contains more than one word, it must be surrounded by quotes: "".

Examples:
create_preset "Rabbit Jasmine"
create_preset Vladislaus Straud "Vampire Bat Vlad" 
create_preset "Tony's version of a Seagull Yuki Behr"
create_preset Johnny Zest Zagon

There is another cheat for making 'generic' presets, that can be applied to ANY sim, regardless of name. The cheat works the same way:
create_generic_preset [preset name]
OR
create_generic_preset [sim name] [preset name]


This should generate a .ffa file with the preset name in the same location as the preset creator.
Once generated, the .ffa file can be used anywhere in your mods folder, shared, or manually edited for more control (see the custom addons documentation)


