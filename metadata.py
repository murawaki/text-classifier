"""Collect metadata and output it to json

Requirements:
   pip install beautifulsoup4

"""

import sys
import os
import pathlib
import argparse
import bs4
import json
import datetime
import re
import unicodedata
from collections import defaultdict


COVID_PATTERNS = [re.compile(r'(新型)*コロナウ[イィ]ルス(感染症|肺炎)*'),
                  re.compile(r'COVID[-−]19感染症')]
DATE_PATTERN = re.compile(r'2020年([1-9]|1[0-2])月([1-9]|1[0-9]|2[0-9]|3[0-1])日')
SOURCES = [re.compile(r'[-−] Yahoo! JAPAN')]
TIME_PATTERNS = [re.compile(r'[<\(\[\{]第.+?回[>\)\]\}]'),
                 re.compile(r'第.+?回'),
                 re.compile(r'[<\(\[\{]令和.+?年度*[>\)\]\}]'),
                 re.compile(r'令和.+?年度*')]


def extract_url_from_url_file(filepath: pathlib.Path) -> str:
    with filepath.open() as f:
        return f.readline().strip()


def shorten(title):
    title = unicodedata.normalize("NFKC", title)  # 全角->半角(正規化)
    title = title.split('_')[0].split('|')[0]     # 特定の記号で繋がれるsuffixは除く
    title = title.replace('中華人民共和国', '中国')
    title = re.sub(DATE_PATTERN, r'\1月\2日', title)
    for pat in TIME_PATTERNS + SOURCES:
        title = re.sub(pat, '', title)
    for pat in COVID_PATTERNS:
        title = re.sub(pat, 'コロナ', title)
    return title.strip()


def extract_title_from_html_file(filepath: pathlib.Path) -> str:
    with filepath.open() as f:
        title = bs4.BeautifulSoup(f.read(), "html.parser").title.string
        return shorten(title)


def extract_timestamp_from_file(filepath: pathlib.Path) -> str:
    return datetime.datetime.fromtimestamp(os.path.getmtime(str(filepath))).isoformat()


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-d", "--directory", default=".", help="Path prefix of XML files")
    argparser.add_argument("url_files", help="File paths of input URL files (*.url; one path per line)")
    argparser.add_argument("output_file", help="Output file (JSONL)")
    args = argparser.parse_args()

    with open(args.url_files, "r") as f, open(args.output_file, "w") as of:
        for line in f:
            # decompose a url, which is like `./xml/<country>/ja_translated/<domain>/<filename>`, into its parts
            _, country, _, domain, *url_parts = pathlib.Path(line.strip()).parts
            url_filename = pathlib.Path(*url_parts)

            # list file paths
            data_dir = pathlib.Path(args.directory)
            url_filepath = data_dir / "html" / country / "orig" / domain / url_filename.with_suffix(".url")
            orig_filepath = data_dir / "html" / country / "orig" / domain / url_filename.with_suffix(".html")
            ja_filepath = data_dir / "html" / country / "ja_translated" / domain / url_filename.with_suffix(".html")
            xml_filepath = data_dir / "xml" / country / "ja_translated" / domain / url_filename.with_suffix(".xml")

            try:
                # extract metadata by reading the files
                orig_url = extract_url_from_url_file(url_filepath)

                orig_title = extract_title_from_html_file(orig_filepath)
                ja_title = extract_title_from_html_file(ja_filepath)

                orig_timestamp = extract_timestamp_from_file(orig_filepath)
                ja_timestamp = extract_timestamp_from_file(ja_filepath)
                xml_timestamp = extract_timestamp_from_file(xml_filepath)
            except:
                sys.stderr.write(f"file not found error...skip: {line}")
                continue

            # append the metadata
            meta = {
                "country": country,
                "orig": {
                    "file": str(orig_filepath.relative_to(data_dir)),
                    "title": orig_title,
                    "timestamp": orig_timestamp
                },
                "ja_translated": {
                    "file": str(ja_filepath.relative_to(data_dir)),
                    "title": ja_title,
                    "timestamp": ja_timestamp,
                    "xml_file": str(xml_filepath.relative_to(data_dir)),
                    "xml_timestamp": xml_timestamp
                },
                "url": orig_url,
                "domain": domain
            }
            
            # output the metadata as a JSONL file
            json.dump(meta, of, ensure_ascii=False)
            of.write("\n")
