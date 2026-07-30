
# on_icon = 0x016fb76a7867d2f0
# off_icon = 0xd8a7a1ea986b7b0e
# furry_icon = 0x3d5044362259570d
# scaly_icon = 0x3D5044362259570D
#
# settings = {
#     "Automation_Settings": {
#         "type": "category",
#         "name": 0xE4F7E1FC,
#         "description": 0x3DFF08EA,
#         "title": 0xE4F7E1FC,
#         "subtitle": 0x3DFF08EA,
#         "icon": 0x439BDC3E41EA0295,
#         "contains": {
#             "Demo": {
#                 "type": "toggle",
#                 "description": 0xF9E8161A,
#                 "values": ["False", "True"],
#                 "names": [0xB4D78F5E, 0x217E907C],
#                 "icons": [off_icon, on_icon],
#                 "requirements": ""
#             },
#             "Automatic_Mode": {
#                 "type": "toggle",
#                 "description": 0xF9E8161A,
#                 "values": ["False", "True"],
#                 "names": [0xB4D78F5E, 0x217E907C],
#                 "icons": [off_icon, on_icon]
#             },
#             "Exempt_Active_Household": {
#                 "type": "toggle",
#                 "description": 0xDCE138BA,
#                 "values": ["True", "False"],
#                 "names": [0x2E2EF43B, 0x7148151E],
#                 "icons": [on_icon, off_icon]
#             },
#             "Exempt_Played_Household": {
#                 "type": "toggle",
#                 "description": "",
#                 "values": ["False", "True"],
#                 "names": [],
#                 "icons": [off_icon, on_icon]
#             },
#             "Exempt_Premade_Sims": {
#                 "type": "toggle",
#                 "description": "",
#                 "values": ["False", "True"],
#                 "names": [],
#                 "icons": [off_icon, on_icon]
#             }
#         }
#     },
#     "Genetics_Settings": {
#         "type": "category",
#         "name": 0,
#         "description": 0,
#         "title": "",
#         "subtitle": "",
#         "icon": 0,
#         "contains": {
#             "Furry_Genetics": { # This one furrifies kids aging up, even if exempt
#                 "type": "toggle",
#                 "description": "",
#                 "values": ["True", "False"],
#                 "names": [],
#                 "icons": [on_icon, off_icon]
#             },
#             "Age_Up_Helper": {
#                 "type": "toggle",
#                 "description": 0x460F49C2,
#                 "values": ["True", "False"],
#                 "names": [0x6D23C638, 0xA0ED774D],
#                 "icons": [on_icon, off_icon]
#             },
#             "Species_Genetics": {
#                 "type": "toggle",
#                 "description": 0xDCE138BA,
#                 "values": ["True", "False"],
#                 "names": [0x2E2EF43B, 0x0BCFDBDB],
#                 "icons": [on_icon, off_icon]
#             },
#             "Correct_Teen_Species": {
#                 "type": "toggle",
#                 "description": 0xC1D8E005,
#                 "values": ["True", "False"],
#                 "names": [0x361FF68E, 0x63C805C5],
#                 "icons": [off_icon, on_icon]
#             },
#             "Strict_Genetics": {
#                 "type": "toggle",
#                 "description": 0x421560D3,
#                 "values": ["False", "True"],
#                 "names": [0x6813FE9B, 0x4BC77641],
#                 "icons": [off_icon, on_icon]
#             }
#         }
#     },
#     "Preferences": {
#         "type": "category",
#         "name": 0x129B49F9,
#         "description": 0x5A6B9177,
#         "title": 0x129B49F9,
#         "subtitle": 0x5A6B9177,
#         "icon": 0xCD8C8B0E318E84AC,
#         "contains": {
#             "Part_Options": {
#                 "type": "category",
#                 "title": 0xF95AD17C,
#                 "subtitle": 0x5A6B9177,
#                 "name": 0xF95AD17C,
#                 "description": 0x48E29BF2,
#                 "icon": 0x2c0a00e14a430941,
#                 "contains": {
#                     "Leg_Type": {
#                         "type": "hybrid",
#                         "description": 0xFABA3CFE,
#                         "title": 0xC1D42ED5,
#                         "subtitle": 0x30DFCBE5,
#                         "values": ["Digitigrade", "Plantigrade", "Either", "None"],
#                         "names": [0xFF675AB3, 0x71FF504F, 0x348127A6, 0xDBEB40F0],
#                         "icons": [0xf823d47d38ff1e5d, 0xf823d47d38ff1e5d, 0xf823d47d38ff1e5d, 0xf823d47d38ff1e5d],
#                         "contains": {
#                             "Digitigrade": {
#                                 "type": "set",
#                                 "description": 0xDEB41EDE,
#                                 "target": "Preferences.Leg_Type",
#                                 "name": 0x3E02186B,
#                                 "icon": 0
#                             },
#                             "Plantigrade": {
#                                 "type": "set",
#                                 "description": 0x8EED995F,
#                                 "target": "Preferences.Leg_Type",
#                                 "name": 0x4B144169,
#                                 "icon": 0
#                             },
#                             "Either": {
#                                 "type": "set",
#                                 "description": 0xD34F9BB4,
#                                 "target": "Preferences.Leg_Type",
#                                 "name": 0xB2C6A01,
#                                 "icon": 0
#                             },
#                             "None": {
#                                 "type": "set",
#                                 "description": 0xE9512E49,
#                                 "target": "Preferences.Leg_Type",
#                                 "name": 0x1E8DFBC3,
#                                 "icon": 0
#                             },
#                         }
#                     },
#                     "Head_Type": {
#                         "type": "hybrid",
#                         "description": 0xC57779DD,
#                         "title": 0x05CDB892,
#                         "subtitle": 0xC57779DD,
#                         "values": ["Fluffy", "Shaved", "Either"],
#                         "names": [0xD95DA394, 0xB23CD3AD, 0x26B8415A],
#                         "icons": [0xC1C2D58B9B7CEA94, 0xC1C2D58B9B7CEA94, 0xC1C2D58B9B7CEA94],
#                         "contains": {
#                             "Fluffy": {
#                                 "type": "set",
#                                 "description": 0xDEB41EDE,
#                                 "target": "Preferences.Head_Type",
#                                 "name": 0x3E02186B,
#                                 "icon": 0
#                             },
#                             "Shaved": {
#                                 "type": "set",
#                                 "description": 0xDEB41EDE,
#                                 "target": "Preferences.Head_Type",
#                                 "name": 0x2CE911D9,
#                                 "icon": 0,
#                                 "requirements": [("Set.SET_LELJAS_HEADS", 0x0731DEAF), ("Set.SET_TOMJJ_2", 0x0731DEAF)]
#                             },
#                             "Either": {
#                                 "type": "set",
#                                 "description": 0x2883904B,
#                                 "target": "Preferences.Head_Type",
#                                 "name": 0xB2C6A01,
#                                 "icon": 0
#                             },
#                             "Avoid_SaveState_Heads": {
#                                 "type": "toggle",
#                                 "description": 0xF9203A5A,
#                                 "values": ["False", "True"],
#                                 "names": [0xDF50B621, 0x1C5C88D8],
#                                 "icons": [off_icon, on_icon],
#                                 "requirements": {
#                                     "False": [("SET.SET_SORAFOXYTEILS", 0x09685139), ("SET.SET_BERNISE", 0x09685139)]
#                                 }
#                             }
#                         }
#                     },
#                     "Furry_Hairs": {
#                         "type": "toggle",
#                         "description": 0x9D10F740,
#                         "values": ["False", "True"],
#                         "names": [0x364D5F8D, 0x9DC92868],
#                         "icons": [off_icon, on_icon]
#                     },
#                     "Neck_Fluff": {
#                         "type": "toggle",
#                         "description": 0x6620A677,
#                         "values": ["False", "True"],
#                         "names": [0x2E69423C, 0x7F45DD90],
#                         "icons": [off_icon, on_icon],
#                         "requirements": {
#                             "False": [("Setting.Preferences.Removable_Parts.Hair", 0xE4912615), ("Setting.Preferences.Part_Options.Use_Furry_Hairs", 0xE4912615)]
#                         }
#                     },
#                     "Furry_Eyebrows": {
#                         "type": "toggle",
#                         "description": 0xEA696BF5,
#                         "values": ["True", "Furry_Only", "False"],
#                         "names": [0xAFB00296, 0x85037564, 0x79C27604],
#                         "icons": [on_icon, furry_icon, off_icon],
#                         "requirements": {
#                             "False": [("Set.SET_SORAFOXYTEILS", 0x86579025)]
#                         }
#                     },
#                     "Furry_Hats_And_Accessories": {
#                         "type": "toggle",
#                         "description": 0x17780700,
#                         "values": ["True", "False"],
#                         "names": [0x701EB620, 0x6CE9C882],
#                         "icons": [on_icon, off_icon],
#                         "requirements": {
#                             "False": [("Set.SET_SORAFOXYTEILS", 0x86579025)]
#                         }
#                     },
#                     "Animated_Tails": {
#                         "type": "toggle",
#                         "description": 0xFB7198A8,
#                         "values": ["False", "True"],
#                         "names": [0x668AB168, 0xF19D55C1],
#                         "icons": [off_icon, on_icon],
#                         "requirements": {
#                             "False": [("Set.SET_ANIMATED_TAILS", 0xBA6A18DE)]
#                         }
#                     },
#                     "Texture_Details": {
#                         "type": "toggle",
#                         "description": 0xD156E738,
#                         "values": ["False", "True"],
#                         "names": [0x7EAD0088, 0x4A1CF928],
#                         "icons": [off_icon, on_icon]
#                     }
#                 }
#             },
#             "Fur_Colors": {
#                 "type": "hybrid",
#                 "description": 0x30DFCBE5,
#                 "title": 0xC1D42ED5,
#                 "subtitle": 0x30DFCBE5,
#                 "values": ["Natural_Only", "Natural_Preferred", "Mixed", "Colorful_Preferred", "Colorful_Only"],
#                 "names": [0x6C336808, 0x33C85908, 0xDE80F776, 0xA395C7CA, 0xDA25B11C],
#                 "icons": [0xc368fecd5e220712, 0xd492b4fdb178cb44, 0x38e5d372d2f30ca2, 0x14ab30842d1923e7, 0x208dc679fae2140d],
#                 "contains": {
#                     "Natural_Only": {
#                         "type": "set",
#                         "description": 0x1D66A79A,
#                         "target": "Preferences.Fur_Colors",
#                         "name": 0xB5E349CF,
#                         "icon": 0xC368FECD5E220712
#                     },
#                     "Natural_Preferred": {
#                         "type": "set",
#                         "description": 0xCD60B386,
#                         "target": "Preferences.Fur_Colors",
#                         "name": 0x32E634E6,
#                         "icon": 0xD492B4FDB178CB44
#                     },
#                     "Mixed": {
#                         "type": "set",
#                         "description": 0xCE948E2F,
#                         "target": "Preferences.Fur_Colors",
#                         "name": 0xF1298987,
#                         "icon": 0x38E5D372D2F30CA2
#                     },
#                     "Colorful_Preferred": {
#                         "type": "set",
#                         "description": 0x762260FC,
#                         "target": "Preferences.Fur_Colors",
#                         "name": 0x4EB1FAB5,
#                         "icon": 0x14AB30842D1923E7
#                     },
#                     "Colorful_Only": {
#                         "type": "set",
#                         "description": 0x2D7FA0B5,
#                         "target": "Preferences.Fur_Colors",
#                         "name": 0x9335E849,
#                         "icon": 0x208DC679FAE2140D
#                     },
#                     "Match_Fur_To_Hair": {
#                         "type": "toggle",
#                         "description": 0x88FDC419,
#                         "values": ["False", "True"],
#                         "names": [0x973CEDC1, 0xBC0B628D],
#                         "icons": [off_icon, on_icon]
#                     }
#                 }
#             },
#             "Removable_Parts": {
#                 "type": "category",
#                 "name": 0x1325F1AD,
#                 "description": 0xF06B62EB,
#                 "title": 0x1325F1AD,
#                 "subtitle": 0,
#                 "icon": 0xd101c931783b4606,
#                 "contains": {
#                     "Hair": {
#                         "type": "toggle",
#                         "description": 0x5DB0D0E0,
#                         "values": ["False", "True", "Furry_Only"],
#                         "names": [0xE581E35E, 0x75A9E16F, 0x7F79143C],
#                         "icons": [off_icon, on_icon, furry_icon]
#                     },
#                     "Body_Hair": {
#                         "type": "toggle",
#                         "description": 0x65319AD0,
#                         "values": ["False", "True", "Furry_Only"],
#                         "names": [0x44DF7553, 0xABE01630, 0x44DF7553],
#                         "icons": [off_icon, on_icon, furry_icon]
#                     },
#                     "Facial_Hair": {
#                         "type": "toggle",
#                         "description": 0x19D336A9,
#                         "values": ["True", "False"],
#                         "names": [0xCE0B30B7, 0x6ADE523D],
#                         "icons": [on_icon, off_icon]
#                     },
#                     "Hats": {
#                         "type": "toggle",
#                         "description": 0xA0A56556,
#                         "values": ["True", "False"],
#                         "names": [0xDD3CE3A, 0xC5E1BA98],
#                         "icons": [on_icon, off_icon]
#                     },
#                     "Socks_and_Shoes": {
#                         "type": "toggle",
#                         "description": 0x34C0CD7,
#                         "values": ["True", "False"],
#                         "names": [0xCEC9DC69, 0xEB2CA9C],
#                         "icons": [on_icon, off_icon]
#                     },
#                     "Earrings": {
#                         "type": "toggle",
#                         "description": 0xACA3454C,
#                         "values": ["False", "True"],
#                         "names": [0x5B4A9FF8, 0x5E5938A4],
#                         "icons": [off_icon, on_icon]
#                     },
#                     "Piercings": {
#                         "type": "toggle",
#                         "description": 0x311B3F06,
#                         "values": ["True", "False"],
#                         "names": [0x774E5B38, 0x88FB35B9],
#                         "icons": [on_icon, off_icon]
#                     },
#                     "Glasses": {
#                         "type": "0x2990CF37",
#                         "description": 0xACA3454C,
#                         "values": ["False", "True"],
#                         "names": [0x8E83AE1D, 0x45F9AD82],
#                         "icons": [off_icon, on_icon]
#                     },
#                     "Makeup": {
#                         "type": "toggle",
#                         "description": 0x850570EB,
#                         "values": ["True", "False"],
#                         "names": [0xD2A1D94E, 0x38C91118],
#                         "icons": [on_icon, off_icon]
#                     },
#                     "Breasts": {
#                         "type": "0xEA8286E2",
#                         "description": 0xACA3454C,
#                         "values": ["False", "Scaly_Only"],
#                         "names": [0x48A5592A, 0xCAF6E88F],
#                         "icons": [off_icon, scaly_icon]
#                     },
#                     "Clothes": {
#                         "type": "0xEA8286E2",
#                         "description": 0xC6EA70B2,
#                         "values": ["False", "True"],
#                         "names": [0x95BDBC1D, 0x58DCE76E],
#                         "icons": [off_icon, on_icon],
#                         "requirements": {
#                             "False": [("Set.SET_INVISIBLE_CLOTHES", 0xC9F6A363)]
#                         }
#                     }
#                 }
#             },
#             "Manual_Fixes": {
#                 "type": "category",
#                 "name": 0x37404B4B,
#                 "description": 0x9BC80502,
#                 "title": 0xF95AD17C,
#                 "subtitle": 0x5A6B9177,
#                 "icon": 0x9f29cf5d1f6002ae,
#                 "contains": {
#                     "Unlock_Child_Fur": {
#                         "type": "toggle",
#                         "description": 0xE49F39BE,
#                         "values": ["False", "True"],
#                         "names": [0xDC3AAFCE, 0xC0E3C3CF],
#                         "icons": [off_icon, on_icon]
#                     },
#                     "Frame_Restricted_Heads": {
#                         "type": "toggle",
#                         "description": 0x3C5B2A8E,
#                         "values": ["False", "True"],
#                         "names": [0x58DCE1E6, 0x66C275DF],
#                         "icons": [off_icon, on_icon]
#                     }
#                 }
#             },
#             "Apply_Preferences": {
#                 "type": "category",
#                 "name": 0xB1ADDAE8,
#                 "description": 0xF93F13C6,
#                 "title": 0xB1ADDAE8,
#                 "subtitle": 0xEAAC7433,
#                 "icon": 0x5a0e4da0df3e7f12,
#                 "contains": {
#                     "To_Sim": {
#                         "type": "action",
#                         "name": 0x20428B45,
#                         "description": 0xDEFBB5A2,
#                         "icon": 0x8A69B6D34FD4AFA3
#                     },
#                     "To_World": {
#                         "type": "action",
#                         "name": 0xB9E1B31,
#                         "description": 0xA5C4EDD4,
#                         "icon": 0x72E2E4E19CEBDAF7
#                     }
#                 }
#             }
#         }
#     }
# }
#
# def get_settings():
#     return settings
