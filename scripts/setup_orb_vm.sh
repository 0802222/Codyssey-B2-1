#!/usr/bin/env bash
# OrbStack Linux VM에서 최초 1회 실행하는 준비 스크립트.
# apt 패키지 설치 + 레포 클론 + demo.sh 실행까지 한 번에 수행한다.
#
# 사용법 (VM 안에서):
#   curl -fsSL https://raw.githubusercontent.com/0802222/Codyssey-B2-1/main/scripts/setup_orb_vm.sh | bash
# 또는 이미 레포가 있다면:
#   bash scripts/setup_orb_vm.sh

set -euo pipefail

REPO_URL="https://github.com/0802222/Codyssey-B2-1"
REPO_DIR="$HOME/Codyssey-B2-1"

echo "=== 1. apt 패키지 설치 (git, nano, python3) ==="
sudo apt-get update -y
sudo apt-get install -y git nano python3 python3-venv

echo
echo "=== 2. python3 버전 확인 (요구사항: 3.10 이상) ==="
python3 --version

echo
echo "=== 3. 레포 클론 ==="
if [ -d "$REPO_DIR/.git" ]; then
  echo "이미 클론되어 있음: $REPO_DIR (git pull로 갱신)"
  git -C "$REPO_DIR" pull
else
  git clone "$REPO_URL" "$REPO_DIR"
fi

echo
echo "=== 4. 10개 기능 데모 스크립트 실행 ==="
cd "$REPO_DIR"
chmod +x scripts/demo.sh
./scripts/demo.sh
