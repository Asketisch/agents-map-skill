#!/usr/bin/env bash
# check_agents_docs.sh —— AGENTS.md 体系自检(链接 / 行数预算 / 章节完整性 / 索引闭合)
# 用法: check_agents_docs.sh [repo_root]     默认当前目录
# 退出码: 0=通过(warning 不计) 1=有 error 2=用法错误
set -u
ROOT="${1:-.}"
cd "$ROOT" 2>/dev/null || { echo "找不到目录: $ROOT" >&2; exit 2; }
ROOT=$(pwd -P)

# ---- 收集篇目(排除构建产物与 submodule 镜像目录) ----
DOCS=$(find . \( -path '*/.git' -o -path '*/target' -o -path '*/node_modules' \
       -o -path '*/dist' -o -path '*/build' -o -path '*/vendor' \) -prune -o \
       -name AGENTS.md -print | sed 's|^\./||' | sort)
if [ -f .gitmodules ]; then
  for s in $(git config -f .gitmodules --get-regexp '\.path$' 2>/dev/null | awk '{print $2}'); do
    DOCS=$(echo "$DOCS" | grep -v "^${s}/" || true)
  done
fi
# 排除 submodule 镜像(gitlink:祖先目录有 .git 文件而非目录)
FILTERED=""; MIRRORS=""
for f in $DOCS; do
  p=$(dirname "$f"); skip=0
  while [ "$p" != "." ]; do
    if [ -f "$p/.git" ]; then skip=1
      case "$MIRRORS" in *" $p/"*) ;; *) MIRRORS="$MIRRORS $p/";; esac; break; fi
    p=$(dirname "$p")
  done
  [ "$skip" = 0 ] && FILTERED="$FILTERED
$f"
done
DOCS=$(echo "$FILTERED" | sed '/^$/d')
[ -n "$MIRRORS" ] && echo "  [note ] 已排除 submodule 镜像目录:$MIRRORS"
[ -n "$DOCS" ] || { echo "未发现任何 AGENTS.md"; exit 1; }

ERR=0; WARN=0
w(){ echo "  [warn ] $*"; WARN=$((WARN+1)); }
e(){ echo "  [ERROR] $*"; ERR=$((ERR+1)); }

abspath(){ # 规范化相对路径(不要求存在),纯字符串处理 ../ 与 ./
  local p="$1" out="" seg
  p="${p#./}"
  local IFS=/
  for seg in $p; do
    case "$seg" in
      .|"") ;;
      ..) case "$out" in */*) out="${out%/*}" ;; ?*) out="" ;; esac ;;
      *) out="${out:+$out/}$seg" ;;
    esac
  done
  echo "$out"
}

# ---- 链接检查 + 汇总被指向路径(供孤儿检测;空格分隔) ----
LINKED=" "
for d in $DOCS; do
  dir=$(dirname "$d")
  # 先剔除行内代码片段,避免把示例 `[text](url)` 当链接
  for t in $(sed -E 's/`[^`]*`//g' "$d" | grep -oE '\]\([^)]+\)' | sed -E 's/^\]\(//; s/\)$//; s/#.*$//' | sort -u); do
    [ -z "$t" ] && continue
    case "$t" in http*) continue ;; esac
    case "$t" in
      /*) t="${t#/}" ;;
      *)  t="${dir}/${t}" ;;
    esac
    t=$(abspath "$t")
    ok=0
    case "$t" in
      *.md) [ -e "$t" ] && ok=1 ;;
      *)    t2="${t%/}"; { [ -d "$t2" ] || [ -f "$t2" ]; } && ok=1 ;;
    esac
    if [ "$ok" = 1 ]; then
      case "$t" in
        */)  LINKED="$LINKED${t%/}/AGENTS.md " ;;   # 目录链接视为指向其 AGENTS.md
        *)   LINKED="$LINKED$t " ;;
      esac
    else
      e "$d: 死链 -> $t"
    fi
  done
done

# ---- 行数预算 & 章节完整性 ----
for f in $DOCS; do
  n=$(wc -l < "$f" | tr -d ' ')
  # 按"相对所属仓库根的深度"分类:0=根篇/路由篇 1=目录篇 2=层篇 3+=成员篇
  rr=$(dirname "$f"); rrroot=""
  while :; do
    [ -d "$rr/.git" ] && { rrroot="$rr/"; break; }
    [ "$rr" = "." ] && break
    rr=$(dirname "$rr")
  done
  rel="${f#$rrroot}"
  depth=$(echo "$rel" | tr -cd '/' | wc -c | tr -d ' ')
  case "$depth:$rrroot" in
    0:"")          kind=router; hi=120 ;;
    0:*)           kind=root;   hi=200 ;;
    1:*)           kind=dir;    hi=130 ;;
    2:*)           kind=layer;  hi=130 ;;
    *)             kind=member; hi=90  ;;
  esac
  [ "$n" -gt "$hi" ] && w "$f: ${n} 行 > ${kind} 上限 ${hi} → 考虑下拆(见 splitting.md)"
  [ "$n" -lt 15 ] && w "$f: ${n} 行,过薄 → 考虑上合进父篇"
  case "$kind" in root|router) ;; \
    *) grep -q '何时读我' "$f" || w "$f: 缺「何时读我」句" ;; esac
  case "$kind" in
    layer) grep -q '速览' "$f" || w "$f: 层篇缺「速览」表"
           grep -q '^## 深入阅读' "$f" || w "$f: 层篇缺「深入阅读」" ;;
    member|dir)
           grep -q '契约' "$f" || w "$f: 缺本地契约类小节"
           grep -q '禁止事项' "$f" || w "$f: 缺「禁止事项」节" ;;
  esac
done

# ---- 索引闭合:每篇(除根)必须被某篇链接指向 ----
for f in $DOCS; do
  [ "$f" = "AGENTS.md" ] && continue
  case "$LINKED" in *" $f "*) ;; *) e "孤儿篇: $f 未被任何 AGENTS.md 链接指向" ;; esac
done

echo
cnt=$(echo "$DOCS" | wc -w | tr -d ' ')
echo "AGENTS.md 体系自检(${ROOT}): ${cnt} 篇 | error=${ERR} warning=${WARN}"
[ "$ERR" -eq 0 ] && exit 0 || exit 1
