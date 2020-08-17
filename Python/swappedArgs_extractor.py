import sys
import os, os.path
from io import open
import glob, time
from lark import Lark
from lark.indenter import Indenter
from lark import tree
import json
import tokenize
from tokenize import tok_name
import keyword

functionDefDict = {}

allCalls = []
# __path__ = os.path.dirname(__file__)
class PythonIndenter(Indenter):
    NL_type = '_NEWLINE'
    OPEN_PAREN_types = ['LPAR', 'LSQB', 'LBRACE']
    CLOSE_PAREN_types = ['RPAR', 'RSQB', 'RBRACE']
    INDENT_type = '_INDENT'
    DEDENT_type = '_DEDENT'
    tab_len = 8

kwargs = dict(rel_to =__file__, postlex=PythonIndenter(), start='file_input')
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

def _get_lib_path():
    if os.name == 'nt':
        if 'PyPy' in sys.version:
            return os.path.join(sys.prefix, 'lib-python', sys.winver)
        else:
            return os.path.join(sys.prefix, 'Lib')
    else:
        return [x for x in sys.path if x.endswith('%s.%s' % sys.version_info[:2])][0]

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
                    tokens_dict[token.string] = "ID:"
                    # string_of_tokens.append()
                elif token.string in ['True', 'False', 'Null', 'None']:
                    # list_of_tokens += "LIT:" + token.string + "$%#~"
                    # list_of_tokens.append("LIT:" + token.string)
                    tokens_dict[token.string] = "LIT:"
                elif token.string in keyword.kwlist:
                    # list_of_tokens += "STD:" + token.string + "$%#~"
                    # list_of_tokens.append("STD:" + token.string)
                    tokens_dict[token.string] = "STD:"
            elif tok_name[token.type] in ["NUMBER", "STRING"]:
                # list_of_tokens += "LIT:" + token.string + "$%#~"
                # list_of_tokens.append("LIT:" + token.string)
                tokens_dict[token.string] = "LIT:"

            else:
                if token.string == '\n':
                    # list_of_tokens.append(r"STD:\n")
                    tokens_dict[r"\n"] = "STD:"
                elif tok_name[token.type] == "INDENT":
                    # list_of_tokens.append(r"STD:\t")
                    tokens_dict[r"\t"] = "STD:"
                elif tok_name[token.type] == "DEDENT":
                    # list_of_tokens.append(r"STD:DEDENT")
                    tokens_dict["DEDENT"] = "STD:"
                elif tok_name[token.type] == "ENDMARKER":
                    # list_of_tokens.append(r"STD:ENDMARKER")
                    tokens_dict["ENDMARKER"] = "STD:"
                else:
                    # list_of_tokens.append("STD:" + token.string)
                    tokens_dict[token.string] = "STD:"
    return tokens_dict

def functionDef(node, fileName, dict_tokens):
    for child in node.children:
        if isinstance(child, tree.Tree):
            try:
                if child.data == "funcdef":
                    if int(len(child.children[1].children)) > 1:
                        argument1 = dict_tokens.get(print_non_tree_node(child.children[1].children[0]), "unknown")
                        argument2 = dict_tokens.get(print_non_tree_node(child.children[1].children[1]), "unknown")
                        callee = dict_tokens.get(child.children[0], "unknown")
                        if argument1 != "unknown" and argument2 != "unknown" and callee != "unknown":
                            functionDefDict[ callee + child.children[0]] = [argument1 + print_non_tree_node(child.children[1].children[0]), argument2 + print_non_tree_node(child.children[1].children[1])]
                            print("Funcdef name : ", callee + child.children[0])
                            print("Funcdef argument1 : ", argument1 + print_non_tree_node(child.children[1].children[0]))
                            print("Funcdef argument2 : ", argument2 + print_non_tree_node(child.children[1].children[1]))
            except:
                print("error occured in functionDef for file :", fileName)
            functionDef(child, fileName, dict_tokens)

def findfunctionDefParams(key):
    if key in functionDefDict:
        return functionDefDict[key]
    else:
        return["",""]

def checkArgument(child):
    if child.data == 'const_none':
        argument = "None"
    elif child.data == 'const_false':
        argument = "False"
    elif child.data == 'const_true':
        argument = "True"
    else:
        argument = print_non_tree_node(child.children[0])
    return argument

def functionCall(node,fileName, dict_tokens):
    for child in node.children:
        if isinstance(child, tree.Tree):
            try:
                if child.data == "funccall":
                    call = {}
                    if child.children[0].data == 'getattr':
                        if child.children[0].children.__len__() == 2 and int(len(child.children)) == 2 \
                                and isinstance(child.children[1], tree.Tree) and child.children[1].children.__len__() == 2:
                            callee_type = dict_tokens.get(print_non_tree_node(child.children[0].children[1]), "unknown")
                            base_type = dict_tokens.get(print_non_tree_node(child.children[0].children[0].children[0]),
                                                        "unknown")


                            # if print_non_tree_node(child.children[0].children[1]) == "get":
                            #     print("error ")
                            argument1 = checkArgument(child.children[1].children[0])
                            argument2 = checkArgument(child.children[1].children[1])

                            argument1_type = dict_tokens.get(argument1, "unknown")
                            argument2_type = dict_tokens.get(argument2, "unknown")


                            if argument1_type != "unknown" and argument2_type != "unknown" and callee_type != "unknown" and base_type != "unknown":

                                print("Funccall base calle : ",
                                      base_type + print_non_tree_node(child.children[0].children[0].children[0]))
                                print("Funccall func name : ",
                                      callee_type + print_non_tree_node(child.children[0].children[1]))
                                print("Funccall base calle : ", base_type + print_non_tree_node(child.children[0].children[0].children[0]))
                                print("Funccall func name : ", callee_type + print_non_tree_node(child.children[0].children[1]))
                                print("Funccall argument1 : ", argument1_type + argument1)
                                print("Funccall argument1 type : ", child.children[1].children[0].data)
                                print("Funccall argument2 : ", argument2_type + argument2)
                                print("Funccall argument2 type : ", child.children[1].children[1].data)


                                call["base"] = base_type + print_non_tree_node(child.children[0].children[0].children[0])
                                call["callee"] = callee_type + print_non_tree_node(child.children[0].children[1])
                                call["calleeLocation"] = 0
                                call["arguments"] = [argument1_type + argument1, argument2_type + argument2]
                                call["argumentLocations"] = [0,0]
                                call["argumentTypes"] = [child.children[1].children[0].data, child.children[1].children[1].data]
                                call["parameters"] = findfunctionDefParams(child.children[0].children[1])
                                call["src"] = fileName + " : " +  str(child.line) + " - " + str(child.end_line)
                                call["filename"] = fileName
                                allCalls.append(call)

                    elif int(len(child.children)) == 2:
                        if int(len(child.children[1].children)) == 2:

                            argument1 = checkArgument(child.children[1].children[0])
                            argument2 = checkArgument(child.children[1].children[1])

                            argument1_type = dict_tokens.get(argument1, "unknown")
                            argument2_type = dict_tokens.get(argument2, "unknown")
                            callee_type = dict_tokens.get(child.children[0].children[0], "unknown")
                            if argument1_type != "unknown" and argument2_type != "unknown" and callee_type != "unknown":
                                print("Funccall base calle : unknown")
                                print("Funccall name : ", callee_type + print_non_tree_node(child.children[0].children[0]))
                                print("Funccall argument1 : ", argument1_type + argument1)
                                print("Funccall argument1 type : ", child.children[1].children[0].data)
                                print("Funccall argument2 : ", argument2_type + argument2)
                                print("Funccall argument2 type : ", child.children[1].children[1].data)

                                call["base"] = ""
                                call["callee"] = callee_type + print_non_tree_node(child.children[0].children[0])
                                call["calleeLocation"] = 0
                                call["arguments"] = [argument1_type + argument1, argument2_type + argument2]
                                call["argumentLocations"] = [0, 0]
                                call["argumentTypes"] = [child.children[1].children[0].data, child.children[1].children[1].data]
                                call["parameters"] = findfunctionDefParams(child.children[0].children[0])
                                call["src"] = fileName + " : " +  str(child.line) + " - " + str(child.end_line)
                                call["filename"] = fileName
                                allCalls.append(call)
            except:
                print("error occured in functionCall for file :", fileName)
            functionCall(child, fileName, dict_tokens)



def test_python_lib():
    # start = time.time()
    with open(r'D:\UWaterloo\SPRING2020\ECE653\project\py150_files\python100k_train.txt', encoding="utf8") as f:
        content = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    content = [x.rstrip() for x in content]
    count = 0
    error_count = 0
    for c in content:
        fullPath = r'D:/UWaterloo/SPRING2020/ECE653/project/py150_files/' + c
        try:
            dict_tokens = {}
            t = chosen_parser.parse(_read(fullPath) + '\n')
            print(fullPath)
            dict_tokens = tokenize_py(fullPath)
            # print_node_recursively(t)

        except:
            print("error occured for file :", c)
            error_count += 1
        functionDef(t, c, dict_tokens)
        functionCall(t, c, dict_tokens)

        # count += 1
        # if count == 50:
        #     break
    print("function definitions : ", functionDefDict)
    print("function calls : ", allCalls)
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(allCalls, f, separators=(',', ':'), ensure_ascii=False, indent=4)
    print(len(allCalls))
    print("error files count :", str(error_count))
    # print(chosen_parser)
    # t = chosen_parser.parse(_read(r"D:/UWaterloo/SPRING2020/ECE653/project/py150_files/data/HenryHu/pybbs/digest.py") + '\n')



def print_non_tree_node(node):
    if not isinstance(node,tree.Tree):
        return node
    else:
        return "unknown"

def print_node_recursively(node):
    for child in node.children:
        if isinstance(child, tree.Tree):

            if child.data == "funccall":
                if child.children[0].data == 'getattr':
                    if child.children[0].children.__len__() == 2 and int(len(child.children)) == 2:
                        print("Funccall base calle : ", print_non_tree_node(child.children[0].children[0].children[0]))

                        print("Funccall func name : ", print_non_tree_node(child.children[0].children[1]))



                        if isinstance(child.children[1], tree.Tree) and int(len(child.children[1].children)) == 2:
                            print("Funccall argument1 : ", print_non_tree_node(child.children[1].children[0].children[0]))
                            print("Funccall argument1 type : ", child.children[1].children[0].data)
                            print("Funccall argument2 : ", print_non_tree_node(child.children[1].children[1].children[0]))
                            print("Funccall argument2 type : ", child.children[1].children[1].data)
                        # else :
                        #     print("Funccall argument1 : Null")
                        #     print("Funccall argument1 type : Null")
                        #     print("Funccall argument2 : Null")
                        #     print("Funccall argument2 type : Null")
                elif int(len(child.children)) == 2:
                    if int(len(child.children[1].children)) == 2:
                        print("Funccall base calle : unknown")
                        print("Funccall name : ", child.children[0].children[0])
                        print("Funccall argument1 : ", print_non_tree_node(child.children[1].children[0].children[0]))
                        print("Funccall argument1 type : ", child.children[1].children[0].data)
                        print("Funccall argument2 : ", print_non_tree_node(child.children[1].children[1].children[0]))
                        print("Funccall argument2 type : ", child.children[1].children[1].data)
            elif child.data == "funcdef":
                if int(len(child.children[1].children)) >1:
                    print("Funcdef name : ", child.children[0])
                    print("Funcdef argument1 : ", print_non_tree_node(child.children[1].children[0]))
                    print("Funcdef argument2 : ", print_non_tree_node(child.children[1].children[1]))
            print_node_recursively(child)





def test_earley_equals_lalr():
    path = _get_lib_path()
    files = glob.glob(path + '/*.py')
    for f in files:
        print(f)
        tree1 = python_parser2.parse(_read(os.path.join(path, f)) + '\n')
        tree2 = python_parser2_earley.parse(_read(os.path.join(path, f)) + '\n')
        assert tree1 == tree2

if __name__ == '__main__':
    test_python_lib()
