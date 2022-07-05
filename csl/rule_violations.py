import csv

violations = {}

with open("output/colgate/csl_jun30/vlan700_spanning-0_coverage.csv", 'r') as coverage_csv:
    coverage_reader = csv.DictReader(coverage_csv)
    for line in coverage_reader:
        rows_not_covered = line["rows_not_covered"]
        if rows_not_covered and len(rows_not_covered.split(',')) < 10:
            for row in rows_not_covered.split(','):
                row = int(row)
                if row not in violations:
                    violations[row] = []
                violations[row].append(line["rule"])

with open("/shared/configs/colgate/daily/2022-03-06/csl_jun27/network.csv", 'r') as db_csv:
    db_reader = csv.DictReader(db_csv)
    line_num = 0
    for line in db_reader:
        if line_num in violations:
            print("{} violates {} rules".format(line["interface"], len(violations[line_num])))
            #for rule in violations[line_num]:
            #    print("\t{}".format(rule))
        line_num += 1

