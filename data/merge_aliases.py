import sys
import unicodecsv


def merge_aliases(file_a, file_b, file_out):
    aliases = {}
    with open(file_a, 'rb') as fh:
        for row in unicodecsv.DictReader(fh):
            aliases[row.get('alias')] = row
    with open(file_b, 'rb') as fh:
        for row in unicodecsv.DictReader(fh):
            alias = row.get('alias')
            ex = aliases.get(alias)
            if ex is None:
                aliases[alias] = row
                continue
            if row.get('canonical') == alias:
                continue
            aliases[alias] = row

    with open(file_out, 'wb') as fh:
        keys = set()
        for v in aliases.values():
            keys.update(v.keys())
        writer = unicodecsv.DictWriter(fh, keys)
        writer.writeheader()
        for alias in sorted(aliases.keys()):
            row = aliases.get(alias)
            writer.writerow(row)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print 'Usage: python merge.py FILE_A FILE_B OUT_FILE'
        sys.exit(1)
    file_a = sys.argv[1]
    file_b = sys.argv[2]
    file_out = sys.argv[3]
    merge_aliases(file_a, file_b, file_out)
