def make_bound_model(*args):
#*! Bound Arguments Start
    param_idx = args[0]
    conditions = args[1]
    param_vector = args[2]

#*! Parameters Start
    k_deg = param_vector[param_idx['k_deg']]
    k_synt = param_vector[param_idx['k_synt']]
#*! Parameters End



    def sensitivity_model(y, t):


        #---------------------------------------------------------#
        #Variables#
        #---------------------------------------------------------#

        _y = y[0]


        #---------------------------------------------------------#
        #sensitivity Variables#
        #---------------------------------------------------------#

        sens_y_k_deg = y[1]
        sens_y_k_synt = y[2]


        #---------------------------------------------------------#
        #Differential Equations#
        #---------------------------------------------------------#

        d_y = (-_y*k_deg + k_synt)


        #---------------------------------------------------------#
        #sensitivity Equations#
        #---------------------------------------------------------#

        d_sens_y_k_deg = (-_y - k_deg*sens_y_k_deg)
        d_sens_y_k_synt = (-k_deg*sens_y_k_synt + 1)


        return (d_y, d_sens_y_k_deg, d_sens_y_k_synt)


    return sensitivity_model
