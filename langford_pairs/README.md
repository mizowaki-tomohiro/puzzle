# Langford pairs

`langford.py` は 与えられた自然数 n から
langford pairs が満たすべき制約を DIMACS CNF式
で記述し，SAT ソルバー *kissat* に制約を与えて
問題を解くスクリプトです．  
プログラムの実行には *kissat* を実行できるようにしておく必要があります．

入力 : 自然数 n  
出力 : SAT or UNSAT（SATの場合は解も出力）

実行例（n=3） : `./langford.py 3`