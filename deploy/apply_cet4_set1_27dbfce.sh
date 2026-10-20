#!/usr/bin/env bash
# Deploy CET-4 Set 1 from the exact reviewed Git commit to the existing
# non-Git production checkout. Run on the server as ubuntu via WebShell.
set -euo pipefail

revision=27dbfcee7a2590273b0d93ca9a36f8e2790c55de
live_dir=/var/www/english-ai
stage_dir=$(mktemp -d /home/ubuntu/cet4-set1.XXXXXX)
backup=/home/ubuntu/english-ai-before-cet4-set1-$(date +%Y%m%d-%H%M%S).tar.gz
success=0
installed=0

if [[ $(id -un) != ubuntu || ! -d "$live_dir/backend/listening" || ! -d "$live_dir/frontend/src" ]]; then
  echo '服务器用户或项目目录与预期不符，停止部署。' >&2
  exit 1
fi

cat > "$stage_dir/sha256.manifest" <<'HASHES'
ae5238385eee75fea52934236240ee726e88eeaa3b1ca7dc7cfe8a3fb07bc3e0  backend/listening/learning_content.py
69bc91c286e81c0ad5d3cbc658818a888946d31eaed8c70a50fa6598748afca8  backend/listening/learning_service.py
4e8d2978aa83d6eabef4fae5f99a932a4f888f082335b43a14420f1f18ca399b  backend/listening/router.py
8e0c2170d60e83787b31d5bcb66cef729e0dd8541b6898edc4090028282ffdeb  backend/listening/v2_exam_service.py
7837200b4a4c93bfcad5f1720d155d9d867e0450b9b8b95fbdccf241a399de70  backend/listening/v2_explanation_service.py
e23e55f27b0195fa2d387af3046567d0881c3dbd60516b4b582cc020e16d2bee  backend/listening/data/audio/cet4_202606_set1.mp3
d83e1bdfc9d2a824f81b164c6dcd531040dbf61518b970eb8d7e6301b30a5e7a  backend/listening/data/v2_full/cet4_202606_set1.candidate.json
1025dd12bcd4007f57b490a56a482cf482ee5ac787dda4b49ca84f6425613218  backend/listening/data/v2_full/cet4_202606_set1.explanations.json
3deefa87fe2f815a793a7366d27fe81c3bdaa03e9f81186c73076823c9128fbf  backend/listening/data/v2_full/cet4_202606_set1.learning_notes.json
4a7b45ade7fbbc71d66882d591ce54ddec56e02d507e5d56996fc425576be16b  backend/listening/data/v2_full/cet4_202606_set1.segment_timing.json
a5cf53b460c6c7fd4828dc07b8a19bf0257a1b9d3e8a804f126b87106c22f6ea  backend/listening/data/v2_full/cet4_202606_set2.explanations.json
ee76794e70ff5b5de986de0a180cd723e56b3d998e0c32113844b8012c167e33  backend/listening/data/v2_full/cet4_202606_set2.segment_timing.json
a0ab92d3a6f1ed88e389971aafa5c701366eb82aa9d052849cf9559d35337856  backend/listening/data/v2_full/cet6_202606_set2.segment_timing.json
e5b979aa8d9e8fce78dda8ff99153b613991d3377ff20df3479809725356b8c9  frontend/src/services/listeningApi.ts
c901f9efef94f6712a537cacc0b961a84c2548cebb822847a15c58e0a7a52689  frontend/src/services/learningApi.ts
11cc50542f9b02121dd0a5420ec588db143d2a78d9a9f4d3cf24b9a7d91ee8f2  frontend/src/views/ListeningView.vue
5f4601c71c6e785a7809b76d9917fb72f16d7de167d2c38dfa0597f07c79421c  frontend/src/views/listening/ListeningExamV2View.vue
ce2034458d69ede29bf98ad8037d6c718f2fc29f3a8a94a44422affdef40c010  frontend/src/views/listening/ListeningLearningView.vue
HASHES

mapfile -t files < <(awk '{print $2}' "$stage_dir/sha256.manifest")
echo "开始下载 ${#files[@]} 个发布文件到 $stage_dir"
for rel in "${files[@]}"; do
  mkdir -p "$stage_dir/$(dirname "$rel")"
  curl --fail --location --retry 8 --retry-all-errors --retry-delay 5 \
    --connect-timeout 20 --output "$stage_dir/$rel" \
    "https://raw.githubusercontent.com/Somuns1007/english-ai/$revision/$rel"
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
        'import json,sys; payload=json.load(sys.stdin); rows=payload.get("data",[]); assert any(r.get("id")=="cet4_202606_set1_v2" and r.get("has_audio") for r in rows)' \
      2>/dev/null; then
    success=1
    break
  fi
  sleep 2
done
if [[ "$success" != 1 ]]; then
  echo "新后端未在套题列表中返回四级第 1 套。日志：$stage_dir/uvicorn.log" >&2
  exit 1
fi
echo "部署成功：cet4_202606_set1_v2；备份：$backup"
