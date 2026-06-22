#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AI故障诊断 - 基于规则的DMX/网络/灯具故障诊断工具"""

import sys
import json
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QCheckBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QTabWidget, QFileDialog, QMessageBox, QScrollArea,
    QFrame, QGridLayout, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont


# ── 故障数据库 (20+ 条目) ──────────────────────────────────────────────────────

SYMPTOM_CATEGORIES = {
    "DMX信号问题": [
        {"id": "dmx_no_signal", "text": "完全没有DMX信号", "category": "DMX信号问题"},
        {"id": "dmx_flicker", "text": "DMX信号闪烁/不稳定", "category": "DMX信号问题"},
        {"id": "dmx_partial", "text": "部分通道无响应", "category": "DMX信号问题"},
        {"id": "dmx_cross", "text": "通道串扰/错误通道响应", "category": "DMX信号问题"},
        {"id": "dmx_freeze", "text": "灯具卡死不响应控制", "category": "DMX信号问题"},
        {"id": "dmx_lag", "text": "控制延迟明显", "category": "DMX信号问题"}
    ],
    "网络问题": [
        {"id": "net_no_connect", "text": "无法连接到灯光网络", "category": "网络问题"},
        {"id": "net_drop", "text": "网络连接间歇性断开", "category": "网络问题"},
        {"id": "net_slow", "text": "Art-Net/sACN响应缓慢", "category": "网络问题"},
        {"id": "net_ip_conflict", "text": "IP地址冲突", "category": "网络问题"},
        {"id": "net_dhcp_fail", "text": "DHCP分配失败", "category": "网络问题"}
    ],
    "灯具问题": [
        {"id": "fix_no_power", "text": "灯具完全不亮", "category": "灯具问题"},
        {"id": "fix_dim", "text": "灯具亮度明显降低", "category": "灯具问题"},
        {"id": "fix_color_wrong", "text": "颜色显示不正确", "category": "灯具问题"},
        {"id": "fix_move_stuck", "text": "摇头灯移动卡顿/异响", "category": "灯具问题"},
        {"id": "fix_gobo_stuck", "text": "图案盘卡住", "category": "灯具问题"},
        {"id": "fix_lamp_blow", "text": "灯泡突然熄灭", "category": "灯具问题"},
        {"id": "fix_fan_noise", "text": "风扇噪音异常", "category": "灯具问题"},
        {"id": "fix_strobe_uncontrollable", "text": "频闪无法控制", "category": "灯具问题"}
    ],
    "控制台问题": [
        {"id": "console_freeze", "text": "控制台死机/无响应", "category": "控制台问题"},
        {"id": "console_fader", "text": "推子不灵敏/跳值", "category": "控制台问题"},
        {"id": "console_display", "text": "显示屏异常", "category": "控制台问题"},
        {"id": "console_save_fail", "text": "无法保存/加载演出文件", "category": "控制台问题"}
    ],
    "电源问题": [
        {"id": "pwr_trip", "text": "断路器跳闸", "category": "电源问题"},
        {"id": "pwr_overload", "text": "电路过载警告", "category": "电源问题"},
        {"id": "pwr_ground_loop", "text": "接地回路噪音(灯光闪烁)", "category": "电源问题"}
    ]
}

# 诊断规则库
DIAGNOSIS_DB = {
    "dmx_no_signal": {
        "title": "DMX信号完全丢失",
        "severity": "严重",
        "possible_causes": [
            "DMX线缆断开或损坏",
            "DMX接口故障",
            "控制台DMX输出卡故障",
            "DMX信号分配器故障"
        ],
        "solutions": [
            "检查DMX线缆两端是否牢固连接",
            "用万用表测量DMX线缆通断(针1-针1, 针2-针2, 针1/2-屏蔽层)",
            "更换DMX线缆测试",
            "检查控制台DMX输出指示灯是否闪烁",
            "尝试使用另一个DMX输出口",
            "检查DMX信号分配器电源和连接",
            "如有备用控制台，交叉测试确认问题源头"
        ]
    },
    "dmx_flicker": {
        "title": "DMX信号闪烁/不稳定",
        "severity": "中等",
        "possible_causes": [
            "DMX终端电阻缺失",
            "线缆过长或质量差",
            "电磁干扰(靠近电源线)",
            "DMX线缆接头虚焊"
        ],
        "solutions": [
            "在DMX链路末端加装120Ω终端电阻",
            "检查线缆长度是否超过300米限制",
            "确保DMX线缆远离大功率电源线(至少30cm)",
            "重新焊接DMX接头(注意针脚1=地, 2=数据-, 3=数据+)",
            "检查是否有环形拓扑导致信号反射",
            "使用DMX信号中继器/放大器"
        ]
    },
    "dmx_partial": {
        "title": "部分DMX通道无响应",
        "severity": "中等",
        "possible_causes": [
            "DMX地址设置错误",
            "灯具DMX模式不匹配",
            "DMX链路中某台设备故障中断信号",
            "DMX通道超限"
        ],
        "solutions": [
            "逐台检查灯具的DMX起始地址",
            "确认灯具的DMX通道模式(如16ch/24ch模式)",
            "从最后正常工作的灯具开始往后排查",
            "检查控制台patch表是否正确",
            "尝试将问题灯具直接连接到控制台测试",
            "重置灯具DMX地址"
        ]
    },
    "dmx_cross": {
        "title": "通道串扰",
        "severity": "中等",
        "possible_causes": [
            "DMX地址重叠",
            "Patch配置错误",
            "灯具固件Bug"
        ],
        "solutions": [
            "检查所有灯具DMX地址是否有重叠",
            "重新核对控制台patch表",
            "更新灯具固件",
            "使用DMX分析仪检查实际信号数据"
        ]
    },
    "dmx_freeze": {
        "title": "灯具卡死不响应",
        "severity": "中等",
        "possible_causes": [
            "灯具控制板故障",
            "DMX信号中断",
            "灯具过热保护"
        ],
        "solutions": [
            "断电等待30秒后重新上电",
            "检查灯具温度是否过高",
            "检查DMX连接",
            "尝试灯具自检模式",
            "如持续故障，联系维修"
        ]
    },
    "dmx_lag": {
        "title": "DMX控制延迟",
        "severity": "轻微",
        "possible_causes": [
            "网络延迟(Art-Net/sACN)",
            "DMX刷新率设置过低",
            "处理链路过长"
        ],
        "solutions": [
            "检查网络交换机配置和延迟",
            "增加DMX刷新率设置",
            "减少DMX链路中的设备数量",
            "使用专用灯光网络交换机",
            "避免网络拥塞(隔离灯光网络)"
        ]
    },
    "net_no_connect": {
        "title": "灯光网络无法连接",
        "severity": "严重",
        "possible_causes": [
            "网线断开或损坏",
            "交换机故障",
            "网络配置错误",
            "防火墙阻拦"
        ],
        "solutions": [
            "检查所有网线连接",
            "确认交换机指示灯正常",
            "使用ping命令测试连通性",
            "检查IP地址和子网掩码配置",
            "临时关闭防火墙测试",
            "更换网线/交换机端口测试",
            "确认Art-Net/sACN协议版本兼容"
        ]
    },
    "net_drop": {
        "title": "网络间歇性断开",
        "severity": "严重",
        "possible_causes": [
            "网线接触不良",
            "交换机端口故障",
            "电磁干扰",
            "网络环路"
        ],
        "solutions": [
            "检查网线水晶头是否松动",
            "更换网线测试",
            "尝试交换机不同端口",
            "确保使用屏蔽网线(STP)",
            "检查是否有网络环路(启用STP)",
            "远离强电设备布线"
        ]
    },
    "net_slow": {
        "title": "Art-Net/sACN响应缓慢",
        "severity": "中等",
        "possible_causes": [
            "网络带宽不足",
            "交换机性能瓶颈",
            "过多广播包"
        ],
        "solutions": [
            "使用千兆交换机",
            "隔离灯光网络(不与其他设备共享)",
            "减少universe数量",
            "检查交换机端口流量统计",
            "使用IGMP组播优化"
        ]
    },
    "net_ip_conflict": {
        "title": "IP地址冲突",
        "severity": "严重",
        "possible_causes": [
            "手动IP设置重复",
            "DHCP范围与静态IP重叠",
            "设备记忆了旧IP"
        ],
        "solutions": [
            "记录所有设备IP地址列表",
            "使用arp-scan或类似工具扫描冲突",
            "统一分配静态IP或全部使用DHCP",
            "确保DHCP范围不与静态IP重叠",
            "冲突设备断网后重新配置"
        ]
    },
    "net_dhcp_fail": {
        "title": "DHCP分配失败",
        "severity": "中等",
        "possible_causes": [
            "DHCP服务器未运行",
            "DHCP地址池已满",
            "网络连接问题"
        ],
        "solutions": [
            "确认DHCP服务器正在运行",
            "检查DHCP地址池范围",
            "缩短网线距离测试",
            "临时手动设置静态IP",
            "重启DHCP服务"
        ]
    },
    "fix_no_power": {
        "title": "灯具完全不亮",
        "severity": "严重",
        "possible_causes": [
            "电源线断开",
            "保险丝烧断",
            "电源模块故障",
            "断路器跳闸"
        ],
        "solutions": [
            "检查电源线连接是否牢固",
            "检查灯具保险丝(通常在电源入口处)",
            "用万用表测量电源插座电压",
            "检查配电箱对应断路器",
            "尝试使用其他电源插座",
            "如电源模块有烧焦气味，停止使用并联系维修"
        ]
    },
    "fix_dim": {
        "title": "灯具亮度降低",
        "severity": "中等",
        "possible_causes": [
            "灯泡老化",
            "反光镜脏污",
            "透镜污染",
            "电源电压不足"
        ],
        "solutions": [
            "检查灯泡使用时长，接近寿命需更换",
            "清洁反光镜和透镜(使用专业清洁剂)",
            "测量供电电压是否达到要求",
            "检查灯具散热是否正常(过热会降低亮度)",
            "LED灯具检查驱动电流设置"
        ]
    },
    "fix_color_wrong": {
        "title": "颜色显示不正确",
        "severity": "轻微",
        "possible_causes": [
            "色轮/颜色盘卡住",
            "LED灯珠损坏",
            "DMX通道映射错误",
            "校色配置丢失"
        ],
        "solutions": [
            "重置灯具到出厂默认",
            "检查DMX通道映射是否正确",
            "运行灯具自检模式查看颜色",
            "检查是否有LED灯珠不亮",
            "LED灯具尝试重新校色",
            "更新灯具配置文件"
        ]
    },
    "fix_move_stuck": {
        "title": "摇头灯移动卡顿/异响",
        "severity": "中等",
        "possible_causes": [
            "步进电机故障",
            "齿轮磨损",
            "机械限位故障",
            "灰尘积累"
        ],
        "solutions": [
            "⚠ 操作前请断电！",
            "断电后手动轻轻转动灯头，感受阻力",
            "检查是否有异物卡住",
            "清洁齿轮和导轨",
            "检查皮带是否松弛(如有)",
            "如电机有异响，可能需要更换",
            "联系专业维修处理机械问题"
        ]
    },
    "fix_gobo_stuck": {
        "title": "图案盘卡住",
        "severity": "中等",
        "possible_causes": [
            "图案盘变形",
            "驱动电机故障",
            "定位传感器脏污"
        ],
        "solutions": [
            "断电后检查图案盘是否可以自由旋转",
            "清洁图案盘和定位传感器",
            "检查是否有Gobo片安装不当",
            "运行灯具自检旋转图案盘",
            "如持续故障，需专业维修"
        ]
    },
    "fix_lamp_blow": {
        "title": "灯泡突然熄灭",
        "severity": "严重",
        "possible_causes": [
            "灯泡寿命到期",
            "电源突波",
            "散热不良导致过热保护",
            "灯泡质量问题"
        ],
        "solutions": [
            "等待灯具完全冷却(至少15分钟)",
            "检查灯泡外观是否有黑化/断裂",
            "检查散热风扇是否正常工作",
            "清洁进风口和滤网",
            "更换同型号灯泡",
            "检查供电电压稳定性",
            "避免频繁开关(间隔至少5分钟)"
        ]
    },
    "fix_fan_noise": {
        "title": "风扇噪音异常",
        "severity": "轻微",
        "possible_causes": [
            "风扇轴承磨损",
            "灰尘积累",
            "风扇叶片变形",
            "安装松动"
        ],
        "solutions": [
            "清洁风扇叶片和周围区域",
            "检查风扇固定螺丝是否松动",
            "如轴承噪音，需更换风扇",
            "确认风扇转速是否正常",
            "检查温度传感器(高转速可能是散热问题)"
        ]
    },
    "fix_strobe_uncontrollable": {
        "title": "频闪无法控制",
        "severity": "中等",
        "possible_causes": [
            "触发信号干扰",
            "控制电路故障",
            "DMX信号问题"
        ],
        "solutions": [
            "断电重启灯具",
            "检查DMX信号质量",
            "将灯具设为DMX模式而非自走模式",
            "重置灯具DMX设置",
            "尝试更换DMX地址"
        ]
    },
    "console_freeze": {
        "title": "控制台死机",
        "severity": "严重",
        "possible_causes": [
            "软件崩溃",
            "内存不足",
            "硬件过热",
            "固件Bug"
        ],
        "solutions": [
            "长按电源键强制关机，等待10秒后重启",
            "检查散热通风口是否被堵",
            "加载最近的备份演出文件",
            "检查USB设备是否有问题(拔掉非必要USB)",
            "更新控制台固件到最新版本",
            "如频繁死机，考虑恢复出厂设置",
            "联系厂家技术支持"
        ]
    },
    "console_fader": {
        "title": "推子不灵敏/跳值",
        "severity": "中等",
        "possible_causes": [
            "推子触点脏污",
            "推子磨损",
            "固件问题"
        ],
        "solutions": [
            "使用电子清洁剂喷入推子缝隙",
            "反复推拉推子多次清洁触点",
            "重新校准推子(查看控制台手册)",
            "更新控制台固件",
            "如单个推子故障，可能需要更换"
        ]
    },
    "console_display": {
        "title": "显示屏异常",
        "severity": "中等",
        "possible_causes": [
            "显示排线松动",
            "背光故障",
            "液晶屏损坏"
        ],
        "solutions": [
            "检查显示亮度设置",
            "重启控制台",
            "外接显示器确认是否软件问题",
            "如物理损坏需返厂维修"
        ]
    },
    "console_save_fail": {
        "title": "无法保存/加载文件",
        "severity": "中等",
        "possible_causes": [
            "存储空间已满",
            "USB设备故障",
            "文件系统损坏"
        ],
        "solutions": [
            "检查USB设备是否有写保护",
            "尝试格式化USB设备(FAT32)",
            "更换新的USB设备",
            "清理控制台内部存储空间",
            "使用另一台电脑读取USB确认是否损坏"
        ]
    },
    "pwr_trip": {
        "title": "断路器跳闸",
        "severity": "严重",
        "possible_causes": [
            "电路过载",
            "短路",
            "漏电",
            "断路器老化"
        ],
        "solutions": [
            "⚠ 安全第一！如不确定请找专业电工",
            "记录跳闸断路器对应的回路",
            "断开该回路所有负载",
            "逐一接入设备找出问题设备",
            "检查是否有线缆破损导致短路",
            "计算总负载是否超过断路器额定值",
            "使用漏电检测器检查漏电"
        ]
    },
    "pwr_overload": {
        "title": "电路过载",
        "severity": "严重",
        "possible_causes": [
            "灯具总功率超出回路容量",
            "同时启动电流过大",
            "电源线径不足"
        ],
        "solutions": [
            "计算所有灯具总功率(含启动电流)",
            "将负载分散到多个回路",
            "使用顺序上电功能(如有)",
            "确保电源线径足够(10A回路至少2.5mm²)",
            "考虑增加电源回路"
        ]
    },
    "pwr_ground_loop": {
        "title": "接地回路问题",
        "severity": "中等",
        "possible_causes": [
            "多点接地形成回路",
            "接地线接触不良",
            "混合使用不同电源"
        ],
        "solutions": [
            "确保所有设备使用同一电源回路",
            "检查接地线连接",
            "使用隔离变压器",
            "DMX使用光电隔离器",
            "检查设备机壳接地是否良好"
        ]
    }
}


class DiagnosisEngine:
    """故障诊断引擎"""
    
    def diagnose(self, symptom_ids):
        if not symptom_ids:
            return {"diagnoses": [], "summary": "未选择任何症状"}
        
        diagnoses = []
        for sid in symptom_ids:
            if sid in DIAGNOSIS_DB:
                entry = DIAGNOSIS_DB[sid]
                diagnoses.append({
                    "symptom_id": sid,
                    "title": entry["title"],
                    "severity": entry["severity"],
                    "possible_causes": entry["possible_causes"],
                    "solutions": entry["solutions"]
                })
        
        # 按严重程度排序
        severity_order = {"严重": 0, "中等": 1, "轻微": 2}
        diagnoses.sort(key=lambda d: severity_order.get(d["severity"], 99))
        
        summary = f"共诊断 {len(diagnoses)} 个问题\n"
        severe = sum(1 for d in diagnoses if d["severity"] == "严重")
        medium = sum(1 for d in diagnoses if d["severity"] == "中等")
        mild = sum(1 for d in diagnoses if d["severity"] == "轻微")
        if severe:
            summary += f"  ⚠ 严重: {severe} 个\n"
        if medium:
            summary += f"  ⚡ 中等: {medium} 个\n"
        if mild:
            summary += f"  ℹ 轻微: {mild} 个\n"
        
        return {"diagnoses": diagnoses, "summary": summary}
    
    def generate_report(self, symptom_ids, diagnoses):
        report = {
            "report_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tool": "AI故障诊断 v1.0.0",
            "selected_symptoms": symptom_ids,
            "summary": diagnoses["summary"],
            "diagnoses": []
        }
        
        for d in diagnoses["diagnoses"]:
            solutions = d["solutions"]
            if isinstance(solutions, dict):
                solutions = solutions.get("steps", [])
            report["diagnoses"].append({
                "title": d["title"],
                "severity": d["severity"],
                "possible_causes": d["possible_causes"],
                "solutions": solutions
            })
        
        return report


class AITroubleshooter(BaseToolWindow):
    def __init__(self):
        super().__init__('AITroubleshooter', 'AI故障诊断', '1.0.0', 1100, 800)
        self.engine = DiagnosisEngine()
        self.symptom_checkboxes = {}
        self.current_diagnoses = None
        self.current_symptoms = []
        self._build_ui()
        self._connect_signals()
        self.logger.info("AI故障诊断已初始化")
    
    def _build_ui(self):
        central = QWidget()
        main_layout = QHBoxLayout(central)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧症状选择
        symptom_panel = self._build_symptom_panel()
        splitter.addWidget(symptom_panel)
        
        # 右侧诊断结果
        result_panel = self._build_result_panel()
        splitter.addWidget(result_panel)
        
        splitter.setSizes([350, 750])
        main_layout.addWidget(splitter)
        
        self.set_central_content(central)
    
    def _build_symptom_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        header = QLabel("选择症状（可多选）")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800; padding: 5px;")
        layout.addWidget(header)
        
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        for category, symptoms in SYMPTOM_CATEGORIES.items():
            group = QGroupBox(category)
            group_layout = QVBoxLayout(group)
            
            for symptom in symptoms:
                cb = QCheckBox(symptom["text"])
                cb.setProperty("symptom_id", symptom["id"])
                self.symptom_checkboxes[symptom["id"]] = cb
                group_layout.addWidget(cb)
            
            scroll_layout.addWidget(group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.btn_diagnose = QPushButton("▶ 开始诊断")
        self.btn_diagnose.setStyleSheet("QPushButton { background-color: #F44336; color: white; padding: 10px; font-size: 13px; font-weight: bold; border-radius: 4px; } QPushButton:hover { background-color: #D32F2F; }")
        btn_layout.addWidget(self.btn_diagnose)
        
        self.btn_clear = QPushButton("清除选择")
        btn_layout.addWidget(self.btn_clear)
        
        layout.addLayout(btn_layout)
        
        self.btn_export = QPushButton("导出诊断报告")
        self.btn_export.setEnabled(False)
        layout.addWidget(self.btn_export)
        
        return panel
    
    def _build_result_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        self.result_tabs = QTabWidget()
        
        # 摘要标签页
        self.summary_tab = QWidget()
        summary_layout = QVBoxLayout(self.summary_tab)
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet("QTextEdit { background-color: #1a1a2e; color: #e0e0e0; font-size: 13px; }")
        summary_layout.addWidget(self.summary_text)
        self.result_tabs.addTab(self.summary_tab, "诊断摘要")
        
        # 详细结果标签页
        self.detail_tab = QWidget()
        detail_layout = QVBoxLayout(self.detail_tab)
        self.detail_list = QListWidget()
        self.detail_list.setStyleSheet("QListWidget { background-color: #1a1a2e; }")
        detail_layout.addWidget(self.detail_list)
        self.result_tabs.addTab(self.detail_tab, "详细方案")
        
        # 报告预览标签页
        self.report_tab = QWidget()
        report_layout = QVBoxLayout(self.report_tab)
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setStyleSheet("QTextEdit { background-color: #1a1a2e; color: #e0e0e0; font-family: Consolas, monospace; font-size: 12px; }")
        report_layout.addWidget(self.report_text)
        self.result_tabs.addTab(self.report_tab, "报告预览")
        
        layout.addWidget(self.result_tabs)
        return panel
    
    def _connect_signals(self):
        self.btn_diagnose.clicked.connect(self._on_diagnose)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_export.clicked.connect(self._on_export)
    
    def _on_diagnose(self):
        symptom_ids = []
        for sid, cb in self.symptom_checkboxes.items():
            if cb.isChecked():
                symptom_ids.append(sid)
        
        if not symptom_ids:
            QMessageBox.warning(self, "提示", "请至少选择一个症状")
            return
        
        self.current_symptoms = symptom_ids
        self.current_diagnoses = self.engine.diagnose(symptom_ids)
        self._display_results(self.current_diagnoses)
        self.btn_export.setEnabled(True)
        self.logger.info(f"诊断完成: {len(symptom_ids)} 个症状")
    
    def _display_results(self, diagnoses):
        # 摘要
        self.summary_text.clear()
        severity_colors = {"严重": "#FF4444", "中等": "#FFAA00", "轻微": "#44AAFF"}
        
        html = "<h2 style='color:#FF9800;'>诊断结果</h2>"
        html += f"<p>{diagnoses['summary']}</p>"
        html += "<hr>"
        
        for d in diagnoses["diagnoses"]:
            color = severity_colors.get(d["severity"], "#FFFFFF")
            html += f"<h3 style='color:{color};'>【{d['severity']}】{d['title']}</h3>"
            html += "<p><b>可能原因:</b></p><ul>"
            for cause in d["possible_causes"]:
                html += f"<li>{cause}</li>"
            html += "</ul>"
            
            solutions = d["solutions"]
            html += "<p><b>解决步骤:</b></p><ol>"
            for s in solutions:
                html += f"<li>{s}</li>"
            html += "</ol><hr>"
        
        self.summary_text.setHtml(html)
        
        # 详细列表
        self.detail_list.clear()
        for d in diagnoses["diagnoses"]:
            color = severity_colors.get(d["severity"], "#FFFFFF")
            
            solutions = d["solutions"]
            if isinstance(solutions, dict):
                solutions = solutions.get("steps", [])
            
            item_text = f"{'='*50}\n"
            item_text += f"[{d['severity']}] {d['title']}\n"
            item_text += f"{'='*50}\n"
            item_text += "可能原因:\n"
            for cause in d["possible_causes"]:
                item_text += f"  • {cause}\n"
            item_text += "解决方案:\n"
            for i, s in enumerate(solutions, 1):
                item_text += f"  {i}. {s}\n"
            
            item = QListWidgetItem(item_text)
            item.setForeground(QColor(color))
            self.detail_list.addItem(item)
        
        # 报告预览
        report = self.engine.generate_report(self.current_symptoms, self.current_diagnoses)
        report_text = json.dumps(report, ensure_ascii=False, indent=2)
        self.report_text.setPlainText(report_text)
    
    def _on_clear(self):
        for cb in self.symptom_checkboxes.values():
            cb.setChecked(False)
        self.summary_text.clear()
        self.detail_list.clear()
        self.report_text.clear()
        self.current_diagnoses = None
        self.btn_export.setEnabled(False)
    
    def _on_export(self):
        if not self.current_diagnoses:
            QMessageBox.warning(self, "提示", "请先进行诊断")
            return
        
        path, _ = QFileDialog.getSaveFileName(self, "导出诊断报告", "diagnostic_report.json", "JSON文件 (*.json)")
        if path:
            try:
                report = self.engine.generate_report(self.current_symptoms, self.current_diagnoses)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", f"已导出到: {path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))


if __name__ == '__main__':
    import traceback
    try:

        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = AITroubleshooter()
        window.show()
        sys.exit(app.exec())
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "AITroubleshooter - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
