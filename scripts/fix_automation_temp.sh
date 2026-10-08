#!/bin/bash
# WorkBuddy 定时任务启动配置目录守护
#
# 背景（2026-10-04 / 10-08 两次实测事故）：
#   WorkBuddy 的 TEMP 指向 D:\Temp。定时任务启动时需要
#   D:\Temp\workbuddy-conversation-product-<随机后缀>\acc-product-config-v3-*.json.N.tmp
#   作为会话启动配置。该目录一旦被任何磁盘清理工具删掉，**所有**定时任务
#   会在 1 秒内启动失败：
#     CONNECT_FAILED: ENOENT ... acc-product-config-v3-*.json.N.tmp
#     external:automation.failed
#   业务代码一行都没跑，且任务自己发不出报告（天然盲区）。
#
# 处置：重建目录即可恢复，无需重启 WorkBuddy（2026-10-04 探针实测通过）。
# 本脚本做幂等重建，可安全重复执行。
#
# 用法：bash scripts/fix_automation_temp.sh
# 建议：挂到 Windows 计划任务每小时跑一次（见文件末尾说明）。

set -u
TEMP_ROOT="${WORKBUDDY_TEMP_ROOT:-/d/Temp}"

if [ ! -d "$TEMP_ROOT" ]; then
  mkdir -p "$TEMP_ROOT" || { echo "[FAIL] 无法创建 $TEMP_ROOT"; exit 1; }
  echo "[fix] 已创建 TEMP 根目录 $TEMP_ROOT"
fi

# 找出 daemon 最近一次使用过的会话目录后缀，只重建用过的那些。
# 兜底：若一个都没扫到，则建一个通用的占位目录（daemon 下次启动会自建自己的）。
SUFFIXES=$(grep -ao 'workbuddy-conversation-product-[A-Za-z0-9]\{4,\}' \
             "$HOME/.workbuddy/logs/daemon.log" 2>/dev/null \
           | sed 's/.*-product-//' | sort -u)

CREATED=0
if [ -n "$SUFFIXES" ]; then
  for s in $SUFFIXES; do
    d="$TEMP_ROOT/workbuddy-conversation-product-$s"
    if [ ! -d "$d" ]; then
      mkdir -p "$d" && CREATED=$((CREATED+1)) && echo "[fix] 重建 $d"
    fi
  done
else
  d="$TEMP_ROOT/workbuddy-conversation-product-watchdog"
  [ -d "$d" ] || { mkdir -p "$d" && CREATED=$((CREATED+1)) && echo "[fix] 兜底重建 $d"; }
fi

TOTAL=$(ls -d "$TEMP_ROOT"/workbuddy-conversation-product-* 2>/dev/null | wc -l)
echo "[ok] 本次新建 $CREATED 个，当前可用会话目录 $TOTAL 个"
[ "$TOTAL" -gt 0 ] || { echo "[FAIL] 仍无任何会话目录"; exit 1; }
exit 0
