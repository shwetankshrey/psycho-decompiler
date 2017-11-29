from utill import *

"""
    Think about blocks and visibility 
    association with r7,#4 and variables 
"""


class Function(object):
    def __init__(self, name, start_line_text, start_line_no, end_line_text, end_line_no):
        self.name = name
        self.start_line_text = start_line_text
        self.end_line_text = end_line_text
        self.start_line_no = start_line_no
        self.end_line_no = end_line_no
        self.parameters = []
        self.parameters_type = []
        self.parameters_line_no = []
        self.return_ = []
        self.return_type = []
        self.return_line_no = []
        self.callers_line_no = []


# stuff to which values are assigned
def getRHS(lines, f, before=False):
    rhs = dict()
    for i in range(f.start_line_no + 1, f.end_line_no):
        opcode = getOpcode(lines[i])
        if "ldr" in opcode:
            if not getArgs(lines[i])[0] in rhs.keys() or before:
                rhs[getArgs(lines[i])[0]] = i
        elif "mov" in opcode:
            if not getArgs(lines[i])[0] in rhs.keys() or before:
                rhs[getArgs(lines[i])[0]] = i
        elif not "str" in opcode:
            try:
                if not getArgs(lines[i])[0] in rhs.keys() or before:
                    rhs[getArgs(lines[i])[0]] = i
            except Exception:
                pass
    return rhs


def getFunctions(filename):
    global getLoopsAndIfs
    file = open(filename)
    lines = dict()
    i = 0

    while True:
        line = file.readline().strip().lower()
        if line is '':
            break
        # if not (line.startswith("@") or line.startswith(".")):
        #     lines[i] = line
        # else:
        #     i = i - 1
        lines[i] = line
        i += 1

    # function detection can be done in the following ways:
    # label -> push -> sub, sp, sp #? -> add r7, sp, 0
    # or
    # label -> sub, sp, sp #? -> add r7, sp, 0
    #
    # end withs adds r7, r7,  #? -> mov sp, r7
    # and maybe ldr r7, [sp], #4 -> bx	lr

    functions = []

    for i in range(len(lines.keys())):
        if isLabel(lines[i]):
            if getOpcode(lines[i + 1]) == "push" and getOpcode(lines[i + 2]) == "sub":
                x = getArgs(lines[i + 2])
                print("start @" + lines[i])
                j = i
                for j in range(i, len(lines.keys())):
                    if getOpcode(lines[j]) == "adds":
                        y = getArgs(lines[j])
                        if x[2] == y[2]:
                            print("ends @" + lines[j + 1])
                            break
                functions.append(Function(
                    name=lines[i].replace(":", ""), start_line_text=lines[i + 1], start_line_no=i + 1,
                    end_line_text=lines[j + 2], end_line_no=j + 2
                ))
            pass

    for f in functions:
        """
                finding parameters of each function
        """
        rhs = getRHS(lines, f)

        for i in range(f.start_line_no, f.end_line_no):

            opcode = getOpcode(lines[i])

            """
                ASSUMPTION: each argument of a function is first used with "str" or "mov"
                int are usually stored with mov
                while str for other type of data
                
            """

            if "str" in opcode:

                """
                    This is too check if the  parameter/register 
                    has been used before this line in function.
                    
                    z = a
                    to filter "a" which hasn't been initialised before
                """
                if getArgs(lines[i])[0] in rhs.keys():
                    if rhs[getArgs(lines[i])[0]] >= i:
                        pass
                    else:
                        break

                f.parameters.append(getArgs(lines[i])[0])
                if opcode == "vstr.32":
                    f.parameters_type.append("float")
                elif opcode == "strb":
                    f.parameters_type.append("char")
                elif opcode == "vstr.64":
                    f.parameters_type.append("double")
                elif opcode == "str":
                    f.parameters_type.append("int")
            elif "mov" in opcode:
                """
                    This is too check if the  parameter/register 
                    has been used before this line in function.

                    z = a
                    to filter "a" which hasn't been initialised before
                """

                if getArgs(lines[i])[0] in rhs.keys():
                    if rhs[getArgs(lines[i])[0]] >= i:
                        pass
                    else:
                        break

                f.parameters.append(getArgs(lines[i])[1])
                f.parameters_type.append("int")

    """
        Callers 
    """
    for i in range(len(lines.keys())):
        if "bl" in lines[i]:
            label = getArgs(lines[i])[0].split("(")[0]

            for f in functions:
                if f.name == label:
                    f.callers_line_no.append(i)

    for f in functions:
        """
                finding return type of each function
        """

        for i in range(f.end_line_no, f.start_line_no, -1):

            if len(f.return_) > 0 or isBranching(lines[i]):
                break

            opcode = getOpcode(lines[i])

            """
                ASSUMPTION: return type of a function is last used with "str" or "mov"
            """

            if "ldr" in opcode:

                if not getArgs(lines[i])[0].endswith("0"):
                    continue

                f.return_.append(getArgs(lines[i])[0])
                f.return_line_no.append(i)

                if opcode == "vldr.32":
                    f.return_type.append("float")
                elif opcode == "ldrb":
                    f.return_type.append("char")
                elif opcode == "vldr.64":
                    f.return_type.append("double")
                elif opcode == "ldr":
                    f.return_type.append("int")

            elif "mov" in opcode:

                if not getArgs(lines[i])[0].endswith("0"):
                    continue

                f.return_.append(getArgs(lines[i])[0])
                if "f32" in opcode:
                    f.return_type.append("float")
                elif "f64" in opcode:
                    f.return_type.append("double")
                elif "b" in opcode:
                    f.return_type.append("char")
                else:
                    # TODO Detect char
                    f.return_type.append("int")

        print(f.return_atype)

    # from DetectingLoops import *
    # loops, ifelses, ifs = getLoopsAndIfs(filename)
    # thingsToConsider = []

    for f in functions:

        if len(f.return_type) == 0:
            final_str = "void"
        else:
            final_str = f.return_type[0]

        final_str = final_str + " " + f.name + " ( "
        for i in range(len(f.parameters_type)):
            if not i == 0:
                final_str = final_str + ", "
            final_str = final_str + f.parameters_type[i] + " " + f.parameters[i]

        final_str = final_str + " ) { \n"

        for i in range(f.start_line_no + 1, f.end_line_no):
            """
                Very weird assumption:
                do not consider
            """
            if not ("sp" in lines[i] or "push" in lines[i] or "pop" in lines[i] or "adds" in lines[i] or "nop" in lines[
                i]):
                final_str = final_str + lines[i] + "\n"

        if len(f.return_) == 0:
            final_str = final_str + "return;"
        else:
            final_str = final_str + "return " + f.return_[0]

        final_str = final_str + "\n}"

        print(final_str)

    return functions


if __name__ == "__main__":
    getFunctions("examples/chars.s")
