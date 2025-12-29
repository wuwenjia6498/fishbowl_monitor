#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试黄金价格获取功能
"""
import sys
import io
import yfinance as yf

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("Test Gold Price Retrieval")
print("=" * 60)

# 测试 GLD ETF
print("\nMethod 1: Testing GLD ETF data...")
try:
    gld = yf.Ticker("GLD")
    gld_hist = gld.history(period="5d")

    if not gld_hist.empty:
        print(f"[OK] Retrieved {len(gld_hist)} days of data")
        print("\nRecent 5 days:")
        print(gld_hist[['Close']])

        latest_data = gld_hist.iloc[-1]
        prev_close = gld_hist.iloc[-2]['Close'] if len(gld_hist) > 1 else latest_data['Close']

        gld_price = float(latest_data['Close'])
        conversion_factor = 10.87
        gold_price = gld_price * conversion_factor
        price_change = ((gld_price - prev_close) / prev_close) * 100

        print(f"\n[SUCCESS] GLD Close: ${gld_price:.2f}")
        print(f"[SUCCESS] Gold Price: ${gold_price:.2f}/oz")
        print(f"[SUCCESS] Change: {'+' if price_change >= 0 else ''}{price_change:.2f}%")
    else:
        print("[WARN] GLD data is empty")
except Exception as e:
    print(f"[ERROR] GLD retrieval failed: {str(e)}")

# 测试黄金期货
print("\n" + "=" * 60)
print("\nMethod 2: Testing Gold Futures (GC=F)...")
try:
    gc = yf.Ticker("GC=F")
    gc_hist = gc.history(period="5d")

    if not gc_hist.empty:
        print(f"[OK] Retrieved {len(gc_hist)} days of data")
        print("\nRecent 5 days:")
        print(gc_hist[['Close']])

        latest_data = gc_hist.iloc[-1]
        prev_close = gc_hist.iloc[-2]['Close'] if len(gc_hist) > 1 else latest_data['Close']

        gold_price = float(latest_data['Close'])
        price_change = ((gold_price - prev_close) / prev_close) * 100

        print(f"\n[SUCCESS] Gold Futures Price: ${gold_price:.2f}/oz")
        print(f"[SUCCESS] Change: {'+' if price_change >= 0 else ''}{price_change:.2f}%")
    else:
        print("[WARN] Gold futures data is empty")
except Exception as e:
    print(f"[ERROR] Gold futures retrieval failed: {str(e)}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
