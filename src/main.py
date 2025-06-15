from tree_sitter_languages import get_parser

parser = get_parser("c")
code = b"""
int add(int a, int b) {
    return a + b;
}
"""

tree = parser.parse(code)
root_node = tree.root_node

def extract_functions(node):
    if node.type == "function_definition":
        # 함수 이름 추출
        identifier = node.child_by_field_name("declarator") \
                         .child_by_field_name("declarator")
        func_name = code[identifier.start_byte:identifier.end_byte].decode()
        print(f"함수 이름: {func_name}")
        print(f"  위치: 줄 {node.start_point[0]+1} ~ {node.end_point[0]+1}")
        print("--- 함수 코드 ---")
        print(code[node.start_byte:node.end_byte].decode())
        print()
    for child in node.children:
        extract_functions(child)

extract_functions(root_node)