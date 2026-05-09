"""Populate database with default paper types, knowledge articles, and sample history."""

from __future__ import annotations

import json

from database.db_manager import get_connection


def seed_paper_types() -> None:
    """Insert default paper profiles with pre-computed conversion matrices."""
    papers = [
        {
            "name": "157g铜版纸",
            "weight_gsm": 157,
            "surface": "glossy",
            "dot_gain_pct": 14.0,
            "max_ink_pct": 340.0,
            "white_point_l": 95.0,
            "white_point_a": 0.5,
            "white_point_b": -1.5,
            "description": "常用高档印刷纸张，表面光滑，色彩还原优秀，适用于画册、海报、宣传页等。",
            "conversion_matrix": json.dumps([
                [0.20, 0.04, 0.01, 0.70],
                [0.04, 0.55, 0.04, 0.32],
                [0.01, 0.05, 0.75, 0.14],
            ]),
        },
        {
            "name": "128g铜版纸",
            "weight_gsm": 128,
            "surface": "glossy",
            "dot_gain_pct": 15.0,
            "max_ink_pct": 330.0,
            "white_point_l": 93.0,
            "white_point_a": 0.5,
            "white_point_b": -1.0,
            "description": "中档铜版纸，常用于杂志内页、产品目录等。",
            "conversion_matrix": json.dumps([
                [0.19, 0.04, 0.01, 0.68],
                [0.04, 0.53, 0.04, 0.31],
                [0.01, 0.05, 0.73, 0.13],
            ]),
        },
        {
            "name": "80g双胶纸",
            "weight_gsm": 80,
            "surface": "uncoated",
            "dot_gain_pct": 20.0,
            "max_ink_pct": 300.0,
            "white_point_l": 90.0,
            "white_point_a": 1.0,
            "white_point_b": -3.0,
            "description": "普通书刊印刷用纸，吸墨性强，网点扩大较大，色彩饱和度较铜版纸低。",
            "conversion_matrix": json.dumps([
                [0.18, 0.04, 0.01, 0.65],
                [0.04, 0.50, 0.04, 0.29],
                [0.01, 0.05, 0.70, 0.12],
            ]),
        },
        {
            "name": "105g哑粉纸",
            "weight_gsm": 105,
            "surface": "matte",
            "dot_gain_pct": 16.0,
            "max_ink_pct": 320.0,
            "white_point_l": 92.0,
            "white_point_a": 0.8,
            "white_point_b": -2.0,
            "description": "哑光涂布纸，无反光，阅读舒适，适用于高端画册、艺术书籍等。",
            "conversion_matrix": json.dumps([
                [0.19, 0.04, 0.01, 0.67],
                [0.04, 0.52, 0.04, 0.30],
                [0.01, 0.05, 0.72, 0.13],
            ]),
        },
    ]

    conn = get_connection()
    try:
        for p in papers:
            conn.execute(
                """
                INSERT OR IGNORE INTO paper_types
                    (name, weight_gsm, surface, dot_gain_pct, max_ink_pct,
                     white_point_l, white_point_a, white_point_b, description, conversion_matrix)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    p["name"], p["weight_gsm"], p["surface"],
                    p["dot_gain_pct"], p["max_ink_pct"],
                    p["white_point_l"], p["white_point_a"], p["white_point_b"],
                    p["description"], p["conversion_matrix"],
                ),
            )
        conn.commit()
    finally:
        conn.close()


def seed_knowledge_base() -> None:
    """Insert seed knowledge articles on color management topics."""
    articles = [
        ("CMYK色彩模式基础", "术语",
         "CMYK是印刷行业标准的色彩模式，由青色(Cyan)、品红色(Magenta)、黄色(Yellow)和黑色(Key/Black)四种油墨组成。每种油墨的取值范围为0-100%，0%表示该油墨完全不使用，100%表示最大浓度。四种油墨通过减色混合原理在纸张上呈现各种颜色。",
         "CMYK 印刷 色彩模式 油墨"),
        ("CIE L*a*b*色彩空间", "术语",
         "CIE L*a*b*是一种与设备无关的色彩空间，用于量化描述人眼可感知的颜色。L*表示明度(0=黑,100=白)，a*表示红绿轴(正=红,负=绿)，b*表示黄蓝轴(正=黄,负=蓝)。Lab空间广泛用于色彩管理和色差计算。",
         "Lab L*a*b* 色彩空间 明度 色差"),
        ("色差ΔE的理解与应用", "术语",
         "ΔE( Delta E)是衡量两个颜色之间差异的数值指标。ΔE76基于Lab空间的欧氏距离计算。判断标准：ΔE<1为不可感知差异，1-3为可感知但不明显，3-6为明显差异，>6为显著差异。印刷行业通常要求ΔE<3为合格。",
         "色差 ΔE Delta E 色差标准 合格"),
        ("网点扩大(Dot Gain)", "术语",
         "网点扩大是指印刷过程中网点面积比印版上预期面积增大的现象。主要由纸张吸墨性和印刷压力造成。铜版纸网点扩大约14-16%，双胶纸约18-22%。网点扩大会导致印刷品整体偏暗，需要在印前进行补偿。",
         "网点扩大 补偿 偏暗 铜版纸 双胶纸"),
        ("灰平衡(Gray Balance)", "术语",
         "灰平衡是指CMY三色油墨按特定比例混合后产生中性灰的状态。理想的灰平衡要求C、M、Y三色的等量混合不产生色偏。灰平衡是色彩管理的核心指标，灰平衡偏移会导致整个印刷品出现色偏。",
         "灰平衡 中性灰 色偏 CMY 校准"),
        ("油墨叠印与陷印", "工艺",
         "油墨叠印(Trapping)是指一种油墨印在另一种油墨上的能力。良好的叠印率(通常>80%)确保色彩准确。陷印(Trapping)是印前处理技术，通过在相邻色块间添加微小重叠来避免套准偏差造成的白边。",
         "叠印 陷印 套准 油墨"),
        ("总墨量控制", "工艺",
         "总墨量(Total Ink Coverage/TIC)是指CMYK四色油墨百分比之和。不同纸张有不同上限：铜版纸约320-340%，双胶纸约280-300%。超过限制会导致干燥困难、蹭脏、透印等问题。",
         "总墨量 墨量上限 干燥 蹭脏"),
        ("印刷色差的常见原因", "故障排除",
         "印刷色差的常见原因包括：1)墨量控制不当(过量或不足)；2)网点扩大超出预期；3)纸张批次间白度差异；4)印刷压力不均匀；5)环境温湿度变化影响油墨流动性；6)印版磨损或老化。系统性排查应从墨量、压力、纸张三方面入手。",
         "色差 原因 墨量 压力 纸张 排查"),
        ("墨量调整的基本方法", "校准方法",
         "当印刷品出现色偏时，应按以下步骤调整：1)确定偏色方向(偏红/偏绿/偏蓝/偏黄)；2)对应调整油墨通道(偏红减M，偏绿加M，偏黄减Y，偏蓝加Y)；3)单次调整幅度建议2-5%；4)调整后需重新打样验证；5)记录调整参数供后续参考。",
         "墨量 调整 校准 偏色"),
        ("铜版纸与双胶纸的色彩差异", "工艺",
         "铜版纸因表面涂布光滑，网点扩大较小(14-16%)，色彩还原鲜艳饱和。双胶纸表面粗糙，吸墨性强，网点扩大较大(18-22%)，色彩表现较暗淡。同一CMYK值在两种纸张上的表现差异显著：双胶纸通常需要更高的墨量补偿，且总墨量上限更低。",
         "铜版纸 双胶纸 差异 色彩 网点"),
        ("ICC色彩配置文件", "术语",
         "ICC配置文件是由国际色彩联盟(ICC)标准定义的文件，描述特定设备或纸张的色彩特性。包含设备色彩空间到PCS(色彩连接空间，通常为Lab或XYZ)的转换映射。印刷中常用的ICC配置文件类型为CMYK输入配置文件和打印机配置文件。",
         "ICC 配置文件 色彩管理"),
        ("密度计与分光光度计", "术语",
         "密度计测量油墨密度(吸光度)，用于监控墨层厚度和网点扩大。分光光度计测量光谱反射率，可计算Lab值和色差ΔE，是色彩管理的核心测量工具。印刷品质检通常使用分光光度计进行Lab值测量。",
         "密度计 分光光度计 测量 检测"),
        ("印刷压力对色彩的影响", "工艺",
         "印刷压力直接影响油墨转移率和网点扩大。压力过大会导致网点严重扩大、色彩偏暗；压力过小则墨色浅淡、实地不实。理想的印刷压力应使网点扩大率控制在标准范围内，同时保证实地密度达标。",
         "压力 色彩 网点扩大 实地密度"),
        ("油墨干燥与色彩变化", "工艺",
         "油墨干燥过程中色彩会发生变化：湿墨通常比干墨颜色更深更鲜艳。干燥后色彩会略有变淡，尤其是哑光纸张上的变化更明显。建议在墨膜干燥后(通常15-30分钟)再进行色彩评估，避免误判。",
         "干燥 色彩变化 湿墨 干墨"),
        ("印刷校准流程", "校准方法",
         "标准印刷校准流程：1)确认纸张类型和目标色值；2)首次印刷样张；3)用分光光度计测量样张Lab值；4)计算与目标值的色差ΔE；5)如ΔE>3，根据色差方向调整墨量；6)重新印刷验证；7)记录最终参数。整个流程应形成闭环，确保每次调整都有据可依。",
         "校准 流程 Lab ΔE 墨量"),
    ]

    conn = get_connection()
    try:
        for title, category, content, tags in articles:
            conn.execute(
                "INSERT OR IGNORE INTO knowledge_base (title, category, content, tags) VALUES (?, ?, ?, ?)",
                (title, category, content, tags),
            )
        conn.commit()
    finally:
        conn.close()


def seed_calibration_history() -> None:
    """Insert sample calibration records for demonstration."""
    records = [
        ("157g铜版纸", 50.0, 30.0, 80.0, 10.0, (62.5, 5.2, 38.1), (60.8, 7.1, 42.3), 4.8,
         "预测色偏黄偏红，建议减Y 3-5%，减M 2-3%", "首印校准，已调整"),
        ("157g铜版纸", 70.0, 20.0, 10.0, 0.0, (78.2, 12.5, -8.3), (76.5, 15.2, -5.1), 4.1,
         "预测色偏红偏黄，建议减M 2-4%，减Y 1-2%", "客户要求高饱和度"),
        ("80g双胶纸", 40.0, 50.0, 60.0, 20.0, (45.8, 18.3, 22.5), (43.2, 21.5, 28.7), 7.2,
         "色差显著，建议减M 4-6%，减Y 5-7%，检查网点扩大补偿", "双胶纸网点扩大较大"),
        ("80g双胶纸", 60.0, 10.0, 90.0, 5.0, (72.1, -15.2, 55.8), (69.5, -12.8, 60.2), 5.5,
         "预测色偏黄偏红，建议减Y 3-5%，加C 1-2%", "绿色系校准"),
        ("128g铜版纸", 30.0, 70.0, 20.0, 15.0, (42.5, 35.2, -5.8), (40.8, 38.5, -2.1), 5.1,
         "预测色偏红偏黄，建议减M 3-5%，减Y 1-2%", "紫色系印刷"),
        ("105g哑粉纸", 80.0, 40.0, 10.0, 0.0, (65.3, 28.5, -22.1), (63.2, 32.1, -18.5), 5.8,
         "预测色偏红偏黄，建议减M 3-5%，减Y 2-3%", "蓝色系校准"),
        ("157g铜版纸", 0.0, 0.0, 0.0, 100.0, (15.2, 0.3, -0.8), (14.8, 0.5, -1.2), 0.6,
         "色差不可感知，无需调整", "纯黑印刷，状态良好"),
        ("157g铜版纸", 25.0, 25.0, 25.0, 0.0, (55.8, 0.2, -0.5), (54.2, 1.8, 2.1), 3.5,
         "灰平衡偏移，建议减M 1-2%，减Y 1-2%，加C 1%", "灰平衡校准"),
        ("80g双胶纸", 50.0, 50.0, 50.0, 50.0, (35.2, 8.5, 12.3), (32.1, 12.8, 18.5), 8.5,
         "色差显著，四色墨量均偏高，建议全面减量5-8%", "总墨量接近上限"),
        ("128g铜版纸", 90.0, 10.0, 0.0, 0.0, (55.8, -25.2, -38.5), (53.5, -22.1, -35.2), 4.8,
         "预测色偏绿偏黄，建议加M 2-3%，加Y 1-2%", "青色专色校准"),
        ("105g哑粉纸", 20.0, 80.0, 40.0, 10.0, (48.5, 42.1, 15.2), (46.2, 45.8, 19.8), 5.9,
         "预测色偏红偏黄，建议减M 3-5%，减Y 2-3%", "红色系印刷"),
        ("157g铜版纸", 35.0, 65.0, 0.0, 0.0, (52.3, 45.8, -15.2), (50.1, 49.2, -11.8), 5.5,
         "预测色偏红偏黄，建议减M 3-4%，减Y 1-2%", "品红色校准"),
    ]

    conn = get_connection()
    try:
        for paper, tc, tm, ty, tk, tlab, plab, de, advice, notes in records:
            conn.execute(
                """
                INSERT OR IGNORE INTO calibration_history
                    (paper_type, target_c, target_m, target_y, target_k,
                     target_l, target_a, target_b,
                     predicted_l, predicted_a, predicted_b,
                     delta_e, advice_summary, operator_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (paper, tc, tm, ty, tk,
                 tlab[0], tlab[1], tlab[2],
                 plab[0], plab[1], plab[2],
                 de, advice, notes),
            )
        conn.commit()
    finally:
        conn.close()


def run_all_seeding() -> None:
    """Run all seed functions. Checks if tables are empty before seeding."""
    conn = get_connection()
    try:
        paper_count = conn.execute("SELECT COUNT(*) FROM paper_types").fetchone()[0]
        kb_count = conn.execute("SELECT COUNT(*) FROM knowledge_base").fetchone()[0]
        cal_count = conn.execute("SELECT COUNT(*) FROM calibration_history").fetchone()[0]
    finally:
        conn.close()

    if paper_count == 0:
        seed_paper_types()
    if kb_count == 0:
        seed_knowledge_base()
    if cal_count == 0:
        seed_calibration_history()
