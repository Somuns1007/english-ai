#!/usr/bin/env bash
# Deploy CET-6 Set 1 and CET-4 timing review from the exact Git commit to the existing
# non-Git production checkout. Run on the server as ubuntu via WebShell.
set -euo pipefail

revision=5cabd0c4f7a0b86df6d9c7f5397b6ba95de3a0ef
live_dir=/var/www/english-ai
stage_dir=$(mktemp -d /home/ubuntu/cet6-set1.XXXXXX)
backup=/home/ubuntu/english-ai-before-cet6-set1-$(date +%Y%m%d-%H%M%S).tar.gz
success=0
installed=0

if [[ $(id -un) != ubuntu || ! -d "$live_dir/backend/listening" || ! -d "$live_dir/frontend/src" ]]; then
  echo '服务器用户或项目目录与预期不符，停止部署。' >&2
  exit 1
fi

cat > "$stage_dir/sha256.manifest" <<'HASHES'
1223b85e16b9a008d035002e05c43e7a3af5fe2c3927613fad04eb3aa32ffb42  backend/listening/learning_content.py
30976f25a291caf396a250ae0efdbe06bfe292d1e81691776f100041985b6e06  backend/listening/learning_service.py
fa6b4bfc21545f780a7f3154b2d0feb03d55fe87013fd98b052dfe6af6bc395e  backend/listening/router.py
b210f2b72b24331a86448f5b67309699b52332812376fdaaf8da45d1c37af1ac  backend/listening/v2_explanation_service.py
408b12bf018af7053270b270d51267e901f17a7ea8d5b87f528d733352b8b4bd  backend/listening/data/audio/cet6_202606_set1.mp3
a9f2ab334fab7f80b4cd5ed6812783f5f1300966b63d783fe0f6dfc3d564b085  backend/listening/data/exams/cet6_202606_set1.json
5a383dfa30d4d6d4e5647d5d3bd76068c566c6ae929853dd9f2f4d64f88a8184  backend/listening/data/v2_full/cet4_202606_set1.segment_timing.json
da6100f0376aeb5206c1ff17ab617e3c2a5a3a193800052b43bfa8196778a941  backend/listening/data/v2_full/cet6_202606_set1.candidate.json
de69adb9732786302806f8161cc5cf8f13728763de67c77c26a5e5cf2908a5c0  backend/listening/data/v2_full/cet6_202606_set1.learning_notes.json
1302efefd2e7afd5c33a75d063805ed7d15b4f94dc8a0a6798504c4a419c1a3e  backend/listening/data/v2_full/cet6_202606_set1.segment_timing.json
5c061c5104cef5af7e6b0bdfb61ee6103cf123050e474bc727214e7e414ac489  frontend/src/views/ListeningView.vue
802fe81df363f4a55f29634c3b57b5886535b769f8f00065bf48b1c0fb56c7be  frontend/src/views/listening/ListeningExamV2View.vue
def3ba568a442a1d2af92269ad755e6059b17b7179f3ff2ddf9e3b615a57b33b  frontend/src/views/listening/ListeningPracticeV2View.vue
a0c9e1b3ba665dced67a937cc78ab76d9842f0452c45b3b7cffd5951d585e873  frontend/src/services/learningApi.ts
c94e811b8c2f01108c7a2c1e124ac991642766fdd0d9f1a25fa0aeaa288285a1  frontend/src/views/listening/ListeningLearningView.vue
HASHES

mapfile -t files < <(awk '{print $2}' "$stage_dir/sha256.manifest")
echo "开始下载 ${#files[@]} 个发布文件到 $stage_dir"
for rel in "${files[@]}"; do
  mkdir -p "$stage_dir/$(dirname "$rel")"
  expected=$(awk -v path="$rel" '$2 == path {print $1}' "$stage_dir/sha256.manifest")
  if [[ -f "$live_dir/$rel" && $(sha256sum "$live_dir/$rel" | cut -d' ' -f1) == "$expected" ]]; then
    cp "$live_dir/$rel" "$stage_dir/$rel"
  else
    curl --fail --location --retry 8 --retry-all-errors --retry-delay 5 \
      --connect-timeout 20 --output "$stage_dir/$rel" \
      "https://raw.githubusercontent.com/Somuns1007/english-ai/$revision/$rel"
  fi
done
(cd "$stage_dir" && sha256sum --check sha256.manifest)

existing=()
new_files=()
for rel in "${files[@]}"; do
  if [[ -f "$live_dir/$rel" ]]; then existing+=("$rel"); else new_files+=("$rel"); fi
done
if [[ -d "$live_dir/frontend/dist" ]]; then existing+=(frontend/dist); fi
tar -czf "$backup" -C "$live_dir" "${existing[@]}"
tar -tzf "$backup" >/dev/null
echo "旧文件和前端产物已备份到 $backup"

restart_backend() {
  if systemctl is-active --quiet english-ai; then
    sudo systemctl restart english-ai
    return
  fi
  local old_pid cmd process_dir
  old_pid=$(sudo ss -H -ltnp '( sport = :8000 )' | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u || true)
  # Some WebShell environments omit process details from ss. Fall back to the
  # exact known bare uvicorn command, then validate its cwd below.
  if [[ -z "$old_pid" ]]; then
    old_pid=$(pgrep -f '^/var/www/english-ai/backend/venv/bin/python3 venv/bin/uvicorn main:app --host 127\.0\.0\.1 --port 8000$' || true)
  fi
  if [[ -n "$old_pid" && ! "$old_pid" =~ ^[0-9]+$ ]]; then
    echo "无法唯一确认 8000 端口监听进程：$old_pid" >&2
    return 1
  fi
  if [[ -n "$old_pid" ]]; then
    cmd=$(tr '\0' ' ' < "/proc/$old_pid/cmdline")
    process_dir=$(readlink -f "/proc/$old_pid/cwd")
    if [[ "$process_dir" != "$(readlink -f "$live_dir/backend")" || "$cmd" != *uvicorn* || "$cmd" != *main:app* ]]; then
      echo "8000 端口进程不属于预期后端，停止部署：PID=$old_pid" >&2
      return 1
    fi
    kill "$old_pid"
    for _ in {1..10}; do
      if ! kill -0 "$old_pid" 2>/dev/null; then break; fi
      sleep 1
    done
    if kill -0 "$old_pid" 2>/dev/null; then
      echo '旧后端进程尚未退出。' >&2
      return 1
    fi
  elif curl -fsS --max-time 2 http://127.0.0.1:8000/ >/dev/null 2>&1; then
    echo '8000 端口已有未识别的后端进程，停止部署。' >&2
    return 1
  fi
  (cd "$live_dir/backend"; nohup venv/bin/python3 venv/bin/uvicorn main:app \
    --host 127.0.0.1 --port 8000 > "$stage_dir/uvicorn.log" 2>&1 < /dev/null &)
}

rollback_on_error() {
  if [[ "$success" == 1 || "$installed" == 0 ]]; then return; fi
  echo "部署中断，正在从 $backup 恢复旧文件。" >&2
  sudo tar -xzf "$backup" -C "$live_dir"
  for rel in "${new_files[@]}"; do
    if [[ -f "$live_dir/$rel" ]]; then
      mkdir -p "$stage_dir/failed/$(dirname "$rel")"
      mv "$live_dir/$rel" "$stage_dir/failed/$rel"
    fi
  done
  if [[ "$backend_restart_attempted" == 1 ]]; then restart_backend || true; fi
}
trap rollback_on_error EXIT

installed=1
backend_restart_attempted=0
for rel in "${files[@]}"; do
  install -D -m 644 "$stage_dir/$rel" "$live_dir/$rel"
done
(cd "$live_dir/backend" && venv/bin/python3 -m py_compile \
  listening/learning_content.py listening/learning_service.py listening/router.py \
  listening/v2_exam_service.py listening/v2_explanation_service.py)
(cd "$live_dir/frontend" && sudo npm run build)
backend_restart_attempted=1
restart_backend

for _ in {1..12}; do
  if curl -fsS http://127.0.0.1:8000/api/listening/v2/exams \
      | "$live_dir/backend/venv/bin/python3" -c \
        'import json,sys; payload=json.load(sys.stdin); rows=payload.get("data",[]); assert any(r.get("id")=="cet6_202606_set1_v2" and r.get("has_audio") for r in rows)' \
      2>/dev/null; then
    success=1
    break
  fi
  sleep 2
done
if [[ "$success" != 1 ]]; then
  echo "新后端未在套题列表中返回六级第 1 套。日志：$stage_dir/uvicorn.log" >&2
  exit 1
fi
echo "部署成功：cet6_202606_set1_v2；备份：$backup"
