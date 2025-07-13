#! /usr/bin/python3

import re
import subprocess
import argparse
from collections import defaultdict

LINE = "--------------------------------------------------------------------------------------"

def print_caption(caption : str):
    print(LINE)
    print(caption)
    print(LINE)

def create_options(n : int, break_mode):
    options = []
    var_index = 1
    for i in range(1, n-1):
        for j in range(1, 2*n-i):
            options.append([var_index,i, j, i+j+1])
            var_index += 1

    if break_mode == 0 and n > 1:
        for i in range(n-1, n+1):
            for j in range(1, 2*n-i):
                options.append([var_index, i, j, i+j+1])
                var_index += 1
    else:
        if n % 2 == 1 and n > 1:
            for j in range(1, n+1):
                options.append([var_index, n-1, j, n+j])
                var_index += 1
            for j in range(1, (n // 2) + 1):
                options.append([var_index, n, j, n+j+1])
                var_index += 1
        else:
            for j in range(1, (n // 2) + 1):
                options.append([var_index, n-1, j, n+j])
                var_index += 1
            for j in range(1, n):
                options.append([var_index, n, j, n+j+1])
                var_index += 1

    return options


def create_clause(options):
    clauses = []
    result = defaultdict(list)
    
    for item in options:
        key = item[1]
        value = item[0]
        result[key].append(value)
    
    d = dict(result)

    result = defaultdict(list)
    for option in options:
        idx0, _, idx2, idx3 = option
        result[idx2].append(idx0)
        result[idx3].append(idx0)
    s = dict(sorted(dict(result).items()))

    at_most_set = set()

    for d_i, values in d.items():
        for i in range(len(values)):
            for j in range(i+1,len(values)):
                #clauses.append(["not", f"x_{values[i]}", "or", "not", f"x_{values[j]}"])
                at_most_set.add((values[i], values[j]))
        clauses.append(sum([["x_" + str(v), "or"] for v in values], [])[:-1])

    for s_i, values in s.items():
        for i in range(len(values)):
            for j in range(i+1,len(values)):
                #clauses.append(["not", f"x_{values[i]}", "or", "not", f"x_{values[j]}"])
                at_most_set.add((values[i], values[j]))
        clauses.append(sum([["x_" + str(v), "or"] for v in values], [])[:-1])

    for at_most_clause in at_most_set:
        v1, v2 = at_most_clause
        clauses.append(["not", f"x_{v1}", "or", "not", f"x_{v2}"])

    groups = ["("+" ".join(clause) + ")"for clause in clauses]
    string_result = " and ".join(groups)
    return string_result, clauses
    

def create_cnf(options,clauses, file_name=None):
    if file_name is None:
        cnf_file = subprocess.run("mktemp",
                                  stdout=subprocess.PIPE,
                                  text=True).stdout.strip()
    else:
        cnf_file = file_name
    
    with open(cnf_file, "w") as f:
        num_clause = len(clauses)
        if num_clause == 0:
            num_clause = 1
        print(f"p cnf {len(options)} {num_clause}", file=f)
        sign = 1
        for clause in clauses:
            for e in clause:
                if e == "not":
                    sign = -1
                elif e == "or":
                    sign = 1
                else:
                    v = int(re.match("x_(\d+)", e).groups()[0])
                    print(sign*v, end=" ", file=f)
                    sign = 1
            print("0", file=f)
        if len(clauses) == 0:
            print("0", file=f)


    return cnf_file

def solve(cnf_file):
    process = subprocess.Popen(
        f"kissat {cnf_file}",
        stdout=subprocess.PIPE,
        shell=True,
        text=True
    )

    ans = ""
    ret = None
    while True:
        line = process.stdout.readline().strip()
        if line:
            print(line)
            s = re.match(r"s (.+)$",line) # kissatの出力 s SATISFIABLE を取り出す
            if s is not None:
                ret = s.group(1)
                continue
            v_tail = re.match(r"v (.+) 0$", line)
            if v_tail is not None:
                ans += v_tail.group(1)
                continue
            v = re.match(r"v (.+)$", line)
            if v is not None:
                ans += v.group(1) + " "
                continue
        else:
            if process.poll() is not None:
                break
    assignments = None
    if ret == "SATISFIABLE":
        assignments = [int(a) for a in ans.split()]
    return ret, assignments
    
def decode(assignments, options, n):
    ans = [0]*n*2
    for v in assignments:
        if v > 0:
            option = options[v-1]
            ans[option[2]-1] = option[1]
            ans[option[3]-1] = option[1]
    return ans


def main():
    parser = argparse.ArgumentParser(
        description="input : n, output : langford_pairs"
    )

    parser.add_argument(
        'n',
        type=int,
        help="intger n",
        metavar="N"
    )
    parser.add_argument(
        '--file', '-f',
        type=str,
        metavar="FILE_NAME_CREATED",
        help="create cnf"
    )
    parser.add_argument(
        '--symmetry', '-s',
        type=int,
        choices=[0, 1],
        default=0,
        help="0 : no symmetry break, 1 : symmetry break (default=0)"
    )

    parser.add_argument(
        '--model', '-m',
        type=int,
        default=1,
        help="0 : enumerate all solutions, 1 : enumerate single solution"
    )

    args = parser.parse_args()

    n = args.n
    break_mode = args.symmetry
    file_name = args.file
    options = sorted(create_options(n, break_mode))
    string_result, clauses = create_clause(options)
    cnf_file = create_cnf(options, clauses, file_name)

    print_caption("Clauses")
    print(string_result)
    ret = "SATISFIABLE"

    ans = []
    ret2 = "UNSATISFIABLE"
    if args.model == 0:
        while ret == "SATISFIABLE":
            ret,assignments = solve(cnf_file)
            if ret == "SATISFIABLE":
                ret2 = ret
            if assignments is not None:
                ans.append(decode(assignments, options, n))
                with open(cnf_file, 'r') as f:
                    lines = f.readlines()

                match = re.match(r"^p cnf (\d+) (\d+)", lines[0])
                if match:
                    num_vars = int(match.group(1))
                    num_clauses = int(match.group(2)) + 1
                    lines[0] = f"p cnf {num_vars} {num_clauses}\n"
                
                with open(cnf_file, "w") as f:
                    f.writelines(lines)

                with open(cnf_file, 'a') as f:
                    conflict = [-x for x in assignments]
                    if conflict[-1] == 0:
                        conflict.pop(-1)
                    #print("ああああああ",*conflict)
                    print(*conflict, 0, file=f)

    else:
        ret2, assignments = solve(cnf_file)
        if assignments is not None:
            ans.append(decode(assignments, options, n))

    print(f"variable  : {len(options):>6}")
    print(f"clause    : {len(clauses):>6}")
    print(f"Result : {ret2}")

    print("Answer :")
    print(*ans)

    
    if file_name is None:
        subprocess.run(
            f"[[ -f {cnf_file} ]] && rm -f {cnf_file}",
            shell=True
        )

if __name__ == '__main__':
    main()
