#!/usr/local/bin/zsh
# called by crond @ jungle3
# 42 * * * * /mnt/berry/home/murawaki/tmp/covid/text-classifier-bert/crawl_update.sh

cd "$(dirname "$0")";

. $HOME/.zshrc
source /mnt/orange/ubrew/brew.zsh

# make -j -f crawl_update.make all PYTHON=/mnt/orange/ubrew/data/bin/python3
# make -j -f crawl_update.make metas metas PYTHON="/home/murawaki/.local/bin/pipenv run python3"
make -f crawl_update.make all PYTHON="/home/murawaki/.local/bin/pipenv run python3" GPUID=0 > cron.log 2>&1
