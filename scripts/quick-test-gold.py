#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试黄金价格获取
"""
import sys
import io
import time

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Waiting 3 seconds to avoid rate limit...")
time.sleep(3)

import yfinance as yf

print("\nTesting GLD ETF...")
try:
    gld = yf.Ticker("GLD")
    gld_hist = gld.history(period="2d")

    if not gld_hist.empty:
        gld_price = float(gld_hist.iloc[-1]['Close'])
        gold_price = gld_price * 10.87
        print(f"[SUCCESS] GLD: ${gld_price:.2f}")
        print(f"[SUCCESS] Gold: ${gold_price:.2f}/oz")
    else:
        print("[WARN] No data")
except Exception as e:
    print(f"[ERROR] {str(e)}")
