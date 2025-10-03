#!/bin/bash

# 使い方: bin/open_terminal.sh R1 R2 R3 ...

# 引数が1つなら wt.exe -p 引数 を実行
# 引数が2つなら wt.exe -p "R1" ; split-pane -V --size 0.5 -p "R2"
# 引数が3つ以上なら必要な数を計算してペイン分割

# 参考
# https://docs.microsoft.com/en-us/windows/terminal/command-line-arguments?tabs=windows
#
# 4分割の場合
#
# wt.exe \
#     \; split-pane -H --size 0.5 \
#     \; move-focus up \
#     \; split-pane -V --size 0.5 \
#     \; move-focus down \
#     \; split-pane -V --size 0.5

if [ $# -lt 1 ]; then
    echo "Usage: $0 <PROFILE1> <PROFILE2> [PROFILE3 ...]"
    exit 1
fi

if [ $# -eq 1 ]; then
    wt.exe -p "$1"
    exit 0
fi

if [ $# -eq 2 ]; then
    wt.exe -p "$1" \; split-pane -V --size 0.5 -p "$2"
    exit 0
fi

#
# 以下、3個以上のペインを開く場合
#

# 必要なペインの総数を取得
N=$#

# 引数で渡されたプロファイル名を配列に格納
PROFILES=("$@")

# 左右の列のペイン数を計算
LEFT_COUNT=$(( (N + 1) / 2 ))  # 左側のペイン数 (切り上げ)
RIGHT_COUNT=$(( N / 2 ))       # 右側のペイン数 (切り捨て)

LEFT_LIST=()
for ((i=0; i<LEFT_COUNT; i++)); do
    LEFT_LIST[$i]="${PROFILES[$i]}"
done

RIGHT_LIST=()
for ((i=0; i<RIGHT_COUNT; i++)); do
    RIGHT_LIST[$i]="${PROFILES[$((LEFT_COUNT + i))]}"
done

# 最初のターミナルを左側の最初のプロファイルで開き、
COMMAND_STRING="wt.exe -p \"${LEFT_LIST[0]}\""

# 垂直分割で右側に右側の最初のプロファイルを開く
COMMAND_STRING="${COMMAND_STRING} \; split-pane -V --size 0.5 -p \"${RIGHT_LIST[0]}\""

# 左のペインにフォーカスを移動
COMMAND_STRING="${COMMAND_STRING} \; move-focus left"

# 左側で2番目以降のペインを水平 (上下) に均等分割
for ((i=1; i<$LEFT_COUNT; i++)); do
    # 現在の残りのスペースに対して、新しいペインが必要な割合を計算
    REMAINING_PANES=$(( LEFT_COUNT - i + 1 ))
    SIZE_ARG=$(echo "scale=3; 1 / $REMAINING_PANES" | bc)
    PROFILE="${LEFT_LIST[$i]}"

    # 水平分割のコマンドを追加
    COMMAND_STRING="${COMMAND_STRING} \; split-pane -H --size ${SIZE_ARG} -p \"${PROFILE}\""

    # 分割後、フォーカスを新しく作成されたペインから上（次に分割すべきペイン）に移動
    if [ "$i" -lt "$((LEFT_COUNT-1))" ]; then
        COMMAND_STRING="${COMMAND_STRING} \; move-focus up"
    fi
done

# 右上のペインにフォーカスを移動
COMMAND_STRING="${COMMAND_STRING} \; move-focus right"

# 右側で2番目以降のペインを水平 (上下) に均等分割
RIGHT_START_INDEX=$LEFT_COUNT
for ((i=1; i<$RIGHT_COUNT; i++)); do
    # 現在の残りのスペースに対して、新しいペインが必要な割合を計算
    REMAINING_PANES=$(( RIGHT_COUNT - i + 1 ))
    SIZE_ARG=$(echo "scale=3; 1 / $REMAINING_PANES" | bc)
    PROFILE="${RIGHT_LIST[$i]}"

    # 水平分割のコマンドを追加
    COMMAND_STRING="${COMMAND_STRING} \; split-pane -H --size ${SIZE_ARG} -p \"${PROFILE}\""

    # 分割後、フォーカスを新しく作成されたペインから上（次に分割すべきペイン）に移動
    if [ "$i" -lt "$((RIGHT_COUNT-1))" ]; then
        COMMAND_STRING="${COMMAND_STRING} \; move-focus up"
    fi
done

# すべてのペイン作成後、左上のペインにフォーカスを移動
COMMAND_STRING="${COMMAND_STRING} \; move-focus first"

# --- Step 4: 実行 ---

# デバッグ用
# echo "実行コマンド: ${COMMAND_STRING}"

# evalを使用して、セミコロンが正しくwt.exeの区切り文字として解釈されるように実行
eval "${COMMAND_STRING}"