
# called by crond @ jungle3
# 42 * * * * /mnt/berry/home/murawaki/tmp/covid/text-classifier/crawl_update.sh

. /home/murawaki/.zshenv
cd "$(dirname "$0")";
make -j -f crawl_update.make all PYTNON=/mnt/orange/ubrew/data/bin/python3
