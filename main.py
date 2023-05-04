HEADERS: str = "#include <stdio.h>\n#include <stdlib.h>\n#include <stdarg.h>\n#include <math.h>\n#include <time.h>\n"
LOOKUP: dict = {
    "type" : "typedef",
    "ptr" : "*",
    "::" : "->",
    "->" : "{",
    "end": "}",
    "object" : "typedef struct",
    "$" : "free",
    "@" : "malloc",
    "deref": "*",
    "ref" : "&"
}
BOILERPLATE: str = """
// [--------------------------------- START OF BOILERPLATE ---------------------------------]
typedef char* string;
typedef unsigned int uint;
typedef void* T;
typedef T(*let)(T, ...);
typedef struct Vec3 {
    T x;
    T y;
    T z;
} vec3;
typedef struct Point {
    int x;
    int y;
} point;
typedef struct Node {
    struct Node *next;
    T data;
} node;
typedef uint bool;
#define false 0
#define true !false
#define null NULL
bool toBoolean(T val) {
    if ((int)val == 0) {
        return false;
    }
    return true;
}

// [--------------------------------- END OF BOILERPLATE ---------------------------------]
"""


def repl_special(line: str, char: str) -> str:
    # The allocator and free keywords must be expanded to their respective function calls
    # This requires inserting the necessary parentheses in the c source
    # This is done by finding the index of the keyword, then finding the index of the next semicolon
    if char == "@":
        i: int = line.index(char)
        j: int = line.index(";", i)
        line = line.replace("@" + line[i+1:j], "malloc(" + line[i+1:j] + ")")
    elif char == "$":
        i: int = line.index(char)
        j: int = line.index(";", i)
        line = line.replace("$" + line[i+1:j], "free(" + line[i+1:j] + ")")
    return line

def convert_file(path: str) -> str:
    # CURRENTLY UNUSED
    # Converts a file to c source, line by line
    file_content: str = ""
    with open(path, "r") as input_file:
        for line in input_file.readlines():
            file_content += convert_line(line)
    return file_content

def convert_import(path: str) -> str:
    # Converts an import statement to c source and inserts it
    # at the start of the file
    # BE VERY WARNED THAT THIS WILL CAUSE NAME COLLISIONS
    file_content: str = "// --------------------------------- [START OF {}] ---------------------------------\n".format(path)
    with open(path, "r") as input:
        line: str = "//////////////"
        while line != "":
            line = input.readline()
            file_content += convert_line(line)
    file_content += "\n// --------------------------------- [END OF {}] ---------------------------------\n".format(path)
    return file_content

def smart_repl_keyword(line: str) -> str:
    # Replaces keywords with their c equivalents
    # Ensures that the keyword is not part of a larger word
    ALPHANUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    for key in LOOKUP.keys():
        i = 0
        while i < 20: # Inefficient as absolute fuck but here we go, hacking it
            if key in line:
                if key == "::": # Always simply replace this since it never naturally occurs
                    line = line.replace(key, LOOKUP[key])
                    continue
                if key == "@" or key == "$": # Special chars need to be replaced differently
                    line = repl_special(line, key)
                    continue
                # Key indices
                key_startIndex = line.index(key)
                key_endIndex = key_startIndex + len(key)
                if key == "end": # End is special as it often occurs at the very end of the line
                        line[key_endIndex-1] == "d"
                        line = line.replace(key, LOOKUP[key], 1)
                if key_endIndex < len(line): # ONLY replace if not part of a word
                    if line[key_startIndex-1] not in ALPHANUM and line[key_endIndex] not in ALPHANUM:
                        line = line.replace(key, LOOKUP[key], 1)
            i += 1
    return line

def convert_line(line: str) -> str:
    # Converts a single line of code to c source
    # This is done by replacing keywords with their c equivalents
    # Also reads and converts import files
    towrite: str = line
    if line.startswith("#import"):
        # IF we are importing a file, we need to convert it to c source
        # and insert it at the start of the file
        # grabs the path and converts it to c source
        path_start: int = line.index("<")
        path_end: int = line.index(">", path_start)
        return convert_import(line[path_start+1:path_end])
    i = 0
    j = 0
    if "\"" in line:
        # We dont want to do replacements in strings
        # So we break up any line that has one, and converts each side independently
        for i in range(len(line)):
            if line[i] == "\"":
                for j in range(len(line)):
                    if line[j] == "\"" and j != i:
                        before: str = smart_repl_keyword(line[0:i])
                        after: str = smart_repl_keyword(line[j+1:-1])
                        string: str = line[i:j+1]
                        towrite = before + string + after + "\n"
                        break
                break
    else:
        towrite = smart_repl_keyword(towrite)
    return towrite

import os
def lazy_convert(infile: str, outexec: str, flags: str) -> None:
    # Converts a file to c source, line by line
    # Starts by initializing a c file with the necessary headers and boilerplate
    global HEADERS, BOILERPLATE
    OUTFILE: str = "TEMPORARY_INTERMEDIATE.c"
    with open(infile, "r+") as input:
        line: str = "//////////////" # arbitrary string that is not empty
        with open(OUTFILE, "w") as out:
            out.write(HEADERS)
            out.write(BOILERPLATE)
        # Ignore comments completely
        IN_BLOCKCOMMENT: bool = False
        while line != "":
            line = input.readline()
            copy: str = line
            copy = copy.lstrip()
            towrite: str = ""
            if copy.startswith("//"):
                continue
            if IN_BLOCKCOMMENT and not copy.startswith("*/"):
                continue
            elif IN_BLOCKCOMMENT and copy.startswith("*/"):
                IN_BLOCKCOMMENT = False
                continue
            if copy.startswith("/*"):
                IN_BLOCKCOMMENT = True
                continue
            # Convert the line and write it to the output file
            towrite = convert_line(line)
            with open(OUTFILE, "a") as out:
                out.write(towrite)
    # Compile the output file with gcc and remove the source file unless --p is specified
    if "." in outexec:
        outexec = outexec.split(".")[0]
    preserve_source: bool = False
    if "--p" in flags:
        preserve_source = True
        flags = flags.replace("--p", "")
    print(flags)
    COMPILER: str = "gcc {} -o {} -O2 -Wall {}".format(OUTFILE, outexec, flags)
    os.system(COMPILER)
    if not preserve_source:
        os.remove(OUTFILE)
    print ("[Z--] compiled to {}.exe".format(outexec))

import sys
if __name__ == "__main__":
    if (sys.argv[1] in ["--help", "-h"]):
        print("usage: zc [SOURCE.zs] [EXEC NAME]")
        print("flags:")
        print("--p: preserve source")
        exit()
    if (len(sys.argv) < 3):
        print("usage: zc [SOURCE] [DEST]")
        exit()
    infile: str = sys.argv[1]
    if ".zs" not in infile:
        infile = infile + ".zs"
    outname: str = sys.argv[2]
    flags: str = " ".join(sys.argv[3:])
    lazy_convert(infile, outname, flags)