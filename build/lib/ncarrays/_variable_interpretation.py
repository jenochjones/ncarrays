import netCDF4


def _determine_variable_types(variables, variable_type_lists):    
    X_STANDARD_NAMES = ['longitude','grid_longitude','projection_x_coordinate', 'projection_x_angular_coordinate']
    Y_STANDARD_NAMES = ['latitude', 'grid_latitude', 'projection_y_coordinate', 'projection_y_angular_coordinate']
    Z_STANDARD_NAMES = ['height', 'altitude']
    X_UNITS = ['degrees_east', 'degree_east', 'degree_E', 'degrees_E', 'degreeE', 'degreesE']
    Y_UNITS = ['degrees_north', 'degree_north', 'degree_N', 'degrees_N', 'degreeN', 'degreesN']
    
    for dimension in variable_type_lists['dimensions']:
        if hasattr(variables[dimension]['dataset'], 'axis'):
            if variables[dimension]['dataset'].axis == 'X':
                variables[dimension]['datatype'] = 'X'
            elif variables[dimension]['dataset'].axis == 'Y':
                variables[dimension]['datatype'] = 'Y'
            elif variables[dimension]['dataset'].axis == 'Z':
                variables[dimension]['datatype'] = 'Z'
            elif variables[dimension]['dataset'].axis == 'T':
                variables[dimension]['datatype'] = 'T'
            else:
                variables[dimension]['datatype'] = 'O'
        elif hasattr(variables[dimension]['dataset'], 'standard_name'):
            if variables[dimension]['dataset'].standard_name in X_STANDARD_NAMES:
                variables[dimension]['datatype'] = 'X'
            elif variables[dimension]['dataset'].standard_name in Y_STANDARD_NAMES:
                variables[dimension]['datatype'] = 'Y'
            elif variables[dimension]['dataset'].standard_name in Z_STANDARD_NAMES:
                variables[dimension]['datatype'] = 'Z'
            elif variables[dimension]['dataset'].standard_name == 'time':
                variables[dimension]['datatype'] = 'T'
            else:
                variables[dimension]['datatype'] = 'O'
        elif hasattr(variables[dimension]['dataset'], 'units'):
            if variables[dimension]['dataset'].units in X_UNITS:
                variables[dimension]['datatype'] = 'X'
            elif variables[dimension]['dataset'].units in Y_UNITS:
                variables[dimension]['datatype'] = 'Y'
            elif 'since' in variables[dimension]['dataset'].units:
                variables[dimension]['datatype'] = 'T'
            else:
                variables[dimension]['datatype'] = 'O'
    
    return variables


def _retrieve_sub_variables(opendap_url, main_variable):
    
    def add_variables_to_url(partial_url, variable):
        partial_url += variable + ','
        return partial_url
    
    other_variables = {
        'dimensions': [],
        'coordinates': [],
        'ancillary_variables': [],
        'grid_mapping': None,
        'scale_factor': None,
        'add_offset': None
        }
    
    opendap_url += '?'
    
    for dimension in main_variable.dimensions:
        other_variables['dimensions'].append(dimension)
        opendap_url = add_variables_to_url(opendap_url, dimension)
    
    if hasattr(main_variable, 'coordinates'):
        coordinate_list = _split_string_to_list(main_variable.coordinates)
        
        for coordinate in coordinate_list:
            other_variables['coordinates'].append(coordinate)
            if coordinate not in other_variables['dimensions']:
                if coordinate != '':
                    opendap_url = add_variables_to_url(opendap_url, coordinate)

    if hasattr(main_variable, 'ancillary_variables'):
        ancillary_variables = _split_string_to_list(main_variable.ancillary_variables)
        
        for ancillary_variable in ancillary_variables:
            other_variables['ancillary_variables'].append(ancillary_variable)
            if ancillary_variable not in other_variables['dimensions']:
                if ancillary_variable != '':
                    opendap_url = add_variables_to_url(opendap_url, ancillary_variable)
        
    if hasattr(main_variable, 'grid_mapping'):
        other_variables['grid_mapping'] = main_variable.grid_mapping
        if main_variable.grid_mapping != '':
            opendap_url = add_variables_to_url(opendap_url, main_variable.grid_mapping)
        
    if hasattr(main_variable, 'scale_factor'):
        other_variables['scale_factor'] = main_variable.scale_factor
        
    if hasattr(main_variable, 'add_offset'):
        other_variables['add_offset'] = main_variable.add_offset
        
    opendap_url = opendap_url[:-1]
    
    sub_dataset = netCDF4.Dataset(opendap_url)
    
    variable_dict = {}
    
    for variable in sub_dataset.variables:
        variable_dict[variable] = {'dataset': sub_dataset.variables[variable]}
    
    return variable_dict, other_variables


def _split_string_to_list(string):
    if ',' in string:
        new_list = string.split(',')
    else:
        new_list = string.split(' ')
    return new_list
