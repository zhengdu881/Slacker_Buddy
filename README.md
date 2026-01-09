
# 📅 Daka Tracker - 个人打卡与收益追踪工具

这是一个基于 Python 的轻量级命令行工具，用于追踪每日打卡状态、计算预计收益，并自动根据当月剩余工作日提醒你是否需要周末补卡。

## ✨ 主要功能

* **智能收益计算**：根据单价（20元）和月上限（1000元）自动计算已到手金额。
* **动态预测**：基于当前进度，预测本月最终能拿到的最高金额（如果上限已无法达成，会变红提醒）。
* **考勤补位分析**：
* **Allowed absences**: 提醒你为了拿满奖金，本月还能“翘课”多少次。
* **Weekend punches needed**: 如果工作日打满也拿不满上限，会自动计算还需要在周末补打多少卡。


* **缺勤统计**：自动列出本月所有漏打卡的工作日日期。
* **自动月结**：每月初第一次运行程序时，会自动归档上月数据到历史记录。

---

## 🚀 快速开始

### 1. 准备工作

确保你已安装 Python 3.x，并将 `daka_status.py` 放在一个固定的目录下。

### 2. 使用方法

| 命令 | 说明 |
| --- | --- |
| `python daka_status.py` | **正式打卡**：增加一次打卡记录并保存日期 |
| `python daka_status.py s` | **查看状态**：显示当前进度、预测、缺勤等统计 |
| `python daka_status.py 9:30` | **可疑日志**：记录一个时间点，不计入正式金额（用于备忘） |
| `python daka_status.py h` | **查看历史**：列出往月结算的金额 |

---

## 🔥 进阶：配置别名 (Alias)

为了实现“随手打卡”，强烈建议配置别名。这样你只需要在终端输入 `dk` 即可完成打卡。

### 在 Linux / macOS (zsh 或 bash)

1. 打开配置文件（如 `~/.zshrc` 或 `~/.bashrc`）：
```bash
nano ~/.zshrc

```


2. 在文件末尾添加一行（请修改为你的实际路径）：
```bash
alias dk='python3 /path/to/your/daka_status.py'

```


3. 保存并刷新配置：`source ~/.zshrc`
4. 现在你可以直接使用：
* `dk` (打卡)
* `dk s` (看状态)



### 在 Windows (PowerShell)

1. 打开 PowerShell 配置文件：
```powershell
notepad $PROFILE

```


2. 添加以下函数：
```powershell
function dk {
    python "C:\你的路径\daka_status.py" $args
}

```


3. 重启 PowerShell 即可使用 `dk` 命令。

---

## ⚙️ 逻辑配置

你可以在脚本顶部的 `=== 配置 ===` 区域修改以下参数：

* `CAP`: 每月最高收益限额（默认 1000）。
* `PRICE`: 单次打卡金额（默认 20）。


* `MAX_DAILY`: 每日允许打卡次数（默认 2）。

## 📂 数据存储

数据保存在同目录下的 `daka_status.json` 中，请勿手动编辑该文件以免格式错误。

