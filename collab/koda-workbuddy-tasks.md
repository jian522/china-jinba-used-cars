# Koda ↔ WorkBuddy 协作任务单

> 用途：Koda（云端）与 WorkBuddy（九鼎电脑本地）协作的任务交接单。
> Koda 把需要在电脑上做的事写在这里，WorkBuddy 在电脑上执行，执行完把结果写回这里（或直接提交到仓库）。
> 使用方法：WorkBuddy 每次开始工作前先读这个文件；Koda 有新任务时更新它并告诉用户。

## 进行中的任务

### 1. 官网 Telegram 收尾部署（2026-11-18，待做）
- 详见：`给WorkBuddy的任务-收尾部署.md`（同一目录）
- 要点：git pull → git add 4 个新文件（telegram_config.json、telegram_block.py、assets/telegram.css、images/telegram-qr-placeholder.svg）→ 在 rebuild_home_v7.py 的 foot_cols 里 LANGUAGES 后面加 TELEGRAM 列（4 频道 + Bot）→ 重新生成四语首页 → 运行 一键部署官网.bat → 核对线上四语首页（TELEGRAM 列 + jb-tg 推广有样式 + telegram.css 能打开）。

## 已完成的任务

- （无。完成后把上面的任务移到这里，写清结果和提交号。）

## 约定

- Koda 只写任务，不直接改电脑上的文件；WorkBuddy 只改任务单里写明的文件。
- 部署一律走电脑上的 一键部署官网.bat（Cloudflare Pages 项目 jinba-cars），不要从仓库部署。
- 涉及密码、密钥、验证码的步骤，WorkBuddy 停下来等用户亲自做，不要代填。
- 每次执行完，在“已完成的任务”里写清：做了什么、结果、线上核对情况。
