import argparse
import asyncio
import json
import sys
from pathlib import Path

import scraper.utils
from bson.json_util import dumps

def _save_mongo(result):
    import scraper.db_utils
    scraper.db_utils.save_scraped(result)
    print("→ saved in the database.")

def _save_json(result, directive_path):
    out_dir = Path(__file__).resolve().parent.parent / "output"
    out_dir.mkdir(exist_ok=True)
    name = Path(directive_path).stem
    out_file = out_dir / f"{name}.json"
    out_file.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"→ saved in: {out_file}")

def run_scrape(directive_path: str, dest: str):
    path = Path(directive_path)
    root = Path(__file__).resolve().parent.parent
    if not path.is_absolute():
        path = root / directive_path
    if not path.exists():
        path = root / "scraper" / "directives" / path.name
    if not path.exists():
        print(f"directive not found: {directive_path}", file=sys.stderr)
        sys.exit(1)
    result = asyncio.run(scraper.utils.grab_elements_by_directive(str(path)))
    print(json.dumps(result, indent=2, default=str))
    if dest == "mongo":
        _save_mongo(result)
    else:
        _save_json(result, directive_path)

def update(name, part):
    import scraper.db_utils
    import scraper.logger
    res = scraper.db_utils.get_elements_by_part(name, part)
    data = json.loads(dumps(res))
    scraper.logger.log(f"Updating {name} {part}")
    scraper.utils.parse_coin_to_csv(data)
    return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run scrape from a directive YAML.")
    parser.add_argument("directive", help="Path to the directive (ex: directives/wikipedia.yaml)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--mongo", action="store_true", help="Save in the database")
    group.add_argument("--json", action="store_true", help="Save in output/<name>.json")
    args = parser.parse_args()
    dest = "mongo" if args.mongo else "json"
    run_scrape(args.directive, dest)
