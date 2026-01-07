import sys
import json
import os
import calendar
from datetime import datetime

# === 配置 ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "daka_status.json")

CAP = 1000           # 月上限
PRICE = 20           # 单价
MAX_DAILY = 2        # 日上限
# ============

def load_data():
    now = datetime.now()
    current_month = now.strftime("%Y-%m")
    today_str = now.strftime("%Y-%m-%d")

    default_data = {
        "month": current_month,
        "total_valid_punches": 0,
        "suspect_times": [],
        "today": {"date": today_str, "count": 0},
        "history": {}
    }

    if not os.path.exists(DATA_FILE): return default_data

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
    except: return default_data

    # 轮转逻辑
    history = dict(data.get("history", {}))
    if data.get("month") != current_month:
        prev_month = data.get("month")
        if prev_month:
            prev_total = data.get("total_valid_punches", 0)
            prev_real = min(prev_total * PRICE, CAP)
            history[prev_month] = prev_real
        data = default_data
        data["history"] = history
        save_data(data)
    else:
        data.setdefault("today", {"date": today_str, "count": 0})
        data["history"] = history

    if data.get("today", {}).get("date") != today_str:
        data["today"] = {"date": today_str, "count": 0}
        
    return data

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def count_workdays_remaining():
    """计算本月剩余的工作日天数（不包括今天，不包括周六日）"""
    now = datetime.now()
    _, days_in_month = calendar.monthrange(now.year, now.month)
    
    workdays = 0
    for day in range(now.day + 1, days_in_month + 1):
        date = datetime(now.year, now.month, day)
        # 0=周一, 6=周日
        if date.weekday() < 5:  # 周一到周五
            workdays += 1
    
    return workdays

def calculate_weekend_punches_needed(data):
    """计算假设工作日满勤，还需要在周末补打卡多少次才能达到上限"""
    total_punches = data["total_valid_punches"]
    needed_for_cap = CAP // PRICE  # 要达到上限需要的总打卡次数 (50次)
    
    # 如果已经达到或超过上限，返回None
    if total_punches >= needed_for_cap:
        return None
    
    # 今天还能打卡几次
    today_left = max(0, MAX_DAILY - data["today"]["count"])
    
    # 剩余的工作日天数（不包括今天）
    workdays_remaining = count_workdays_remaining()
    
    # 假设工作日满勤，还能获得的打卡次数
    workday_punches = today_left + workdays_remaining * MAX_DAILY
    
    # 还需要打卡的次数
    remaining_needed = needed_for_cap - total_punches
    
    # 需要在周末补打卡的次数
    weekend_needed = remaining_needed - workday_punches
    
    return weekend_needed if weekend_needed > 0 else 0

def calculate_allowed_absences(data):
    """计算要达到上限最多还可以缺勤多少次"""
    total_punches = data["total_valid_punches"]
    needed_for_cap = CAP // PRICE  # 要达到上限需要的总打卡次数
    
    # 如果已经达到或超过上限，返回None
    if total_punches >= needed_for_cap:
        return None
    
    now = datetime.now()
    _, days_in_month = calendar.monthrange(now.year, now.month)
    
    today_left = max(0, MAX_DAILY - data["today"]["count"])
    days_remaining = max(0, days_in_month - now.day)
    
    # 理论上还能打卡的最大次数
    max_future_punches = today_left + days_remaining * MAX_DAILY
    
    # 还需要打卡的次数
    remaining_needed = needed_for_cap - total_punches
    
    # 可缺勤次数 = 理论最大次数 - 还需次数
    allowed_absences = max_future_punches - remaining_needed
    
    return allowed_absences if allowed_absences >= 0 else 0

def cmd_punch_strict():
    data = load_data()
    if data["today"]["count"] >= MAX_DAILY:
        print(f"\033[93m[Info] Daily limit ({MAX_DAILY}) reached. Ignored.\033[0m")
        return

    data["total_valid_punches"] += 1
    data["today"]["count"] += 1
    save_data(data)
    print(f"\033[92m[STRICT] +{PRICE} RMB.\033[0m")
    
    # 如果需要周末补打卡，显示警告
    weekend_needed = calculate_weekend_punches_needed(data)
    if weekend_needed is not None and weekend_needed > 0:
        print(f"\033[91m[WARNING] Need {weekend_needed} weekend punches to reach cap (assuming full workday attendance)!\033[0m")
    
    cmd_stats(data)

def cmd_punch_suspect(time_str):
    data = load_data()
    if time_str not in data["suspect_times"]:
        data["suspect_times"].append(time_str)
        save_data(data)
        print(f"\033[93m[PROBE] '{time_str}' saved.\033[0m")
    else:
        print(f"'{time_str}' already exists.")
    cmd_stats(data)

def cmd_stats(data=None):
    if not data: data = load_data()
    
    # 1. 算钱
    total_punches = data["total_valid_punches"]
    current_money = total_punches * PRICE
    # 实际到手不能超过总封顶
    real_money = min(current_money, CAP)
    
    # 2. 算上限 (Projection)
    now = datetime.now()
    _, days_in_month = calendar.monthrange(now.year, now.month)
    
    today_left = max(0, MAX_DAILY - data["today"]["count"])
    days_remaining = max(0, days_in_month - now.day)
    
    # 理论还能拿多少钱
    future_potential = (today_left * PRICE) + (days_remaining * MAX_DAILY * PRICE)
    
    # 动态分母：本月最终理论极限
    # = (已落袋 + 未来潜力) 和 1000 取较小值
    dynamic_ceiling = min(current_money + future_potential, CAP)

    # --- 输出 ---
    print(f"\n====== Status ({data['month']}) ======")
    
    # 分母颜色逻辑：如果上限已经低于 1000，把分母标红，警示损失
    denom_color = "\033[96m" if dynamic_ceiling == CAP else "\033[91m"
    
    print(f"Valid Punches : {total_punches}")
    print(f"Money Secured : \033[1;32m{real_money}\033[0m / {denom_color}{dynamic_ceiling}\033[0m")
    
    # 进度条 (基于动态上限)
    if dynamic_ceiling > 0:
        percent = int((real_money / dynamic_ceiling) * 100)
        bar_len = 20
        filled = int((real_money / dynamic_ceiling) * bar_len)
        bar = '█' * filled + '░' * (bar_len - filled)
        print(f"Progress      : [{bar}] {percent}%")

    if data.get("suspect_times"):
        print(f"\n--- Suspect Logs ---")
        print("\033[93m" + ", ".join(data["suspect_times"]) + "\033[0m")

    history = data.get("history", {})
    if history:
        print(f"\n--- Monthly Earnings ---")
        for month in sorted(history.keys(), reverse=True):
            print(f"{month} : {history[month]}")
    
    # 简短的文字总结
    diff = dynamic_ceiling - real_money
    if diff <= 0:
        if real_money >= CAP:
            print(f"\n\033[92m[DONE] Cap reached ({CAP}).\033[0m")
        else:
            print(f"\n\033[91m[DONE] Maxed out at {dynamic_ceiling}. You missed too many.\033[0m")
    else:
        print(f"\nTarget: Need {diff} more to hit possible max.")

    remaining_punches = (diff + PRICE - 1) // PRICE if diff > 0 else 0
    print(f"Remaining punches to hit current ceiling ({dynamic_ceiling}): {remaining_punches}")
    
    # 显示可缺勤次数
    allowed_absences = calculate_allowed_absences(data)
    if allowed_absences is not None:
        color = "\033[91m" if allowed_absences <= 3 else "\033[93m" if allowed_absences <= 10 else "\033[92m"
        print(f"Allowed absences to reach cap ({CAP}): {color}{allowed_absences}\033[0m")
    else:
        print(f"Allowed absences to reach cap ({CAP}): \033[92mCap already reached!\033[0m")
    
    # 显示周末补打卡需求
    weekend_needed = calculate_weekend_punches_needed(data)
    if weekend_needed is not None:
        if weekend_needed > 0:
            color = "\033[91m" if weekend_needed > 0 else "\033[92m"
            print(f"Weekend punches needed (if workdays full): {color}{weekend_needed}\033[0m")
        else:
            print(f"Weekend punches needed (if workdays full): \033[92m0 (workdays enough)\033[0m")
    else:
        print(f"Weekend punches needed (if workdays full): \033[92mN/A (cap reached)\033[0m")

def cmd_history():
    data = load_data()
    history = data.get("history", {})
    if not history:
        print("\n[History] No recorded earnings yet.")
        return

    print(f"\n--- Monthly Earnings ---")
    for month in sorted(history.keys(), reverse=True):
        print(f"{month} : {history[month]}")

def main():
    if len(sys.argv) == 1: cmd_punch_strict()
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg == 's': cmd_stats()
        elif arg == 'h': cmd_history()
        else: cmd_punch_suspect(arg)
    else: print("Usage: dk | dk 9:34 | dk s")

if __name__ == "__main__":
    main()