import enum

mod_version = "2.1.4"

# Change this whenever the schema of the parts register changes to make sure any json used is up-to-date
expected_json_version = 9

# Game version Data
expected_game_version = "1.116.202.1030"
expected_update_date = "July 1st, 2025"
expected_update_name = "Enchanted by Nature"


class FurryTag(enum.Int):
    # Settings Tags
    LEG_DIGITIGRADE = 1
    LEG_PLANTIGRADE = 2
    PREF_NO_SS_HEADS = 40
    PREF_USE_SS_HAIR = 41
    PREF_USE_NECK_FLUFF = 42
    PREF_EYEBROWS_ALL = 43
    PREF_EYEBROWS_FURRY = 44
    PREF_MATCH_FUR_HAIR = 45
    PREF_UNLOCKED_CHILD_FUR = 46
    PREF_FLAT_SCALY_CHESTS = 47
    PREF_FIXED_HEADS = 48
    PREF_USE_ANIMATED_TAILS = 49
    PREF_HEADS_SHAVED = 50
    PREF_HEADS_FLUFFY = 51
    PREF_USE_DETAILS = 52
    PREF_COMPATIBLE_PRESETS = 53
    PREF_STRICT_CHILD_GENES = 54
    PREF_FURRY_ACCESSORIES = 55
    COLORS_MIXED = 60
    COLORS_NATURAL_PREF = 61
    COLORS_NATURAL_ONLY = 62
    COLORS_COLORFUL_PREF = 63
    COLORS_COLORFUL_ONLY = 64
    AUTO_REMOVE_HAIR_ALL = 70
    AUTO_REMOVE_HAIR_SCALY = 71
    AUTO_REMOVE_BODY_HAIR_ALL = 72
    AUTO_REMOVE_BODY_HAIR_SCALY = 73
    AUTO_REMOVE_FACIAL_HAIR = 74
    AUTO_REMOVE_HATS = 75
    AUTO_REMOVE_SHOES_SOCKS = 76
    AUTO_REMOVE_EARRINGS = 77
    AUTO_REMOVE_PIERCINGS = 78
    AUTO_REMOVE_GLASSES = 79
    AUTO_REMOVE_MAKEUP = 80
    AUTO_REMOVE_BREASTS = 81
    AUTO_REMOVE_CLOTHES = 82

    # Intrinsic Tags
    FRAME_MASCULINE = 120
    FRAME_FEMININE = 121
    STYLE_MASCULINE = 122
    STYLE_FEMININE = 123
    GENDER_MALE = 124
    GENDER_FEMALE = 125
    OCCULT_HUMAN = 130
    OCCULT_SPELLCASTER = 131
    OCCULT_ALIEN = 132
    OCCULT_VAMPIRE = 133
    OCCULT_MERMAID = 134
    OCCULT_WEREWOLF = 135
    OCCULT_PLANTSIM = 136
    OCCULT_FAIRY = 137
    HAIR_NEUTRAL_BLACK = 140
    HAIR_BLACK = 141
    HAIR_DARK_BROWN = 142
    HAIR_WARM_BROWN = 143
    HAIR_BROWN = 144
    HAIR_LIGHT_BROWN = 145
    HAIR_RED = 146
    HAIR_AUBURN = 147
    HAIR_ORANGE = 148
    HAIR_NEUTRAL_BLONDE = 149
    HAIR_LIGHT_BLONDE = 150
    HAIR_BLONDE = 151
    HAIR_DIRTY_BLONDE = 152
    HAIR_PLATINUM = 153
    HAIR_WHITE = 154
    HAIR_WHITE_BLONDE = 155
    HAIR_GRAY = 156
    HAIR_PURPLE_PASTEL = 157
    HAIR_HOT_PINK = 158
    HAIR_DARK_BLUE = 159
    HAIR_TURQUOISE = 160
    HAIR_GREEN = 161
    HAIR_BLACK_SALT_AND_PEPPER = 162
    HAIR_BROWN_SALT_AND_PEPPER = 163
    HAIR_BALD = 164
    AGE_BABY = 170
    AGE_INFANT = 171
    AGE_TODDLER = 172
    AGE_CHILD = 173
    AGE_TEEN = 174
    AGE_YOUNG_ADULT = 175
    AGE_ADULT = 176
    AGE_ELDER = 177
    AGE_GROUP_TEEN_UP = 178
    BODY_FLAT_CHEST = 180
    CAREER_FIREFIGHTER = 190
    CAREER_MAILMAN = 191

    # Part Matching Tags
    HEAD_SAVESTATE = 201
    HEAD_SORAFOXYTEILS = 202
    HEAD_BERNI_SCULPTED = 203
    HEAD_BERNI_STANDARD = 204
    HEAD_BERNI_HUSKY = 205
    HEAD_BERNI_PANDA = 206
    HEAD_BERNI_SCULPTED_CANINE = 207
    HEAD_BERNI_SCULPTED_FELINE = 208
    HEAD_BROKEN = 209
    NECK_STANDARD = 210
    NECK_SEPARATE = 211
    NECK_THIN = 212
    NECK_THICK = 213
    NECK_VERY_THICK = 214
    EAR_NONE = 220
    EAR_CANINE_UP = 221
    EAR_CANINE_DOWN = 222
    EAR_FELINE = 223
    EAR_SHARK = 224
    EAR_HORN = 225
    EAR_DRAGON = 226
    EAR_FOX = 227
    EAR_CANINE_FULL_UP_L = 228
    EAR_CANINE_FULL_UP_R = 229
    EAR_BUNNY = 230
    EARS_SEPARATE = 239
    EARS_UNICORN_HORN = 240
    TAIL_LION = 250
    TAIL_HORSE = 251
    NOSE_CANINE = 260
    NOSE_FELINE = 261
    NOSE_RAT = 262
    NOSE_PIG = 263
    NOSE_BEAK = 274
    FUR_SKIN = 270
    FUR_EYEBROWS = 271
    TEXTURES_SPACE_1 = 280
    TEXTURES_LIMITED = 285
    SLEEVES_ELBOWS = 291
    SLEEVES_KNEES = 292
    SLEEVES_WRISTS = 293
    SLEEVES_ANKLES = 294

    # Species Tags
    FURRYTYPE_HUMAN = 300
    FURRYTYPE_FURRY = 301
    FURRYTYPE_SCALY = 302
    FURRYTYPE_FEATHERY = 303
    SPECIES_CANINE = 310
    SPECIES_FELINE = 311
    SPECIES_LIZARD = 312
    SPECIES_SHARK = 313
    SPECIES_RABBIT = 314
    SPECIES_BAT = 315
    SPECIES_DEER = 316
    SPECIES_DRAGON = 317
    SPECIES_HORSE = 318
    SPECIES_RAT = 319
    SPECIES_SERGAL = 320
    SPECIES_BEAR = 321
    SPECIES_RACOON = 322
    SPECIES_COW = 323
    SPECIES_CHIMERA = 324
    SPECIES_GOAT = 325
    SPECIES_KANGAROO = 326
    SPECIES_RED_PANDA = 327
    SPECIES_HIPPO = 328
    SPECIES_GIRAFFE = 329
    SPECIES_ELEPHANT = 330
    SPECIES_RHINO = 331
    SPECIES_PIG = 332
    SPECIES_BIRD = 333
    SPECIES_HAWK = 334
    SPECIES_EAGLE = 335
    SPECIES_PARROT = 336
    SPECIES_OWL = 337
    SPECIES_PENGUIN = 338
    SPECIES_GRIFFIN = 339
    SPECIES_FLAMINGO = 340
    SPECIES_DODO = 341
    SPECIES_PELICAN = 342
    SPECIES_TOUCAN = 343
    SPECIES_CHICKEN = 344
    SPECIES_PUFFIN = 345
    SPECIES_PEAFOWL = 346
    SPECIES_OSTRICH = 347
    SPECIES_SECRETARY = 348
    SPECIES_DUCK = 351
    SPECIES_SWAN = 352
    VARIETY_TIGER = 380
    VARIETY_LEOPARD = 381
    VARIETY_LION = 382
    VARIETY_TIGERSHARK = 383
    VARIETY_LEOPARDSHARK = 384
    VARIETY_FOX = 385
    VARIETY_DALMATIAN = 386
    VARIETY_PANDA = 387
    VARIETY_ANTELOPE = 388
    VARIETY_UNICORN = 389
    VARIETY_ZEBRA = 390
    VARIETY_DINO = 391
    VARIETY_HYENA = 392
    VARIETY_BOAR = 393
    VARIETY_COCKATIEL = 394
    VARIETY_BALDEAGLE = 395

    # Operation Tags
    MISC_INVALID = 400
    MISC_VALID = 401
    MISC_FURRIFIABLE = 402
    OPERATION_INHERIT = 410
    OPERATION_AGE_UP = 411
    OPERATION_RANDOMIZE_FUR = 412
    OPERATION_UPDATE_PREFS = 413
    OPERATION_RESET_SCULPTS = 414
    CONDITION_NOT_VALID = 440
    CONDITION_NOT_POSSIBLE = 441
    CONDITION_NOT_VALID_ALL = 442
    CONDITION_NOT_POSSIBLE_ALL = 443
    CONDITION_NO_VALID_ALTERNATIVES = 444
    CONDITION_NO_POSSIBLE_ALTERNATIVES = 445
    ADDON_COPY = 480


class ColorFormat(enum.Int):
    BLOCK_COLORS = 0
    FULL_COLORS = 1
    NATURAL_AND_SORA_COLORS = 2
    SAVESTATE_COLORS = 3
    HAIR_COLORS = 4


class FurryFlag(enum.Int):
    # Format Flags
    FORMAT_FULL = 1
    FORMAT_NATURAL_AND_SORA = 2
    FORMAT_SAVESTATE = 3
    FORMAT_HAIR = 4

    # Random Flags
    RANDOMIZE_COLOR = 11
    RANDOMIZE_PART = 12

    # Set Flags
    SET_SAVESTATE = 21
    SET_CYANGEOM_KIDS = 22
    SET_SPRINGROLL_NATURAL = 23
    SET_SPRINGROLL_SORBET = 24
    SET_SPRINGROLL_EXTRA = 25
    SET_SORAFOXYTEILS = 26
    SET_BERNISE = 27
    SET_TOMJJ_1 = 28
    SET_TOMJJ_2 = 29
    SET_LELJAS_HEADS = 30
    SET_ANIMATED_TAILS = 31
    SET_INVISIBLE_CLOTHES = 32

    # Other flags
    INHERITANCE_STRONG = 50


class ColorBlock(enum.Int):
    ssRed = 0
    ssPink = 1
    ssOrange = 2
    ssYellow = 3
    ssLime = 4
    ssGreen = 5
    ssCyan = 6
    ssBlue = 7
    ssPurple = 8
    ssTan = 9
    ssBrown = 10
    ssBlack = 11
    ssWhite = 12

    naYellow = 13
    naBrown = 14
    naRed = 15
    naDark = 16
    naDarkBlue = 17
    naDarkRed = 18
    naDarkGreen = 19
    naDarkPurple = 20
    naBlack = 21
    naGreen = 22
    naTan = 23
    naOrange = 24
    naDirt = 25

    soPink = 26
    soBlue = 27
    soPurple = 28

    noRed = 29
    noRedOrange = 30
    noOrange = 31
    noYellow = 32
    noLime = 33
    noGreen = 34
    noBlueGreen = 35
    noCyan = 36
    noBlue = 37
    noDarkBlue = 38
    noViolet = 39
    noPurple = 40
    noPink = 41
    noHotPink = 42
    noLightRed = 43
    noGray = 44


class ColorIndex(enum.Int):
    ssRed = 0
    ssPink = 1
    ssOrange = 2
    ssYellow = 3
    ssLime = 4
    ssGreen = 5
    ssCyan = 6
    ssBlue = 7
    ssPurple = 8
    ssTan = 9
    ssBrown = 10
    ssBlack = 11
    ssWhite = 12

    naYellow1 = 13
    naYellow2 = 14
    naYellow3 = 15
    naYellow4 = 16
    naYellow5 = 17

    naBrown1 = 18
    naBrown2 = 19
    naBrown3 = 20
    naBrown4 = 21
    naBrown5 = 22

    naRed1 = 23
    naRed2 = 24
    naRed3 = 25
    naRed4 = 26
    naRed5 = 27

    naDark = 28
    naDarkBlue = 29
    naDarkRed = 30
    naDarkGreen = 31
    naDarkPurple = 32

    naBlack1 = 33
    naBlack2 = 34
    naBlack3 = 35
    naBlack4 = 36
    naBlack5 = 37

    naGreen1 = 38
    naGreen2 = 39
    naGreen3 = 40
    naGreen4 = 41
    naGreen5 = 42

    naTan1 = 43
    naTan2 = 44
    naTan3 = 45
    naTan4 = 46
    naTan5 = 47

    naOrange1 = 48
    naOrange2 = 49
    naOrange3 = 50
    naOrange4 = 51
    naOrange5 = 52

    naDirt1 = 53
    naDirt2 = 54
    naDirt3 = 55
    naDirt4 = 56
    naDirt5 = 57

    soPink = 58
    soBlue = 59
    soPurple = 60

    noRed1 = 61
    noRed2 = 62
    noRed3 = 63
    noRed4 = 64

    noRedOrange1 = 65
    noRedOrange2 = 66
    noRedOrange3 = 67
    noRedOrange4 = 68

    noOrange1 = 69
    noOrange2 = 70
    noOrange3 = 71
    noOrange4 = 72

    noYellow1 = 73
    noYellow2 = 74
    noYellow3 = 75
    noYellow4 = 76

    noLime1 = 77
    noLime2 = 78
    noLime3 = 79
    noLime4 = 80

    noGreen1 = 81
    noGreen2 = 82
    noGreen3 = 83
    noGreen4 = 84

    noBlueGreen1 = 85
    noBlueGreen2 = 86
    noBlueGreen3 = 87
    noBlueGreen4 = 88

    noCyan1 = 89
    noCyan2 = 90
    noCyan3 = 91
    noCyan4 = 92

    noBlue1 = 93
    noBlue2 = 94
    noBlue3 = 95
    noBlue4 = 96

    noDarkBlue1 = 97
    noDarkBlue2 = 98
    noDarkBlue3 = 99
    noDarkBlue4 = 100

    noViolet1 = 101
    noViolet2 = 102
    noViolet3 = 103
    noViolet4 = 104

    noPurple1 = 105
    noPurple2 = 106
    noPurple3 = 107
    noPurple4 = 108

    noPink1 = 109
    noPink2 = 110
    noPink3 = 111
    noPink4 = 112

    noHotPink1 = 113
    noHotPink2 = 114
    noHotPink3 = 115
    noHotPink4 = 116

    noLightRed1 = 117
    noLightRed2 = 118
    noLightRed3 = 119
    noLightRed4 = 120

    noGray1 = 121
    noGray2 = 122
    noGray3 = 123
    noGray4 = 124
