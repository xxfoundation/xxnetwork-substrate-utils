"""
dump_all_balances.py - dumps all wallet addresses and their current token counts

Usage:
  python3 dump_all_balances.py [websocket port to connect with]

Example:
  python3 dump_all_balances.py ws://localhost:63007 > output.csv

You may need to pip install substrate-interface and click for this script to
work.

"""

import sys
import csv
import click
from substrateinterface import SubstrateInterface

@click.command(help='Dump all balances for a substrate blockchain')
@click.option('--output', '-o', type=click.File('wb'), default=sys.stdout,
              help='Optional output file')
@click.argument("url", default="ws://localhost:63007")
def main(url, output):
    substrate = SubstrateInterface(url=url)
    account_len = 0
    result = substrate.query_map('System', 'Account', page_size=200,
                                 max_results=400)
    out = csv.writer(output, delimiter=',')
    headers = False
    out.writerow(["account id", "free balance"])
    for account, account_info in result:
        if not headers:
            r = ["account id"]
            r.extend(account_info.value['data'].keys())
            out.writerow(r)

        r = [f"{account.value}"]
        r.extend(account_info.value['data'].values())
        out.writerow(r)
        account_len += 1

    print(f"{account_len} accounts", file=sys.stderr)


if __name__ == '__main__':
    main()
