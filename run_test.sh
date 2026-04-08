#!/bin/bash
cd /root/dev_work/stock-analyzer
source local_venv/bin/activate
python stock_analyzer.py 600276.SH --output both --days 30
