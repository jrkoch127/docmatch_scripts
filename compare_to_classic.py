import sys
import argparse
import csv


def read_classic_results(classic, source):
    """

    :param classic:
    :return:
    """
    results = {}
    with open(classic, 'r') as fp:
        for line in fp.readlines():
            if len(line) > 1:
                columns = line[:-1].split('\t')
                if source == 'eprint':
                    results[columns[0]] = columns[1]
                elif source == 'pub':
                    results[columns[1]] = columns[0]
    return results

def read_nowadays_results(nowadays):
    """

    :param nowadays:
    :return:
    """
    results = []
    with open(nowadays, 'r') as fp:
        for line in fp.readlines():
             results.append(line[:-1].split('\t'))
    return results

def read_nowadays_results_audit(nowadays):
    """

    :param nowadays:
    :return:
    """
    results = []
    with open(nowadays, 'r') as fp:
        reader = csv.reader(fp, delimiter=',')
        next(reader)
        for columns in reader:
            results.append(columns)
    return results


def combine_classic_with_nowadays(classic_results, nowadays_results):
    """

    :param classic_results:
    :param nowadays_results:
    :return:
    """
    combined_results = []
    combined_results.append(['source bibcode (link)','classic bibcode (link)','curator comment','verified bibcode','matched bibcode (link)','comment','label','confidence','matched scores'])

    hyperlink_format = '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/%s/abstract"",""%s"")"'
    for nowadays_result in nowadays_results:
        if len(nowadays_result) == 1:
            continue
        # insert three columns: 'classic bibcode (link)','curator comment','verified bibcode' between the source and matched bibcode columns
        classic_bibcode = classic_results.get(nowadays_result[0], '')
        classic_bibcode_link = hyperlink_format % (classic_bibcode, classic_bibcode) if classic_bibcode else ''
        # need to format the two linked columns again
        source_bibcode_link = hyperlink_format % (nowadays_result[0], nowadays_result[0])
        matched_bibcode_link = hyperlink_format % (nowadays_result[1], nowadays_result[1]) if not nowadays_result[1][-21:-2].startswith('.') else ''
        combined_results.append([source_bibcode_link, classic_bibcode_link, '', '', matched_bibcode_link, '"%s"'%nowadays_result[5], nowadays_result[2], nowadays_result[3], '"%s"'%nowadays_result[4]])
    return combined_results

def combine_classic_with_nowadays_audit(classic_results, nowadays_results):
    """

    :param classic_results:
    :param nowadays_results:
    :return:
    """
    combined_results = []
    combined_results.append(['source bibcode (link)','classic bibcode (link)','curator comment','verified bibcode','matched bibcode (link)','comment','label','confidence','matched scores'])

    hyperlink_format = '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/%s/abstract"",""%s"")"'
    for nowadays_result in nowadays_results:
        # if there was an error in the csv file, transfer it and move on
        if len(nowadays_result) == 1:
            combined_results.append(nowadays_result)
            continue
        # insert two columns: 'classic bibcode (link)','curator comment' between the source and matched bibcode columns
        classic_bibcode = classic_results.get(nowadays_result[0][-21:-2], '')
        classic_bibcode_link = hyperlink_format % (classic_bibcode, classic_bibcode) if classic_bibcode else ''
        # need to format the two linked columns again
        source_bibcode_link = '"%s"'%nowadays_result[0].replace('"','""')
        matched_bibcode_link = '"%s"'%nowadays_result[2].replace('"','""') if not nowadays_result[2][-21:-2].startswith('.') else ''
        combined_results.append([source_bibcode_link, classic_bibcode_link, '', '', matched_bibcode_link, '"%s"'%nowadays_result[6], nowadays_result[3], nowadays_result[4], '"%s"'%nowadays_result[5]])
    return combined_results

def write_output(combined_results, filename):
    """

    :param combined_results:
    :param filename:
    :return:
    """
    with open(filename, 'w') as fp:
        fp.write(','.join(combined_results[0]) + '\n')
        # error lines are one element that have no confidence column
        combined_results = sorted(combined_results[1:], key=lambda result: float(result[7]) if len(result) > 7 else -1)
        for combined_result in combined_results:
            # error lines are one element, include them
            if len(combined_result) == 1:
                fp.write(','.join(combined_result) + '\n')
            # include only the lines with classic bibcode, or matched bibcode
            elif len(combined_result[1]) > 0 or len(combined_result[4]) > 0:
                # if there is a classic match see if it agrees or disagrees with oracle
                if len(combined_result[1]) > 0:
                    combined_result[2] = 'agree' if combined_result[1] == combined_result[4] else 'disagree'
                # if there is a multi match and confidence is high
                # or if there was no abstract for comparison and confidence is high
                # mark it to be verified
                elif (len(combined_result) >= 8 and float(combined_result[7]) >= 0.5 and
                          (('None' in combined_result[8]) or ('Multi match' in combined_result[5]))):
                    combined_result[2] = 'verify'
                fp.write(','.join(combined_result)+'\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combine results with classic')
    parser.add_argument('-c', '--classic', help='the path to an output results file from classic.')
    parser.add_argument('-n', '--nowadays', help='the path to a output results file from docmatching.')
    parser.add_argument('-a', '--nowadays_audit', help='the path to a output cav results file from docmatching for audit.')
    parser.add_argument('-o', '--output', help='the output file name to write the combined results, else the result shall be written to console.')
    parser.add_argument('-s', '--source', help='specify if source is eprint or pub')
    args = parser.parse_args()
    if args.source:
        if args.source not in ['eprint', 'pub']:
            print('source file type not specified, either eprint or pub should be included')
            sys.exit(1)
    if args.classic and args.nowadays:
        classic_results = read_classic_results(args.classic, args.source)
        nowadays_results = read_nowadays_results(args.nowadays)
        if classic_results and nowadays_results:
            combined_results = combine_classic_with_nowadays(classic_results, nowadays_results)
    elif args.classic and args.nowadays_audit:
        classic_results = read_classic_results(args.classic, args.source)
        nowadays_results = read_nowadays_results_audit(args.nowadays_audit)
        if classic_results and nowadays_results:
            combined_results = combine_classic_with_nowadays_audit(classic_results, nowadays_results)
    else:
        print('not all input parameters was included, either classic and nowadays or classic and nowadays_audit is needed')
        sys.exit(1)

    if combined_results:
        if args.output:
            write_output(combined_results, args.output)
        else:
            for combined_result in combined_results:
                print('\t'.join(combined_result))
    sys.exit(0)
