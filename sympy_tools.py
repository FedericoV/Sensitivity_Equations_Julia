import os
import sys
import cPickle as pickle

from collections import OrderedDict
from sympy import *
import imp


def _process_chunk(chunk, sympify_rhs=False):
    symbols_dict = OrderedDict()

    for line in chunk:
        line = line.replace(" ", "")  # Spaces
        line = line.replace("\t", "")  # Tabs

        if line.startswith("#") or line == "":
            continue

        lhs = line[:line.find("=")]
        rhs = line[line.find("=")+1:]
        if not sympify_rhs:
            symbols_dict[lhs] = Symbol(lhs)
        else:
            symbols_dict[lhs] = sympify(rhs)

    return symbols_dict


def parse_model_file(model_fh):
    model_text = model_fh.read()

    categories = {'Parameters': False, 'Variables': False,
                  'Conservation Laws': True, 'Rate Laws': True,
                  'Differential Equations': True}

    parsed_model_dict = {}

    for category, sympify_rhs in categories.items():
        start_idx = model_text.find("#*! %s Start" % category)
        end_idx = model_text.find("#*! %s End" % category)

        chunk = model_text[start_idx:end_idx].split('\n')
        symbols_dict = _process_chunk(chunk, sympify_rhs)

        parsed_model_dict[category] = symbols_dict

    bound_start_idx = model_text.find("#*! Bound Arguments Start")
    bound_end_idx = model_text.find("#*! Bound Arguments End")
    bound_args = model_text[bound_start_idx:bound_end_idx].split("\n")
    parsed_model_dict["Bound Arguments"] = bound_args
    return parsed_model_dict


def write_model(variables, diff_eqns, bound_args, output_fh, sens_eqns=None,
                model_name="sensitivity_model"):
    lines = []
    pad = "    "
    dpad = pad + pad

    lines.append("def make_bound_model(*args):")

    for line in bound_args:
        lines.append(line)
    lines.append("\n")

    lines.append(pad + "def %s(y, t):" % model_name)

    lines.append("\n")
    lines.append(dpad + "#---------------------------------------------------------#")
    lines.append(dpad + "#Variables#")
    lines.append(dpad + "#---------------------------------------------------------#\n")
    for idx, var in enumerate(variables):
        lines.append(dpad + "%s = y[%d]" % (var, idx))

    if sens_eqns is not None:
        lines.append("\n")
        lines.append(dpad + "#---------------------------------------------------------#")
        lines.append(dpad + "#sensitivity Variables#")
        lines.append(dpad + "#---------------------------------------------------------#\n")
        total_vars = len(variables)
        for idx, var in enumerate(sens_eqns.keys()):
            lines.append(dpad + "%s = y[%d]" % (var, idx + total_vars))

    lines.append("\n")
    lines.append(dpad + "#---------------------------------------------------------#")
    lines.append(dpad + "#Differential Equations#")
    lines.append(dpad + "#---------------------------------------------------------#\n")

    return_vars = []
    for var, eqn in diff_eqns.items():
        lines.append(dpad + "d%s = (%s)" %(var, eqn))
        return_vars.append("d%s" %var)

    if sens_eqns is not None:
        lines.append("\n")
        lines.append(dpad + "#---------------------------------------------------------#")
        lines.append(dpad + "#sensitivity Equations#")
        lines.append(dpad + "#---------------------------------------------------------#\n")

        for var, eqn in sens_eqns.items():
            lines.append(dpad + "d_%s = (%s)" % (var, eqn))
            return_vars.append("d_%s" % var)

    lines.append("\n")
    lines.append(dpad + "return (%s)" % (", ".join(return_vars)))

    lines.append("\n")
    lines.append(pad + "return %s" % model_name)

    for line in lines:
        output_fh.write(line + "\n")


def make_sensitivity_model(model_fh, sens_model_fh, ordered_params=None,
                           calculate_sensitivities=True):
    model_dict = parse_model_file(model_fh)
    model_fh.close()

    eqns = model_dict['Differential Equations']
    rate_laws = model_dict['Rate Laws']
    cons_laws = model_dict['Conservation Laws']
    variables = model_dict['Variables']
    bound_args = model_dict['Bound Arguments']

    if ordered_params is None:
        parameters = model_dict['Parameters']
    else:
        parameters = ordered_params

    expanded_eqns = OrderedDict()
    for d_var, eqn in eqns.items():
        expanded_eqns[d_var[1:]] = eqn.subs(rate_laws).subs(cons_laws)

    if calculate_sensitivities:

        sens_eqns = OrderedDict()
        for var_i, f_i in expanded_eqns.items():
            for par_j in parameters.keys():
                dsens = diff(f_i, par_j)
                for var_k in expanded_eqns.keys():
                    sens_kj = Symbol('sens%s_%s' % (var_k, par_j))
                    dsens += diff(f_i, var_k)*sens_kj

                sens_eqns['sens%s_%s' % (var_i, par_j)] = simplify(dsens)
    else:
        sens_eqns = None

    write_model(variables, expanded_eqns, bound_args, sens_model_fh,
                sens_eqns)

    if ordered_params is None:
        return parameters.keys()


if __name__ == "__main__":

    fp = sys.argv[0]
    cur_dir = os.path.join(os.path.dirname(fp))
    model_fh = open(os.path.join(cur_dir, 'simple_model.py'))
    model_output_fh = open(os.path.join(cur_dir, 'simple_model_sens.py'), 'w')

    make_sensitivity_model(model_fh, model_output_fh)
