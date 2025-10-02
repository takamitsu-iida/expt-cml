#!/bin/bash

# Windows Terminalを指定したペイン数で左右2分割して起動するスクリプト
# 使い方: ./open_terminal.sh <ペイン数>
# 例: ./open_terminal.sh 4

# 参考
# https://docs.microsoft.com/en-us/windows/terminal/command-line-arguments?tabs=windows

# 4分割の場合
#
# wt.exe \
#     \; split-pane -H --size 0.5 \
#     \; move-focus up \
#     \; split-pane -V --size 0.5 \
#     \; move-focus down \
#     \; split-pane -V --size 0.5

# ペインの総数を取得
N=$1

# ルータ番号を取得
START_ROUTER=$2

if [ -z "$N" ] || ! [[ "$N" =~ ^[0-9]+$ ]] || [ "$N" -lt 2 ]; then
    echo "エラー: 2以上のペインの数を引数として指定してください (例: ./equal_split_v3.sh 4)"
    exit 1
fi

if [ "$N" -gt 10 ]; then
    echo "エラー: ペインの最大数は10です。10以下の値を指定してください。"
    exit 1
fi

if [ -z "$START_ROUTER" ] || ! [[ "$START_ROUTER" =~ ^[0-9]+$ ]]; then
    echo "エラー: 2番目の引数として、最初のペインで使うルータ番号を指定してください (例: 1)。"
    exit 1
fi

# 左右の列のペイン数を計算
LEFT_COUNT=$(( (N + 1) / 2 ))  # 左側のペイン数 (切り上げ)
RIGHT_COUNT=$(( N / 2 ))       # 右側のペイン数 (切り捨て)

# 全ペインのポート番号を計算し、視覚的な順序で配列に格納する
declare -a PROFILE_NAMES

# R1, R2, ... のプロファイル名を配列に格納
for ((i=0; i<N; i++)); do
    PROFILE_NAMES[$i]="R$((START_ROUTER + i))"
done


# ---------------------------------
# 1. コマンドの組み立て
# ---------------------------------
COMMAND_STRING="wt.exe"

# --- Step 1: 左右に均等に2分割 ---
# 現在アクティブなペインを垂直に分割し、右側に新しいペインを作成
COMMAND_STRING="${COMMAND_STRING} split-pane -V --size 0.5 -p \"${PROFILE_NAMES[0]}\""

# --- Step 2: 左の列の上下分割（左上のペインにフォーカスがある状態） ---

# 左上のペインにフォーカスを移動（これが最小ポート番号のペイン）
COMMAND_STRING="${COMMAND_STRING} \; move-focus left"

# 左側で2番目以降のペインを水平 (上下) に均等分割
for ((i=2; i<=$LEFT_COUNT; i++)); do
    # 現在の残りのスペースに対して、新しいペインが必要な割合を計算
    REMAINING_PANES=$(( LEFT_COUNT - i + 2 ))
    SIZE_ARG=$(echo "scale=3; 1 / $REMAINING_PANES" | bc)
    PROFILE="${PROFILE_NAMES[$((i-1))]}"

    # 水平分割のコマンドを追加
    COMMAND_STRING="${COMMAND_STRING} \; split-pane -H --size ${SIZE_ARG} -p \"${PROFILE}\""

    # 分割後、フォーカスを新しく作成されたペインから上（次に分割すべきペイン）に移動
    if [ "$i" -lt "$LEFT_COUNT" ]; then
        COMMAND_STRING="${COMMAND_STRING} \; move-focus up"
    fi

done


# --- Step 3: 右の列の上下分割（右上のペインにフォーカスがある状態） ---
# 右上のペインにフォーカスを移動
COMMAND_STRING="${COMMAND_STRING} \; move-focus right"

# 右側で2番目以降のペインを水平 (上下) に均等分割
for ((i=2; i<=$RIGHT_COUNT; i++)); do
    # 現在の残りのスペースに対して、新しいペインが必要な割合を計算
    REMAINING_PANES=$(( RIGHT_COUNT - i + 2 ))
    SIZE_ARG=$(echo "scale=3; 1 / $REMAINING_PANES" | bc)
    PROFILE="${PROFILE_NAMES[$((LEFT_COUNT + i - 1))]}"

    # 水平分割のコマンドを追加
    COMMAND_STRING="${COMMAND_STRING} \; split-pane -H --size ${SIZE_ARG} -p \"${PROFILE}\""

    # 分割後、フォーカスを新しく作成されたペインから上（次に分割すべきペイン）に移動
    if [ "$i" -lt "$RIGHT_COUNT" ]; then
        COMMAND_STRING="${COMMAND_STRING} \; move-focus up"
    fi

done


# --- Step 4: 最終的なフォーカス移動 ---
# すべてのペイン作成後、左上のペインにフォーカスを移動
COMMAND_STRING="${COMMAND_STRING} \; move-focus first"

# --- Step 4: 実行 ---
echo "実行コマンド: ${COMMAND_STRING}"

# evalを使用して、セミコロンが正しくwt.exeの区切り文字として解釈されるように実行
eval "${COMMAND_STRING}"