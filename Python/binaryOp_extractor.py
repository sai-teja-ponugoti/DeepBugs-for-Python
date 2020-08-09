# This example demonstrates usage of the included Python grammars
# !pip install lark-parser
import sys
import os, os.path
from io import open
import glob, time
from lark import Lark
from lark.indenter import Indenter
from lark import tree
import json
import re
from io import BytesIO
import tokenize
from tokenize import tok_name
import keyword

allBinaryOps = []


class PythonIndenter(Indenter):
    NL_type = '_NEWLINE'
    OPEN_PAREN_types = ['LPAR', 'LSQB', 'LBRACE']
    CLOSE_PAREN_types = ['RPAR', 'RSQB', 'RBRACE']
    INDENT_type = '_INDENT'
    DEDENT_type = '_DEDENT'
    tab_len = 8


kwargs = dict(rel_to=__file__, postlex=PythonIndenter(), start='file_input')
python_parser2 = Lark.open('python2.lark', parser='lalr', propagate_positions=True, **kwargs)
python_parser3 = Lark.open('python3.lark', parser='lalr', propagate_positions=True, **kwargs)
python_parser2_earley = Lark.open('python2.lark', parser='earley', lexer='standard', propagate_positions=True, **kwargs)

try:
    xrange
except NameError:
    chosen_parser = python_parser3
else:
    chosen_parser = python_parser2


def _read(fn, *args):
    kwargs = {'encoding': 'iso-8859-1'}
    with open(fn, *args, **kwargs) as f:
        return f.read()


def tokenize_py(file_path):
    all_token_text_list = []
    python_key_words = []
    count = 0
    tokens_dict = {}
    list_of_tokens = []
    with tokenize.open(file_path) as f:
        tokens = tokenize.generate_tokens(f.readline)
        for token in tokens:
            if tok_name[token.type] == "NAME":
                if token.string not in ['True', 'False', 'Null', 'None'] and token.string not in keyword.kwlist:
                    # list_of_tokens.append("ID:" + token.string)
                    tokens_dict[token.string] = "ID"
                    # string_of_tokens.append()
                elif token.string in ['True', 'False', 'Null', 'None']:
                    # list_of_tokens.append("LIT:" + token.string)
                    tokens_dict[token.string] = "LIT"
                elif token.string in keyword.kwlist:
                    # list_of_tokens.append("STD:" + token.string)
                    tokens_dict[token.string] = "STD"
            elif tok_name[token.type] in ["NUMBER", "STRING"]:
                # list_of_tokens += "LIT:" + token.string + "$%#~"
                # list_of_tokens.append("LIT:" + token.string)
                tokens_dict[token.string] = "LIT"

            else:
                if token.string == '\n':
                    # list_of_tokens.append(r"STD:\n")
                    tokens_dict[r"\n"] = "STD"
                elif tok_name[token.type] == "INDENT":
                    # list_of_tokens.append(r"STD:\t")
                    tokens_dict[r"\t"] = "STD"
                elif tok_name[token.type] == "DEDENT":
                    # list_of_tokens.append(r"STD:DEDENT")
                    tokens_dict["DEDENT"] = "STD"
                elif tok_name[token.type] == "ENDMARKER":
                    # list_of_tokens.append(r"STD:ENDMARKER")
                    tokens_dict["ENDMARKER"] = "STD"
                else:
                    # list_of_tokens.append("STD:" + token.string)
                    tokens_dict[token.string] = "STD"

    # print(len(tokens_dict))
    return tokens_dict


def test_python_lib():
    with open(r'/home/sai/Desktop/653/NBG/DataSets/py150_files/python50k_eval.txt', encoding="utf8") as f:
        content = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    content = [x.rstrip() for x in content]
    count = 0
    error_count = 0
    for sub_file_path in content:
        file_path = r'/home/sai/Desktop/653/NBG/DataSets/py150_files/' + sub_file_path
        # c = "/home/sai/Desktop/653/NBG/DataSets/py150_files/data/HenryHu/pybbs/digest.py"
        try:
            dict_tokens = {}
            tokens = chosen_parser.parse(_read(file_path) + '\n')
            dict_tokens = tokenize_py(file_path)
        except:
            # print("error occured for file :", file_path)
            error_count += 1

        print_node_recursively(tokens, sub_file_path, dict_tokens)
        count += 1
        print("finished :", str(count))

        break
        # if count > 150000:
        #     break
    with open('BinaryOps.json', 'w', encoding='utf-8') as f:
        json.dump(allBinaryOps, f, separators=(',', ': '), ensure_ascii=False, indent=4)
    print(len(allBinaryOps))
    print("error files count :", str(error_count))


# def print_non_tree_node(node):
#     if not isinstance(node, tree.Tree):
#         return node
#     else:
#         return print_non_tree_node(node.children[0])


def print_non_tree_node(node):
    if not isinstance(node, tree.Tree):
        return node
    else:
        return "unknown"


def print_node_recursively(node, sub_file_path, dict_tokens):
    if isinstance(node, tree.Tree):
        for child in node.children:
            if isinstance(child, tree.Tree):
                for chil in child.children:
                    if isinstance(chil, tree.Tree):
                        if chil.data == "comparison" or chil.data == "term" or chil.data == "star_expr" or chil.data == \
                                "xor_expr" or chil.data == "and_expr" or chil.data == \
                                "shift_expr" or chil.data == "arith_expr":
                            ops = {}
                            try:
                                # print("printing node type :",chil.data)
                                # print("\"left\": ",chil.children[0].children[0])
                                # print("\"right\": ", chil.children[2].children[0])
                                # print("\"op\":", chil.children[1])
                                # print("\"leftType\":",chil.children[0].data )
                                # print("\"rightType\":", chil.children[2].data)
                                # print("\"parent\"",child.data)
                                # print("\"grandParent\":", node.data)
                                # print("\"src\":"+c+" in line - " + str(chil.meta.line))
                                left = dict_tokens.get(chil.children[0].children[0], "unknown")
                                right = dict_tokens.get(print_non_tree_node(chil.children[2].children[0]), "unknown")
                                if left != "unknown" and right != "unknown":
                                    ops["left"] = left + ":" + print_non_tree_node(chil.children[0].children[0])
                                    ops["right"] = right + ":" + print_non_tree_node(chil.children[2].children[0])
                                    ops["op"] = print_non_tree_node(chil.children[1])
                                    ops["leftType"] = chil.children[0].data
                                    ops["rightType"] = chil.children[2].data
                                    ops["parent"] = child.data
                                    ops["grandParent"] = node.data
                                    ops["src"] = sub_file_path + " : " + str(chil.line) + " - " + str(chil.end_line)
                                    allBinaryOps.append(ops)
                            except:
                                # print("error occured for file :", c)
                                pass

            print_node_recursively(child, sub_file_path, dict_tokens)


if __name__ == '__main__':
    test_python_lib()
