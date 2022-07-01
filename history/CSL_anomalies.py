import argparse
import os
import sys
import csv

graphs_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.dirname(graphs_dir))
import get_rule_coverage

def main():

    parser = argparse.ArgumentParser(description='Get anomalies from a set of CSL rules')
    parser.add_argument('db_path',type=str, help='Path for a CSV file containing the pruned dataframe')
    parser.add_argument('rules_path',type=str, help='Path for a CSV file which stores the rules')
    parser.add_argument('out_path',type=str, help='Path for a CSV file which stores anomalies')
    arguments = parser.parse_args()

    rules_df = get_rule_coverage.main(arguments.db_path, arguments.rules_path)
   
    rules_df.drop(["coverage","rule_coverage"], axis=1, inplace=True)
    rules_df.to_csv(arguments.out_path,index=False)

    violations = {}

    for index, rule in rules_df.iterrows():
        rows_not_covered = rule["rows_not_covered"]
        if rows_not_covered and len(rows_not_covered.split(',')) < 10:
            for row in rows_not_covered.split(','):
                row = int(row)
                if row not in violations:
                    violations[row] = []
                violations[row].append((rule["rule"], rule["consequent"]))

    with open(arguments.db_path, 'r') as db_csv:
        db_reader = csv.DictReader(db_csv)
        line_num = 0
        for line in db_reader:
            if line_num in violations:
                print("{} violates {} rules".format(line["date"], len(violations[line_num])))
                for rule in violations[line_num]:
                    print("\t{}".format(rule))
            line_num += 1


if __name__ == "__main__":
    #doctest.testmod()
    main()