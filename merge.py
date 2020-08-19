"""Classify new texts into pre-defined classes"""

import logging
import argparse
import unicodedata
import json
import re
import os
import sys
from collections import defaultdict

logger = logging.getLogger(__name__)

def read_keywords(keyword_file):
    keywords = {}
    for line in keyword_file:
        clss, *words = line.strip().split()
        keywords[clss] = [unicodedata.normalize("NFKC", k) for k in words]
    return keywords

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(levelname)s: %(message)s')

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-b", "--blacklist", help="List of URLs")
    argparser.add_argument("-k", "--keep-going", dest="keep_going", default=False, action="store_true")
    argparser.add_argument("-o", "--output", help="Output file (JSON)")
    argparser.add_argument("inputs", nargs="+", help="Input files (JSON)")
    args = argparser.parse_args()    

    with open(args.blacklist, "r") as f:
        bad_urls = read_keywords(f)

    path2date = {}
    date_re = re.compile("(\d\d\d\d-\d\d-\d\d-\d\d-\d\d)")
    for fpath in args.inputs:
        matched = date_re.search(fpath)
        if matched is not None:
            path2date[fpath] = matched.group(1)
        else:
            exit(1)
        
    registered = {}
    num_bad_urls = 0
    with open(args.output, "w") as of:
        for fp in sorted(args.inputs, key=lambda x: path2date[x], reverse=True):
            if not os.path.isfile(fp) and args.keep_going:
                sys.stderr.write("{} not found ... skip\n".format(fp))
                continue
            try:
                with open(fp, "r") as input_file:
                    logger.info("Processing: %s", fp)
                    for line in input_file:
                        line = line.strip()
                        page = json.loads(line)
                        if page["url"] in registered:
                            continue
                        registered[page["url"]] = True

                        # dump matching
                        # TODO: efficiency
                        bad_url = False
                        for keyword in bad_urls:
                            if re.search(keyword, page["url"]):
                                sys.stderr.write("blacklisted\t{}\tskip\n".format(page["url"]))
                                bad_url = True
                                break
                        if bad_url:
                            num_bad_urls += 1
                            continue

                        # output the results into JSONL file
                        of.write("{}\n".format(json.dumps(page, ensure_ascii=False)))
            except Exception as e:
                sys.stderr.write("JSON error {}".format(e))

    logger.info("Files: %s", len(args.inputs))
    logger.info("Duplicate: %s", len(registered))
    logger.info("Bad URLs: %s", num_bad_urls)

if __name__ == "__main__":
    main()
