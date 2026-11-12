#!/usr/bin/env bash
set -Eeuo pipefail

repo_root="$(git rev-parse --show-toplevel)"
# shellcheck disable=SC1091
source "${repo_root}/SOURCE_PIN.env"

analysis_root="${repo_root}/.codebase-memory-worktree"
engine_root="${SELACO_ANALYSIS_ROOT:-${analysis_root}/GZSelaco-controls}"

if [[ -e "${engine_root}" ]]; then
  echo "error: analysis tree already exists: ${engine_root}" >&2
  echo "move it aside or pass its path directly to Codebase Memory" >&2
  exit 2
fi

mkdir -p "${analysis_root}"

git init -q "${engine_root}"
git -C "${engine_root}" remote add origin "${GZSELACO_REPOSITORY}"
git -C "${engine_root}" fetch -q --depth=1 origin "${GZSELACO_COMMIT}"
git -C "${engine_root}" checkout -q --detach FETCH_HEAD

resolved_commit="$(git -C "${engine_root}" rev-parse HEAD)"
if [[ "${resolved_commit}" != "${GZSELACO_COMMIT}" ]]; then
  echo "error: resolved GZSelaco commit does not match SOURCE_PIN.env" >&2
  exit 1
fi

python3 "${repo_root}/scripts/patch-gzselaco-ios-m0.py" \
  "${engine_root}" \
  "${repo_root}/overlays/gzselaco-ios/i_platform_stub.cpp"
python3 "${repo_root}/scripts/patch-gzselaco-vulkan-only-ios-m0.py" \
  "${engine_root}"
python3 "${repo_root}/scripts/patch-gzselaco-runtime-bootstrap-ios-m1.py" \
  "${engine_root}"
python3 "${repo_root}/scripts/patch-gzselaco-swapchain-ios-m2.py" \
  "${engine_root}"
python3 "${repo_root}/scripts/run-m3-local-asset-patcher.py" \
  "${engine_root}"
python3 "${repo_root}/scripts/patch-gzselaco-engine-init-ios-m4.py" \
  "${engine_root}"
python3 "${repo_root}/scripts/patch-gzselaco-engine-renderer-ios-m4b.py" \
  "${engine_root}"
python3 "${repo_root}/scripts/patch-gzselaco-runtime-handoff-ios-m4b.py" \
  "${engine_root}"
python3 "${repo_root}/scripts/patch-gzselaco-title-menu-ios-m4b.py" \
  "${engine_root}"
python3 "${repo_root}/scripts/patch-zvulkan-engine-renderer-ios-m4b.py" \
  "${engine_root}"
python3 "${repo_root}/scripts/patch-gzselaco-title-menu-closure-ios-m4c.py" \
  "${engine_root}"
python3 "${repo_root}/scripts/patch-gzselaco-mach-class-registry-ios-m4d.py" \
  "${engine_root}"
python3 "${repo_root}/scripts/patch-gzselaco-zscript-diagnostics-ios-m4e.py" \
  "${engine_root}"
python3 "${repo_root}/scripts/patch-gzselaco-saveguard-ios-m4m.py" "${engine_root}"

python3 "${repo_root}/scripts/patch-gzselaco-touch-ios.py" "${engine_root}"
python3 "${repo_root}/scripts/patch-gzselaco-resolution-launcher.py" "${engine_root}"
python3 "${repo_root}/scripts/patch-gzselaco-scene-scale.py" "${engine_root}"
if [[ "${SELACO_IOS_AUDIO_CANDIDATE:-0}" == 1 ]]; then
  python3 "${repo_root}/scripts/patch-gzselaco-audio-candidate.py" "${engine_root}"
fi
if [[ "${SELACO_IOS_SAVES_CANDIDATE:-0}" == 1 ]]; then
  python3 "${repo_root}/scripts/patch-gzselaco-atomic-save-candidate.py" "${engine_root}"
fi

git -C "${engine_root}" diff --check

echo "materialized=${engine_root}"
echo "source_commit=${resolved_commit}"
echo "patch_level=M4M"
