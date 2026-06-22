# -*- coding: utf-8 -*-
"""
FixtureLibrary - 灯具数据库
内置灯具配置数据，包含常见灯具的通道模式信息
"""

BUILTIN_FIXTURES = [
    # ========== Clay Paky ==========
    {
        "name": "Sharpy",
        "manufacturer": "Clay Paky",
        "type": "光束灯(Beam)",
        "weight": 18.0,
        "power": 470,
        "description": "经典光束灯，189W放电灯泡，极致光束效果，5°光束角",
        "modes": [
            {
                "name": "标准模式 (16CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "色轮1", "offset": 8},
                    {"name": "色轮2", "offset": 9},
                    {"name": "固定图案", "offset": 10},
                    {"name": "旋转图案", "offset": 11},
                    {"name": "棱镜", "offset": 12},
                    {"name": "雾化", "offset": 13},
                    {"name": "光圈", "offset": 14},
                    {"name": "功能", "offset": 15},
                    {"name": "复位", "offset": 16},
                ]
            }
        ]
    },
    {
        "name": "Mythos 2",
        "manufacturer": "Clay Paky",
        "type": "光束灯(Beam)",
        "weight": 27.5,
        "power": 470,
        "description": "多功能灯具，兼具光束和图案功能，6°-50°变焦",
        "modes": [
            {
                "name": "扩展模式 (24CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "色轮1", "offset": 8},
                    {"name": "色轮2", "offset": 9},
                    {"name": "固定图案", "offset": 10},
                    {"name": "旋转图案", "offset": 11},
                    {"name": "图案旋转", "offset": 12},
                    {"name": "棱镜", "offset": 13},
                    {"name": "棱镜旋转", "offset": 14},
                    {"name": "雾化", "offset": 15},
                    {"name": "光圈", "offset": 16},
                    {"name": "变焦", "offset": 17},
                    {"name": "对焦", "offset": 18},
                    {"name": "CTO", "offset": 19},
                    {"name": "CMY", "offset": 20},
                    {"name": "CMY2", "offset": 21},
                    {"name": "CMY3", "offset": 22},
                    {"name": "功能", "offset": 23},
                    {"name": "复位", "offset": 24},
                ]
            }
        ]
    },
    {
        "name": "K-Eye K20",
        "manufacturer": "Clay Paky",
        "type": "染色灯(Wash)",
        "weight": 12.5,
        "power": 240,
        "description": "LED染色灯，RGBW色彩引擎，20°光束角，高CRI",
        "modes": [
            {
                "name": "标准模式 (18CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "红(R)", "offset": 8},
                    {"name": "绿(G)", "offset": 9},
                    {"name": "蓝(B)", "offset": 10},
                    {"name": "白(W)", "offset": 11},
                    {"name": "CTO", "offset": 12},
                    {"name": "色彩宏", "offset": 13},
                    {"name": "变焦", "offset": 14},
                    {"name": "光圈", "offset": 15},
                    {"name": "特殊功能", "offset": 16},
                    {"name": "复位", "offset": 17},
                    {"name": "LED温度", "offset": 18},
                ]
            }
        ]
    },

    # ========== Robe ==========
    {
        "name": "BMFL Spot",
        "manufacturer": "Robe",
        "type": "图案灯(Spot)",
        "weight": 32.0,
        "power": 1700,
        "description": "超亮图案灯，1700W放电光源，5°-55°变焦，双图案轮",
        "modes": [
            {
                "name": "标准模式 (26CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "色轮1", "offset": 8},
                    {"name": "色轮2", "offset": 9},
                    {"name": "CMY", "offset": 10},
                    {"name": "CMY2", "offset": 11},
                    {"name": "CMY3", "offset": 12},
                    {"name": "CTO", "offset": 13},
                    {"name": "固定图案轮", "offset": 14},
                    {"name": "旋转图案轮", "offset": 15},
                    {"name": "图案旋转", "offset": 16},
                    {"name": "棱镜1", "offset": 17},
                    {"name": "棱镜2", "offset": 18},
                    {"name": "棱镜旋转", "offset": 19},
                    {"name": "雾化", "offset": 20},
                    {"name": "光圈", "offset": 21},
                    {"name": "变焦", "offset": 22},
                    {"name": "对焦", "offset": 23},
                    {"name": "效果", "offset": 24},
                    {"name": "功能", "offset": 25},
                    {"name": "复位", "offset": 26},
                ]
            }
        ]
    },
    {
        "name": "MegaPointe",
        "manufacturer": "Robe",
        "type": "光束灯(Beam)",
        "weight": 25.6,
        "power": 470,
        "description": "多功能Beam/Spot/Wash灯具，470W光源，多棱镜效果",
        "modes": [
            {
                "name": "标准模式 (22CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "色彩", "offset": 8},
                    {"name": "色温", "offset": 9},
                    {"name": "图案轮1", "offset": 10},
                    {"name": "图案轮2", "offset": 11},
                    {"name": "图案旋转", "offset": 12},
                    {"name": "棱镜轮1", "offset": 13},
                    {"name": "棱镜轮2", "offset": 14},
                    {"name": "雾化", "offset": 15},
                    {"name": "光圈", "offset": 16},
                    {"name": "变焦", "offset": 17},
                    {"name": "对焦", "offset": 18},
                    {"name": "CMY", "offset": 19},
                    {"name": "效果", "offset": 20},
                    {"name": "功能", "offset": 21},
                    {"name": "复位", "offset": 22},
                ]
            }
        ]
    },
    {
        "name": "Spiider",
        "manufacturer": "Robe",
        "type": "染色灯(Wash)",
        "weight": 22.8,
        "power": 480,
        "description": "LED Wash Beam效果灯具，19颗RGBW LED，中心可做光束效果",
        "modes": [
            {
                "name": "标准模式 (21CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "红(R)", "offset": 8},
                    {"name": "绿(G)", "offset": 9},
                    {"name": "蓝(B)", "offset": 10},
                    {"name": "白(W)", "offset": 11},
                    {"name": "CTO", "offset": 12},
                    {"name": "色彩宏", "offset": 13},
                    {"name": "变焦", "offset": 14},
                    {"name": "内置效果", "offset": 15},
                    {"name": "像素效果", "offset": 16},
                    {"name": "中心LED", "offset": 17},
                    {"name": "光圈", "offset": 18},
                    {"name": "LED速率", "offset": 19},
                    {"name": "功能", "offset": 20},
                    {"name": "复位", "offset": 21},
                ]
            }
        ]
    },

    # ========== Martin ==========
    {
        "name": "MAC Viper Profile",
        "manufacturer": "Martin",
        "type": "图案灯(Spot)",
        "weight": 32.7,
        "power": 1200,
        "description": "高性能图案灯，1000W放电光源，双图案轮，CMY+CTO色彩系统",
        "modes": [
            {
                "name": "标准模式 (22CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "CMY 青", "offset": 8},
                    {"name": "CMY 品红", "offset": 9},
                    {"name": "CMY 黄", "offset": 10},
                    {"name": "CTO", "offset": 11},
                    {"name": "固定图案轮", "offset": 12},
                    {"name": "旋转图案轮", "offset": 13},
                    {"name": "图案旋转", "offset": 14},
                    {"name": "棱镜", "offset": 15},
                    {"name": "雾化", "offset": 16},
                    {"name": "光圈", "offset": 17},
                    {"name": "变焦", "offset": 18},
                    {"name": "对焦", "offset": 19},
                    {"name": "效果", "offset": 20},
                    {"name": "功能", "offset": 21},
                    {"name": "复位", "offset": 22},
                ]
            }
        ]
    },
    {
        "name": "MAC Aura XB",
        "manufacturer": "Martin",
        "type": "染色灯(Wash)",
        "weight": 12.0,
        "power": 260,
        "description": "单颗LED染色灯，RGBW色彩，BeamShaper功能，专利Aura效果",
        "modes": [
            {
                "name": "标准模式 (16CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "红(R)", "offset": 8},
                    {"name": "绿(G)", "offset": 9},
                    {"name": "蓝(B)", "offset": 10},
                    {"name": "白(W)", "offset": 11},
                    {"name": "CTO", "offset": 12},
                    {"name": "变焦", "offset": 13},
                    {"name": "Aura效果", "offset": 14},
                    {"name": "色彩宏", "offset": 15},
                    {"name": "功能", "offset": 16},
                ]
            }
        ]
    },
    {
        "name": "Rush MH 7",
        "manufacturer": "Martin",
        "type": "摇头灯(Moving Head)",
        "weight": 9.0,
        "power": 160,
        "description": "入门级LED摇头灯，RGBW 7x10W LED，紧凑设计，适合中小型场所",
        "modes": [
            {
                "name": "标准模式 (14CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "红(R)", "offset": 8},
                    {"name": "绿(G)", "offset": 9},
                    {"name": "蓝(B)", "offset": 10},
                    {"name": "白(W)", "offset": 11},
                    {"name": "宏", "offset": 12},
                    {"name": "功能", "offset": 13},
                    {"name": "复位", "offset": 14},
                ]
            }
        ]
    },

    # ========== Chauvet ==========
    {
        "name": "Rogue R1 Spot",
        "manufacturer": "Chauvet",
        "type": "图案灯(Spot)",
        "weight": 15.2,
        "power": 300,
        "description": "紧凑型图案灯，200W放电光源，双图案轮，适用于中小型舞台",
        "modes": [
            {
                "name": "标准模式 (16CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "色轮", "offset": 8},
                    {"name": "固定图案", "offset": 9},
                    {"name": "旋转图案", "offset": 10},
                    {"name": "图案旋转", "offset": 11},
                    {"name": "棱镜", "offset": 12},
                    {"name": "雾化", "offset": 13},
                    {"name": "变焦", "offset": 14},
                    {"name": "功能", "offset": 15},
                    {"name": "复位", "offset": 16},
                ]
            }
        ]
    },
    {
        "name": "COLORado Panel Q40",
        "manufacturer": "Chauvet",
        "type": "LED PAR",
        "weight": 10.8,
        "power": 350,
        "description": "RGBW LED面板灯，40颗10W LED，均匀光输出，适合洗墙和染色",
        "modes": [
            {
                "name": "标准模式 (12CH)",
                "channels": [
                    {"name": "调光", "offset": 1},
                    {"name": "频闪", "offset": 2},
                    {"name": "红(R)", "offset": 3},
                    {"name": "绿(G)", "offset": 4},
                    {"name": "蓝(B)", "offset": 5},
                    {"name": "白(W)", "offset": 6},
                    {"name": "CTO", "offset": 7},
                    {"name": "色彩宏", "offset": 8},
                    {"name": "速度", "offset": 9},
                    {"name": "模式", "offset": 10},
                    {"name": "功能", "offset": 11},
                    {"name": "复位", "offset": 12},
                ]
            }
        ]
    },
    {
        "name": "Intimidator Spot 375Z",
        "manufacturer": "Chauvet",
        "type": "图案灯(Spot)",
        "weight": 11.4,
        "power": 240,
        "description": "紧凑型图案灯，200W放电光源，变焦功能，内置宏效果",
        "modes": [
            {
                "name": "标准模式 (14CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "色轮", "offset": 8},
                    {"name": "图案轮", "offset": 9},
                    {"name": "棱镜", "offset": 10},
                    {"name": "变焦", "offset": 11},
                    {"name": "对焦", "offset": 12},
                    {"name": "功能", "offset": 13},
                    {"name": "复位", "offset": 14},
                ]
            }
        ]
    },

    # ========== ADJ ==========
    {
        "name": "Focus Spot 4Z",
        "manufacturer": "ADJ",
        "type": "图案灯(Spot)",
        "weight": 12.5,
        "power": 200,
        "description": "变焦图案灯，200W放电光源，5°-25°变焦，双图案轮",
        "modes": [
            {
                "name": "标准模式 (16CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "色轮", "offset": 8},
                    {"name": "固定图案", "offset": 9},
                    {"name": "旋转图案", "offset": 10},
                    {"name": "图案旋转", "offset": 11},
                    {"name": "棱镜", "offset": 12},
                    {"name": "雾化", "offset": 13},
                    {"name": "变焦", "offset": 14},
                    {"name": "功能", "offset": 15},
                    {"name": "复位", "offset": 16},
                ]
            }
        ]
    },
    {
        "name": "Vizi Beam RX2",
        "manufacturer": "ADJ",
        "type": "光束灯(Beam)",
        "weight": 19.5,
        "power": 470,
        "description": "高效光束灯，2R放电灯泡，极致光束效果，13色色轮",
        "modes": [
            {
                "name": "标准模式 (15CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "色轮", "offset": 8},
                    {"name": "图案轮", "offset": 9},
                    {"name": "棱镜", "offset": 10},
                    {"name": "雾化", "offset": 11},
                    {"name": "光圈", "offset": 12},
                    {"name": "效果", "offset": 13},
                    {"name": "功能", "offset": 14},
                    {"name": "复位", "offset": 15},
                ]
            }
        ]
    },

    # ========== 通用灯具 ==========
    {
        "name": "通用LED PAR灯 (12CH)",
        "manufacturer": "Generic",
        "type": "LED PAR",
        "weight": 2.5,
        "power": 100,
        "description": "通用LED PAR灯，RGBW 4合1 LED，适用于基础染色和氛围照明",
        "modes": [
            {
                "name": "标准模式 (12CH)",
                "channels": [
                    {"name": "调光", "offset": 1},
                    {"name": "红(R)", "offset": 2},
                    {"name": "绿(G)", "offset": 3},
                    {"name": "蓝(B)", "offset": 4},
                    {"name": "白(W)", "offset": 5},
                    {"name": "频闪", "offset": 6},
                    {"name": "色彩宏", "offset": 7},
                    {"name": "色彩速度", "offset": 8},
                    {"name": "自走程序", "offset": 9},
                    {"name": "自走速度", "offset": 10},
                    {"name": "声音模式", "offset": 11},
                    {"name": "模式", "offset": 12},
                ]
            },
            {
                "name": "简单模式 (6CH)",
                "channels": [
                    {"name": "红(R)", "offset": 1},
                    {"name": "绿(G)", "offset": 2},
                    {"name": "蓝(B)", "offset": 3},
                    {"name": "白(W)", "offset": 4},
                    {"name": "频闪", "offset": 5},
                    {"name": "调光", "offset": 6},
                ]
            }
        ]
    },
    {
        "name": "通用摇头灯 (16CH)",
        "manufacturer": "Generic",
        "type": "摇头灯(Moving Head)",
        "weight": 15.0,
        "power": 250,
        "description": "通用LED摇头灯，RGBW LED光源，适用于中小型活动和演出",
        "modes": [
            {
                "name": "标准模式 (16CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "红(R)", "offset": 8},
                    {"name": "绿(G)", "offset": 9},
                    {"name": "蓝(B)", "offset": 10},
                    {"name": "白(W)", "offset": 11},
                    {"name": "色轮", "offset": 12},
                    {"name": "图案轮", "offset": 13},
                    {"name": "棱镜", "offset": 14},
                    {"name": "功能", "offset": 15},
                    {"name": "复位", "offset": 16},
                ]
            }
        ]
    },

    # ========== 激光 ==========
    {
        "name": "Kvant Clubmax 30",
        "manufacturer": "Kvant",
        "type": "激光(Laser)",
        "weight": 12.0,
        "power": 300,
        "description": "全彩激光投影系统，30W RGB输出，ILDA/DMX控制，适用于大型演出",
        "modes": [
            {
                "name": "DMX模式 (12CH)",
                "channels": [
                    {"name": "图案选择", "offset": 1},
                    {"name": "图案速度", "offset": 2},
                    {"name": "X位置", "offset": 3},
                    {"name": "Y位置", "offset": 4},
                    {"name": "X尺寸", "offset": 5},
                    {"name": "Y尺寸", "offset": 6},
                    {"name": "旋转", "offset": 7},
                    {"name": "红(R)", "offset": 8},
                    {"name": "绿(G)", "offset": 9},
                    {"name": "蓝(B)", "offset": 10},
                    {"name": "调光", "offset": 11},
                    {"name": "安全锁", "offset": 12},
                ]
            }
        ]
    },
    {
        "name": "通用激光灯 (8CH)",
        "manufacturer": "Generic",
        "type": "激光(Laser)",
        "weight": 5.0,
        "power": 50,
        "description": "通用RGB激光灯，DMX控制，适用于小型演出和娱乐场所",
        "modes": [
            {
                "name": "标准模式 (8CH)",
                "channels": [
                    {"name": "图案模式", "offset": 1},
                    {"name": "速度", "offset": 2},
                    {"name": "X位置", "offset": 3},
                    {"name": "Y位置", "offset": 4},
                    {"name": "红(R)", "offset": 5},
                    {"name": "绿(G)", "offset": 6},
                    {"name": "蓝(B)", "offset": 7},
                    {"name": "调光", "offset": 8},
                ]
            }
        ]
    },

    # ========== 追光灯 ==========
    {
        "name": "Robert Juliat Cyrano",
        "manufacturer": "Robert Juliat",
        "type": "追光灯(Follow Spot)",
        "weight": 85.0,
        "power": 2500,
        "description": "高功率追光灯，HMI 2500W光源，远程控制光圈/色片/频闪",
        "modes": [
            {
                "name": "DMX模式 (6CH)",
                "channels": [
                    {"name": "调光", "offset": 1},
                    {"name": "光圈", "offset": 2},
                    {"name": "色片1", "offset": 3},
                    {"name": "色片2", "offset": 4},
                    {"name": "频闪", "offset": 5},
                    {"name": "对焦", "offset": 6},
                ]
            }
        ]
    },
    {
        "name": "通用追光灯 (4CH)",
        "manufacturer": "Generic",
        "type": "追光灯(Follow Spot)",
        "weight": 25.0,
        "power": 575,
        "description": "通用追光灯，575W光源，手动操作，DMX辅助控制调光和色片",
        "modes": [
            {
                "name": "标准模式 (4CH)",
                "channels": [
                    {"name": "调光", "offset": 1},
                    {"name": "色片", "offset": 2},
                    {"name": "光圈", "offset": 3},
                    {"name": "频闪", "offset": 4},
                ]
            }
        ]
    },

    # ========== 更多灯具 ==========
    {
        "name": "MAC Quantum Wash",
        "manufacturer": "Martin",
        "type": "染色灯(Wash)",
        "weight": 19.0,
        "power": 450,
        "description": "LED染色灯，RGBW色彩引擎，专利BeamShaper，均匀光输出",
        "modes": [
            {
                "name": "标准模式 (18CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "红(R)", "offset": 8},
                    {"name": "绿(G)", "offset": 9},
                    {"name": "蓝(B)", "offset": 10},
                    {"name": "白(W)", "offset": 11},
                    {"name": "CTO", "offset": 12},
                    {"name": "变焦", "offset": 13},
                    {"name": "BeamShaper", "offset": 14},
                    {"name": "色彩宏", "offset": 15},
                    {"name": "效果", "offset": 16},
                    {"name": "功能", "offset": 17},
                    {"name": "复位", "offset": 18},
                ]
            }
        ]
    },
    {
        "name": "Rogue R2 Wash",
        "manufacturer": "Chauvet",
        "type": "染色灯(Wash)",
        "weight": 11.0,
        "power": 250,
        "description": "LED染色灯，19颗RGBW LED，7°-56°变焦，快速移动",
        "modes": [
            {
                "name": "标准模式 (15CH)",
                "channels": [
                    {"name": "Pan 粗调", "offset": 1},
                    {"name": "Pan 细调", "offset": 2},
                    {"name": "Tilt 粗调", "offset": 3},
                    {"name": "Tilt 细调", "offset": 4},
                    {"name": "速度", "offset": 5},
                    {"name": "调光", "offset": 6},
                    {"name": "频闪", "offset": 7},
                    {"name": "红(R)", "offset": 8},
                    {"name": "绿(G)", "offset": 9},
                    {"name": "蓝(B)", "offset": 10},
                    {"name": "白(W)", "offset": 11},
                    {"name": "CTO", "offset": 12},
                    {"name": "变焦", "offset": 13},
                    {"name": "功能", "offset": 14},
                    {"name": "复位", "offset": 15},
                ]
            }
        ]
    },
]

# 灯具类别定义
FIXTURE_CATEGORIES = [
    {"id": "moving_head", "name": "摇头灯(Moving Head)"},
    {"id": "wash", "name": "染色灯(Wash)"},
    {"id": "beam", "name": "光束灯(Beam)"},
    {"id": "spot", "name": "图案灯(Spot)"},
    {"id": "led_par", "name": "LED PAR"},
    {"id": "laser", "name": "激光(Laser)"},
    {"id": "follow_spot", "name": "追光灯(Follow Spot)"},
]

CATEGORY_TYPE_MAP = {
    "moving_head": "摇头灯(Moving Head)",
    "wash": "染色灯(Wash)",
    "beam": "光束灯(Beam)",
    "spot": "图案灯(Spot)",
    "led_par": "LED PAR",
    "laser": "激光(Laser)",
    "follow_spot": "追光灯(Follow Spot)",
}

TYPE_CATEGORY_MAP = {v: k for k, v in CATEGORY_TYPE_MAP.items()}
