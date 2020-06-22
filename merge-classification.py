"""Classify new texts into pre-defined classes"""

import logging
import argparse
import sys
import json

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
    argparser.add_argument("meta", help="metadata/text JSONL)")
    argparser.add_argument("classified", help="classification result (JSONL)")
    args = argparser.parse_args()    

    with open(args.meta, "r") as input_file:
        with open(args.classified, "r") as classified_file:
            for l1, l2 in zip(input_file, classified_file):
                page = json.loads(l1)
                classified = json.loads(l2)
                if "classes" in page:
                    page["classes_kwd"] = page["classes"]
                page["classes_bert"] = classified["classes"]
                page["classes"] = {}
                for k, v in classified["classes"].items():
                    page["classes"][k] = 1 if v >= 0.5 else 0
                sys.stdout.write("{}\n".format(json.dumps(page, ensure_ascii=False)))

if __name__ == "__main__":
    main()
